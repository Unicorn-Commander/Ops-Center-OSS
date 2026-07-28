"""
Federation Pipeline System

Define and execute multi-step inference workflows that chain services across
federation nodes. Each step routes through the InferenceRouter to find the
best backend.

Example pipeline:
    pipeline = Pipeline(
        name="music-production",
        steps=[
            PipelineStep(
                name="write-lyrics",
                service_type="llm",
                model="qwen3.5-27b",
                input_template={"messages": [{"role": "user", "content": "Write lyrics about {topic} in {genre} style"}]},
                output_key="lyrics"
            ),
            PipelineStep(
                name="generate-music",
                service_type="music_gen",
                input_template={"params": {"lyrics": "{lyrics}", "tags": "{genre}", "duration": 60}},
                output_key="audio_job_id",
                wait_for_completion=True  # poll job status
            ),
            PipelineStep(
                name="generate-artwork",
                service_type="image_gen",
                input_template={"title": "{topic}", "genre": "{genre}", "mood": "epic"},
                output_key="artwork_job_id",
                parallel_with="generate-music"  # run alongside music gen
            ),
            PipelineStep(
                name="transcribe-audio",
                service_type="stt",
                input_from="generate-music",  # uses output of generate-music step
                output_key="transcription",
                depends_on=["generate-music"]
            )
        ]
    )
"""


