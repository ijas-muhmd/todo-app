from typing import Optional

from pydantic import BaseModel


class Todo(BaseModel):
    name: str
    description: str
    completed: bool
    image_path: Optional[str] = None
