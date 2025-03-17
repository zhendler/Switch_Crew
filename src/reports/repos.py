from sqlalchemy.ext.asyncio import AsyncSession


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_report(self, report):
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