import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("federation.pipelines")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class StepStatus(Enum):
    """Status of an individual pipeline step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    """A single step in a pipeline.

    Attributes:
        name:               Unique step identifier within the pipeline.
        service_type:       Federation service type to route to
                            (llm, tts, stt, embeddings, image_gen, music_gen, reranker).
        model:              Optional model identifier (e.g. "qwen3.5-27b").
        input_template:     Dict with ``{variable}`` placeholders resolved at runtime.
        input_from:         Use the output of another step verbatim as input.
        output_key:         Key under which this step's result is stored in the
                            shared variable namespace.
        depends_on:         Steps that must complete before this one starts.
        parallel_with:      Name of another step to run concurrently with.
        wait_for_completion: If *True* the executor will poll ``poll_endpoint``
                            until the job finishes (for async services like
                            music or image generation).
        poll_endpoint:      Endpoint to poll for async job status.
        poll_interval:      Seconds between polls.
        timeout:            Maximum seconds to wait for this step.
        constraints:        Extra routing constraints forwarded to InferenceRouter.
        on_failure:         ``"stop"`` to abort the pipeline, ``"skip"`` to mark
                            the step skipped and continue, ``"retry"`` to retry.
        max_retries:        How many times to retry on failure (0 = no retries).
    """

    name: str
    service_type: str
    model: Optional[str] = None
    input_template: Optional[Dict[str, Any]] = None
    input_from: Optional[str] = None
    output_key: str = "result"
    depends_on: List[str] = field(default_factory=list)
    parallel_with: Optional[str] = None
    wait_for_completion: bool = False
    poll_endpoint: Optional[str] = None
    poll_interval: int = 5
    timeout: int = 300
    constraints: Optional[Dict[str, Any]] = None
    on_failure: str = "stop"
    max_retries: int = 1


@dataclass
class Pipeline:
    """A multi-step inference workflow definition.

    Pipelines are *templates* — they carry default variable values but can be
    overridden at execution time.
    """

    name: str
    description: str = ""
    steps: List[PipelineStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "variables": self.variables,
            "created_by": self.created_by,
            "steps": [
                {
                    "name": s.name,
                    "service_type": s.service_type,
                    "model": s.model,
                    "input_template": s.input_template,
                    "input_from": s.input_from,
                    "output_key": s.output_key,
                    "depends_on": s.depends_on,
                    "parallel_with": s.parallel_with,
                    "wait_for_completion": s.wait_for_completion,
                    "poll_endpoint": s.poll_endpoint,
                    "poll_interval": s.poll_interval,
                    "timeout": s.timeout,
                    "constraints": s.constraints,
                    "on_failure": s.on_failure,
                    "max_retries": s.max_retries,
                }
                for s in self.steps
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pipeline":
        """Reconstruct a *Pipeline* from a plain dict (e.g. JSON body)."""
        steps = [
            PipelineStep(**step_data)
            for step_data in data.get("steps", [])
        ]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            variables=data.get("variables", {}),
            created_by=data.get("created_by"),
        )


# ---------------------------------------------------------------------------
# Execution engine
# ---------------------------------------------------------------------------


class PipelineExecution:
    """Executes a pipeline, tracking state across steps.

    The executor resolves ``{variable}`` placeholders in step input templates
    using a shared variable namespace that grows as steps complete.  Steps
    with ``parallel_with`` annotations are grouped and awaited concurrently.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        inference_router: Any,
        variables: Optional[Dict[str, Any]] = None,
    ):
        self.pipeline = pipeline
        self.router = inference_router
        self.execution_id = str(uuid.uuid4())

        # Merge caller-supplied variables over pipeline defaults.
        self.variables: Dict[str, Any] = {**pipeline.variables, **(variables or {})}

        self.step_results: Dict[str, Any] = {}
        self.step_status: Dict[str, StepStatus] = {
            s.name: StepStatus.PENDING for s in pipeline.steps
        }

        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.status: str = "pending"
        self.error: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(self) -> Dict[str, Any]:
        """Run all pipeline steps and return an execution summary."""
        self.started_at = time.time()
        self.status = "running"
        logger.info(
            "Pipeline '%s' started (execution_id=%s)",
            self.pipeline.name,
            self.execution_id,
        )

        try:
            executed: set[str] = set()

            while len(executed) < len(self.pipeline.steps):
                # Gather steps whose dependencies have all completed.
                ready: List[PipelineStep] = []
                for step in self.pipeline.steps:
                    if step.name in executed:
                        continue
                    if all(dep in executed for dep in step.depends_on):
                        ready.append(step)

                if not ready:
                    raise RuntimeError(
                        "Pipeline deadlock: no steps are ready but "
                        f"{len(self.pipeline.steps) - len(executed)} remain"
                    )

                # Group ready steps that should run concurrently.
                parallel_groups = self._group_parallel(ready)

                for group in parallel_groups:
                    if len(group) == 1:
                        await self._execute_step(group[0])
                    else:
                        await asyncio.gather(
                            *(self._execute_step(s) for s in group)
                        )

                    for step in group:
                        executed.add(step.name)

                        if (
                            self.step_status[step.name] == StepStatus.FAILED
                            and step.on_failure == "stop"
                        ):
                            err_detail = (
                                self.step_results.get(step.name, {}).get("error")
                            )
                            raise RuntimeError(
                                f"Step '{step.name}' failed: {err_detail}"
                            )

            self.status = "completed"

        except Exception as exc:
            self.status = "failed"
            self.error = str(exc)
            logger.error("Pipeline '%s' failed: %s", self.pipeline.name, exc)

        self.completed_at = time.time()

        return self._build_summary()

    def get_status(self) -> Dict[str, Any]:
        """Return current execution status (useful while the pipeline is running)."""
        return self._build_summary()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _execute_step(self, step: PipelineStep) -> None:
        """Execute a single pipeline step with optional retries."""
        self.step_status[step.name] = StepStatus.RUNNING
        logger.info(
            "Step '%s' starting (service=%s, model=%s)",
            step.name,
            step.service_type,
            step.model,
        )

        retries = 0
        while retries <= step.max_retries:
            try:
                # 1. Build input by resolving templates / forwarding outputs.
                input_data = self._resolve_input(step)

                # 2. Route to best backend via InferenceRouter.
                route_request: Dict[str, Any] = {
                    "service_type": step.service_type,
                    "priority": "cost",
                }
                if step.model:
                    route_request["model"] = step.model
                if step.constraints:
                    route_request["constraints"] = step.constraints

                route = await self.router.route(route_request)

                # 3. Execute the request.
                result: Dict[str, Any] = {
                    "route": route,
                    "input": input_data,
                    "routed_to": route.get("target", "unknown"),
                    "endpoint": route.get("endpoint_url", ""),
                }

                # If the router supports proxying to a peer, use it.
                if (
                    hasattr(self.router, "proxy_to_node")
                    and route.get("target") == "peer"
                ):
                    endpoint_path = (
                        (step.input_template or {}).get("endpoint_path")
                        or route.get("endpoint_path", "")
                    )
                    result = await self.router.proxy_to_node(
                        route["node_id"],
                        endpoint_path,
                        input_data,
                    )

                # 4. If this is an async service, poll until completion.
                if step.wait_for_completion and step.poll_endpoint:
                    result = await self._poll_for_completion(step, result)

                # 5. Store result and make it available as a variable.
                self.step_results[step.name] = result
                self.variables[step.output_key] = result
                self.step_status[step.name] = StepStatus.COMPLETED
                logger.info("Step '%s' completed", step.name)
                return

            except Exception as exc:  # noqa: BLE001
                retries += 1
                if retries > step.max_retries:
                    self.step_status[step.name] = StepStatus.FAILED
                    self.step_results[step.name] = {"error": str(exc)}
                    if step.on_failure == "skip":
                        logger.warning(
                            "Step '%s' failed, skipping: %s", step.name, exc
                        )
                        self.step_status[step.name] = StepStatus.SKIPPED
                    else:
                        logger.error(
                            "Step '%s' failed after %d retries: %s",
                            step.name,
                            retries,
                            exc,
                        )
                    return
                logger.warning(
                    "Step '%s' retry %d/%d: %s",
                    step.name,
                    retries,
                    step.max_retries,
                    exc,
                )

    async def _poll_for_completion(
        self, step: PipelineStep, initial_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Poll an async service until it reports completion or timeout."""
        deadline = time.time() + step.timeout
        result = initial_result

        while time.time() < deadline:
            await asyncio.sleep(step.poll_interval)

            # A concrete implementation would issue an HTTP request to
            # step.poll_endpoint here.  For now, return the initial result.
            status = result.get("status", "completed")
            if status in ("completed", "done", "finished", "ready"):
                return result
            if status in ("failed", "error"):
                raise RuntimeError(
                    f"Async job failed for step '{step.name}': "
                    f"{result.get('error', 'unknown')}"
                )

        raise TimeoutError(
            f"Step '{step.name}' timed out after {step.timeout}s waiting "
            "for async job completion"
        )

    def _resolve_input(self, step: PipelineStep) -> Dict[str, Any]:
        """Build the input payload for a step.

        If ``input_from`` is set, the raw output of the referenced step is
        used.  Otherwise ``input_template`` is processed, replacing
        ``{variable}`` placeholders with values from the shared namespace.
        """
        if step.input_from and step.input_from in self.step_results:
            return self.step_results[step.input_from]

        if not step.input_template:
            return {}

        return self._resolve_template(step.input_template)

    def _resolve_template(self, obj: Any) -> Any:
        """Recursively resolve ``{variable}`` placeholders."""
        if isinstance(obj, str):
            for key, value in self.variables.items():
                placeholder = f"{{{key}}}"
                if placeholder not in obj:
                    continue
                # If the entire string is just the placeholder, return the
                # native type (dict, list, int, …) instead of stringifying.
                if obj == placeholder:
                    return value
                if isinstance(value, dict):
                    obj = obj.replace(placeholder, json.dumps(value))
                else:
                    obj = obj.replace(placeholder, str(value))
            return obj
        if isinstance(obj, dict):
            return {k: self._resolve_template(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._resolve_template(item) for item in obj]
        return obj

    def _group_parallel(
        self, ready_steps: List[PipelineStep]
    ) -> List[List[PipelineStep]]:
        """Partition *ready_steps* into groups that can run concurrently.

        Two steps land in the same group when one references the other via
        ``parallel_with``.
        """
        groups: List[List[PipelineStep]] = []
        used: set[str] = set()

        for step in ready_steps:
            if step.name in used:
                continue

            group = [step]
            used.add(step.name)

            # Collect steps annotated to run alongside this one.
            for other in ready_steps:
                if other.name in used:
                    continue
                if (
                    other.parallel_with == step.name
                    or step.parallel_with == other.name
                ):
                    group.append(other)
                    used.add(other.name)

            groups.append(group)

        # Anything not yet grouped runs in its own single-step group.
        for step in ready_steps:
            if step.name not in used:
                groups.append([step])

        return groups

    def _build_summary(self) -> Dict[str, Any]:
        """Assemble the execution summary dict."""
        duration_ms: Optional[int] = None
        if self.started_at is not None and self.completed_at is not None:
            duration_ms = int((self.completed_at - self.started_at) * 1000)

        return {
            "execution_id": self.execution_id,
            "pipeline": self.pipeline.name,
            "status": self.status,
            "duration_ms": duration_ms,
            "steps": {
                name: {
                    "status": status.value,
                    "result": self.step_results.get(name),
                }
                for name, status in self.step_status.items()
            },
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Pipeline registry — built-in templates and runtime storage
# ---------------------------------------------------------------------------


# Pre-built pipeline templates
MUSIC_PRODUCTION_PIPELINE = Pipeline(
    name="music-production",
    description="Generate a complete music track with lyrics, audio, and artwork",
    steps=[
        PipelineStep(
            name="write-lyrics",
            service_type="llm",
            input_template={
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Write song lyrics about {topic} in {genre} style. "
                            "Return only the lyrics, no explanations."
                        ),
                    }
                ]
            },
            output_key="lyrics",
        ),
        PipelineStep(
            name="generate-music",
            service_type="music_gen",
            input_template={
                "params": {
                    "lyrics": "{lyrics}",
                    "tags": "{genre}",
                    "duration": 60,
                }
            },
            output_key="music_result",
            depends_on=["write-lyrics"],
            timeout=600,
        ),
        PipelineStep(
            name="generate-artwork",
            service_type="image_gen",
            input_template={
                "title": "{topic}",
                "genre": "{genre}",
                "mood": "cinematic",
            },
            output_key="artwork_result",
            depends_on=["write-lyrics"],
            parallel_with="generate-music",
        ),
    ],
    variables={"topic": "a journey through space", "genre": "synthwave"},
)

TRANSCRIPTION_PIPELINE = Pipeline(
    name="transcribe-and-summarize",
    description="Transcribe audio and generate a summary",
    steps=[
        PipelineStep(
            name="transcribe",
            service_type="stt",
            output_key="transcription",
        ),
        PipelineStep(
            name="summarize",
            service_type="llm",
            input_template={
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Summarize this transcription concisely:\n\n"
                            "{transcription}"
                        ),
                    }
                ]
            },
            output_key="summary",
            depends_on=["transcribe"],
        ),
    ],
)

RAG_PIPELINE = Pipeline(
    name="embed-and-rerank",
    description="Embed a query, retrieve documents, and rerank results",
    steps=[
        PipelineStep(
            name="embed-query",
            service_type="embeddings",
            input_template={"input": "{query}"},
            output_key="query_embedding",
        ),
        PipelineStep(
            name="rerank-results",
            service_type="reranker",
            input_template={
                "query": "{query}",
                "documents": "{documents}",
            },
            output_key="reranked",
            depends_on=["embed-query"],
        ),
    ],
    variables={"query": "", "documents": []},
)


# All built-in templates keyed by name.
BUILTIN_PIPELINES: Dict[str, Pipeline] = {
    p.name: p
    for p in [
        MUSIC_PRODUCTION_PIPELINE,
        TRANSCRIPTION_PIPELINE,
        RAG_PIPELINE,
    ]
}


class PipelineRegistry:
    """In-memory registry of pipeline templates.

    Stores both built-in templates and user-defined ones.  A future iteration
    could back this with PostgreSQL for persistence.
    """

    def __init__(self) -> None:
        self._pipelines: Dict[str, Pipeline] = dict(BUILTIN_PIPELINES)
        self._executions: Dict[str, PipelineExecution] = {}

    # -- Template management ------------------------------------------------

    def list_pipelines(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered pipeline templates."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "steps": len(p.steps),
                "variables": list(p.variables.keys()),
                "created_by": p.created_by,
            }
            for p in self._pipelines.values()
        ]

    def get_pipeline(self, name: str) -> Optional[Pipeline]:
        return self._pipelines.get(name)

    def register_pipeline(self, pipeline: Pipeline) -> None:
        self._pipelines[pipeline.name] = pipeline
        logger.info("Registered pipeline '%s'", pipeline.name)

    def unregister_pipeline(self, name: str) -> bool:
        if name in BUILTIN_PIPELINES:
            logger.warning("Cannot unregister built-in pipeline '%s'", name)
            return False
        return self._pipelines.pop(name, None) is not None

    # -- Execution tracking -------------------------------------------------

    def track_execution(self, execution: PipelineExecution) -> None:
        self._executions[execution.execution_id] = execution

    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        return self._executions.get(execution_id)

    def list_executions(
        self, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Return recent executions (most recent first)."""
        execs = sorted(
            self._executions.values(),
            key=lambda e: e.started_at or 0,
            reverse=True,
        )
        return [e.get_status() for e in execs[:limit]]


# Module-level singleton.
_registry: Optional[PipelineRegistry] = None


def get_pipeline_registry() -> PipelineRegistry:
    """Return (or lazily create) the module-level PipelineRegistry."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = PipelineRegistry()
    return _registry
