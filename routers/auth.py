from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import uuid4

from database import get_db
from models import Sesion, User
from oauth import verificar_access_token_facebook, verificar_id_token_google
from rate_limit import verificar_limite
from schemas import (
    FacebookLoginRequest,
    GoogleLoginRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
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


def _crear_sesion(db: Session, usuario: User) -> LoginResponse:
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
    return LoginResponse(token=token, user_id=usuario.id, expira_en=sesion.expira_en)


def _obtener_o_crear_usuario_oauth(
    db: Session, email: str, nombre: str | None, apellido: str | None, foto_url: str | None
) -> User:
    usuario = db.query(User).filter(User.email == email).first()
    if usuario:
        if not usuario.activo:
            raise HTTPException(status_code=403, detail="Cuenta desactivada")
        return usuario

    # Google y Facebook verifican el email antes de entregarlo, asi que confiamos
    # en el y creamos la cuenta. Los datos de perfil (dni, fecha_nacimiento, genero)
    # quedan vacios: el usuario los completa despues con PUT /users/{id}.
    ahora = utcnow()
    usuario = User(
        id=uuid4(),
        nombre=nombre or "",
        apellido=apellido or "",
        dni=None,
        email=email,
        password=None,
        fecha_nacimiento=None,
        genero=None,
        foto_perfil_url=foto_url,
        activo=True,
        created_at=ahora,
        updated_at=ahora,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=LoginResponse)
def login(datos: LoginRequest, request: Request, db: Session = Depends(get_db)):
    verificar_limite(request, "login", limite=5, ventana_segundos=15 * 60)

    usuario = db.query(User).filter(User.email == datos.email).first()

    # Se verifica el password aunque el usuario no exista para no filtrar por
    # el tiempo de respuesta que emails estan registrados.
    password_ok = verify_password(datos.password, usuario.password if usuario else None)
    if not usuario or not password_ok:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    return _crear_sesion(db, usuario)


@router.post("/google", response_model=LoginResponse)
def login_google(datos: GoogleLoginRequest, request: Request, db: Session = Depends(get_db)):
    verificar_limite(request, "oauth", limite=20, ventana_segundos=15 * 60)

    payload = verificar_id_token_google(datos.id_token)
    usuario = _obtener_o_crear_usuario_oauth(
        db,
        email=payload["email"],
        nombre=payload.get("given_name"),
        apellido=payload.get("family_name"),
        foto_url=payload.get("picture"),
    )
    return _crear_sesion(db, usuario)


@router.post("/facebook", response_model=LoginResponse)
def login_facebook(datos: FacebookLoginRequest, request: Request, db: Session = Depends(get_db)):
    verificar_limite(request, "oauth", limite=20, ventana_segundos=15 * 60)

    perfil = verificar_access_token_facebook(datos.access_token)
    nombre, _, apellido = perfil.get("name", "").partition(" ")
    usuario = _obtener_o_crear_usuario_oauth(
        db,
        email=perfil["email"],
        nombre=nombre or None,
        apellido=apellido or None,
        foto_url=None,
    )
    return _crear_sesion(db, usuario)


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
