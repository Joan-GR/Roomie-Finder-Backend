from fastapi import APIRouter, Depends, UploadFile

from models import User
from security import get_current_user
from storage import subir_imagen

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/imagen")
async def subir_imagen_endpoint(
    archivo: UploadFile,
    usuario: User = Depends(get_current_user),
):
    """Sube una imagen y devuelve su URL.

    Esa URL despues se usa con POST /publicaciones/{id}/fotos (campo "url") o con
    PUT /users/{id} (campo "foto_perfil_url") -- este endpoint no toca la base de datos.
    """
    url = await subir_imagen(archivo, carpeta=str(usuario.id))
    return {"url": url}
