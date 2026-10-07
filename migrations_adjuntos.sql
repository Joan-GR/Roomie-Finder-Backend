-- Roomie Finder - agrega soporte de adjuntos (fotos/documentos) a los mensajes del chat.
-- Idempotente, se puede correr mas de una vez sin romper nada.

BEGIN;

ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS adjunto_url varchar;
ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS adjunto_nombre varchar;
ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS adjunto_tipo varchar;

-- contenido ya era nullable en la base (todas las columnas de mensajes lo son salvo
-- id), asi que un mensaje de "solo adjunto" ya funciona sin tocar esa columna.

COMMIT;
