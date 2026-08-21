from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    id: int
    username: str = Field(min_length=1, max_length=50)


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=20)


class UserResponse(UserBase):
    # Allows returning SQLAlchemy models directly from the endpoints.
    model_config = ConfigDict(from_attributes=True)
