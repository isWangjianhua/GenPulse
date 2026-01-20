from typing import Any, Dict, Optional
from sqlalchemy import update, select
from .engine import async_session
from .models import Task
from loguru import logger

class DBManager:
    @staticmethod
    async def create_task(task_id: str, task_type: str, params: Dict[str, Any]):
        async with async_session() as session:
            async with session.begin():
                task = Task(
                    task_id=task_id,
                    task_type=task_type,
                    params=params,
                    status="pending"
                )
                session.add(task)
            await session.commit()
            return task

    @staticmethod
    async def update_task(task_id: str, status: str, progress: int = None, result: Dict[str, Any] = None):
        async with async_session() as session:
            async with session.begin():
                stmt = update(Task).where(Task.task_id == task_id).values(
                    status=status,
                    updated_at=None # Let server_default handle it or specify
                )
                if progress is not None:
                    stmt = stmt.values(progress=progress)
                if result is not None:
                    stmt = stmt.values(result=result)
                
                await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def get_task(task_id: str) -> Optional[Task]:
        async with async_session() as session:
            result = await session.execute(select(Task).where(Task.task_id == task_id))
            return result.scalars().first()

    @staticmethod
    async def list_tasks(limit: int = 50) -> list[Task]:
        async with async_session() as session:
            result = await session.execute(
                select(Task).order_by(Task.created_at.desc()).limit(limit)
            )
            return list(result.scalars().all())

