from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import uuid4

from database import get_db
from models import Sesion, User
from schemas import LoginRequest, LoginResponse, UserResponse
from security import (
    DURACION_SESION,
    bearer_scheme,
    generar_token,
    get_current_user,
    hash_token,
    utcnow,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.email == datos.email).first()

    # Se verifica el password aunque el usuario no exista para no filtrar por
    # el tiempo de respuesta que emails estan registrados.
    password_ok = verify_password(datos.password, usuario.password if usuario else None)
    if not usuario or not password_ok:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token = generar_token()
    ahora = utcnow()

    sesion = Sesion(
        id=uuid4(),
        user_id=usuario.id,
        token_hash=hash_token(token),
        expira_en=ahora + DURACION_SESION,
        created_at=ahora,
    )

    db.add(sesion)
    db.commit()
    db.refresh(sesion)

    # El token en claro solo se devuelve aca; en la base queda unicamente su hash.
    return LoginResponse(
        token=token,
        user_id=usuario.id,
        expira_en=sesion.expira_en,
    )


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="No autenticado")

    sesion = (
        db.query(Sesion)
        .filter(Sesion.token_hash == hash_token(credentials.credentials))
        .first()
    )
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")

    db.delete(sesion)
    db.commit()

    return {"message": "Sesion cerrada correctamente"}


@router.get("/me", response_model=UserResponse)
def usuario_actual(usuario: User = Depends(get_current_user)):
    return usuario
