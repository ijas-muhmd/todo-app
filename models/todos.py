from typing import Optional

from pydantic import BaseModel


class Todo(BaseModel):
    name: str
    description: str
    completed: bool
    image_path: Optional[str] = None


class TodoUpdate(BaseModel):
    name: str
    description: str


class User(BaseModel):
    email: str
    hashed_password: str

