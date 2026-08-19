from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from database import get_db
from models import User
from schemas import UserCreate, UserResponse, UserUpdate
from security import get_current_user, hash_password, utcnow

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=201)
def crear_usuario(user: UserCreate, db: Session = Depends(get_db)):
    existe = db.query(User).filter(User.email == user.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    ahora = utcnow()
    nuevo_usuario = User(
        id=uuid4(),
        nombre=user.nombre,
        apellido=user.apellido,
        dni=user.dni,
        email=user.email,
        password=hash_password(user.password),
        fecha_nacimiento=user.fecha_nacimiento,
        genero=user.genero,
        foto_perfil_url=user.foto_perfil_url,
        descripcion=user.descripcion,
        preferencias=user.preferencias,
        activo=True,
        created_at=ahora,
        updated_at=ahora,
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.get("/", response_model=list[UserResponse])
def listar_usuarios(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(User)
        .filter(User.activo == True)  # noqa: E712 - SQLAlchemy necesita la comparacion
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{user_id}", response_model=UserResponse)
def obtener_usuario(user_id: UUID, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/{user_id}", response_model=UserResponse)
def actualizar_usuario(
    user_id: UUID,
    user: UserUpdate,
    db: Session = Depends(get_db),
    usuario_actual: User = Depends(get_current_user),
):
    if usuario_actual.id != user_id:
        raise HTTPException(status_code=403, detail="Solo podes editar tu propio perfil")

    cambios = user.model_dump(exclude_unset=True)

    # Sin este chequeo el UNIQUE de la base explotaba como 500 en vez de 400.
    nuevo_email = cambios.get("email")
    if nuevo_email and nuevo_email != usuario_actual.email:
        if db.query(User).filter(User.email == nuevo_email).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

    for campo, valor in cambios.items():
        setattr(usuario_actual, campo, valor)
    usuario_actual.updated_at = utcnow()

    db.commit()
    db.refresh(usuario_actual)
    return usuario_actual


@router.delete("/{user_id}")
def desactivar_usuario(
    user_id: UUID,
    db: Session = Depends(get_db),
    usuario_actual: User = Depends(get_current_user),
):
    if usuario_actual.id != user_id:
        raise HTTPException(status_code=403, detail="Solo podes desactivar tu propia cuenta")

    usuario_actual.activo = False
    usuario_actual.updated_at = utcnow()

    # Al desactivar la cuenta se cierran todas sus sesiones abiertas.
    usuario_actual.sesiones.clear()

    db.commit()
    return {"message": "Usuario desactivado correctamente"}
