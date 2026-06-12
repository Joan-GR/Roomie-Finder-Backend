from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Postulacion, Estado
from schemas import PostulacionCreate, PostulacionResponse
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/postulaciones", tags=["postulaciones"])


@router.post("/", response_model=PostulacionResponse)
def crear_postulacion(postulacion: PostulacionCreate, postulante_id: str, db: Session = Depends(get_db)):
    existe = db.query(Postulacion).filter(
        Postulacion.publicacion_id == postulacion.publicacion_id,
        Postulacion.postulante_id == postulante_id
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya te postulaste a esta publicacion")

    nueva = Postulacion(
        id=uuid4(),
        publicacion_id=postulacion.publicacion_id,
        postulante_id=postulante_id,
        estado_id=postulacion.estado_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/{publicacion_id}", response_model=list[PostulacionResponse])
def listar_postulaciones(publicacion_id: str, db: Session = Depends(get_db)):
    return db.query(Postulacion).filter(Postulacion.publicacion_id == publicacion_id).all()


@router.put("/{postulacion_id}")
def actualizar_estado(postulacion_id: str, estado_id: str, db: Session = Depends(get_db)):
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulacion no encontrada")

    # Verificar que el estado existe
    estado = db.query(Estado).filter(Estado.id == estado_id).first()
    if not estado:
        raise HTTPException(status_code=404, detail="Estado no encontrado")

    postulacion.estado_id = estado_id
    postulacion.updated_at = datetime.now()

    db.commit()
    db.refresh(postulacion)
    return {"message": "Estado actualizado correctamente"}