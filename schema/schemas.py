def individual_serializer(todo) -> dict:
    return {
        "id": str(todo["_id"]),
        "name": todo["name"],
        "description": todo["description"],
        "completed": todo["completed"],
        "image_path": todo["image_path"]
    }


def list_serializer(todos) -> list:
    return [individual_serializer(todo) for todo in todos]
