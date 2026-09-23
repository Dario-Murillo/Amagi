from datetime import datetime

from pydantic import BaseModel

# One page of history: what a room shows on entry, and what each scroll to the
# top loads before it.
MESSAGE_PAGE_SIZE = 100


class MessageResponse(BaseModel):
    """Same field names as the `message` broadcast, so the client reads history
    and live frames through one code path."""

    id: int
    username: str
    message: str
    timestamp: datetime
