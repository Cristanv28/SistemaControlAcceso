-- Ejecuta esto UNA VEZ en tu base de datos Railway
-- Agrega la columna id_area a la tabla usuario

ALTER TABLE usuario
ADD COLUMN id_area INT NULL,
ADD CONSTRAINT fk_usuario_area
    FOREIGN KEY (id_area) REFERENCES area(id_area);
