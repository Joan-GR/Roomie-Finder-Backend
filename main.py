import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, fotos, postulaciones, publicaciones, users

app = FastAPI(title="Roomie Finder API")

# allow_origins=["*"] junto a allow_credentials=True es invalido segun la spec de CORS
# y el navegador descarta la respuesta. Con tokens Bearer no hacen falta credenciales,
# asi que solo se habilitan si se declaran origenes concretos en CORS_ORIGINS.
origenes = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes or ["*"],
    allow_credentials=bool(origenes),
    allow_methods=["*"],
    allow_headers=["*"],
)

# El esquema se administra con migraciones SQL (ver migrations.sql), no con create_all:
# create_all no altera tablas existentes y en Vercel corria en cada cold start,
# tirando abajo toda la app si la base no respondia.

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(publicaciones.router)
app.include_router(postulaciones.router)
app.include_router(fotos.router)


@app.get("/")
def root():
    return {"message": "Roomie Finder API funcionando"}


@app.get("/health")
def health():
    return {"status": "ok"}
