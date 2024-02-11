
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import os

from jose import jwt, JWTError
from starlette import status
from passlib.context import CryptContext


from models.todos import Todo, TodoUpdate, User
from config.database import collection_name, user_collection

from schema.schemas import list_serializer, individual_serializer, user_serializer
from bson import ObjectId
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user = user_collection.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def authenticate_user(email: str, password: str):
    user = user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return user


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
async def register(user: User):
    if user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = pwd_context.hash(user.hashed_password)
    user.hashed_password = hashed_password

    try:
        user_collection.insert_one(user.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register user: {e}")

    return {"message": "User created successfully"}


@router.get("/")
async def status():
    return {"status": "ok"}


@router.get("/list-all-todo/")
async def get_todos(current_user: User = Depends(get_current_user)):
    todos = list_serializer(collection_name.find())
    return todos


@router.get("/list-one-todo/{id}")
async def get_todo(id: str, current_user: User = Depends(get_current_user)):
    todo_doc = collection_name.find_one({"_id": ObjectId(id)})
    if not todo_doc:
        raise HTTPException(status_code=404, detail="Todo not found")
    return list_serializer(collection_name.find_one({"_id": ObjectId(id)}))


@router.post("/create-todo/")
async def create_todo(todo: Todo, current_user: User = Depends(get_current_user)):
    _id = collection_name.insert_one(dict(todo))
    return list_serializer(collection_name.find({"_id": _id.inserted_id}))


@router.post("/upload-image/{id}")
async def upload_image(id: str, image: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        todo = collection_name.find_one({"_id": ObjectId(id)})
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")

        allowed_mime_types = ["image/jpeg", "image/png", "image/gif"]
        if image.content_type not in allowed_mime_types:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        filename = f"todo_{id}_{image.filename}"
        image_path = os.path.join("images", filename)
        with open(image_path, "wb") as f:
            f.write(await image.read())

        collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": {"image_path": image_path, "completed": True}})
        updated_todo = collection_name.find_one({"_id": ObjectId(id)})

        return individual_serializer(updated_todo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update-todo/{id}")
async def update_todo(id: str, todo_update: TodoUpdate, current_user: User = Depends(get_current_user)):

    todo_doc = collection_name.find_one({"_id": ObjectId(id)})
    if not todo_doc:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    collection_name.find_one_and_update({"_id": ObjectId(id)}, {"$set": todo_update.dict()})
    updated_todo = collection_name.find_one({"_id": ObjectId(id)})

    return individual_serializer(updated_todo)


@router.delete("/delete-todo/{id}")
async def delete_todo(id: str, current_user: User = Depends(get_current_user)):
    todo_doc = collection_name.find_one({"_id": ObjectId(id)})
    if not todo_doc:
        raise HTTPException(status_code=404, detail="Todo not found")

    collection_name.find_one_and_delete({"_id": ObjectId(id)})
    return {"status": "ok"}


@router.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return user_serializer(current_user)
