"""Rate limiting por IP usando Upstash Redis (REST API).

Vercel ejecuta cada funcion como serverless: no hay memoria compartida entre
instancias, asi que un contador en memoria del proceso no sirve. Upstash expone
Redis por HTTPS, lo que encaja bien con ese modelo.

Requiere UPSTASH_REDIS_REST_URL y UPSTASH_REDIS_REST_TOKEN. Si no estan seteadas,
no se bloquea nada (se loguea una vez y se deja pasar) -- preferible a que un rate
limiter mal configurado tire abajo el login de todo el mundo.
"""

import os

import requests
from fastapi import HTTPException, Request

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

TIMEOUT_SEGUNDOS = 5


def _ip_del_cliente(request: Request) -> str:
    # Vercel (como la mayoria de los proxies) manda la IP real del cliente en este
    # header; request.client.host detras de un proxy casi siempre es interno.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "desconocido"


def verificar_limite(request: Request, accion: str, limite: int, ventana_segundos: int) -> None:
    """Lanza 429 si esta IP ya hizo mas de `limite` veces `accion` en la ventana."""
    if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
        return

    clave = f"ratelimit:{accion}:{_ip_del_cliente(request)}"

    try:
        resp = requests.post(
            f"{UPSTASH_REDIS_REST_URL}/pipeline",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"},
            # INCR crea la clave en 1 si no existia. EXPIRE ... NX le pone vencimiento
            # solo la primera vez, asi la ventana es fija y no se reinicia en cada intento.
            json=[["INCR", clave], ["EXPIRE", clave, str(ventana_segundos), "NX"]],
            timeout=TIMEOUT_SEGUNDOS,
        )
        resp.raise_for_status()
        intentos = resp.json()[0]["result"]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        # Si Upstash esta caido o responde raro, no tiramos abajo el endpoint por eso.
        return

    if intentos > limite:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos. Espera unos minutos y volve a intentar.",
        )
