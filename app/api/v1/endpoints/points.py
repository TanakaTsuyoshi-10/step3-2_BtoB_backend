from typing import Any, List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, extract
from datetime import datetime, date

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.reduction_record import ReductionRecord
from app.models.points_ledger import PointsLedger
from app.models.employee import Employee
from app.schemas.points import PointsSummary, RankingEntry, PointsLedger as PointsLedgerSchema
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/me", response_model=PointsSummary)
def get_my_points(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> Any:
    """現在のユーザーのポイント情報を取得"""
    
    # 現在のポイント残高を取得（最新の記録から）
    latest_ledger = db.query(PointsLedger).filter(
        PointsLedger.user_id == current_user.id
    ).order_by(desc(PointsLedger.created_at)).first()
    
    current_balance = latest_ledger.balance_after if latest_ledger else 0
    
    # 総獲得ポイント（正の値のみ）
    total_earned = db.query(func.sum(PointsLedger.delta)).filter(
        PointsLedger.user_id == current_user.id,
        PointsLedger.delta > 0
    ).scalar() or 0
    
    # 総消費ポイント（負の値の絶対値）
    total_spent = db.query(func.sum(PointsLedger.delta * -1)).filter(
        PointsLedger.user_id == current_user.id,
        PointsLedger.delta < 0
    ).scalar() or 0
    
    # 今月の獲得ポイント
    current_month = datetime.now().month
    current_year = datetime.now().year
    this_month_earned = db.query(func.sum(PointsLedger.delta)).filter(
        PointsLedger.user_id == current_user.id,
        PointsLedger.delta > 0,
        extract('month', PointsLedger.created_at) == current_month,
        extract('year', PointsLedger.created_at) == current_year
    ).scalar() or 0
    
    return PointsSummary(
        current_balance=int(current_balance),
        total_earned=int(total_earned),
        total_spent=int(total_spent),
        this_month_earned=int(this_month_earned)
    )


@router.get("/history", response_model=List[PointsLedgerSchema])
def get_points_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
    offset: int = 0
) -> Any:
    """ポイント履歴を取得"""
    
    history = db.query(PointsLedger).filter(
        PointsLedger.user_id == current_user.id
    ).order_by(desc(PointsLedger.created_at)).offset(offset).limit(limit).all()
    
    return history


@router.get("/ranking", response_model=List[RankingEntry])
def get_ranking(
    db: Annotated[Session, Depends(get_db)],
    period: str = "monthly",  # monthly, quarterly, yearly
    department: str = None,
    limit: int = 100
) -> Any:
    """ランキングを取得"""
    
    # 期間の計算
    today = date.today()
    if period == "monthly":
        start_date = today.replace(day=1)
    elif period == "quarterly":
        # 四半期の開始月を計算
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="期間は monthly, quarterly, yearly のいずれかを指定してください"
        )
    
    # CO2削減量を集計してランキング作成
    query = db.query(
        User.id.label('user_id'),
        User.full_name.label('user_name'),
        Employee.department,
        func.sum(ReductionRecord.reduced_co2_kg).label('reduced_co2_kg')
    ).join(
        ReductionRecord, User.id == ReductionRecord.user_id
    ).outerjoin(
        Employee, User.id == Employee.user_id
    ).filter(
        ReductionRecord.date >= start_date
    )
    
    # 部門フィルタ
    if department:
        query = query.filter(Employee.department == department)
    
    # グループ化とソート
    ranking_data = query.group_by(
        User.id, User.full_name, Employee.department
    ).order_by(
        desc('reduced_co2_kg')
    ).limit(limit).all()
    
    # ランキング作成（ポイント計算含む）
    ranking = []
    for rank, row in enumerate(ranking_data, 1):
        # 簡単なポイント計算（1kg = 10ポイント）
        points_earned = int(row.reduced_co2_kg * 10)
        
        ranking.append(RankingEntry(
            user_id=row.user_id,
            user_name=row.user_name or f"ユーザー{row.user_id}",
            department=row.department,
            reduced_co2_kg=float(row.reduced_co2_kg or 0),
            rank=rank,
            points_earned=points_earned
        ))
    
    return ranking