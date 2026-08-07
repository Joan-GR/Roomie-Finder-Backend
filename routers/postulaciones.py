from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from database import get_db
from models import Estado, Postulacion, Publicacion, User
from schemas import (
    EstadoResponse,
    PostulacionCreate,
    PostulacionResponse,
    PostulacionUpdate,
)
from security import get_current_user, utcnow

router = APIRouter(prefix="/postulaciones", tags=["postulaciones"])

ESTADO_INICIAL = "pendiente"


@router.get("/estados", response_model=list[EstadoResponse])
def listar_estados(db: Session = Depends(get_db)):
    """Los ids de estado son necesarios para el PUT, asi que el front los pide aca."""
    return db.query(Estado).all()


@router.get("/mias", response_model=list[PostulacionResponse])
def mis_postulaciones(
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    return db.query(Postulacion).filter(Postulacion.postulante_id == usuario.id).all()


@router.post("/", response_model=PostulacionResponse, status_code=201)
def crear_postulacion(
    postulacion: PostulacionCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    publicacion = (
        db.query(Publicacion).filter(Publicacion.id == postulacion.publicacion_id).first()
    )
    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicacion no encontrada")
    if not publicacion.activo:
        raise HTTPException(status_code=400, detail="La publicacion no esta activa")
    if publicacion.propietario_id == usuario.id:
        raise HTTPException(status_code=400, detail="No podes postularte a tu propia publicacion")

    existe = (
        db.query(Postulacion)
        .filter(
            Postulacion.publicacion_id == postulacion.publicacion_id,
            Postulacion.postulante_id == usuario.id,
        )
        .first()
    )
    if existe:
        raise HTTPException(status_code=400, detail="Ya te postulaste a esta publicacion")

    # El estado inicial lo pone el backend: antes se pedia un estado_id al cliente
    # y la tabla estado estaba vacia, asi que la FK fallaba siempre.
    estado_inicial = db.query(Estado).filter(Estado.estado_actual == ESTADO_INICIAL).first()
    if not estado_inicial:
        raise HTTPException(
            status_code=500,
            detail=f"Falta el estado '{ESTADO_INICIAL}' en la tabla estado",
        )

    ahora = utcnow()
    nueva = Postulacion(
        id=uuid4(),
        publicacion_id=postulacion.publicacion_id,
        postulante_id=usuario.id,
        estado_id=estado_inicial.id,
        created_at=ahora,
        updated_at=ahora,
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/publicacion/{publicacion_id}", response_model=list[PostulacionResponse])
def listar_postulaciones(
    publicacion_id: UUID,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicacion no encontrada")
    if publicacion.propietario_id != usuario.id:
        raise HTTPException(
            status_code=403, detail="Solo el propietario puede ver las postulaciones"
        )

    return db.query(Postulacion).filter(Postulacion.publicacion_id == publicacion_id).all()


@router.put("/{postulacion_id}", response_model=PostulacionResponse)
def actualizar_estado(
    postulacion_id: UUID,
    datos: PostulacionUpdate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    postulacion = db.query(Postulacion).filter(Postulacion.id == postulacion_id).first()
    if not postulacion:
        raise HTTPException(status_code=404, detail="Postulacion no encontrada")

    if postulacion.publicacion is None or postulacion.publicacion.propietario_id != usuario.id:
        raise HTTPException(
            status_code=403, detail="Solo el propietario puede cambiar el estado"
        )

    estado = db.query(Estado).filter(Estado.id == datos.estado_id).first()
    if not estado:
        raise HTTPException(status_code=404, detail="Estado no encontrado")

    postulacion.estado_id = estado.id
    postulacion.updated_at = utcnow()

    db.commit()
    db.refresh(postulacion)
    return postulacion
