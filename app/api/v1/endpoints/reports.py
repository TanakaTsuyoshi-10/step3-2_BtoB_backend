from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from datetime import date
import io
import csv
from decimal import Decimal

from app.db.database import get_db
from app.auth.deps import get_current_active_user
from app.models.user import User
from app.services.report import get_report_service, ReportService
from app.schemas.report import (
    Report, 
    ReportCreate, 
    ReportUpdate, 
    ReportSummary,
    ReportExportRequest
)

router = APIRouter()


@router.post("/", response_model=Report)
def create_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """レポート作成"""
    return report_service.create_report(report_data, current_user.email)


@router.get("/", response_model=List[ReportSummary])
def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """レポート一覧取得"""
    reports = report_service.get_reports(
        skip=skip, 
        limit=limit, 
        search=search,
        period_start=period_start,
        period_end=period_end
    )
    return [ReportSummary.from_orm(report) for report in reports]


@router.get("/{report_id}", response_model=Report)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """レポート詳細取得"""
    report = report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.put("/{report_id}", response_model=Report)
def update_report(
    report_id: str,
    report_data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """レポート更新"""
    report = report_service.update_report(report_id, report_data)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/publish", response_model=Report)
def publish_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """レポート確定発行"""
    report = report_service.publish_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    format: str = Query(..., regex="^(csv|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """レポートエクスポート（CSV/PDF）"""
    report = report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if format == "csv":
        return _export_csv(report)
    elif format == "pdf":
        return _export_pdf(report)
    else:
        raise HTTPException(status_code=400, detail="Invalid format")


def _export_csv(report) -> Response:
    """CSV エクスポート"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # ヘッダー情報
    writer.writerow(["レポート名", report.name])
    writer.writerow(["対象期間", f"{report.period_start} - {report.period_end}"])
    writer.writerow(["方法論", report.methodology])
    writer.writerow(["作成者", report.created_by])
    writer.writerow(["ステータス", report.status])
    writer.writerow(["合計削減量(t-CO₂)", f"{report.total_reduction_tonnes}"])
    writer.writerow([])  # 空行
    
    # Scope別合計
    writer.writerow(["Scope", "削減量(kg)", "削減量(t-CO₂)"])
    writer.writerow(["Scope1", float(report.scope1_reduction_kg), round(float(report.scope1_reduction_kg)/1000, 1)])
    writer.writerow(["Scope2", float(report.scope2_reduction_kg), round(float(report.scope2_reduction_kg)/1000, 1)])
    writer.writerow(["Scope3", float(report.scope3_reduction_kg), round(float(report.scope3_reduction_kg)/1000, 1)])
    writer.writerow([])  # 空行
    
    # 明細
    writer.writerow(["サイト名", "設備名", "Scope", "削減量(kg)", "削減量(t-CO₂)"])
    for item in report.items:
        writer.writerow([
            item.site_name,
            item.device_name,
            item.scope,
            float(item.amount_kg),
            round(float(item.amount_kg)/1000, 1)
        ])
    
    if report.notes:
        writer.writerow([])  # 空行
        writer.writerow(["備考", report.notes])
    
    content = output.getvalue()
    output.close()
    
    filename = f"report_{report.name}_{report.period_start}_{report.period_end}.csv"
    
    return Response(
        content=content.encode('utf-8'),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _export_pdf(report) -> Response:
    """PDF エクスポート（簡易HTML版）"""
    # PDFライブラリが複雑なので、まずはHTMLを返す
    # 実際のPDF生成は後で追加可能
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>CO₂削減量レポート - {report.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
            .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
            .card {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CO₂削減量レポート</h1>
            <h2>{report.name}</h2>
            <p>対象期間: {report.period_start} - {report.period_end}</p>
            <p>作成者: {report.created_by} | ステータス: {report.status}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>Scope1</h3>
                <p>{round(float(report.scope1_reduction_kg)/1000, 1)} t-CO₂</p>
            </div>
            <div class="card">
                <h3>Scope2</h3>
                <p>{round(float(report.scope2_reduction_kg)/1000, 1)} t-CO₂</p>
            </div>
            <div class="card">
                <h3>Scope3</h3>
                <p>{round(float(report.scope3_reduction_kg)/1000, 1)} t-CO₂</p>
            </div>
            <div class="card">
                <h3>合計</h3>
                <p>{report.total_reduction_tonnes} t-CO₂</p>
            </div>
        </div>
        
        <h3>削減量内訳</h3>
        <table>
            <thead>
                <tr>
                    <th>サイト名</th>
                    <th>設備名</th>
                    <th>Scope</th>
                    <th>削減量(kg)</th>
                    <th>削減量(t-CO₂)</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f"<tr><td>{item.site_name}</td><td>{item.device_name}</td><td>{item.scope}</td><td>{float(item.amount_kg):,}</td><td>{round(float(item.amount_kg)/1000, 1)}</td></tr>" for item in report.items])}
            </tbody>
        </table>
        
        {f"<h3>備考</h3><p>{report.notes}</p>" if report.notes else ""}
        
        <p><small>方法論: {report.methodology}</small></p>
    </body>
    </html>
    """
    
    return Response(
        content=html_content.encode('utf-8'),
        media_type="text/html",
        headers={"Content-Disposition": f"inline; filename=report_{report.name}.html"}
    )