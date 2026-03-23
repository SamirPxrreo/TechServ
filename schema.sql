-- ============================================
--  TECHSERV - Base de datos MySQL
--  Ejecuta este archivo en tu servidor MySQL
-- ============================================

CREATE DATABASE IF NOT EXISTS techserv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE techserv;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    rol ENUM('usuario', 'admin') DEFAULT 'usuario',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de servicios disponibles
CREATE TABLE IF NOT EXISTS servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL,
    icono VARCHAR(10),
    activo TINYINT(1) DEFAULT 1
);

-- Tabla de carrito (items por usuario)
CREATE TABLE IF NOT EXISTS carrito (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    servicio_id INT NOT NULL,
    cantidad INT DEFAULT 1,
    fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE CASCADE
);

-- Tabla de pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    estado ENUM('pendiente', 'en proceso', 'completado', 'cancelado') DEFAULT 'pendiente',
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    notas TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla detalle de pedidos
CREATE TABLE IF NOT EXISTS pedido_detalle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT NOT NULL,
    servicio_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (servicio_id) REFERENCES servicios(id)
);

-- ============================================
--  Datos iniciales
-- ============================================

-- Admin por defecto (contraseña: admin123)
INSERT INTO usuarios (nombre, telefono, correo, contrasena, rol) VALUES
('Administrador', '3001234567', 'admin@techserv.com', 'pbkdf2:sha256:600000$placeholder', 'admin');

-- Servicios de mantenimiento
INSERT INTO servicios (nombre, descripcion, precio, icono) VALUES
('Limpieza Física', 'Limpieza interna completa del equipo, eliminación de polvo y suciedad de componentes', 45000, '🧹'),
('Formateo + Windows', 'Formateo completo del disco duro e instalación limpia del sistema operativo Windows', 80000, '💿'),
('Eliminación de Virus', 'Escaneo profundo, eliminación de malware, spyware y virus del sistema', 55000, '🛡️'),
('Optimización del Sistema', 'Limpieza de archivos temporales, desfragmentación y aceleración del arranque', 40000, '⚡'),
('Recuperación de Datos', 'Recuperación de archivos eliminados o de discos dañados', 120000, '💾'),
('Instalación de Programas', 'Instalación y configuración de software de oficina, seguridad y utilidades', 35000, '📦'),
('Revisión General', 'Diagnóstico completo del equipo con informe detallado del estado', 30000, '🔍'),
('Mantenimiento Preventivo', 'Servicio completo: limpieza, optimización y revisión preventiva programada', 95000, '🔧');
