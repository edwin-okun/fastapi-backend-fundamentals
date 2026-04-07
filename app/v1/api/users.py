from dataclasses import dataclass
from itertools import cycle
import uuid
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/users", tags=["users"])

@dataclass
class User:
    id: uuid.UUID
    name: str


users: list[User] = [
    User(id=uuid.uuid4(), name="Alice"),
    User(id=uuid.uuid4(), name="Bob"),
]

POSSIBLE_RESPONSES = [status.HTTP_201_CREATED, status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE, status.HTTP_504_GATEWAY_TIMEOUT]
RESPONSE_CYCLE = cycle(POSSIBLE_RESPONSES)

@router.get("/all", response_model=list[User])
async def get_users():
    return users


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: uuid.UUID):
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/create", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(name: str):
    # reliably simulate transient errors
    response_status = next(RESPONSE_CYCLE)
    if response_status not in {status.HTTP_201_CREATED, status.HTTP_200_OK}:
        raise HTTPException(status_code=response_status, detail="Service unavailable")

    new_user = User(id=uuid.uuid4(), name=name)
    users.append(new_user)
    return new_user
