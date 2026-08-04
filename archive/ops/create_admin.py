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

async def make_admin():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id FROM auth.users WHERE email = 'admin@scholarpath.com'"))
        row = res.fetchone()
        if not row:
            print("User admin@scholarpath.com does not exist. Please create it manually via UI first, or we can use supabase client to create it.")
            return

        user_id = row[0]
        # set role to exam_admin
        await conn.execute(
            text("UPDATE public.user_profiles SET role = 'exam_admin' WHERE id = :uid"),
            {"uid": user_id}
        )
        # Update raw_user_meta_data in auth.users
        await conn.execute(
            text("UPDATE auth.users SET raw_app_meta_data = jsonb_set(COALESCE(raw_app_meta_data, '{}'::jsonb), '{role}', '\"exam_admin\"') WHERE id = :uid"),
            {"uid": user_id}
        )
        print("Updated admin@scholarpath.com to exam_admin")

if __name__ == "__main__":
    asyncio.run(make_admin())
