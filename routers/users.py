from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserResponse
from passlib.context import CryptContext
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/", response_model=UserResponse)
def crear_usuario(user: UserCreate, db: Session = Depends(get_db)):
    # Verificar si el email ya existe
    existe = db.query(User).filter(User.email == user.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    nuevo_usuario = User(
        id=uuid4(),
        nombre=user.nombre,
        apellido=user.apellido,
        dni=user.dni,
        email=user.email,
        password=pwd_context.hash(user.password),
        fecha_nacimiento=user.fecha_nacimiento,
        genero=user.genero,
        activo=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.get("/{user_id}", response_model=UserResponse)
def obtener_usuario(user_id: str, db: Session = Depends(get_db)):
    usuario = db.query(User).filter(User.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario