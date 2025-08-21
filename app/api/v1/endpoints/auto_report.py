from datetime import date, datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
import io

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.employee import Employee
from app.models.device import Device
from app.models.energy_record import EnergyRecord
from app.schemas.user import User as UserSchema
from app.schemas.report_auto import AutoReportData, EnergyMetrics, ComparisonMetrics, ParticipationMetrics
from app.services.report_writer import ReportWriter

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


def calculate_energy_metrics(
    db: Session, 
    company_id: int, 
    start_date: date, 
    end_date: date
) -> EnergyMetrics:
    """期間のエネルギーメトリクスを計算"""
    
    # エネルギーデバイスタイプ
    electricity_types = ["スマートメーター", "エアコン", "照明システム", "冷蔵庫", "electric_meter"]
    gas_types = ["ガスメーター", "ガス給湯器", "暖房器具", "gas_meter"]
    
    # 電力使用量
    electricity_query = db.query(func.sum(EnergyRecord.energy_consumed)).join(Device).join(User).join(Employee).filter(
        Employee.company_id == company_id,
        Device.device_type.in_(electricity_types),
        EnergyRecord.timestamp >= start_date,
        EnergyRecord.timestamp < end_date
    )
    electricity_kwh = electricity_query.scalar() or 0.0
    
    # ガス使用量
    gas_query = db.query(func.sum(EnergyRecord.energy_consumed)).join(Device).join(User).join(Employee).filter(
        Employee.company_id == company_id,
        Device.device_type.in_(gas_types),
        EnergyRecord.timestamp >= start_date,
        EnergyRecord.timestamp < end_date
    )
    gas_m3 = gas_query.scalar() or 0.0
    
    # CO2削減量計算（電力: 0.518kg-CO2/kWh、ガス: 2.23kg-CO2/m³）
    co2_reduction_kg = (electricity_kwh * 0.518) + (gas_m3 * 2.23)
    
    return EnergyMetrics(
        electricity_kwh=float(electricity_kwh),
        gas_m3=float(gas_m3),
        co2_reduction_kg=float(co2_reduction_kg)
    )


def calculate_participation_metrics(
    db: Session, 
    company_id: int, 
    start_date: date, 
    end_date: date
) -> ParticipationMetrics:
    """参加状況メトリクスを計算"""
    
    # 全従業員数
    total_employees = db.query(Employee).filter(Employee.company_id == company_id).count()
    
    # 参加従業員数（期間中にエネルギーレコードがある従業員）
    participating_query = db.query(func.count(func.distinct(Employee.user_id))).join(User).join(Device).join(EnergyRecord).filter(
        Employee.company_id == company_id,
        EnergyRecord.timestamp >= start_date,
        EnergyRecord.timestamp < end_date
    )
    participating_employees = participating_query.scalar() or 0
    
    participation_rate = (participating_employees / total_employees * 100) if total_employees > 0 else 0.0
    
    return ParticipationMetrics(
        total_employees=total_employees,
        participating_employees=participating_employees,
        participation_rate=float(participation_rate)
    )


@router.get("/auto", response_model=AutoReportData)
async def get_auto_report_data(
    start: date = Query(..., description="開始日 (YYYY-MM-DD)"),
    end: date = Query(..., description="終了日 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission),
    company_id: int = Depends(get_user_company_id)
):
    """自動レポートデータを取得"""
    
    if start >= end:
        raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")
    
    # 現在期間のメトリクス
    current_metrics = calculate_energy_metrics(db, company_id, start, end)
    
    # 前年同期のメトリクス計算
    period_days = (end - start).days
    prev_start = date(start.year - 1, start.month, start.day)
    prev_end = prev_start + timedelta(days=period_days)
    
    previous_metrics = calculate_energy_metrics(db, company_id, prev_start, prev_end)
    
    # 変化率計算
    def calculate_change_percent(current: float, previous: float) -> float:
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return ((current - previous) / previous) * 100
    
    comparison = ComparisonMetrics(
        current_period=current_metrics,
        previous_period=previous_metrics,
        electricity_change_percent=calculate_change_percent(
            current_metrics.electricity_kwh, previous_metrics.electricity_kwh
        ),
        gas_change_percent=calculate_change_percent(
            current_metrics.gas_m3, previous_metrics.gas_m3
        ),
        co2_change_percent=calculate_change_percent(
            current_metrics.co2_reduction_kg, previous_metrics.co2_reduction_kg
        )
    )
    
    # 参加状況
    participation = calculate_participation_metrics(db, company_id, start, end)
    
    # レポートデータ作成
    report_data = AutoReportData(
        period_start=start,
        period_end=end,
        energy_metrics=current_metrics,
        comparison=comparison,
        participation=participation,
        generated_text=""  # 後で生成
    )
    
    # 生成された文章を追加
    report_data.generated_text = ReportWriter.generate_report_text(report_data)
    
    return report_data


@router.get("/auto/download")
async def download_auto_report(
    start: date = Query(..., description="開始日 (YYYY-MM-DD)"),
    end: date = Query(..., description="終了日 (YYYY-MM-DD)"),
    format: str = Query("pdf", regex="^(pdf|docx)$", description="出力フォーマット (pdf or docx)"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(check_admin_permission),
    company_id: int = Depends(get_user_company_id)
):
    """自動レポートをダウンロード"""
    
    if start >= end:
        raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")
    
    # レポートデータ取得（上記と同じロジック）
    current_metrics = calculate_energy_metrics(db, company_id, start, end)
    
    period_days = (end - start).days
    prev_start = date(start.year - 1, start.month, start.day)
    prev_end = prev_start + timedelta(days=period_days)
    previous_metrics = calculate_energy_metrics(db, company_id, prev_start, prev_end)
    
    def calculate_change_percent(current: float, previous: float) -> float:
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return ((current - previous) / previous) * 100
    
    comparison = ComparisonMetrics(
        current_period=current_metrics,
        previous_period=previous_metrics,
        electricity_change_percent=calculate_change_percent(
            current_metrics.electricity_kwh, previous_metrics.electricity_kwh
        ),
        gas_change_percent=calculate_change_percent(
            current_metrics.gas_m3, previous_metrics.gas_m3
        ),
        co2_change_percent=calculate_change_percent(
            current_metrics.co2_reduction_kg, previous_metrics.co2_reduction_kg
        )
    )
    
    participation = calculate_participation_metrics(db, company_id, start, end)
    
    report_data = AutoReportData(
        period_start=start,
        period_end=end,
        energy_metrics=current_metrics,
        comparison=comparison,
        participation=participation,
        generated_text=""
    )
    
    # フォーマットに応じてファイル生成
    if format == "pdf":
        content = ReportWriter.generate_pdf(report_data)
        media_type = "application/pdf"
        filename = f"環境報告書_{start}_{end}.pdf"
    else:  # docx
        content = ReportWriter.generate_docx(report_data)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"環境報告書_{start}_{end}.docx"
    
    # ストリーミングレスポンス
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )