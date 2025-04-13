from fastapi import HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.mail_utils import send_verification_grid
from src.models.models import Photo, Report, User
from src.reports.schemas import ReportPhotoCreate, ReportStatus


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_comment_report(self, report):
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def check_photo_exists(self, photo_id: int):
        """Перевіряє, чи існує фото в базі даних."""
        result = await self.session.execute(select(Photo).where(Photo.id == photo_id))
        return result.scalar_one_or_none()

    async def create_photo_report(self, report: ReportPhotoCreate, user_id: int, photo) -> Report:
        """Створює новий запис скарги на фото."""
        new_report = Report(
            reported_user_id=photo.owner_id,
            photo_id=report.photo_id,
            user_id=user_id,
            status=ReportStatus.PENDING,  # Скарга починається зі статусу "очікує розгляду"
            reason=report.reason
        )
        self.session.add(new_report)

        try:
            await self.session.commit()
            await self.session.refresh(new_report)
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("Error creating report")

        return new_report

    async def get_user_reports(self, user_id):
        result = await self.session.execute(select(Report).where(Report.reported_user_id == user_id))
        return result.scalars().all()

    async def resolve_report(self, report_id, status: ReportStatus):
        report = await self.session.get(Report, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        report.status = status
        await self.session.commit()
        await self.session.refresh(report)

        count_result = await self.session.execute(
            select(func.count(Report.id))
            .where(Report.reported_user_id == report.reported_user_id)
            .where(Report.status == ReportStatus.APPROVED)
        )
        count = count_result.scalar_one()

        if count > 2:
            user = await self.session.get(User, report.reported_user_id)
            user.is_banned = True
            await self.session.commit()
            await self.session.refresh(user)
            send_verification_grid("zhendlerbing@gmail.com", "You have been banned")

            return f"Status of report has been changed to '{status}'. User has 5 or more reports. User has been banned"

        return f"Status of report has been changed to '{status}'"
