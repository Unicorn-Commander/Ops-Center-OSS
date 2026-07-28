---
name: brigade-delegation
description: Delegate tasks to Unicorn Brigade agents when a question falls outside server management expertise
actions:
  - name: delegate_task
    description: Send a task to a Brigade agent and get their response. Use when you need research, analysis, coding help, or domain expertise beyond server operations.
    confirmation_required: false
    parameters:
      agent_id:
        type: string
        description: "The agent to delegate to: the-general (orchestration), detective-holmes (OSINT/research), col-finance (finance), cpt-fullstack (software engineering), maj-devops (DevOps), prof-datasci (data science), judge-advocate (legal), doc-medresearch (medical), gunny (agent building), sgt-scribe (meeting notes), lt-docanalyst (document analysis)"
        required: true
      task:
        type: string
        description: The task or question to send to the agent
        required: true
      context:
        type: string
        description: Optional context from the current conversation to pass along
        required: false
  - name: list_agents
    description: List available Brigade agents and their specialties
    confirmation_required: false
    parameters: {}
---
Delegate tasks to Unicorn Brigade agents for capabilities beyond server management.
The Colonel can ask Brigade agents for help with research, analysis, coding,
finance, legal, medical, and other domain expertise. This is one-way delegation:
the Colonel tasks Brigade agents, but they cannot task the Colonel.
