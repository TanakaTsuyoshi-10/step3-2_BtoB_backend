from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, datetime
import io
import csv
import json
from decimal import Decimal

from app.db.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.reduction_record import ReductionRecord
from app.models.employee import Employee

router = APIRouter()


# 既存のレポート機能は一旦削除（存在しない依存関係のため）
# 新しいCSRレポート機能のみ提供


# 新しいBtoBtoC CSRレポート機能
def get_current_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """管理者権限チェック"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user


@router.post("/csr-export")
def export_csr_report(
    admin_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[Session, Depends(get_db)],
    range_start: str,  # YYYY-MM-DD
    range_end: str,    # YYYY-MM-DD
    granularity: str,  # monthly, quarterly, yearly
    department: str = None,
    format: str = "csv"  # csv or json
):
    """CSRレポートをエクスポート"""
    
    try:
        start_date = datetime.strptime(range_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(range_end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日付はYYYY-MM-DD形式で指定してください"
        )
    
    # データ集計
    query = db.query(
        User.id.label('user_id'),
        User.full_name.label('user_name'),
        Employee.department,
        func.sum(ReductionRecord.reduced_co2_kg).label('total_co2_reduction')
    ).join(
        ReductionRecord, User.id == ReductionRecord.user_id
    ).outerjoin(
        Employee, User.id == Employee.user_id
    ).filter(
        ReductionRecord.date >= start_date,
        ReductionRecord.date <= end_date
    )
    
    if department:
        query = query.filter(Employee.department == department)
    
    results = query.group_by(
        User.id, User.full_name, Employee.department
    ).order_by(desc('total_co2_reduction')).all()
    
    # レポートデータ構築
    total_co2 = sum(r.total_co2_reduction or 0 for r in results)
    
    if format == "json":
        report_data = {
            "企業名": "貴社",
            "期間": f"{range_start} ～ {range_end}",
            "総CO2削減量": round(total_co2, 2),
            "参加者数": len(results),
            "ランキング": [
                {
                    "氏名": r.user_name or f"ユーザー{r.user_id}",
                    "部門": r.department or "未設定",
                    "CO2削減量": round(r.total_co2_reduction or 0, 2)
                }
                for r in results[:10]
            ]
        }
        return Response(
            content=json.dumps(report_data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=csr_report_{range_start}_{range_end}.json"}
        )
    
    else:  # CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["CSRレポート - 従業員CO2削減実績"])
        writer.writerow(["期間", f"{range_start} ～ {range_end}"])
        writer.writerow(["総CO2削減量(kg)", round(total_co2, 2)])
        writer.writerow(["参加者数", len(results)])
        writer.writerow([])
        writer.writerow(["順位", "氏名", "部門", "CO2削減量(kg)"])
        
        for rank, result in enumerate(results[:20], 1):
            writer.writerow([
                rank,
                result.user_name or f"ユーザー{result.user_id}",
                result.department or "未設定",
                round(result.total_co2_reduction or 0, 2)
            ])
        
        writer.writerow([])
        writer.writerow(["注意事項"])
        writer.writerow(["本データは従業員の個人生活におけるエネルギー削減実績です"])
        writer.writerow(["企業の直接的な排出削減とは異なりますが、CSRとして活用可能です"])
        
        csv_content = output.getvalue().encode('utf-8-sig')
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=csr_report_{range_start}_{range_end}.csv"}
        )