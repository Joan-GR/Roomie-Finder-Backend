from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Sesion
from passlib.context import CryptContext
from uuid import uuid4
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):

    usuario = db.query(User).filter(User.email == email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not pwd_context.verify(password, usuario.password):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token = secrets.token_hex(32)

    sesion = Sesion(
        id=uuid4(),
        user_id=usuario.id,
        token_hash=token,
        expira_en=datetime.now() + timedelta(days=7),
        created_at=datetime.now()
    )

    db.add(sesion)
    db.commit()

    return {
        "token": token,
        "user_id": str(usuario.id),
        "expira_en": sesion.expira_en
    }


@router.post("/logout")
def logout(token: str, db: Session = Depends(get_db)):
    sesion = db.query(Sesion).filter(Sesion.token_hash == token).first()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")

    db.delete(sesion)
    db.commit()

    return {"message": "Sesion cerrada correctamente"}