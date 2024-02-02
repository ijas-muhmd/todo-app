from fastapi import APIRouter, File, UploadFile, HTTPException, Form
import os

from models.todos import Todo
from config.database import collection_name

from schema.schemas import list_serializer, individual_serializer
from bson import ObjectId

router = APIRouter()


@router.get("/")
async def get_todos():
    todos = list_serializer(collection_name.find())
    return todos


@router.get("/{id}")
async def get_todo(id: str):
    return list_serializer(collection_name.find_one({"_id": ObjectId(id)}))


@router.post("/")
async def create_todo(todo: Todo):
    _id = collection_name.insert_one(dict(todo))
    return list_serializer(collection_name.find({"_id": _id.inserted_id}))


@router.put("/{id}")
async def update_todo(id: str,
                      name: str = Form(...),
                      description: str = Form(...),
                      completed: bool = Form(...),
                      image: UploadFile = File(default=None)):
    try:

        todo_data = {"name": name, "description": description, "completed": completed}
        todo = Todo(**todo_data)

        todo_doc = collection_name.find_one({"_id": ObjectId(id)})
        if not todo_doc:
            raise HTTPException(status_code=404, detail="Todo not found")

        allowed_mime_types = ["image/jpeg", "image/png", "image/gif"]
        if image and image.content_type not in allowed_mime_types:
            raise HTTPException(status_code=400, detail="The uploaded file must be an image (JPEG, PNG, or GIF).")

        if completed and not image:
            raise HTTPException(status_code=400, detail="An image must be uploaded when marking a todo as completed.")

        image_path = None
        if todo.completed and image:
            filename = f"todo_{id}_{image.filename}"
            image_path = os.path.join("images", filename)
            with open(image_path, "wb") as f:
                f.write(await image.read())

        if image_path:
            todo.image_path = image_path

        collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": todo.dict()})
        updated_todo = collection_name.find_one({"_id": ObjectId(id)})

        return individual_serializer(updated_todo)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
async def delete_todo(id: str):
    collection_name.find_one_and_delete({"_id": ObjectId(id)})
    return {"status": "ok"}
