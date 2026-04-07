from fastapi import FastAPI
from app.v1.api import health_router, users_router


app = FastAPI(root_path="/api/v1")

app.include_router(health_router)
app.include_router(users_router)