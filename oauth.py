"""Verificacion de tokens de Google y Facebook para "iniciar sesion con...".

El frontend hace el login contra el SDK de Google/Facebook y nos manda el token
que le devuelven. Ac  no manejamos redirects ni callbacks: solo verificamos ese
token contra el proveedor y confiamos en el email porque ambos lo verifican antes
de emitirlo.
"""

import os

import requests
from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")

TIMEOUT_SEGUNDOS = 10


def verificar_id_token_google(token: str) -> dict:
    """Devuelve el payload del id_token (email, given_name, family_name, picture, etc)."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Login con Google no configurado")

    try:
        payload = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Token de Google invalido")

    if not payload.get("email_verified"):
        raise HTTPException(status_code=401, detail="El email de Google no esta verificado")

    return payload


def verificar_access_token_facebook(token: str) -> dict:
    """Devuelve el perfil de Facebook (id, name, email)."""
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise HTTPException(status_code=500, detail="Login con Facebook no configurado")

    # debug_token confirma que el access_token fue emitido para NUESTRA app, no para
    # otra: sin este chequeo, un token valido de cualquier app de Facebook pasaria.
    app_token = f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}"
    try:
        debug = requests.get(
            "https://graph.facebook.com/debug_token",
            params={"input_token": token, "access_token": app_token},
            timeout=TIMEOUT_SEGUNDOS,
        ).json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"No se pudo validar el token de Facebook: {e}")

    datos_token = debug.get("data", {})
    if not datos_token.get("is_valid") or datos_token.get("app_id") != FACEBOOK_APP_ID:
        raise HTTPException(status_code=401, detail="Token de Facebook invalido")

    try:
        perfil = requests.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email", "access_token": token},
            timeout=TIMEOUT_SEGUNDOS,
        ).json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"No se pudo obtener el perfil de Facebook: {e}")

    if "email" not in perfil:
        raise HTTPException(
            status_code=400,
            detail="Tu cuenta de Facebook no tiene un email asociado o no dio permiso para verlo",
        )

    return perfil
