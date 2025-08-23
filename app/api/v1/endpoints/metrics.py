from datetime import date, datetime, timedelta
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func, extract

from app.auth.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.schemas.user import User
from app.schemas.metrics import (
    KPIResponse, MonthlyUsageResponse, Co2TrendResponse, YoyUsageResponse,
    DateRangeModel, MonthlyUsageItem, Co2TrendItem, UsageData
)

router = APIRouter(tags=["metrics"])

# CO2係数定数（日本国内の一般的係数）
CO2_FACTOR_ELECTRICITY = 0.000518  # kg-CO2/kWh (2021年度全国平均)
CO2_FACTOR_GAS = 0.0023  # kg-CO2/m3


async def get_user_company_id(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> int:
    """Get company_id for the current user"""
    result = db.execute(
        text("SELECT company_id FROM employees WHERE user_id = :user_id"),
        {"user_id": current_user.id}
    ).fetchone()
    
    if not result or result[0] is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ユーザーは会社に所属していません"
        )
    
    return result[0]


@router.get("/kpi", response_model=KPIResponse)
async def get_kpi_metrics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    company_id: Optional[int] = Query(None, description="Company ID"),
    from_date: Optional[date] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="To date (YYYY-MM-DD)")
):
    """Get KPI metrics for dashboard overview cards"""
    
    # Get user's company_id if not provided
    user_company_id = await get_user_company_id(db, current_user)
    target_company_id = company_id or user_company_id
    
    # Verify user has access to requested company
    if target_company_id != user_company_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="指定された会社のデータにアクセスする権限がありません"
        )
    
    # Default to last 12 months if no dates provided (better UX for populated dashboard)
    if not from_date or not to_date:
        to_date = date.today()
        from_date = to_date.replace(year=to_date.year - 1)  # 12 months ago
    
    # Active users count (users with any activity in the period)
    active_users_result = db.execute(text("""
        SELECT COUNT(DISTINCT u.id) as cnt FROM users u
        JOIN employees e ON u.id = e.user_id
        WHERE e.company_id = :company_id
        AND u.id IN (
            SELECT DISTINCT user_id FROM energy_records 
            WHERE DATE(`timestamp`) BETWEEN :from_date AND :to_date
            UNION
            SELECT DISTINCT user_id FROM points_ledger 
            WHERE DATE(created_at) BETWEEN :from_date AND :to_date
        )
    """), {
        "company_id": target_company_id,
        "from_date": from_date,
        "to_date": to_date
    }).fetchone()
    
    active_users = active_users_result[0] if active_users_result else 0
    
    # Total electricity and gas usage from energy_records
    usage_result = db.execute(text("""
        SELECT 
            SUM(er.energy_consumed) as electricity_total,
            SUM(er.energy_produced) as electricity_produced,
            SUM(er.energy_consumed * 0.000518) as co2_total
        FROM energy_records er
        JOIN employees e ON er.user_id = e.user_id
        WHERE e.company_id = :company_id
        AND DATE(er.`timestamp`) BETWEEN :from_date AND :to_date
    """), {
        "company_id": target_company_id,
        "from_date": from_date,
        "to_date": to_date
    }).fetchone()
    
    electricity_total = float(usage_result[0] or 0)
    electricity_produced = float(usage_result[1] or 0)  # Produced energy (solar, etc.)
    co2_total = float(usage_result[2] or 0)
    
    # Calculate "energy saved" as net consumption reduction (placeholder logic)
    energy_saved = max(0, electricity_produced * 0.8)  # 80% of produced energy considered "saved"
    
    # Redemption metrics (handling missing points system gracefully)
    try:
        redemption_result = db.execute(text("""
            SELECT 
                COUNT(r.id) as total_redemptions,
                SUM(r.points_used) as total_points_spent
            FROM redemptions r
            JOIN employees e ON r.user_id = e.user_id
            WHERE e.company_id = :company_id
            AND DATE(r.created_at) BETWEEN :from_date AND :to_date
            AND (r.status = 'completed' OR r.status IS NULL)
        """), {
            "company_id": target_company_id,
            "from_date": from_date,
            "to_date": to_date
        }).fetchone()
        
        total_redemptions = int(redemption_result[0] or 0)
        total_points_spent = int(redemption_result[1] or 0)
        
        # Get total points awarded from points_ledger
        points_awarded_result = db.execute(text("""
            SELECT SUM(delta) as total_points_awarded
            FROM points_ledger pl
            JOIN employees e ON pl.user_id = e.user_id
            WHERE e.company_id = :company_id
            AND DATE(pl.created_at) BETWEEN :from_date AND :to_date
            AND pl.delta > 0
        """), {
            "company_id": target_company_id,
            "from_date": from_date,
            "to_date": to_date
        }).fetchone()
        
        total_points_awarded = int(points_awarded_result[0] or 0)
        
    except Exception as e:
        # Handle missing points tables gracefully
        total_redemptions = 0
        total_points_spent = 0
        total_points_awarded = 0
    
    return KPIResponse(
        company_id=target_company_id,
        range=DateRangeModel(from_date=from_date, to_date=to_date),
        active_users=active_users,
        electricity_total_kwh=electricity_total,
        gas_total_m3=0.0,  # Gas not available in current schema
        co2_reduction_total_kg=co2_total,
        total_redemptions=total_redemptions,
        total_points_spent=total_points_spent,
        total_energy_saved=energy_saved,
        total_points_awarded=total_points_awarded
    )


