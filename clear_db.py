import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    with open(".env") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                DATABASE_URL = line.split("=", 1)[1].strip()
                break

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")

async def clear():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM responses"))
        await conn.execute(text("DELETE FROM options"))
        await conn.execute(text("DELETE FROM question_stats"))
        await conn.execute(text("DELETE FROM questions"))
        print("Cleared questions data.")

if __name__ == "__main__":
    asyncio.run(clear())
