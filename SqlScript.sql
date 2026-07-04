/* DROPEO DE LA BD */
DROP DATABASE DB_SistemaHotelero;

/* BASE DE DATOS */
CREATE DATABASE DB_SistemaHotelero;
USE DB_SistemaHotelero;

/* TABLAS */
CREATE TABLE SIS_Administrador (
    ADM_id      	INT             AUTO_INCREMENT      PRIMARY KEY,
    ADM_nombre  	VARCHAR(100)                        NOT NULL,
    ADM_correo  	VARCHAR(100)    UNIQUE              NOT NULL,
    ADM_contrasenia	NVARCHAR(80)						NOT NULL
);

CREATE TABLE SIS_Cliente (
    CLI_id          INT             AUTO_INCREMENT  PRIMARY KEY,
    CLI_nombre      VARCHAR(100)    NOT NULL,
    CLI_direccion   VARCHAR(255)    NOT NULL,  
    CLI_telefono    VARCHAR(20)     NOT NULL,
    CLI_contrasenia	NVARCHAR(80)	NOT NULL
);

CREATE TABLE SIS_Habitacion (
    HAB_id                  INT             AUTO_INCREMENT   PRIMARY KEY,
    HAB_numero              VARCHAR(10)     NOT NULL         UNIQUE,     
    HAB_tipo_habitacion     VARCHAR(50)     NOT NULL,   
    HAB_tipo_cama           VARCHAR(50)     NOT NULL,       
    HAB_precio              DECIMAL(10, 2)  NOT NULL,   
    HAB_estado              VARCHAR(20)     DEFAULT 'Disponible',
    HAB_foto                VARCHAR(255)    NULL
);

CREATE TABLE SIS_Platillo (
    PLA_id      INT             AUTO_INCREMENT PRIMARY KEY,
    PLA_nombre  VARCHAR(100)    NOT NULL,    
    PLA_tipo    VARCHAR(50)     NOT NULL,   
    PLA_precio  DECIMAL(10, 2)  NOT NULL,
    PLA_foto    VARCHAR(255)    NULL
);

CREATE TABLE SIS_Reservacion (
    RES_id          INT             AUTO_INCREMENT PRIMARY KEY,
    CLI_id_fk       INT             NOT NULL,
    HAB_id_fk       INT             NOT NULL,
    RES_num_dias    INT             NOT NULL,                 
    RES_total       DECIMAL(10, 2)  NOT NULL,   
    
    FOREIGN KEY (CLI_id_fk) REFERENCES SIS_Cliente(CLI_id) ON DELETE CASCADE,
    FOREIGN KEY (HAB_id_fk) REFERENCES SIS_Habitacion(HAB_id) ON DELETE CASCADE
);

CREATE TABLE SIS_Pedido (
    PED_id      INT             AUTO_INCREMENT PRIMARY KEY,
    CLI_id_fk   INT             NOT NULL,
    PED_total   DECIMAL(10, 2)  DEFAULT 0.00,  

    FOREIGN KEY (CLI_id_fk) REFERENCES SIS_Cliente(CLI_id) ON DELETE CASCADE
);

CREATE TABLE SIS_Detalle_Pedido (
    PED_id_fk       INT,
    PLA_id_fk       INT,
    DET_cantidad    INT NOT NULL DEFAULT 1,

    PRIMARY KEY (PED_id_fk, PLA_id_fk),
    FOREIGN KEY (PED_id_fk) REFERENCES SIS_Pedido(PED_id) ON DELETE CASCADE,
    FOREIGN KEY (PLA_id_fk) REFERENCES SIS_Platillo(PLA_id) ON DELETE CASCADE
);

CREATE TABLE SIS_Recibo (
    REC_id              INT             AUTO_INCREMENT PRIMARY KEY,
    REC_costo_comida    DECIMAL(10, 2)  DEFAULT 0.00,
    REC_costo_bebidas   DECIMAL(10, 2)  DEFAULT 0.00,
    REC_monto_total     DECIMAL(10, 2)  NOT NULL,

    RES_id_fk           INT NULL,
    PED_id_fk           INT NULL,

    FOREIGN KEY (RES_id_fk) REFERENCES SIS_Reservacion(RES_id) ON DELETE SET NULL,
    FOREIGN KEY (PED_id_fk) REFERENCES SIS_Pedido(PED_id) ON DELETE SET NULL
);

/* DATOS DE PRUEBA */
INSERT INTO SIS_Cliente VALUES
("0", "Koko", "koko@gmail.com", "7751346188", "1234567890");

/* PROCEDIMIENTOS ALMACENADOS */
DELIMITER $$
CREATE PROCEDURE SP_IniciarSesion
(
	IN SP_Correo		VARCHAR(255),
    IN SP_Contrasenia	NVARCHAR(80)
)
BEGIN
	IF EXISTS(SELECT 1 FROM SIS_Cliente WHERE CLI_direccion = SP_Correo AND CLI_contrasenia = SP_Contrasenia) THEN
		SELECT
			CLI_id			Id,
            CLI_nombre		Nombre,
			CLI_direccion	Direccion,
			CLI_telefono	Telefono
		FROM SIS_Cliente WHERE CLI_direccion = SP_Correo AND CLI_contrasenia = SP_Contrasenia;
    ELSE
		SELECT 0 Id;
    END IF;
END $$
DELIMITER ;

CALL SP_IniciarSesion("koko@gmail.com", "1234567890");

-- Plantilla 
/*
DELIMITER $$
CREATE PROCEDURE SP_
(
)
BEGIN
END $$
DELIMITER ;
*/