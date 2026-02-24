import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.modules.catalog.models import ExamBoard, Exam
from app.modules.user.models import UserProfile
from app.modules.attempt.models import Attempt

async def main():
    async with async_session_maker() as session:
        boards = (await session.execute(select(ExamBoard))).scalars().all()
        exams = (await session.execute(select(Exam))).scalars().all()
        users = (await session.execute(select(UserProfile))).scalars().all()
        attempts = (await session.execute(select(Attempt))).scalars().all()
        print(f"Boards: {len(boards)}")
        print(f"Exams: {len(exams)}")
        print(f"Users: {len(users)}")
        print(f"Attempts: {len(attempts)}")
        if exams:
            print(f"Exam 1 name: {exams[0].title_en} (Active: {exams[0].is_active})")

asyncio.run(main())
