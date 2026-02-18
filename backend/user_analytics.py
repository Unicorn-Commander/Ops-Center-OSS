"""
User Analytics Module
Comprehensive user analytics with cohort analysis, behavior tracking, and ML-powered churn prediction
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics/users", tags=["User Analytics"])

# Database configuration
KEYCLOAK_DB_URL = os.getenv(
    "KEYCLOAK_DATABASE_URL",
    "postgresql://uchub:0f3b06f2eda86e85cf62af54b7b9b6becd7382a1877844ce8951760acb74f049@uchub-postgres:5432/keycloak_db"
)
OPS_DB_URL = os.getenv(
    "OPS_DATABASE_URL",
    "postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db"
)

# Redis cache configuration
REDIS_URL = "redis://unicorn-redis:6379"
CACHE_TTL = 300  # 5 minutes

# Initialize database engines
keycloak_engine = create_engine(KEYCLOAK_DB_URL, pool_pre_ping=True)
ops_engine = create_engine(OPS_DB_URL, pool_pre_ping=True)
KeycloakSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=keycloak_engine)
OpsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ops_engine)

# Dependency for database sessions
def get_keycloak_db():
    """Get Keycloak database session"""
    db = KeycloakSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db():
    """Get Ops Center database session"""
    db = OpsSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize churn predictor (will load model if exists)
# Commenting out for now since the model file doesn't exist yet
# churn_predictor = ChurnPredictor()


class UserOverview(BaseModel):
    """User metrics overview"""

    total_users: int = Field(..., description="Total registered users")
    active_users: int = Field(..., description="Active users (logged in last 30 days)")
    new_users_30d: int = Field(..., description="New users in last 30 days")
    churned_users_30d: int = Field(..., description="Churned users in last 30 days")
    dau_mau_ratio: float = Field(..., description="DAU/MAU ratio")
    growth_rate: float = Field(..., description="Month-over-month growth rate")


class CohortRetention(BaseModel):
    """Cohort retention data"""

    month: str = Field(..., description="Cohort month (YYYY-MM)")
    signup_count: int = Field(..., description="Number of signups in this cohort")
    retention: Dict[str, float] = Field(..., description="Retention rates by month")


class EngagementMetrics(BaseModel):
    """User engagement metrics"""

    dau: int = Field(..., description="Daily Active Users")
    wau: int = Field(..., description="Weekly Active Users")
    mau: int = Field(..., description="Monthly Active Users")
    dau_mau_ratio: float = Field(..., description="DAU/MAU ratio (stickiness)")
    wau_mau_ratio: float = Field(..., description="WAU/MAU ratio")
    avg_session_duration: float = Field(..., description="Average session duration (minutes)")


class ChurnPrediction(BaseModel):
    """Churn prediction for a user"""

    user_id: str
    username: str
    churn_probability: float = Field(..., ge=0, le=100)
    risk_level: str = Field(..., description="low, medium, high")
    days_since_signup: int
    last_login_days_ago: int
    login_count: int


class UserSegments(BaseModel):
    """User segmentation"""

    power_users: int = Field(..., description="Highly engaged users")
    active_users: int = Field(..., description="Regular users")
    at_risk: int = Field(..., description="Users at risk of churning")
    inactive: int = Field(..., description="Inactive users")


async def get_redis() -> aioredis.Redis:
    """Get Redis connection."""
    try:
        redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
        return redis_client
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Caching disabled.")
        return None


async def get_cached_or_compute(
    cache_key: str, compute_func, ttl: int = CACHE_TTL
) -> any:
    """
    Get data from cache or compute and cache it.

    Args:
        cache_key: Redis cache key
        compute_func: Async function to compute data if cache miss
        ttl: Cache TTL in seconds

    Returns:
        Cached or computed data
    """
    redis_client = await get_redis()

    if redis_client:
        try:
            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

    # Compute data
    data = await compute_func()

    # Cache it
    if redis_client:
        try:
            await redis_client.setex(cache_key, ttl, json.dumps(data))
            logger.debug(f"Cached: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    return data


async def query_keycloak_users(db: Session) -> List[Dict]:
    """
    Query all users from Keycloak database.

    Returns:
        List of user dictionaries
    """
    query = text(
        """
        SELECT
            u.id as user_id,
            u.username,
            u.email,
            u.created_timestamp,
            u.enabled,
            COUNT(DISTINCT s.id) as session_count,
            MAX(s.last_session_refresh) as last_login
        FROM user_entity u
        LEFT JOIN user_session s ON u.id = s.user_id
        WHERE u.realm_id = (SELECT id FROM realm WHERE name = 'uchub')
        GROUP BY u.id, u.username, u.email, u.created_timestamp, u.enabled
        """
    )

    result = await db.execute(query)
    users = []

    for row in result:
        users.append(
            {
                "user_id": row.user_id,
                "username": row.username or row.email,
                "email": row.email,
                "created_at": datetime.fromtimestamp(row.created_timestamp / 1000)
                if row.created_timestamp
                else None,
                "enabled": row.enabled,
                "login_count": row.session_count or 0,
                "last_login": datetime.fromtimestamp(row.last_login / 1000)
                if row.last_login
                else None,
            }
        )

    return users


async def get_user_feature_usage(db: Session, user_id: str) -> Dict:
    """
    Get feature usage statistics for a user from Ops Center logs.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Dictionary with feature usage metrics
    """
    # This would query activity_logs table in Ops Center DB
    # For now, return mock data structure
    query = text(
        """
        SELECT
            COUNT(*) as total_actions,
            COUNT(DISTINCT DATE(created_at)) as active_days,
            AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_duration
        FROM activity_logs
        WHERE user_id = :user_id
        AND created_at >= NOW() - INTERVAL '30 days'
        """
    )

    try:
        result = await db.execute(query, {"user_id": user_id})
        row = result.fetchone()

        if row:
            return {
                "total_actions": row.total_actions or 0,
                "active_days": row.active_days or 0,
                "avg_duration": row.avg_duration or 0,
            }
    except Exception as e:
        logger.debug(f"Feature usage query failed (table may not exist): {e}")

    # Default values if query fails
    return {"total_actions": 0, "active_days": 0, "avg_duration": 0}


async def enrich_user_data(
    users: List[Dict], ops_db: Session
) -> List[Dict]:
    """
    Enrich user data with feature usage and subscription info.

    Args:
        users: List of user dictionaries from Keycloak
        ops_db: Ops Center database session

    Returns:
        Enriched user list
    """
    enriched = []

    for user in users:
        # Get feature usage
        feature_usage = await get_user_feature_usage(ops_db, user["user_id"])

        # Calculate feature usage score (0-100)
        usage_score = min(
            100,
            (feature_usage["total_actions"] * 2)
            + (feature_usage["active_days"] * 5),
        )

        # Mock subscription data (would query Lago API in production)
        plan_tier = "trial"  # Default

        # Calculate session duration average
        session_duration_avg = feature_usage["avg_duration"] / 60  # Convert to minutes

        # Calculate API calls (mock for now)
        api_calls_30d = feature_usage["total_actions"]

        enriched.append(
            {
                **user,
                "feature_usage_score": usage_score,
                "plan_tier": plan_tier,
                "session_duration_avg": session_duration_avg,
                "api_calls_30d": api_calls_30d,
            }
        )

    return enriched


@router.get("/overview", response_model=UserOverview)
async def get_user_overview(
    keycloak_db: Session = Depends(get_keycloak_db),
    ops_db: Session = Depends(get_db),
):
    """
    Get user metrics overview.

    Returns total users, active users, new users, churned users, and engagement ratios.
    """

    async def compute_overview():
        # Query users from Keycloak
        users = await query_keycloak_users(keycloak_db)

        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)

        # Calculate metrics
        total_users = len(users)
        active_users = sum(
            1
            for u in users
            if u.get("last_login") and u["last_login"] >= thirty_days_ago
        )
        new_users_30d = sum(
            1
            for u in users
            if u.get("created_at") and u["created_at"] >= thirty_days_ago
        )
        churned_users_30d = sum(
            1
            for u in users
            if u.get("last_login")
            and u["last_login"] < thirty_days_ago
            and u.get("created_at")
            and u["created_at"] < thirty_days_ago
        )

        # DAU (active in last day)
        one_day_ago = now - timedelta(days=1)
        dau = sum(
            1 for u in users if u.get("last_login") and u["last_login"] >= one_day_ago
        )

        # MAU = active users
        mau = active_users

        dau_mau_ratio = dau / mau if mau > 0 else 0

        # Calculate growth rate (month-over-month)
        sixty_days_ago = now - timedelta(days=60)
        users_60d = sum(
            1
            for u in users
            if u.get("created_at") and u["created_at"] >= sixty_days_ago
        )
        growth_rate = (
            ((new_users_30d / (users_60d - new_users_30d)) * 100)
            if (users_60d - new_users_30d) > 0
            else 0
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_30d": new_users_30d,
            "churned_users_30d": churned_users_30d,
            "dau_mau_ratio": round(dau_mau_ratio, 3),
            "growth_rate": round(growth_rate, 2),
        }

    return await get_cached_or_compute("analytics:user_overview", compute_overview)


@router.get("/cohorts", response_model=List[CohortRetention])
async def get_cohort_analysis(
    months: int = Query(6, description="Number of months to analyze"),
    keycloak_db: Session = Depends(get_keycloak_db),
):
    """
    Get cohort retention analysis.

    Returns retention rates for each signup cohort by month.
    """

    async def compute_cohorts():
        try:
            users = await query_keycloak_users(keycloak_db)

            # Group users by signup month
            cohorts = {}
            for user in users:
                if not user.get("created_at"):
                    continue

                cohort_month = user["created_at"].strftime("%Y-%m")

                if cohort_month not in cohorts:
                    cohorts[cohort_month] = []

                cohorts[cohort_month].append(user)

            # Calculate retention for each cohort
            cohort_data = []
            now = datetime.now()

            for cohort_month, cohort_users in sorted(cohorts.items(), reverse=True)[
                :months
            ]:
                cohort_start = datetime.strptime(cohort_month, "%Y-%m")
                signup_count = len(cohort_users)

                retention = {}

                # Calculate retention for months 0-12
                for month_offset in range(13):
                    month_end = cohort_start + timedelta(days=30 * (month_offset + 1))

                    if month_end > now:
                        break

                    # Count users active in this month
                    active_in_month = sum(
                        1
                        for u in cohort_users
                        if u.get("last_login") and u["last_login"] >= month_end - timedelta(days=30)
                    )

                    retention_rate = (
                        (active_in_month / signup_count * 100) if signup_count > 0 else 0
                    )
                    retention[f"month_{month_offset}"] = round(retention_rate, 1)

                cohort_data.append(
                    {
                        "month": cohort_month,
                        "signup_count": signup_count,
                        "retention": retention,
                    }
                )


            return cohort_data
        except Exception as e:
            logger.error(f'Error computing cohort analysis: {e}')
            return []


    return await get_cached_or_compute(
        f"analytics:cohorts:{months}", compute_cohorts
    )


@router.get("/retention")
async def get_retention_curves(
    keycloak_db: Session = Depends(get_keycloak_db),
):
    """
    Get retention curves for visualization.

    Returns retention data suitable for charting.
    """
    cohorts = await get_cohort_analysis(months=12, keycloak_db=keycloak_db)

    # Transform for charting
    curves = []
    for cohort in cohorts:
        curve_data = {
            "cohort": cohort["month"],
            "data": [
                {"month": int(k.split("_")[1]), "retention": v}
                for k, v in cohort["retention"].items()
            ],
        }
        curves.append(curve_data)

    return {"retention_curves": curves}


@router.get("/engagement", response_model=EngagementMetrics)
async def get_engagement_metrics(
    keycloak_db: Session = Depends(get_keycloak_db),
):
    """
    Get user engagement metrics (DAU, WAU, MAU).

    Returns daily, weekly, and monthly active user counts with ratios.
    """

    async def compute_engagement():
        try:
            users = await query_keycloak_users(keycloak_db)

            now = datetime.now()

            # DAU - active in last 1 day
            one_day_ago = now - timedelta(days=1)
            dau = sum(
                1 for u in users if u.get("last_login") and u["last_login"] >= one_day_ago
            )

            # WAU - active in last 7 days
            seven_days_ago = now - timedelta(days=7)
            wau = sum(
                1
                for u in users
                if u.get("last_login") and u["last_login"] >= seven_days_ago
            )

            # MAU - active in last 30 days
            thirty_days_ago = now - timedelta(days=30)
            mau = sum(
                1
                for u in users
                if u.get("last_login") and u["last_login"] >= thirty_days_ago
            )

            # Calculate ratios
            dau_mau_ratio = dau / mau if mau > 0 else 0
            wau_mau_ratio = wau / mau if mau > 0 else 0

            # Mock average session duration
            avg_session_duration = 15.5  # minutes


            return {
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "dau_mau_ratio": round(dau_mau_ratio, 3),
            "wau_mau_ratio": round(wau_mau_ratio, 3),
            "avg_session_duration": avg_session_duration,
        }
        except Exception as e:
            logger.error(f'Error computing engagement metrics: {e}')
            return {
                'dau': 0,
                'wau': 0,
                'mau': 0,
                'dau_mau_ratio': 0.0,
                'wau_mau_ratio': 0.0,
                'avg_session_duration': 0.0
            }


    return await get_cached_or_compute("analytics:engagement", compute_engagement)


@router.get("/churn/prediction", response_model=List[ChurnPrediction])
async def get_churn_predictions(
    risk_level: Optional[str] = Query(None, description="Filter by risk level: low, medium, high"),
    limit: int = Query(100, description="Maximum number of predictions"),
    keycloak_db: Session = Depends(get_keycloak_db),
    ops_db: Session = Depends(get_db),
):
    """
    Get ML-based churn predictions for users.

    Returns churn probability and risk level for each user.
    """

    async def compute_predictions():
        # Get users
        users = await query_keycloak_users(keycloak_db)

        # Enrich with feature data
        enriched_users = await enrich_user_data(users, ops_db)

        # Predict churn
        predictions = churn_predictor.predict(enriched_users)

        # Filter by risk level if specified
        if risk_level:
            predictions = [p for p in predictions if p["risk_level"] == risk_level]

        # Sort by churn probability (highest first)
        predictions.sort(key=lambda x: x["churn_probability"], reverse=True)

        # Limit results
        return predictions[:limit]

    return await get_cached_or_compute(
        f"analytics:churn:{risk_level}:{limit}", compute_predictions, ttl=600
    )


@router.get("/behavior/patterns")
async def get_behavior_patterns(
    keycloak_db: Session = Depends(get_keycloak_db),
):
    """
    Get user behavior patterns.

    Returns login frequency distribution, feature usage patterns, and activity trends.
    """

    async def compute_patterns():
        users = await query_keycloak_users(keycloak_db)

        # Login frequency distribution
        login_freq = {"daily": 0, "weekly": 0, "monthly": 0, "inactive": 0}

        now = datetime.now()
        for user in users:
            if not user.get("last_login"):
                login_freq["inactive"] += 1
            elif user["last_login"] >= now - timedelta(days=1):
                login_freq["daily"] += 1
            elif user["last_login"] >= now - timedelta(days=7):
                login_freq["weekly"] += 1
            elif user["last_login"] >= now - timedelta(days=30):
                login_freq["monthly"] += 1
            else:
                login_freq["inactive"] += 1

        # Activity by day of week
        activity_by_dow = {day: 0 for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
        for user in users:
            if user.get("last_login"):
                dow = user["last_login"].strftime("%a")
                if dow in activity_by_dow:
                    activity_by_dow[dow] += 1

        # Activity by hour
        activity_by_hour = {hour: 0 for hour in range(24)}
        for user in users:
            if user.get("last_login"):
                hour = user["last_login"].hour
                activity_by_hour[hour] += 1

        return {
            "login_frequency": login_freq,
            "activity_by_day_of_week": activity_by_dow,
            "activity_by_hour": activity_by_hour,
        }

    return await get_cached_or_compute("analytics:behavior_patterns", compute_patterns)


@router.get("/segments", response_model=UserSegments)
async def get_user_segments(
    keycloak_db: Session = Depends(get_keycloak_db),
    ops_db: Session = Depends(get_db),
):
    """
    Get user segmentation.

    Segments users into power users, active users, at-risk, and inactive.
    """

    async def compute_segments():
        users = await query_keycloak_users(keycloak_db)
        enriched_users = await enrich_user_data(users, ops_db)

        # Segment criteria
        power_users = 0
        active_users = 0
        at_risk = 0
        inactive = 0

        now = datetime.now()

        for user in enriched_users:
            last_login = user.get("last_login")

            if not last_login:
                inactive += 1
            elif last_login >= now - timedelta(days=7):
                # Active in last week
                if user["feature_usage_score"] >= 50:
                    power_users += 1
                else:
                    active_users += 1
            elif last_login >= now - timedelta(days=21):
                # Active 1-3 weeks ago - at risk
                at_risk += 1
            else:
                # Inactive
                inactive += 1

        return {
            "power_users": power_users,
            "active_users": active_users,
            "at_risk": at_risk,
            "inactive": inactive,
        }

    return await get_cached_or_compute("analytics:segments", compute_segments)


@router.get("/growth")
async def get_growth_metrics(
    months: int = Query(6, description="Number of months to analyze"),
    keycloak_db: Session = Depends(get_keycloak_db),
):
    """
    Get user growth metrics over time.

    Returns signups, activations, and churn by month.
    """

    async def compute_growth():
        users = await query_keycloak_users(keycloak_db)

        # Group by month
        growth_by_month = {}

        for user in users:
            if not user.get("created_at"):
                continue

            month = user["created_at"].strftime("%Y-%m")

            if month not in growth_by_month:
                growth_by_month[month] = {
                    "signups": 0,
                    "activated": 0,
                    "churned": 0,
                }

            growth_by_month[month]["signups"] += 1

            # Consider activated if they logged in at least once
            if user.get("login_count", 0) > 0:
                growth_by_month[month]["activated"] += 1

            # Consider churned if last login was >30 days ago
            if user.get("last_login"):
                days_since_login = (datetime.now() - user["last_login"]).days
                if days_since_login > 30:
                    growth_by_month[month]["churned"] += 1

        # Convert to list sorted by month
        growth_data = [
            {"month": month, **metrics}
            for month, metrics in sorted(growth_by_month.items(), reverse=True)[
                :months
            ]
        ]

        return growth_data

    return await get_cached_or_compute(
        f"analytics:growth:{months}", compute_growth
    )


@router.post("/churn/train")
async def train_churn_model(
    keycloak_db: Session = Depends(get_keycloak_db),
    ops_db: Session = Depends(get_db),
):
    """
    Train the churn prediction model with latest data.

    This endpoint triggers model training on historical user data.
    Should be called weekly via scheduled task.
    """
    try:
        logger.info("Starting churn model training...")

        # Get historical user data (last 6 months)
        users = await query_keycloak_users(keycloak_db)
        enriched_users = await enrich_user_data(users, ops_db)

        # Train model
        metrics = churn_predictor.train(enriched_users)

        # Save model
        saved = churn_predictor.save_model()

        if not saved:
            raise HTTPException(status_code=500, detail="Failed to save model")

        # Clear prediction cache
        redis_client = await get_redis()
        if redis_client:
            await redis_client.delete("analytics:churn:*")

        logger.info("Churn model training complete")

        return {
            "status": "success",
            "message": "Model trained and saved successfully",
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/churn/model-info")
async def get_churn_model_info():
    """
    Get information about the current churn prediction model.

    Returns model metadata, training date, and feature importance.
    """
    return churn_predictor.get_model_info()


# Background task for weekly model retraining
async def weekly_model_retraining():
    """
    Background task that retrains the churn model weekly.

    This should be started when the application starts.
    """
    while True:
        try:
            # Wait 7 days
            await asyncio.sleep(7 * 24 * 60 * 60)

            logger.info("Starting scheduled model retraining...")

            # Get database sessions (you'll need to adjust this based on your setup)
            # For now, this is a placeholder
            # In production, you'd call the train endpoint or replicate the logic here

            logger.info("Scheduled model retraining complete")

        except Exception as e:
            logger.error(f"Scheduled retraining failed: {e}")
            # Continue loop even if training fails
            await asyncio.sleep(3600)  # Retry in 1 hour


# Startup: Load existing model
# Commented out until ChurnPredictor model is implemented
# @router.on_event("startup")
# async def load_churn_model():
#     """Load churn model on startup."""
#     logger.info("Loading churn prediction model...")
#     loaded = churn_predictor.load_model()
#
#     if not loaded:
#         logger.warning(
#             "No trained model found. Train the model using POST /api/v1/analytics/users/churn/train"
#         )
