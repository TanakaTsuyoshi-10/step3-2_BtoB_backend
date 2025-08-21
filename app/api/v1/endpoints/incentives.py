from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.reward import Reward
from app.models.point import Point
from app.models.redemption import Redemption
from app.schemas.user import User as UserSchema
from app.schemas.incentives import (
    DistributionResponse, DistributionSummary, DepartmentDistribution, 
    EmployeeDistribution, RewardSummary, RewardCreate, RewardUpdate,
    RedemptionResponse, RedemptionSummary, RewardPopularity
)

router = APIRouter()


async def get_user_company_id(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
) -> int:
    """Get company_id for the current user"""
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return employee.company_id


def check_admin_permission(current_user: UserSchema = Depends(get_current_user)):
    """管理者権限チェック"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    return current_user


@router.get("/distribution/summary", response_model=DistributionResponse)
async def get_distribution_summary(
    start: Optional[date] = Query(None, description="開始日"),
    end: Optional[date] = Query(None, description="終了日"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission),
    company_id: int = Depends(get_user_company_id)
):
    """配布状況サマリーを取得"""
    
    # デフォルト期間設定（今月）
    if not start or not end:
        today = date.today()
        start = date(today.year, today.month, 1)
        if today.month == 12:
            end = date(today.year + 1, 1, 1)
        else:
            end = date(today.year, today.month + 1, 1)
    
    # 基本クエリ
    base_query = db.query(Point).join(User).join(Employee).filter(
        Employee.company_id == company_id,
        Point.earned_at >= start,
        Point.earned_at < end
    )
    
    # 全体サマリー
    points_sum = base_query.with_entities(func.sum(Point.points)).scalar() or 0
    employees_count = base_query.with_entities(func.count(func.distinct(Point.user_id))).scalar() or 0
    avg_points = float(points_sum / employees_count) if employees_count > 0 else 0.0
    
    summary = DistributionSummary(
        total_points=int(points_sum),
        total_employees=employees_count,
        average_points=avg_points,
        period_start=start,
        period_end=end
    )
    
    # 部署別集計
    dept_query = db.query(
        Employee.department,
        func.sum(Point.points).label('total_points'),
        func.count(func.distinct(Point.user_id)).label('employee_count')
    ).join(User).join(Point).filter(
        Employee.company_id == company_id,
        Point.earned_at >= start,
        Point.earned_at < end
    ).group_by(Employee.department)
    
    departments = []
    for dept_row in dept_query:
        dept_avg = float(dept_row.total_points / dept_row.employee_count) if dept_row.employee_count > 0 else 0.0
        departments.append(DepartmentDistribution(
            department=dept_row.department,
            total_points=int(dept_row.total_points),
            employee_count=dept_row.employee_count,
            average_points=dept_avg
        ))
    
    # 従業員別集計
    emp_query = db.query(
        User.id,
        User.full_name,
        Employee.department,
        func.sum(Point.points).label('total_points'),
        func.max(Point.earned_at).label('last_earned')
    ).join(Employee).join(Point).filter(
        Employee.company_id == company_id,
        Point.earned_at >= start,
        Point.earned_at < end
    ).group_by(User.id, User.full_name, Employee.department).order_by(desc('total_points'))
    
    employees = []
    for emp_row in emp_query:
        employees.append(EmployeeDistribution(
            employee_id=emp_row.id,
            employee_name=emp_row.full_name,
            department=emp_row.department,
            total_points=int(emp_row.total_points),
            last_earned_date=emp_row.last_earned
        ))
    
    return DistributionResponse(
        summary=summary,
        departments=departments,
        employees=employees
    )


@router.get("/rewards", response_model=List[RewardSummary])
async def get_rewards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="検索キーワード"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission)
):
    """景品一覧を取得"""
    
    query = db.query(Reward)
    
    if search:
        query = query.filter(Reward.title.contains(search))
    
    rewards = query.offset(skip).limit(limit).all()
    return rewards


@router.post("/rewards", response_model=RewardSummary)
async def create_reward(
    reward: RewardCreate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission)
):
    """新しい景品を作成"""
    
    db_reward = Reward(
        title=reward.title,
        description=reward.description,
        category=reward.category,
        points_required=reward.points_required,
        stock=reward.stock,
        active=reward.active
    )
    
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    
    return db_reward


@router.put("/rewards/{reward_id}", response_model=RewardSummary)
async def update_reward(
    reward_id: int,
    reward: RewardUpdate,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission)
):
    """景品を更新"""
    
    db_reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not db_reward:
        raise HTTPException(status_code=404, detail="景品が見つかりません")
    
    update_data = reward.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reward, field, value)
    
    db.commit()
    db.refresh(db_reward)
    
    return db_reward


@router.patch("/rewards/{reward_id}/publish")
async def toggle_reward_publish(
    reward_id: int,
    active: bool = Query(..., description="公開状態"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission)
):
    """景品の公開状態を切り替え"""
    
    db_reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not db_reward:
        raise HTTPException(status_code=404, detail="景品が見つかりません")
    
    db_reward.active = active
    db.commit()
    
    return {"message": "公開状態を更新しました", "active": active}


@router.get("/redemptions/summary", response_model=RedemptionResponse)
async def get_redemption_summary(
    start: Optional[date] = Query(None, description="開始日"),
    end: Optional[date] = Query(None, description="終了日"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission),
    company_id: int = Depends(get_user_company_id)
):
    """交換実績サマリーを取得"""
    
    # デフォルト期間設定（今月）
    if not start or not end:
        today = date.today()
        start = date(today.year, today.month, 1)
        if today.month == 12:
            end = date(today.year + 1, 1, 1)
        else:
            end = date(today.year, today.month + 1, 1)
    
    # 交換実績の基本クエリ（redemptionsテーブルが存在する場合）
    # 現状はredemptionsテーブルがないため、仮のデータを返却
    # 実際の実装では、適切なテーブルから集計する
    
    summary = RedemptionSummary(
        total_redemptions=0,
        total_points_used=0,
        period_start=start,
        period_end=end
    )
    
    popularity = []
    
    return RedemptionResponse(
        summary=summary,
        popularity=popularity
    )