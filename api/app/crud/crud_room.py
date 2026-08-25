from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.schemas.room import RoomCreate


async def get(db: AsyncSession, room_id: int) -> Room | None:
    result = await db.execute(select(Room).where(Room.id == room_id))
    return result.scalars().first()


async def get_by_slug(db: AsyncSession, slug: str) -> Room | None:
    result = await db.execute(select(Room).where(Room.slug == slug))
    return result.scalars().first()


async def get_by_name(db: AsyncSession, name: str) -> Room | None:
    result = await db.execute(select(Room).where(Room.name == name))
    return result.scalars().first()


async def get_all(db: AsyncSession) -> list[Room]:
    result = await db.execute(select(Room).order_by(Room.id))
    return list(result.scalars().all())


async def create(db: AsyncSession, room_in: RoomCreate) -> Room:
    room = Room(
        slug=room_in.slug,
        name=room_in.name,
        topic=room_in.topic,
        description=room_in.description,
    )
    db.add(room)
    await db.flush()
    await db.refresh(room)
    return room


async def delete(db: AsyncSession, room: Room) -> None:
    await db.delete(room)
