from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import UserRecord

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def authenticate_db(session: AsyncSession, email: str, password: str) -> UserRecord | None:
    result = await session.execute(
        select(UserRecord).where(UserRecord.email == email, UserRecord.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user and pwd_context.verify(password, user.password_hash):
        return user
    return None


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    name: str,
    role: str = "member",
    department: str = "pm_rd",
    monday_user_id: str = "",
) -> UserRecord:
    user = UserRecord(
        email=email,
        password_hash=pwd_context.hash(password),
        name=name,
        role=role,
        department=department,
        monday_user_id=monday_user_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_all_users(session: AsyncSession) -> list[UserRecord]:
    result = await session.execute(
        select(UserRecord).where(UserRecord.is_active == True).order_by(UserRecord.name)
    )
    return list(result.scalars().all())


async def seed_default_users(session: AsyncSession) -> None:
    """Seed initial admin + team users if users table is empty."""
    result = await session.execute(select(UserRecord).limit(1))
    if result.scalar_one_or_none():
        return  # already seeded

    # 名字須與 Monday.com 工單中的名字一致
    team = [
        ("lenny.chen@jgbsmart.com", "lenny123", "Lenny", "admin", "pm_rd", "53088175"),
        ("vann.liu@jgbsmart.com", "vann123", "Vann", "member", "pm_rd", "53088137"),
        ("abu.yang@jgbsmart.com", "abu123", "Abu", "member", "pm_rd", "53088145"),
        ("nora.yang@jgbsmart.com", "nora123", "Nora", "member", "pm_rd", "53088268"),
        ("tuo.yu@jgbsmart.com", "tuo123", "Tuo", "member", "pm_rd", "55351402"),
        ("jet.huang@jgbsmart.com", "jet123", "Jet", "member", "pm_rd", "73751177"),
        ("robin.he@jgbsmart.com", "robin123", "Robin", "member", "pm_rd", "97724820"),
        ("hao.chiu@jgbsmart.com", "hao123", "建豪", "member", "pm_rd", "100626370"),
        ("alice.chen@jgbsmart.com", "alice123", "Alice", "member", "marketing", "99367313"),
        ("aurora.lu@jgbsmart.com", "aurora123", "Aurora", "member", "marketing", "100577389"),
    ]

    for email, pwd, name, role, dept, mid in team:
        session.add(UserRecord(
            email=email,
            password_hash=pwd_context.hash(pwd),
            name=name,
            role=role,
            department=dept,
            monday_user_id=mid,
        ))

    await session.commit()
