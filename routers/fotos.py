from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from database import get_db
from models import Publicacion, PublicacionFoto, User
from schemas import FotoCreate, FotoResponse
from security import get_current_user, utcnow

router = APIRouter(prefix="/publicaciones", tags=["fotos"])


def _publicacion_propia(publicacion_id: UUID, db: Session, usuario: User) -> Publicacion:
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicacion no encontrada")
    if publicacion.propietario_id != usuario.id:
        raise HTTPException(status_code=403, detail="No sos el propietario de esta publicacion")
    return publicacion


@router.get("/{publicacion_id}/fotos", response_model=list[FotoResponse])
def listar_fotos(publicacion_id: UUID, db: Session = Depends(get_db)):
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicacion no encontrada")
    return publicacion.fotos


@router.post("/{publicacion_id}/fotos", response_model=FotoResponse, status_code=201)
def agregar_foto(
    publicacion_id: UUID,
    foto: FotoCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    # Antes esto insertaba sin validar la publicacion: un id inexistente reventaba
    # como 500 por violacion de FK.
    publicacion = _publicacion_propia(publicacion_id, db, usuario)

    orden = foto.orden
    if orden is None:
        ordenes = [f.orden for f in publicacion.fotos if f.orden is not None]
        orden = (max(ordenes) + 1) if ordenes else 0

    ahora = utcnow()
    nueva_foto = PublicacionFoto(
        id=uuid4(),
        publicacion_id=publicacion_id,
        url=foto.url,
        orden=orden,
        created_at=ahora,
        updated_at=ahora,
    )

    db.add(nueva_foto)
    db.commit()
    db.refresh(nueva_foto)
    return nueva_foto


@router.delete("/{publicacion_id}/fotos/{foto_id}")
def eliminar_foto(
    publicacion_id: UUID,
    foto_id: UUID,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    _publicacion_propia(publicacion_id, db, usuario)

    foto = (
        db.query(PublicacionFoto)
        .filter(
            PublicacionFoto.id == foto_id,
            PublicacionFoto.publicacion_id == publicacion_id,
        )
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")

    db.delete(foto)
    db.commit()
    return {"message": "Foto eliminada correctamente"}
