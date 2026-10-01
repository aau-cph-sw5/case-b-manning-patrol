from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db.main import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(title="Manning Patrol Backend", lifespan=lifespan)


@app.get("/ping")
async def ping():
    return {"message": "up"}
