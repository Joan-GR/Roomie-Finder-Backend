-- Roomie Finder - agrega la tabla de mensajes (chat directo entre usuarios).
-- Idempotente, se puede correr mas de una vez sin romper nada.

BEGIN;

CREATE TABLE IF NOT EXISTS mensajes (
    id UUID PRIMARY KEY,
    emisor_id UUID REFERENCES users(id),
    receptor_id UUID REFERENCES users(id),
    contenido TEXT,
    leido BOOLEAN DEFAULT false,
    created_at TIMESTAMP
);

-- Cubre tanto GET /mensajes/conversacion/{id} (ambos sentidos) como el orden por fecha.
CREATE INDEX IF NOT EXISTS ix_mensajes_emisor_receptor ON mensajes (emisor_id, receptor_id, created_at);
CREATE INDEX IF NOT EXISTS ix_mensajes_receptor_emisor ON mensajes (receptor_id, emisor_id, created_at);

-- Acelera el conteo de no leidos en GET /mensajes/conversaciones.
CREATE INDEX IF NOT EXISTS ix_mensajes_receptor_leido ON mensajes (receptor_id, leido);

COMMIT;
