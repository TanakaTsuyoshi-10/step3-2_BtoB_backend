from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.auth.deps import get_current_admin_user
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.user import User
from app.models.point import Point
from app.models.employee import Employee
from app.models.energy_record import EnergyRecord

router = APIRouter()

class PointsSummary(BaseModel):
    total_points_earned: int
    total_points_used: int
    total_employees: int
    active_employees: int
    average_points_per_employee: float
    monthly_growth_rate: float

class EmployeePointsData(BaseModel):
    user_id: int
    employee_name: str
    department: str
    total_points: int
    current_balance: int
    monthly_earned: int
    utilization_rate: float
    last_activity: Optional[datetime]

class DepartmentDistribution(BaseModel):
    department: str
    employee_count: int
    total_points: int
    average_points: float

class MonthlyTrend(BaseModel):
    month: str
    points_earned: int
    points_used: int
    active_users: int

@router.get("/summary", response_model=PointsSummary)
async def get_points_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """組織全体のポイント集計サマリーを取得"""
    
    # 日付範囲の設定
    if start_date and end_date:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    else:
        end = datetime.now()
        start = end - timedelta(days=30)
    
    # 全体統計
    total_earned = db.query(func.sum(Point.points)).filter(
        Point.earned_at.between(start, end),
        Point.points > 0
    ).scalar() or 0
    
    total_used = db.query(func.sum(Point.points)).filter(
        Point.earned_at.between(start, end),
        Point.points < 0
    ).scalar() or 0
    
    total_employees = db.query(User).join(Employee).count()
    
    active_employees = db.query(func.count(func.distinct(Point.user_id))).filter(
        Point.earned_at.between(start, end)
    ).scalar() or 0
    
    average_points = total_earned / total_employees if total_employees > 0 else 0
    
    # 前月比較
    prev_start = start - timedelta(days=30)
    prev_end = start
    prev_earned = db.query(func.sum(Point.points)).filter(
        Point.earned_at.between(prev_start, prev_end),
        Point.points > 0
    ).scalar() or 0
    
    growth_rate = ((total_earned - prev_earned) / prev_earned * 100) if prev_earned > 0 else 0
    
    return PointsSummary(
        total_points_earned=abs(total_earned),
        total_points_used=abs(total_used),
        total_employees=total_employees,
        active_employees=active_employees,
        average_points_per_employee=average_points,
        monthly_growth_rate=growth_rate
    )

@router.get("/employees", response_model=List[EmployeePointsData])
async def get_employee_points(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("total_points"),
    order: Optional[str] = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """従業員別ポイント詳細データを取得"""
    
    # 基本クエリ - Employeeレコードがあるユーザーのみ
    query = db.query(User).join(Employee)
    
    # 検索フィルター
    if search:
        query = query.filter(User.full_name.contains(search))
    
    if department:
        query = query.filter(Employee.department == department)
    
    users = query.offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # ユーザーのポイント統計
        total_earned = db.query(func.sum(Point.points)).filter(
            Point.user_id == user.id,
            Point.points > 0
        ).scalar() or 0
        
        total_used = db.query(func.sum(Point.points)).filter(
            Point.user_id == user.id,
            Point.points < 0
        ).scalar() or 0
        
        current_balance = total_earned + total_used
        
        # 今月の獲得ポイント
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_earned = db.query(func.sum(Point.points)).filter(
            Point.user_id == user.id,
            Point.points > 0,
            Point.earned_at >= month_start
        ).scalar() or 0
        
        # 利用率
        utilization_rate = (abs(total_used) / total_earned * 100) if total_earned > 0 else 0
        
        # 最後の活動
        last_activity = db.query(Point.earned_at).filter(
            Point.user_id == user.id
        ).order_by(Point.earned_at.desc()).first()
        
        # 従業員情報取得
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        
        result.append(EmployeePointsData(
            user_id=user.id,
            employee_name=user.full_name or user.email,
            department=employee.department if employee else "未設定",
            total_points=total_earned,
            current_balance=current_balance,
            monthly_earned=monthly_earned,
            utilization_rate=round(utilization_rate, 1),
            last_activity=last_activity[0] if last_activity else None
        ))
    
    # ソート
    if sort_by == "total_points":
        result.sort(key=lambda x: x.total_points, reverse=(order == "desc"))
    elif sort_by == "current_balance":
        result.sort(key=lambda x: x.current_balance, reverse=(order == "desc"))
    elif sort_by == "utilization_rate":
        result.sort(key=lambda x: x.utilization_rate, reverse=(order == "desc"))
    
    return result

@router.get("/distribution", response_model=List[DepartmentDistribution])
async def get_department_distribution(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """部門別ポイント分布を取得"""
    
    departments = db.query(
        Employee.department,
        func.count(Employee.id).label('employee_count')
    ).filter(
        Employee.department.isnot(None)
    ).group_by(Employee.department).all()
    
    result = []
    for dept_name, emp_count in departments:
        # 部門の総ポイント
        total_points = db.query(func.sum(Point.points)).join(User).join(Employee).filter(
            Employee.department == dept_name,
            Point.points > 0
        ).scalar() or 0
        
        average_points = total_points / emp_count if emp_count > 0 else 0
        
        result.append(DepartmentDistribution(
            department=dept_name,
            employee_count=emp_count,
            total_points=total_points,
            average_points=round(average_points, 1)
        ))
    
    return sorted(result, key=lambda x: x.total_points, reverse=True)

@router.get("/trends", response_model=List[MonthlyTrend])
async def get_monthly_trends(
    months: int = Query(6, ge=1, le=24),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """月次ポイント推移を取得"""
    
    result = []
    current_date = datetime.now()
    
    for i in range(months):
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 1:
            next_month_start = month_start.replace(year=month_start.year + 1, month=2)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)
        
        # 月間獲得ポイント
        earned = db.query(func.sum(Point.points)).filter(
            Point.earned_at.between(month_start, next_month_start),
            Point.points > 0
        ).scalar() or 0
        
        # 月間使用ポイント
        used = db.query(func.sum(Point.points)).filter(
            Point.earned_at.between(month_start, next_month_start),
            Point.points < 0
        ).scalar() or 0
        
        # アクティブユーザー数
        active_users = db.query(func.count(func.distinct(Point.user_id))).filter(
            Point.earned_at.between(month_start, next_month_start)
        ).scalar() or 0
        
        result.append(MonthlyTrend(
            month=f"{month_start.year}/{month_start.month:02d}",
            points_earned=earned,
            points_used=abs(used),
            active_users=active_users
        ))
        
        # 前月に移動
        if current_date.month == 1:
            current_date = current_date.replace(year=current_date.year - 1, month=12)
        else:
            current_date = current_date.replace(month=current_date.month - 1)
    
    return list(reversed(result))