from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.api.deps import get_current_admin_user
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.models.user import User
from app.models.reward import Reward
from app.models.redemption import Redemption

router = APIRouter()

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    points_required: int
    stock: int
    active: bool
    created_at: datetime
    redemption_count: int

class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    points_required: int
    stock: int
    active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    points_required: Optional[int] = None
    stock: Optional[int] = None
    active: Optional[bool] = None

class RedemptionStatsResponse(BaseModel):
    total_redemptions: int
    monthly_redemptions: int
    total_points_used: int
    low_stock_alerts: int
    period_start: str
    period_end: str

class PopularityItem(BaseModel):
    product_name: str
    category: str
    redemption_count: int
    selection_rate: float
    points_per_redemption: int

@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """商品一覧を取得"""
    
    query = db.query(Reward)
    
    if search:
        query = query.filter(Reward.title.contains(search))
    
    if category:
        query = query.filter(Reward.category == category)
    
    if active is not None:
        query = query.filter(Reward.active == active)
    
    products = query.offset(skip).limit(limit).all()
    
    result = []
    for product in products:
        redemption_count = db.query(Redemption).filter(
            Redemption.reward_id == product.id
        ).count()
        
        result.append(ProductResponse(
            id=product.id,
            name=product.title,
            description=product.description,
            category=product.category,
            points_required=product.points_required,
            stock=product.stock,
            active=product.active,
            created_at=product.created_at,
            redemption_count=redemption_count
        ))
    
    return result

@router.post("/products", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """新しい商品を作成"""
    
    product = Reward(
        title=product_data.name,
        description=product_data.description,
        category=product_data.category,
        points_required=product_data.points_required,
        stock=product_data.stock,
        active=product_data.active
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return ProductResponse(
        id=product.id,
        name=product.title,
        description=product.description,
        category=product.category,
        points_required=product.points_required,
        stock=product.stock,
        active=product.active,
        created_at=product.created_at,
        redemption_count=0
    )

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """商品を更新"""
    
    product = db.query(Reward).filter(Reward.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    redemption_count = db.query(Redemption).filter(
        Redemption.reward_id == product.id
    ).count()
    
    return ProductResponse(
        id=product.id,
        name=product.title,
        description=product.description,
        category=product.category,
        points_required=product.points_required,
        stock=product.stock,
        active=product.active,
        created_at=product.created_at,
        redemption_count=redemption_count
    )

@router.patch("/products/{product_id}/toggle")
async def toggle_product_status(
    product_id: int,
    active: bool,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """商品の公開状態を切り替え"""
    
    product = db.query(Reward).filter(Reward.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.active = active
    db.commit()
    
    return {"message": "Product status updated successfully"}

@router.get("/stats", response_model=RedemptionStatsResponse)
async def get_redemption_stats(
    period: str = Query("month", regex="^(month|quarter|year)$"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """交換実績統計を取得"""
    
    # 期間設定
    end_date = datetime.now()
    if period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    # 統計計算
    total_redemptions = db.query(Redemption).filter(
        Redemption.created_at >= start_date
    ).count()
    
    monthly_redemptions = db.query(Redemption).filter(
        Redemption.created_at >= datetime.now() - timedelta(days=30)
    ).count()
    
    total_points_used = db.query(func.sum(Reward.points_required)).join(
        Redemption, Reward.id == Redemption.reward_id
    ).filter(
        Redemption.created_at >= start_date
    ).scalar() or 0
    
    # 在庫警告数（在庫10個以下）
    low_stock_alerts = db.query(Reward).filter(
        Reward.stock <= 10,
        Reward.active == True
    ).count()
    
    return RedemptionStatsResponse(
        total_redemptions=total_redemptions,
        monthly_redemptions=monthly_redemptions,
        total_points_used=total_points_used,
        low_stock_alerts=low_stock_alerts,
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat()
    )

@router.get("/popularity", response_model=List[PopularityItem])
async def get_product_popularity(
    period: str = Query("month", regex="^(month|quarter|year)$"),
    limit: int = Query(10, ge=1, le=50),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """商品人気度分析を取得"""
    
    # 期間設定
    end_date = datetime.now()
    if period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    # 期間内の総交換回数
    total_redemptions = db.query(Redemption).filter(
        Redemption.created_at >= start_date
    ).count()
    
    # 商品別交換統計
    product_stats = db.query(
        Reward.title,
        Reward.category,
        Reward.points_required,
        func.count(Redemption.id).label('redemption_count')
    ).join(
        Redemption, Reward.id == Redemption.reward_id
    ).filter(
        Redemption.created_at >= start_date
    ).group_by(
        Reward.id, Reward.title, Reward.category, Reward.points_required
    ).order_by(
        desc('redemption_count')
    ).limit(limit).all()
    
    result = []
    for name, category, points, count in product_stats:
        selection_rate = (count / total_redemptions * 100) if total_redemptions > 0 else 0
        
        result.append(PopularityItem(
            product_name=name,
            category=category,
            redemption_count=count,
            selection_rate=round(selection_rate, 1),
            points_per_redemption=points
        ))
    
    return result

@router.get("/categories")
async def get_categories(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """利用可能なカテゴリ一覧を取得"""
    
    categories = db.query(Reward.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]