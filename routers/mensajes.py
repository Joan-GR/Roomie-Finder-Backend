from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database import get_db
from models import Mensaje, User
from schemas import ConversacionResponse, MensajeCreate, MensajeResponse
from security import get_current_user, utcnow

router = APIRouter(prefix="/mensajes", tags=["mensajes"])


@router.post("/", response_model=MensajeResponse, status_code=201)
def enviar_mensaje(
    mensaje: MensajeCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    if mensaje.receptor_id == usuario.id:
        raise HTTPException(status_code=400, detail="No podes enviarte un mensaje a vos mismo")

    receptor = db.query(User).filter(User.id == mensaje.receptor_id).first()
    if not receptor or not receptor.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nuevo = Mensaje(
        id=uuid4(),
        emisor_id=usuario.id,
        receptor_id=mensaje.receptor_id,
        contenido=mensaje.contenido,
        leido=False,
        created_at=utcnow(),
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/conversaciones", response_model=list[ConversacionResponse])
def listar_conversaciones(
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    """Bandeja de entrada: un resumen por cada persona con la que hablaste."""
    mensajes = (
        db.query(Mensaje)
        .filter(or_(Mensaje.emisor_id == usuario.id, Mensaje.receptor_id == usuario.id))
        .order_by(Mensaje.created_at.desc())
        .all()
    )

    conversaciones: dict[UUID, ConversacionResponse] = {}
    for m in mensajes:
        otro_id = m.receptor_id if m.emisor_id == usuario.id else m.emisor_id
        if otro_id not in conversaciones:
            # Como ya viene ordenado desc, el primer mensaje que aparece por cada
            # "otro_id" es el mas reciente de esa conversacion.
            conversaciones[otro_id] = ConversacionResponse(
                usuario_id=otro_id,
                ultimo_mensaje=m.contenido,
                ultimo_mensaje_fecha=m.created_at,
                no_leidos=0,
            )
        if m.receptor_id == usuario.id and not m.leido:
            conversaciones[otro_id].no_leidos += 1

    return list(conversaciones.values())


@router.get("/conversacion/{otro_usuario_id}", response_model=list[MensajeResponse])
def obtener_conversacion(
    otro_usuario_id: UUID,
    desde: Optional[datetime] = None,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    """Historial completo con otro usuario. Con "desde" trae solo lo nuevo (para polling)."""
    query = db.query(Mensaje).filter(
        or_(
            and_(Mensaje.emisor_id == usuario.id, Mensaje.receptor_id == otro_usuario_id),
            and_(Mensaje.emisor_id == otro_usuario_id, Mensaje.receptor_id == usuario.id),
        )
    )
    if desde is not None:
        query = query.filter(Mensaje.created_at > desde)

    return query.order_by(Mensaje.created_at.asc()).all()


@router.put("/conversacion/{otro_usuario_id}/leido")
def marcar_leido(
    otro_usuario_id: UUID,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    actualizados = (
        db.query(Mensaje)
        .filter(
            Mensaje.emisor_id == otro_usuario_id,
            Mensaje.receptor_id == usuario.id,
            Mensaje.leido == False,  # noqa: E712
        )
        .update({"leido": True})
    )
    db.commit()
    return {"message": f"{actualizados} mensajes marcados como leidos"}
