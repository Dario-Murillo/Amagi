from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    # Lowercase letters, digits and hyphens only: the slug travels in the
    # WebSocket path, so anything needing escaping there is rejected here.
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=50)


class RoomResponse(BaseModel):
    id: int
    slug: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
