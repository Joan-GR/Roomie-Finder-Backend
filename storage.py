"""Subida de imagenes a Cloudinary.

Requiere la variable de entorno CLOUDINARY_URL (formato
cloudinary://<api_key>:<api_secret>@<cloud_name>), que el SDK lee solo.
"""

import os

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile

CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
if CLOUDINARY_URL:
    cloudinary.config(cloudinary_url=CLOUDINARY_URL, secure=True)

CONTENT_TYPES_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB


async def subir_imagen(archivo: UploadFile, carpeta: str) -> str:
    if not CLOUDINARY_URL:
        raise HTTPException(status_code=500, detail="Storage de imagenes no configurado")

    if archivo.content_type not in CONTENT_TYPES_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {archivo.content_type}",
        )

    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(status_code=400, detail="La imagen no puede superar los 5MB")
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo esta vacio")

    try:
        resultado = cloudinary.uploader.upload(
            contenido,
            folder=f"roomie-finder/{carpeta}",
            resource_type="image",
        )
    except cloudinary.exceptions.Error as e:
        raise HTTPException(status_code=502, detail=f"Error al subir la imagen a Cloudinary: {e}")

    return resultado["secure_url"]
