from sqlalchemy import Column, String, Boolean, Date, Text, Numeric, Integer, ForeignKey, TIMESTAMP, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid
import enum

# Definicion de los ENUMs
class GeneroEnum(enum.Enum):
    masculino = "masculino"
    femenino = "femenino"
    no_binario = "no_binario"
    prefiero_no_decir = "prefiero_no_decir"

class EstadoPublicacionEnum(enum.Enum):
    activo = "activo"
    pausado = "pausado"
    cerrado = "cerrado"

class PreferenciaGeneroEnum(enum.Enum):
    masculino = "masculino"
    femenino = "femenino"
    no_binario = "no_binario"
    indiferente = "indiferente"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String)
    apellido = Column(String)
    dni = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    fecha_nacimiento = Column(Date)
    genero = Column(Enum(GeneroEnum, name="genero_enum", create_type=False))
    foto_perfil_url = Column(String)
    descripcion = Column(Text)
    preferencias = Column(Text)
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    publicaciones = relationship("Publicacion", back_populates="propietario")
    postulaciones = relationship("Postulacion", back_populates="postulante")
    sesiones = relationship("Sesion", back_populates="user", cascade="all, delete-orphan")


class Publicacion(Base):
    __tablename__ = "publicaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    propietario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    titulo = Column(String)
    descripcion = Column(Text)
    direccion = Column(String)
    estado = Column(Enum(EstadoPublicacionEnum, name="estado_publicacion_enum", create_type=False))
    precio = Column(Numeric)
    preferencia_genero = Column(Enum(PreferenciaGeneroEnum, name="preferencia_genero_enum", create_type=False))
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    propietario = relationship("User", back_populates="publicaciones")
    # selectin evita el N+1 al serializar PublicacionResponse.fotos en el listado.
    fotos = relationship(
        "PublicacionFoto",
        back_populates="publicacion",
        cascade="all, delete-orphan",
        order_by="PublicacionFoto.orden",
        lazy="selectin",
    )
    postulaciones = relationship("Postulacion", back_populates="publicacion")


class PublicacionFoto(Base):
    __tablename__ = "publicacion_fotos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publicacion_id = Column(UUID(as_uuid=True), ForeignKey("publicaciones.id"))
    url = Column(String)
    orden = Column(Integer)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    publicacion = relationship("Publicacion", back_populates="fotos")


class Estado(Base):
    __tablename__ = "estado"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estado_actual = Column(String)

    postulaciones = relationship("Postulacion", back_populates="estado")


class Postulacion(Base):
    __tablename__ = "postulaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publicacion_id = Column(UUID(as_uuid=True), ForeignKey("publicaciones.id"))
    postulante_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    estado_id = Column(UUID(as_uuid=True), ForeignKey("estado.id"))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    publicacion = relationship("Publicacion", back_populates="postulaciones")
    postulante = relationship("User", back_populates="postulaciones")
    estado = relationship("Estado", back_populates="postulaciones", lazy="selectin")


class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    token_hash = Column(String, unique=True, index=True)
    expira_en = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="sesiones")
