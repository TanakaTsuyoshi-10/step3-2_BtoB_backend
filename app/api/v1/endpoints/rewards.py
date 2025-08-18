from typing import Any, List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.reward import Reward
from app.models.redemption import Redemption
from app.models.points_ledger import PointsLedger
from app.schemas.rewards import (
    Reward as RewardSchema,
    RewardCreate,
    RewardUpdate,
    Redemption as RedemptionSchema,
    RedemptionCreate,
    RedemptionWithReward
)

router = APIRouter()


@router.get("/", response_model=List[RewardSchema])
def get_rewards(
    db: Annotated[Session, Depends(get_db)],
    category: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 20
) -> Any:
    """景品一覧を取得"""
    
    query = db.query(Reward).filter(Reward.active == True)
    
    # カテゴリフィルタ
    if category:
        query = query.filter(Reward.category == category)
    
    # 検索フィルタ
    if q:
        query = query.filter(
            Reward.title.contains(q) | Reward.description.contains(q)
        )
    
    # ページネーション
    offset = (page - 1) * limit
    rewards = query.order_by(desc(Reward.created_at)).offset(offset).limit(limit).all()
    
    return rewards


@router.get("/categories")
def get_reward_categories(db: Annotated[Session, Depends(get_db)]) -> Any:
    """景品カテゴリ一覧を取得"""
    
    categories = db.query(Reward.category).filter(
        Reward.active == True
    ).distinct().all()
    
    return [cat[0] for cat in categories]


@router.post("/exchange", response_model=RedemptionSchema)
def exchange_reward(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    exchange_data: RedemptionCreate
) -> Any:
    """景品を交換する"""
    
    # 景品存在確認
    reward = db.query(Reward).filter(
        Reward.id == exchange_data.reward_id,
        Reward.active == True
    ).first()
    
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された景品が見つかりません"
        )
    
    # 在庫確認
    if reward.stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="在庫が不足しています"
        )
    
    # 現在のポイント残高を確認
    latest_ledger = db.query(PointsLedger).filter(
        PointsLedger.user_id == current_user.id
    ).order_by(desc(PointsLedger.created_at)).first()
    
    current_balance = latest_ledger.balance_after if latest_ledger else 0
    
    if current_balance < reward.points_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ポイントが不足しています"
        )
    
    # 交換記録作成
    redemption = Redemption(
        user_id=current_user.id,
        reward_id=reward.id,
        points_spent=reward.points_required,
        status="申請中"
    )
    db.add(redemption)
    db.flush()  # IDを取得するため
    
    # ポイント消費記録
    new_balance = current_balance - reward.points_required
    points_record = PointsLedger(
        user_id=current_user.id,
        delta=-reward.points_required,
        reason=f"景品交換: {reward.title}",
        reference_id=redemption.id,
        balance_after=new_balance
    )
    db.add(points_record)
    
    # 在庫減少
    reward.stock -= 1
    
    db.commit()
    db.refresh(redemption)
    
    return redemption


@router.get("/my-redemptions", response_model=List[RedemptionWithReward])
def get_my_redemptions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> Any:
    """自分の交換履歴を取得"""
    
    redemptions = db.query(Redemption).filter(
        Redemption.user_id == current_user.id
    ).order_by(desc(Redemption.created_at)).all()
    
    result = []
    for redemption in redemptions:
        reward = db.query(Reward).filter(Reward.id == redemption.reward_id).first()
        result.append(RedemptionWithReward(
            **redemption.__dict__,
            reward_title=reward.title if reward else "削除された景品",
            reward_category=reward.category if reward else "不明"
        ))
    
    return result