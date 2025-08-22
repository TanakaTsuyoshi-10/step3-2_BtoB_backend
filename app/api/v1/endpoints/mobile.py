from typing import Any, List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.reward import Reward
from app.models.redemption import Redemption
from app.models.points_ledger import PointsLedger
from app.schemas.rewards import Reward as RewardSchema, RedemptionCreate

router = APIRouter()


@router.get("/products", response_model=List[RewardSchema])
def get_mobile_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> Any:
    """モバイル向け景品一覧取得 - アクティブな商品のみ"""
    
    products = db.query(Reward).filter(
        Reward.active == True,
        Reward.stock > 0
    ).order_by(desc(Reward.created_at)).all()
    
    return products


@router.post("/redeem")
def redeem_product(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    product_id: int
) -> Any:
    """モバイル向けポイント交換 - 即座にポイント減算して交換記録を作成"""
    
    # 商品存在確認
    product = db.query(Reward).filter(
        Reward.id == product_id,
        Reward.active == True,
        Reward.stock > 0
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品が見つからないか、在庫がありません"
        )
    
    # 現在のポイント残高確認
    latest_ledger = db.query(PointsLedger).filter(
        PointsLedger.user_id == current_user.id
    ).order_by(desc(PointsLedger.created_at)).first()
    
    current_balance = latest_ledger.balance_after if latest_ledger else 0
    
    if current_balance < product.points_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ポイントが不足しています。必要: {product.points_required}pt, 現在: {current_balance}pt"
        )
    
    try:
        # トランザクション開始 - 即座に確定する（approved）
        redemption = Redemption(
            user_id=current_user.id,
            reward_id=product.id,
            points_spent=product.points_required,
            status="承認"  # 即座に承認状態
        )
        db.add(redemption)
        db.flush()  # IDを取得
        
        # ポイント減算記録
        new_balance = current_balance - product.points_required
        points_record = PointsLedger(
            user_id=current_user.id,
            delta=-product.points_required,
            reason=f"商品交換: {product.title}",
            reference_id=redemption.id,
            balance_after=new_balance
        )
        db.add(points_record)
        
        # 在庫減少
        product.stock -= 1
        
        db.commit()
        
        return {
            "message": "交換が完了しました",
            "product_title": product.title,
            "points_spent": product.points_required,
            "new_balance": new_balance,
            "redemption_id": redemption.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"交換処理でエラーが発生しました: {str(e)}"
        )


@router.get("/points/balance")
def get_points_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> Any:
    """現在のポイント残高を取得"""
    
    latest_ledger = db.query(PointsLedger).filter(
        PointsLedger.user_id == current_user.id
    ).order_by(desc(PointsLedger.created_at)).first()
    
    balance = latest_ledger.balance_after if latest_ledger else 0
    
    return {
        "user_id": current_user.id,
        "current_balance": balance,
        "last_updated": latest_ledger.created_at if latest_ledger else None
    }


@router.get("/points/history")
def get_points_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20
) -> Any:
    """ポイント履歴を取得（付与/消費の両方）"""
    
    history = db.query(PointsLedger).filter(
        PointsLedger.user_id == current_user.id
    ).order_by(desc(PointsLedger.created_at)).limit(limit).all()
    
    return {
        "user_id": current_user.id,
        "history": [
            {
                "id": record.id,
                "delta": record.delta,
                "reason": record.reason,
                "balance_after": record.balance_after,
                "created_at": record.created_at,
                "type": "earn" if record.delta > 0 else "spend"
            }
            for record in history
        ]
    }