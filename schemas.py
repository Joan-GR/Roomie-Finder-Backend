from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from models import GeneroEnum, EstadoPublicacionEnum, PreferenciaGeneroEnum



class UserCreate(BaseModel):
    nombre: str
    apellido: str
    dni: str
    email: EmailStr
    password: str
    fecha_nacimiento: date
    genero: GeneroEnum

class UserResponse(BaseModel):
    id: UUID
    nombre: str
    apellido: str
    email: str
    fecha_nacimiento: date
    genero: GeneroEnum
    foto_perfil_url: Optional[str]
    descripcion: Optional[str]
    preferencias: Optional[str]
    activo: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True



class PublicacionCreate(BaseModel):
    titulo: str
    descripcion: str
    direccion: str
    estado: EstadoPublicacionEnum
    precio: float
    preferencia_genero: PreferenciaGeneroEnum

class PublicacionResponse(BaseModel):
    id: UUID
    propietario_id: UUID
    titulo: str
    descripcion: str
    direccion: str
    estado: EstadoPublicacionEnum
    precio: float
    preferencia_genero: PreferenciaGeneroEnum
    activo: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class PostulacionCreate(BaseModel):
    publicacion_id: UUID
    estado_id: UUID

class PostulacionResponse(BaseModel):
    id: UUID
    publicacion_id: UUID
    postulante_id: UUID
    estado_id: UUID
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class SesionResponse(BaseModel):
    id: UUID
    user_id: UUID
    expira_en: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True