from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    id: int
    text: str
    created_at: datetime
    user_id: int
    room_id: int

    model_config = ConfigDict(from_attributes=True)
