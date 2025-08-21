from datetime import date
from typing import Optional
from pydantic import BaseModel


class EnergyMetrics(BaseModel):
    """エネルギー使用量メトリクス"""
    electricity_kwh: float
    gas_m3: float
    co2_reduction_kg: float


class ComparisonMetrics(BaseModel):
    """前年同期比メトリクス"""
    current_period: EnergyMetrics
    previous_period: EnergyMetrics
    electricity_change_percent: float
    gas_change_percent: float
    co2_change_percent: float


class ParticipationMetrics(BaseModel):
    """参加状況メトリクス"""
    total_employees: int
    participating_employees: int
    participation_rate: float


class AutoReportData(BaseModel):
    """自動レポートデータ"""
    period_start: date
    period_end: date
    energy_metrics: EnergyMetrics
    comparison: ComparisonMetrics
    participation: ParticipationMetrics
    generated_text: str


class AutoReportRequest(BaseModel):
    """自動レポートリクエスト"""
    start_date: date
    end_date: date
    format: str = "pdf"  # pdf or docx