from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from database import get_db
from models import Publicacion, User
from schemas import PublicacionCreate, PublicacionResponse, PublicacionUpdate
from security import get_current_user, utcnow

router = APIRouter(prefix="/publicaciones", tags=["publicaciones"])


def _obtener_publicacion(publicacion_id: UUID, db: Session) -> Publicacion:
    publicacion = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not publicacion:
        raise HTTPException(status_code=404, detail="Publicacion no encontrada")
    return publicacion


def _verificar_propietario(publicacion: Publicacion, usuario: User) -> None:
    if publicacion.propietario_id != usuario.id:
        raise HTTPException(status_code=403, detail="No sos el propietario de esta publicacion")


@router.post("/", response_model=PublicacionResponse, status_code=201)
def crear_publicacion(
    publicacion: PublicacionCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    ahora = utcnow()
    # propietario_id sale del token, no de un query param que cualquiera podia falsear.
    nueva = Publicacion(
        id=uuid4(),
        propietario_id=usuario.id,
        titulo=publicacion.titulo,
        descripcion=publicacion.descripcion,
        direccion=publicacion.direccion,
        estado=publicacion.estado,
        precio=publicacion.precio,
        preferencia_genero=publicacion.preferencia_genero,
        activo=True,
        created_at=ahora,
        updated_at=ahora,
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.get("/", response_model=list[PublicacionResponse])
def listar_publicaciones(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(Publicacion)
        .filter(Publicacion.activo == True)  # noqa: E712
        .order_by(Publicacion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{publicacion_id}", response_model=PublicacionResponse)
def obtener_publicacion(publicacion_id: UUID, db: Session = Depends(get_db)):
    return _obtener_publicacion(publicacion_id, db)


@router.put("/{publicacion_id}", response_model=PublicacionResponse)
def actualizar_publicacion(
    publicacion_id: UUID,
    publicacion: PublicacionUpdate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    pub = _obtener_publicacion(publicacion_id, db)
    _verificar_propietario(pub, usuario)

    for campo, valor in publicacion.model_dump(exclude_unset=True).items():
        setattr(pub, campo, valor)
    pub.updated_at = utcnow()

    db.commit()
    db.refresh(pub)
    return pub


@router.delete("/{publicacion_id}")
def desactivar_publicacion(
    publicacion_id: UUID,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    pub = _obtener_publicacion(publicacion_id, db)
    _verificar_propietario(pub, usuario)

    pub.activo = False
    pub.updated_at = utcnow()

    db.commit()
    return {"message": "Publicacion desactivada correctamente"}
