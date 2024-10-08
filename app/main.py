from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import RefreshTokenMiddleware
from app.users.router import router as users_router
from app.cameras.router import router as cameras_router
from app.authorization.router import router as authorization_router


app = FastAPI()

app.include_router(authorization_router)
app.include_router(users_router)
app.include_router(cameras_router)

origins = ["*"]

app.add_middleware(RefreshTokenMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Set-Cookie", "Access-Control-Allow-Origin", "Access-Control-Allow-Headers"],
)
