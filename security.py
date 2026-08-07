"""Hasheo de contraseñas, manejo de tokens de sesion y dependencia de autenticacion.

Se usa bcrypt directamente en vez de passlib: passlib 1.7.4 esta sin mantenimiento
y es incompatible con bcrypt >= 4.1 (falla al leer bcrypt.__about__ y revienta con
ValueError en cada hash/verify).
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Sesion, User

# bcrypt solo considera los primeros 72 bytes de la contraseña y desde la version 5
# lanza ValueError si recibe mas, en vez de truncar en silencio.
BCRYPT_MAX_BYTES = 72

DURACION_SESION = timedelta(days=7)

bearer_scheme = HTTPBearer(auto_error=False)


def utcnow() -> datetime:
    """Fecha/hora actual en UTC sin tzinfo.

    Las columnas son TIMESTAMP WITHOUT TIME ZONE. Usar datetime.now() guardaba la
    hora local, asi que un token creado en desarrollo (UTC-3) y leido en produccion
    (UTC) quedaba desfasado 3 horas.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_BYTES:
        raise ValueError("La contraseña no puede superar los 72 bytes")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        return False

    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_BYTES:
        return False

    try:
        return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))
    except ValueError:
        # Hash con formato invalido (por ejemplo, una fila vieja en texto plano).
        return False


def generar_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """La columna se llama token_hash, asi que guardamos el hash y no el token crudo.

    Se usa sha256 y no bcrypt a proposito: el token ya tiene 256 bits de entropia,
    no necesita key stretching, y esto se ejecuta en cada request autenticado.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resuelve el usuario dueño del token del header Authorization: Bearer <token>."""
    no_autorizado = HTTPException(
        status_code=401,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or not credentials.credentials:
        raise no_autorizado

    sesion = (
        db.query(Sesion)
        .filter(Sesion.token_hash == hash_token(credentials.credentials))
        .first()
    )
    if not sesion:
        raise no_autorizado

    if sesion.expira_en is not None and sesion.expira_en < utcnow():
        db.delete(sesion)
        db.commit()
        raise HTTPException(status_code=401, detail="La sesion expiro")

    usuario = db.query(User).filter(User.id == sesion.user_id).first()
    if not usuario:
        raise no_autorizado
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    return usuario
