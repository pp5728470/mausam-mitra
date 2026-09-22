import asyncio
from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.models.user import User

async def verify_db():
    async with AsyncSessionLocal() as session:
        # Check current database info
        db_name = await session.scalar(text("SELECT current_database();"))
        
        # Check admin user
        stmt = select(User).where(User.email == 'admin@mausam.in')
        admin = await session.scalar(stmt)
        
        print(f"Database: {db_name}")
        print(f"Admin Exists: {admin is not None}")

if __name__ == "__main__":
    asyncio.run(verify_db())
