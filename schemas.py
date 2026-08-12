from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from models import GeneroEnum, EstadoPublicacionEnum, PreferenciaGeneroEnum


# bcrypt trabaja sobre bytes, no sobre caracteres: "ñ" ocupa 2 bytes en UTF-8.
# Validar por len(str) dejaba pasar contraseñas que bcrypt despues rechazaba.
def _validar_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if len(v.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes")
    return v


class UserCreate(BaseModel):
    nombre: str = Field(min_length=1)
    apellido: str = Field(min_length=1)
    dni: str = Field(min_length=1)
    email: EmailStr
    password: str
    fecha_nacimiento: date
    genero: GeneroEnum
    descripcion: Optional[str] = None
    preferencias: Optional[str] = None

    _check_password = field_validator("password")(_validar_password)

    @field_validator("fecha_nacimiento")
    @classmethod
    def mayor_de_edad(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        return v


class UserUpdate(BaseModel):
    """Todos los campos son opcionales: un PUT de perfil no deberia exigir la contraseña."""

    nombre: Optional[str] = Field(default=None, min_length=1)
    apellido: Optional[str] = Field(default=None, min_length=1)
    dni: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = None
    fecha_nacimiento: Optional[date] = None
    genero: Optional[GeneroEnum] = None
    foto_perfil_url: Optional[str] = None
    descripcion: Optional[str] = None
    preferencias: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    nombre: Optional[str]
    apellido: Optional[str]
    email: Optional[str]
    fecha_nacimiento: Optional[date]
    genero: Optional[GeneroEnum]
    foto_perfil_url: Optional[str]
    descripcion: Optional[str]
    preferencias: Optional[str]
    activo: Optional[bool]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user_id: UUID
    expira_en: datetime


class PublicacionCreate(BaseModel):
    titulo: str = Field(min_length=1)
    descripcion: str = Field(min_length=1)
    direccion: str = Field(min_length=1)
    estado: EstadoPublicacionEnum = EstadoPublicacionEnum.activo
    precio: float = Field(ge=0)
    preferencia_genero: PreferenciaGeneroEnum = PreferenciaGeneroEnum.indiferente


class PublicacionUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=1)
    descripcion: Optional[str] = Field(default=None, min_length=1)
    direccion: Optional[str] = Field(default=None, min_length=1)
    estado: Optional[EstadoPublicacionEnum] = None
    precio: Optional[float] = Field(default=None, ge=0)
    preferencia_genero: Optional[PreferenciaGeneroEnum] = None


class FotoResponse(BaseModel):
    id: UUID
    publicacion_id: UUID
    url: str
    orden: Optional[int]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class PublicacionResponse(BaseModel):
    id: UUID
    propietario_id: Optional[UUID]
    titulo: Optional[str]
    descripcion: Optional[str]
    direccion: Optional[str]
    estado: Optional[EstadoPublicacionEnum]
    precio: Optional[float]
    preferencia_genero: Optional[PreferenciaGeneroEnum]
    activo: Optional[bool]
    created_at: Optional[datetime]
    fotos: list[FotoResponse] = []

    class Config:
        from_attributes = True


class FotoCreate(BaseModel):
    url: str = Field(min_length=1)
    orden: Optional[int] = None


class PostulacionCreate(BaseModel):
    """estado_id ya no se pide: el backend asigna 'pendiente' al crear."""

    publicacion_id: UUID


class PostulacionUpdate(BaseModel):
    estado_id: UUID


class EstadoResponse(BaseModel):
    id: UUID
    estado_actual: Optional[str]

    class Config:
        from_attributes = True


class PostulacionResponse(BaseModel):
    id: UUID
    publicacion_id: Optional[UUID]
    postulante_id: Optional[UUID]
    estado_id: Optional[UUID]
    estado: Optional[EstadoResponse]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class SesionResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    expira_en: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
