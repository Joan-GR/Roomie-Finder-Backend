from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import PublicacionFoto
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/publicaciones", tags=["fotos"])


@router.post("/{publicacion_id}/fotos")
def agregar_foto(publicacion_id: str, url: str, orden: int, db: Session = Depends(get_db)):
    nueva_foto = PublicacionFoto(
        id=uuid4(),
        publicacion_id=publicacion_id,
        url=url,
        orden=orden,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(nueva_foto)
    db.commit()
    db.refresh(nueva_foto)
    return {"message": "Foto agregada correctamente", "foto_id": str(nueva_foto.id)}


@router.delete("/{publicacion_id}/fotos/{foto_id}")
def eliminar_foto(publicacion_id: str, foto_id: str, db: Session = Depends(get_db)):
    foto = db.query(PublicacionFoto).filter(
        PublicacionFoto.id == foto_id,
        PublicacionFoto.publicacion_id == publicacion_id
    ).first()
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")

    db.delete(foto)
    db.commit()
    return {"message": "Foto eliminada correctamente"}