from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import date

from app.models.report import Report, ReportItem, StatusEnum
from app.schemas.report import ReportCreate, ReportUpdate


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, report_data: ReportCreate, created_by: str) -> Report:
        """レポート作成"""
        # 明細から合計を計算
        scope1_total, scope2_total, scope3_total = self._calculate_totals(report_data.items)
        
        db_report = Report(
            name=report_data.name,
            period_start=report_data.period_start,
            period_end=report_data.period_end,
            methodology=report_data.methodology,
            scope1_reduction_kg=scope1_total,
            scope2_reduction_kg=scope2_total,
            scope3_reduction_kg=scope3_total,
            total_reduction_kg=scope1_total + scope2_total + scope3_total,
            notes=report_data.notes,
            created_by=created_by
        )
        self.db.add(db_report)
        self.db.flush()  # IDを取得

        # 明細を追加
        for item_data in report_data.items:
            db_item = ReportItem(
                report_id=db_report.id,
                site_name=item_data.site_name,
                device_name=item_data.device_name,
                scope=item_data.scope,
                amount_kg=item_data.amount_kg
            )
            self.db.add(db_item)

        self.db.commit()
        self.db.refresh(db_report)
        return db_report

    def get_reports(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> List[Report]:
        """レポート一覧取得（フィルタ・検索対応）"""
        query = self.db.query(Report)

        # 検索フィルタ
        if search:
            query = query.filter(
                or_(
                    Report.name.contains(search),
                    Report.created_by.contains(search),
                    Report.notes.contains(search)
                )
            )

        # 期間フィルタ
        if period_start:
            query = query.filter(Report.period_start >= period_start)
        if period_end:
            query = query.filter(Report.period_end <= period_end)

        return query.order_by(desc(Report.created_at)).offset(skip).limit(limit).all()

    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """レポート詳細取得（明細含む）"""
        return self.db.query(Report).filter(Report.id == report_id).first()

    def update_report(self, report_id: str, report_data: ReportUpdate) -> Optional[Report]:
        """レポート更新"""
        db_report = self.get_report_by_id(report_id)
        if not db_report:
            return None

        # 既存の明細を削除
        self.db.query(ReportItem).filter(ReportItem.report_id == report_id).delete()

        # ヘッダー更新
        db_report.name = report_data.name
        db_report.period_start = report_data.period_start
        db_report.period_end = report_data.period_end
        db_report.methodology = report_data.methodology
        db_report.notes = report_data.notes

        # 明細から合計を再計算
        scope1_total, scope2_total, scope3_total = self._calculate_totals(report_data.items)
        db_report.scope1_reduction_kg = scope1_total
        db_report.scope2_reduction_kg = scope2_total
        db_report.scope3_reduction_kg = scope3_total
        db_report.total_reduction_kg = scope1_total + scope2_total + scope3_total

        # 新しい明細を追加
        for item_data in report_data.items:
            db_item = ReportItem(
                report_id=report_id,
                site_name=item_data.site_name,
                device_name=item_data.device_name,
                scope=item_data.scope,
                amount_kg=item_data.amount_kg
            )
            self.db.add(db_item)

        self.db.commit()
        self.db.refresh(db_report)
        return db_report

    def publish_report(self, report_id: str) -> Optional[Report]:
        """レポート確定発行"""
        db_report = self.get_report_by_id(report_id)
        if not db_report:
            return None

        db_report.status = StatusEnum.published
        self.db.commit()
        self.db.refresh(db_report)
        return db_report

    def delete_report(self, report_id: str) -> bool:
        """レポート削除"""
        db_report = self.get_report_by_id(report_id)
        if not db_report:
            return False

        self.db.delete(db_report)
        self.db.commit()
        return True

    def _calculate_totals(self, items) -> tuple:
        """明細からScope別合計を計算"""
        scope1_total = sum(item.amount_kg for item in items if item.scope == 'scope1')
        scope2_total = sum(item.amount_kg for item in items if item.scope == 'scope2')
        scope3_total = sum(item.amount_kg for item in items if item.scope == 'scope3')
        return scope1_total, scope2_total, scope3_total


# Dependency injection用のファクトリ関数
def get_report_service(db: Session) -> ReportService:
    return ReportService(db)