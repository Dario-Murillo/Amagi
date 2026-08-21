# Importing every model here keeps `Base.metadata` complete, which is what
# Alembic autogenerate walks to diff the schema.
from app.models.message import Message
from app.models.room import Room
from app.models.room_member import RoomMember
from app.models.user import User

__all__ = ["Message", "Room", "RoomMember", "User"]
