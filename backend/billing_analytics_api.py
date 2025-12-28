"""
Billing Analytics API
-------------------
Advanced analytics endpoints for billing, revenue, and usage metrics

Features:
- Real-time revenue dashboards (MRR, ARR, growth)
- Customer analytics (LTV, churn, cohorts)
- Usage analytics (API calls, credits, trends)
- Top customers by spend
- Exportable reports (CSV/Excel)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging
import asyncpg
from collections import defaultdict
import csv
import io

# Database connection
from database import get_db_connection

# Authentication
from auth_dependencies import require_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing/analytics", tags=["billing-analytics"])


# ==================== Analytics Endpoints ====================

@router.get("/dashboard")
async def get_billing_dashboard(
    days: int = Query(30, description="Number of days to analyze"),
    admin_user: Dict = Depends(require_admin_user),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Get comprehensive billing dashboard with key metrics
    
    Returns:
    - MRR (Monthly Recurring Revenue)
    - ARR (Annual Recurring Revenue)
    - Growth rate
    - Active subscriptions
    - Churn rate
    - Average revenue per user (ARPU)
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get active subscriptions
        active_subs = await conn.fetch("""
            SELECT 
                COUNT(DISTINCT org_id) as total_orgs,
                SUM(CASE WHEN plan_type = 'platform' THEN 1 ELSE 0 END) as platform_count,
                SUM(CASE WHEN plan_type = 'byok' THEN 1 ELSE 0 END) as byok_count,
                SUM(CASE WHEN plan_type = 'hybrid' THEN 1 ELSE 0 END) as hybrid_count
            FROM organization_subscriptions
            WHERE status = 'active'
        """)
        
        # Calculate MRR (Monthly Recurring Revenue)
        mrr_data = await conn.fetch("""
            SELECT 
                SUM(CASE 
                    WHEN plan_type = 'platform' THEN 50.00
                    WHEN plan_type = 'byok' THEN 30.00
                    WHEN plan_type = 'hybrid' THEN 99.00
                    ELSE 0
                END) as mrr
            FROM organization_subscriptions
            WHERE status = 'active'
        """)
        
        mrr = float(mrr_data[0]['mrr'] or 0)
        arr = mrr * 12  # Annual Recurring Revenue
        
        # Get subscription count for previous period (for growth calculation)
        prev_start = start_date - timedelta(days=days)
        prev_subs = await conn.fetchval("""
            SELECT COUNT(DISTINCT org_id)
            FROM organization_subscriptions
            WHERE created_at >= $1 AND created_at < $2
        """, prev_start, start_date)
        
        current_subs = await conn.fetchval("""
            SELECT COUNT(DISTINCT org_id)
            FROM organization_subscriptions
            WHERE created_at >= $1 AND created_at < $2
        """, start_date, end_date)
        
        # Calculate growth rate
        growth_rate = 0
        if prev_subs and prev_subs > 0:
            growth_rate = ((current_subs - prev_subs) / prev_subs) * 100
        
        # Calculate ARPU (Average Revenue Per User)
        total_orgs = active_subs[0]['total_orgs'] or 1
        arpu = mrr / total_orgs if total_orgs > 0 else 0
        
        # Get churn data
        churned_orgs = await conn.fetchval("""
            SELECT COUNT(DISTINCT org_id)
            FROM organization_subscriptions
            WHERE status IN ('canceled', 'expired')
            AND updated_at >= $1
        """, start_date)
        
        churn_rate = (churned_orgs / total_orgs * 100) if total_orgs > 0 else 0
        
        # Credit usage stats
        credit_stats = await conn.fetch("""
            SELECT 
                SUM(allocated_credits) as total_allocated,
                SUM(used_credits) as total_used,
                AVG(used_credits::float / NULLIF(allocated_credits, 0) * 100) as avg_usage_pct
            FROM org_credit_pools
        """)
        
        return {
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "growth_rate": round(growth_rate, 2),
            "active_subscriptions": {
                "total": active_subs[0]['total_orgs'] or 0,
                "platform": active_subs[0]['platform_count'] or 0,
                "byok": active_subs[0]['byok_count'] or 0,
                "hybrid": active_subs[0]['hybrid_count'] or 0
            },
            "arpu": round(arpu, 2),
            "churn_rate": round(churn_rate, 2),
            "churned_orgs": churned_orgs or 0,
            "credit_usage": {
                "total_allocated": int(credit_stats[0]['total_allocated'] or 0),
                "total_used": int(credit_stats[0]['total_used'] or 0),
                "avg_usage_percent": round(float(credit_stats[0]['avg_usage_pct'] or 0), 2)
            },
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate billing dashboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate analytics")


@router.get("/revenue/trends")
async def get_revenue_trends(
    period: str = Query("month", description="day, week, or month"),
    limit: int = Query(12, description="Number of periods to return"),
    admin_user: Dict = Depends(require_admin_user),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Get revenue trends over time
    
    Returns time-series data for charts
    """
    try:
        # Determine date truncation based on period
        trunc_format = {
            "day": "day",
            "week": "week",
            "month": "month"
        }.get(period, "month")
        
        revenue_data = await conn.fetch(f"""
            SELECT 
                DATE_TRUNC('{trunc_format}', created_at) as period,
                COUNT(DISTINCT org_id) as new_subscriptions,
                SUM(CASE 
                    WHEN plan_type = 'platform' THEN 50.00
                    WHEN plan_type = 'byok' THEN 30.00
                    WHEN plan_type = 'hybrid' THEN 99.00
                    ELSE 0
                END) as revenue
            FROM organization_subscriptions
            WHERE created_at >= NOW() - INTERVAL '{limit} {trunc_format}s'
            GROUP BY period
            ORDER BY period DESC
            LIMIT $1
        """, limit)
        
        return {
            "period": period,
            "data": [
                {
                    "period": row['period'].isoformat(),
                    "new_subscriptions": row['new_subscriptions'],
                    "revenue": float(row['revenue'] or 0)
                }
                for row in reversed(revenue_data)
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get revenue trends: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve revenue trends")


@router.get("/customers/top")
async def get_top_customers(
    limit: int = Query(10, description="Number of top customers"),
    metric: str = Query("spend", description="spend, usage, or credits"),
    admin_user: Dict = Depends(require_admin_user),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """Get top customers by spend, usage, or credit consumption"""
    try:
        if metric == "spend":
            # Top by monthly subscription value
            query = """
                SELECT 
                    o.org_id,
                    o.name as org_name,
                    s.plan_type,
                    CASE 
                        WHEN s.plan_type = 'platform' THEN 50.00
                        WHEN s.plan_type = 'byok' THEN 30.00
                        WHEN s.plan_type = 'hybrid' THEN 99.00
                        ELSE 0
                    END as monthly_spend,
                    s.created_at as subscription_start
                FROM organizations o
                JOIN organization_subscriptions s ON o.org_id = s.org_id
                WHERE s.status = 'active'
                ORDER BY monthly_spend DESC
                LIMIT $1
            """
        elif metric == "usage":
            # Top by API call usage
            query = """
                SELECT 
                    o.org_id,
                    o.name as org_name,
                    cp.used_credits as usage,
                    cp.allocated_credits,
                    (cp.used_credits::float / NULLIF(cp.allocated_credits, 0) * 100) as usage_percent
                FROM organizations o
                JOIN org_credit_pools cp ON o.org_id = cp.org_id
                ORDER BY cp.used_credits DESC
                LIMIT $1
            """
        else:  # credits
            # Top by allocated credits
            query = """
                SELECT 
                    o.org_id,
                    o.name as org_name,
                    cp.allocated_credits,
                    cp.used_credits,
                    (cp.used_credits::float / NULLIF(cp.allocated_credits, 0) * 100) as usage_percent
                FROM organizations o
                JOIN org_credit_pools cp ON o.org_id = cp.org_id
                ORDER BY cp.allocated_credits DESC
                LIMIT $1
            """
        
        customers = await conn.fetch(query, limit)
        
        return {
            "metric": metric,
            "customers": [dict(row) for row in customers]
        }
        
    except Exception as e:
        logger.error(f"Failed to get top customers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve top customers")


@router.get("/usage/summary")
async def get_usage_summary(
    admin_user: Dict = Depends(require_admin_user),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """Get overall platform usage statistics"""
    try:
        # Total credits across all orgs
        credit_summary = await conn.fetch("""
            SELECT 
                SUM(allocated_credits) as total_allocated,
                SUM(used_credits) as total_used,
                SUM(allocated_credits - used_credits) as total_remaining
            FROM org_credit_pools
        """)
        
        # Usage by plan type
        usage_by_plan = await conn.fetch("""
            SELECT 
                s.plan_type,
                COUNT(DISTINCT o.org_id) as org_count,
                SUM(cp.allocated_credits) as allocated,
                SUM(cp.used_credits) as used
            FROM organizations o
            JOIN organization_subscriptions s ON o.org_id = s.org_id
            JOIN org_credit_pools cp ON o.org_id = cp.org_id
            WHERE s.status = 'active'
            GROUP BY s.plan_type
        """)
        
        # Recent usage transactions (last 7 days)
        recent_usage = await conn.fetchval("""
            SELECT SUM(credits_consumed)
            FROM credit_transactions
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        
        return {
            "total_allocated": int(credit_summary[0]['total_allocated'] or 0),
            "total_used": int(credit_summary[0]['total_used'] or 0),
            "total_remaining": int(credit_summary[0]['total_remaining'] or 0),
            "usage_by_plan": [
                {
                    "plan_type": row['plan_type'],
                    "org_count": row['org_count'],
                    "allocated": int(row['allocated'] or 0),
                    "used": int(row['used'] or 0),
                    "usage_percent": round((row['used'] / row['allocated'] * 100) if row['allocated'] > 0 else 0, 2)
                }
                for row in usage_by_plan
            ],
            "last_7_days_usage": int(recent_usage or 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve usage summary")


@router.get("/export/revenue")
async def export_revenue_report(
    start_date: date = Query(..., description="Report start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Report end date (YYYY-MM-DD)"),
    format: str = Query("csv", description="Export format: csv or json"),
    admin_user: Dict = Depends(require_admin_user),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Export revenue report for compliance/accounting
    
    Returns CSV or JSON file with detailed revenue breakdown
    """
    try:
        report_data = await conn.fetch("""
            SELECT 
                o.org_id,
                o.name as organization_name,
                s.plan_type,
                s.status,
                s.created_at as subscription_start,
                s.updated_at as last_updated,
                CASE 
                    WHEN s.plan_type = 'platform' THEN 50.00
                    WHEN s.plan_type = 'byok' THEN 30.00
                    WHEN s.plan_type = 'hybrid' THEN 99.00
                    ELSE 0
                END as monthly_revenue,
                cp.allocated_credits,
                cp.used_credits
            FROM organizations o
            JOIN organization_subscriptions s ON o.org_id = s.org_id
            LEFT JOIN org_credit_pools cp ON o.org_id = cp.org_id
            WHERE s.created_at::date >= $1 AND s.created_at::date <= $2
            ORDER BY s.created_at DESC
        """, start_date, end_date)
        
        if format == "csv":
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'org_id', 'organization_name', 'plan_type', 'status',
                'subscription_start', 'last_updated', 'monthly_revenue',
                'allocated_credits', 'used_credits'
            ])
            writer.writeheader()
            
            for row in report_data:
                writer.writerow({
                    'org_id': row['org_id'],
                    'organization_name': row['organization_name'],
                    'plan_type': row['plan_type'],
                    'status': row['status'],
                    'subscription_start': row['subscription_start'].isoformat() if row['subscription_start'] else '',
                    'last_updated': row['last_updated'].isoformat() if row['last_updated'] else '',
                    'monthly_revenue': float(row['monthly_revenue']),
                    'allocated_credits': row['allocated_credits'] or 0,
                    'used_credits': row['used_credits'] or 0
                })
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=revenue_report_{start_date}_{end_date}.csv"
                }
            )
        else:
            # JSON format
            return {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_records": len(report_data),
                "total_revenue": sum(float(row['monthly_revenue']) for row in report_data),
                "data": [dict(row) for row in report_data]
            }
        
    except Exception as e:
        logger.error(f"Failed to export revenue report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export report")


@router.get("/churn/analysis")
async def get_churn_analysis(
    days: int = Query(90, description="Analysis period in days"),
    admin_user: Dict = Depends(require_admin_user),
    conn: asyncpg.Connection = Depends(get_db_connection)
):
    """
    Analyze customer churn patterns
    
    Returns:
    - Churn rate by plan type
    - Reasons for cancellation (if tracked)
    - Churn trend over time
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Churn by plan type
        churn_by_plan = await conn.fetch("""
            SELECT 
                plan_type,
                COUNT(*) as churned_count,
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) as avg_lifetime_days
            FROM organization_subscriptions
            WHERE status IN ('canceled', 'expired')
            AND updated_at >= $1
            GROUP BY plan_type
        """, start_date)
        
        # Total active subscriptions for churn rate calculation
        total_active = await conn.fetchval("""
            SELECT COUNT(*) FROM organization_subscriptions
            WHERE status = 'active'
        """)
        
        # Churn trend (monthly)
        churn_trend = await conn.fetch("""
            SELECT 
                DATE_TRUNC('month', updated_at) as month,
                COUNT(*) as churned_count
            FROM organization_subscriptions
            WHERE status IN ('canceled', 'expired')
            AND updated_at >= $1
            GROUP BY month
            ORDER BY month
        """, start_date)
        
        total_churned = sum(row['churned_count'] for row in churn_by_plan)
        overall_churn_rate = (total_churned / total_active * 100) if total_active > 0 else 0
        
        return {
            "period_days": days,
            "overall_churn_rate": round(overall_churn_rate, 2),
            "total_churned": total_churned,
            "total_active": total_active,
            "churn_by_plan": [
                {
                    "plan_type": row['plan_type'],
                    "churned_count": row['churned_count'],
                    "avg_lifetime_days": round(float(row['avg_lifetime_days'] or 0), 1)
                }
                for row in churn_by_plan
            ],
            "churn_trend": [
                {
                    "month": row['month'].isoformat(),
                    "churned_count": row['churned_count']
                }
                for row in churn_trend
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze churn: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze churn")
