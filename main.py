from fastapi import FastAPI
from database import engine, Base
from routers import users, publicaciones

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(publicaciones.router)

@app.get("/")
def root():
    return {"message": "cuandoyolavi"}