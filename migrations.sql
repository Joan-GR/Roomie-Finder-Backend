-- Roomie Finder - migracion para alinear la base con el codigo.
-- Corre entero, es idempotente (podes ejecutarlo mas de una vez sin romper nada).
-- Hasta que no lo corras, los endpoints de /publicaciones y /postulaciones siguen fallando.

BEGIN;

-- 1. La columna publicaciones.activo no existia en la base, pero el modelo y todos
--    los endpoints de publicaciones filtran por ella (borrado logico).
--    Sintoma: UndefinedColumn "column publicaciones.activo does not exist" -> 500.
ALTER TABLE publicaciones ADD COLUMN IF NOT EXISTS activo boolean DEFAULT true;
UPDATE publicaciones SET activo = true WHERE activo IS NULL;

-- 2. La columna estaba mal escrita: "estado_actial" en vez de "estado_actual".
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'estado' AND column_name = 'estado_actial'
    ) THEN
        ALTER TABLE estado RENAME COLUMN estado_actial TO estado_actual;
    END IF;
END $$;

-- 3. La tabla estado estaba vacia, asi que POST /postulaciones/ nunca podia crear
--    una fila valida (violaba la FK estado_id). El backend ahora asigna 'pendiente'.
INSERT INTO estado (id, estado_actual)
SELECT gen_random_uuid(), v.nombre
FROM (VALUES ('pendiente'), ('aceptada'), ('rechazada')) AS v(nombre)
WHERE NOT EXISTS (
    SELECT 1 FROM estado e WHERE e.estado_actual = v.nombre
);

-- 4. Indices para las busquedas que hace la API en cada request autenticado.
CREATE UNIQUE INDEX IF NOT EXISTS ix_sesiones_token_hash ON sesiones (token_hash);
CREATE INDEX IF NOT EXISTS ix_publicaciones_propietario_id ON publicaciones (propietario_id);
CREATE INDEX IF NOT EXISTS ix_postulaciones_publicacion_id ON postulaciones (publicacion_id);
CREATE INDEX IF NOT EXISTS ix_postulaciones_postulante_id ON postulaciones (postulante_id);
CREATE INDEX IF NOT EXISTS ix_publicacion_fotos_publicacion_id ON publicacion_fotos (publicacion_id);

-- 5. Evita postulaciones duplicadas a nivel base, no solo por el chequeo del backend.
CREATE UNIQUE INDEX IF NOT EXISTS ux_postulaciones_publicacion_postulante
    ON postulaciones (publicacion_id, postulante_id);

COMMIT;

-- 6. OPCIONAL pero recomendado: los tokens de sesion viejos se guardaban en texto
--    plano en la columna token_hash. Ahora se guarda el sha256, asi que las sesiones
--    existentes ya no sirven. Esto las limpia y obliga a volver a loguearse.
-- DELETE FROM sesiones;
