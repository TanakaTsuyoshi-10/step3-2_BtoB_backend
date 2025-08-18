from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, extract
from datetime import datetime, date

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.reward import Reward
from app.models.point_rule import PointRule
from app.models.reduction_record import ReductionRecord
from app.models.points_ledger import PointsLedger
from app.schemas.rewards import RewardCreate, RewardUpdate, Reward as RewardSchema
from app.schemas.points import PointRuleCreate, PointRuleUpdate, PointRule as PointRuleSchema

router = APIRouter()


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """管理者権限チェック"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user


# 景品管理
@router.get("/rewards", response_model=List[RewardSchema])
def get_all_rewards(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """全景品を取得（管理者用）"""
    return db.query(Reward).order_by(desc(Reward.created_at)).all()


@router.post("/rewards", response_model=RewardSchema)
def create_reward(
    reward_data: RewardCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """景品を作成"""
    reward = Reward(**reward_data.dict())
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return reward


@router.put("/rewards/{reward_id}", response_model=RewardSchema)
def update_reward(
    reward_id: int,
    reward_data: RewardUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """景品を更新"""
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="景品が見つかりません"
        )
    
    update_data = reward_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reward, field, value)
    
    db.commit()
    db.refresh(reward)
    return reward


@router.delete("/rewards/{reward_id}")
def delete_reward(
    reward_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """景品を削除（無効化）"""
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="景品が見つかりません"
        )
    
    reward.active = False
    db.commit()
    return {"message": "景品を無効化しました"}


# ポイントルール管理
@router.get("/points-rules", response_model=List[PointRuleSchema])
def get_point_rules(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """ポイントルール一覧を取得"""
    return db.query(PointRule).order_by(desc(PointRule.created_at)).all()


@router.post("/points-rules", response_model=PointRuleSchema)
def create_point_rule(
    rule_data: PointRuleCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """ポイントルールを作成"""
    rule = PointRule(**rule_data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/points-rules/{rule_id}", response_model=PointRuleSchema)
def update_point_rule(
    rule_id: int,
    rule_data: PointRuleUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """ポイントルールを更新"""
    rule = db.query(PointRule).filter(PointRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ポイントルールが見つかりません"
        )
    
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/points-rules/{rule_id}")
def delete_point_rule(
    rule_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """ポイントルールを削除（無効化）"""
    rule = db.query(PointRule).filter(PointRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ポイントルールが見つかりません"
        )
    
    rule.active = False
    db.commit()
    return {"message": "ポイントルールを無効化しました"}


@router.post("/points/apply-rules")
def apply_point_rules(
    period: str,  # YYYY-MM format
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """指定期間のポイントルールを一括適用"""
    
    try:
        year, month = map(int, period.split('-'))
        start_date = date(year, month, 1)
        # 次月の1日を計算
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="期間はYYYY-MM形式で指定してください"
        )
    
    # アクティブなper_kgルールを取得
    per_kg_rules = db.query(PointRule).filter(
        PointRule.rule_type == 'per_kg',
        PointRule.active == True
    ).all()
    
    if not per_kg_rules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="アクティブなper_kgルールが見つかりません"
        )
    
    # 指定期間の削減記録を取得
    reduction_records = db.query(ReductionRecord).filter(
        ReductionRecord.date >= start_date,
        ReductionRecord.date < end_date
    ).all()
    
    points_awarded = 0
    users_processed = set()
    
    # ユーザーごとに集計してポイント付与
    user_totals = {}
    for record in reduction_records:
        if record.user_id not in user_totals:
            user_totals[record.user_id] = 0
        user_totals[record.user_id] += record.reduced_co2_kg
    
    # ポイント付与
    for user_id, total_co2 in user_totals.items():
        for rule in per_kg_rules:
            points = int(total_co2 * rule.value)
            if points > 0:
                # 現在の残高を取得
                latest_ledger = db.query(PointsLedger).filter(
                    PointsLedger.user_id == user_id
                ).order_by(desc(PointsLedger.created_at)).first()
                
                current_balance = latest_ledger.balance_after if latest_ledger else 0
                new_balance = current_balance + points
                
                # ポイント付与記録
                points_record = PointsLedger(
                    user_id=user_id,
                    delta=points,
                    reason=f"{period} {rule.name} (CO2削減: {total_co2:.2f}kg)",
                    balance_after=new_balance
                )
                db.add(points_record)
                points_awarded += points
                users_processed.add(user_id)
    
    db.commit()
    
    return {
        "message": f"{period}のポイントルールを適用しました",
        "users_processed": len(users_processed),
        "total_points_awarded": points_awarded
    }