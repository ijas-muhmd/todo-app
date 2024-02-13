from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

from models.PyObjectId import DBModelMixin, PyObjectId


class TodoCreate(BaseModel):
    name: str
    description: str
    completed: Optional[bool] = False
    image_path: Optional[str] = None

    
class Todo(DBModelMixin):
    name: str
    description: str
    completed: Optional[bool] = False
    image_path: Optional[str] = None
    created_by: PyObjectId


class TodoUpdate(BaseModel):
    name: str
    description: str


class User(BaseModel):
    email: EmailStr
    hashed_password: str

