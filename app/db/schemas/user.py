from pydantic import BaseModel
import uuid

# For reading
class UserRead(BaseModel):
    id: uuid.UUID
    role: str
    name: str | None
    chat_id: int | None

    class Config:
        from_attributes = True  # 👈 Required to work with ORM objects

# For creating
class UserCreate(BaseModel):
    name: str | None = None
    role: str
    chat_id: int | None = None
