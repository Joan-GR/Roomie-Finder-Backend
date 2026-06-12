from fastapi import FastAPI
from database import engine, Base
from routers import users, publicaciones, auth
from routers import postulaciones
from routers import fotos

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(publicaciones.router)
app.include_router(auth.router)
app.include_router(postulaciones.router)
app.include_router(fotos.router)


@app.get("/")
def root():
    return {"message": "cuandoyolavi"}