@router.get("/monthly-usage", response_model=MonthlyUsageResponse)
async def get_monthly_usage(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    company_id: Optional[int] = Query(None, description="Company ID"),
    year: int = Query(datetime.now().year, description="Year (YYYY)")
):
    """Get monthly usage data for bar chart"""
    
    user_company_id = await get_user_company_id(db, current_user)
    target_company_id = company_id or user_company_id
    
    if target_company_id != user_company_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="指定された会社のデータにアクセスする権限がありません"
        )
    
    # Use energy_records instead of reduction_records
    results = db.execute(text("""
        SELECT 
            MONTH(`timestamp`) as month,
            SUM(energy_consumed) as electricity_kwh,
            0 as gas_m3
        FROM energy_records er
        JOIN employees e ON er.user_id = e.user_id
        WHERE e.company_id = :company_id
        AND YEAR(`timestamp`) = :year
        GROUP BY MONTH(`timestamp`)
        ORDER BY MONTH(`timestamp`)
    """), {
        "company_id": target_company_id,
        "year": year
    }).fetchall()
    
    # Create full 12-month data with zeros for missing months
    months_data = {}
    for result in results:
        months_data[result[0]] = MonthlyUsageItem(
            month=result[0],
            electricity_kwh=float(result[1] or 0),
            gas_m3=float(result[2] or 0)
        )
    
    # Fill missing months with zeros
    full_months = []
    for month in range(1, 13):
        if month in months_data:
            full_months.append(months_data[month])
        else:
            full_months.append(MonthlyUsageItem(
                month=month,
                electricity_kwh=0.0,
                gas_m3=0.0
            ))
    
    return MonthlyUsageResponse(
        company_id=target_company_id,
        year=year,
        months=full_months
    )


@router.get("/co2-trend", response_model=Co2TrendResponse)
async def get_co2_trend(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    company_id: Optional[int] = Query(None, description="Company ID"),
    from_date: Optional[date] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="To date (YYYY-MM-DD)"),
    interval: str = Query("month", description="Interval: month or week")
):
    """Get CO2 reduction trend data for line chart"""
    
    user_company_id = await get_user_company_id(db, current_user)
    target_company_id = company_id or user_company_id
    
    if target_company_id != user_company_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="指定された会社のデータにアクセスする権限がありません"
        )
    
    # Default to last 12 months if no dates provided
    if not from_date or not to_date:
        to_date = date.today()
        from_date = to_date - timedelta(days=365)
    
    if interval == "month":
        date_format = "%Y-%m"
    else:  # week
        date_format = "%Y-%u"  # Year-week
    
    results = db.execute(text(f"""
        SELECT 
            DATE_FORMAT(`timestamp`, '{date_format}') as period,
            SUM(energy_consumed * 0.000518) as co2_kg
        FROM energy_records er
        JOIN employees e ON er.user_id = e.user_id
        WHERE e.company_id = :company_id
        AND DATE(er.`timestamp`) BETWEEN :from_date AND :to_date
        GROUP BY DATE_FORMAT(`timestamp`, '{date_format}')
        ORDER BY period
    """), {
        "company_id": target_company_id,
        "from_date": from_date,
        "to_date": to_date
    }).fetchall()
    
    points = [
        Co2TrendItem(
            period=result[0],
            co2_kg=float(result[1] or 0)
        )
        for result in results
    ]
    
    return Co2TrendResponse(
        company_id=target_company_id,
        points=points
    )


@router.get("/yoy-usage", response_model=YoyUsageResponse)
async def get_yoy_usage(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    company_id: Optional[int] = Query(None, description="Company ID"),
    month: str = Query(datetime.now().strftime("%Y-%m"), description="Month (YYYY-MM)")
):
    """Get year-over-year usage comparison for horizontal bar chart"""
    
    user_company_id = await get_user_company_id(db, current_user)
    target_company_id = company_id or user_company_id
    
    if target_company_id != user_company_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="指定された会社のデータにアクセスする権限がありません"
        )
    
    # Current year data
    current_result = db.execute(text("""
        SELECT 
            SUM(CASE WHEN energy_type = 'electricity' THEN `usage` ELSE 0 END) as electricity_kwh,
            SUM(CASE WHEN energy_type = 'gas' THEN `usage` ELSE 0 END) as gas_m3
        FROM reduction_records rr
        JOIN employees e ON rr.user_id = e.user_id
        WHERE e.company_id = :company_id
        AND DATE_FORMAT(date, '%Y-%m') = :month
    """), {
        "company_id": target_company_id,
        "month": month
    }).fetchone()
    
    # Previous year data (same month, previous year)
    previous_year_month = datetime.strptime(f"{month}-01", "%Y-%m-%d") - timedelta(days=365)
    previous_month = previous_year_month.strftime("%Y-%m")
    
    previous_result = db.execute(text("""
        SELECT 
            SUM(CASE WHEN energy_type = 'electricity' THEN `usage` ELSE 0 END) as electricity_kwh,
            SUM(CASE WHEN energy_type = 'gas' THEN `usage` ELSE 0 END) as gas_m3
        FROM reduction_records rr
        JOIN employees e ON rr.user_id = e.user_id
        WHERE e.company_id = :company_id
        AND DATE_FORMAT(date, '%Y-%m') = :month
    """), {
        "company_id": target_company_id,
        "month": previous_month
    }).fetchone()
    
    current_electricity = float(current_result[0] or 0)
    current_gas = float(current_result[1] or 0)
    previous_electricity = float(previous_result[0] or 0) if previous_result else 0.0
    previous_gas = float(previous_result[1] or 0) if previous_result else 0.0
    
    return YoyUsageResponse(
        company_id=target_company_id,
        month=month,
        current=UsageData(
            electricity_kwh=current_electricity,
            gas_m3=current_gas
        ),
        previous=UsageData(
            electricity_kwh=previous_electricity,
            gas_m3=previous_gas
        ),
        delta=UsageData(
            electricity_kwh=current_electricity - previous_electricity,
            gas_m3=current_gas - previous_gas
        )
    )