from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Publicacion
from schemas import PublicacionCreate, PublicacionResponse
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/publicaciones", tags=["publicaciones"])


@router.post("/", response_model=PublicacionResponse)
def crear_publicacion(publicacion: PublicacionCreate, propietario_id: str, db: Session = Depends(get_db)):
    nueva = Publicacion(
        id=uuid4(),
        propietario_id=propietario_id,
        titulo=publicacion.titulo,
        descripcion=publicacion.descripcion,
        direccion=publicacion.direccion,
        estado=publicacion.estado,
        precio=publicacion.precio,
        preferencia_genero=publicacion.preferencia_genero,
        activo=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/", response_model=list[PublicacionResponse])
def listar_publicaciones(db: Session = Depends(get_db)):
    return db.query(Publicacion).filter(Publicacion.activo == True).all()


@router.get("/{publicacion_id}", response_model=PublicacionResponse)
def obtener_publicacion(publicacion_id: str, db: Session = Depends(get_db)):
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicacion no encontrada")
    return publicacion