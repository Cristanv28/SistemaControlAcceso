-- Ejecuta esto UNA SOLA VEZ en tu base de datos Railway
-- Tabla para guardar configuraciones persistentes (modo de acceso, etc.)

CREATE TABLE IF NOT EXISTS configuracion (
    clave  VARCHAR(50)  PRIMARY KEY,
    valor  VARCHAR(100) NOT NULL
);

-- Insertar valor por defecto del modo de acceso
INSERT IGNORE INTO configuracion (clave, valor)
VALUES ('modo_acceso', 'normal');
