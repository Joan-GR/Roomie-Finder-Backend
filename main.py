from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import users, publicaciones, auth, postulaciones, fotos

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # url de front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(publicaciones.router)
app.include_router(postulaciones.router)
app.include_router(fotos.router)

@app.get("/")
def root():
    return {"message": "Roomie Finder API funcionando"}