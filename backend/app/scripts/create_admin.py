import asyncio
import os
import sys

from sqlalchemy import select

from app.core.enums import Role
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User


async def create_admin() -> None:
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    
    if not email or not password:
        print("ERROR: ADMIN_EMAIL and ADMIN_PASSWORD environment variables are required.")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            print(f"Admin user with email {email} already exists.")
            sys.exit(0)
            
        admin = User(
            email=email,
            full_name="System Admin",
            password_hash=get_password_hash(password),
            role=Role.ADMIN,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin user {email} created successfully.")


if __name__ == "__main__":
    asyncio.run(create_admin())
