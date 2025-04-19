from pydantic import BaseModel

# For reading
class UserRead(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True  # 👈 Required to work with ORM objects

# For creating
class UserCreate(BaseModel):
    name: str
    email: str
