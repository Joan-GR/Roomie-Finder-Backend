from sqlalchemy import Column, String, Boolean, Date, Text, Numeric, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String)
    apellido = Column(String)
    dni = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    fecha_nacimiento = Column(Date)
    genero = Column(String)
    foto_perfil_url = Column(String)
    descripcion = Column(Text)
    preferencias = Column(Text)
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    publicaciones = relationship("Publicacion", back_populates="propietario")
    postulaciones = relationship("Postulacion", back_populates="postulante")
    sesiones = relationship("Sesion", back_populates="user")


class Publicacion(Base):
    __tablename__ = "publicaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    propietario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    titulo = Column(String)
    descripcion = Column(Text)
    direccion = Column(String)
    estado = Column(String)
    precio = Column(Numeric)
    preferencia_genero = Column(String)
    activo = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    propietario = relationship("User", back_populates="publicaciones")
    fotos = relationship("PublicacionFoto", back_populates="publicacion")
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
    estado = relationship("Estado", back_populates="postulaciones")


class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    token_hash = Column(String, unique=True)
    expira_en = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="sesiones")