-- ============================================================
-- Script SQL para crear usuarios iniciales en REDIMA
-- ============================================================
-- IMPORTANTE: Este archivo SQL es solo de referencia.
-- Django usa PBKDF2 para hashear contraseñas, por lo que
-- este SQL NO puede ejecutarse directamente.
-- 
-- Para crear los usuarios, usar:
-- 1. El botón en el dashboard (recomendado)
-- 2. El comando: python manage.py crear_usuarios_iniciales
-- ============================================================

-- ============================================================
-- SUPERUSUARIOS (3)
-- ============================================================

-- Superusuario 1
-- Username: admin1
-- Password: admin123456
-- Email: admin1@redima.edu.pe
-- DNI: 12345678
-- Nombre: Administrador Uno

-- Superusuario 2
-- Username: admin2
-- Password: admin123456
-- Email: admin2@redima.edu.pe
-- DNI: 12345679
-- Nombre: Administrador Dos

-- Superusuario 3
-- Username: admin3
-- Password: admin123456
-- Email: admin3@redima.edu.pe
-- DNI: 12345680
-- Nombre: Administrador Tres

-- ============================================================
-- USUARIOS NORMALES (3)
-- ============================================================

-- Usuario Normal 1
-- Username: usuario1
-- Password: usuario123
-- Email: usuario1@redima.edu.pe
-- DNI: 22345678
-- Nombre: Usuario Uno

-- Usuario Normal 2
-- Username: usuario2
-- Password: usuario123
-- Email: usuario2@redima.edu.pe
-- DNI: 22345679
-- Nombre: Usuario Dos

-- Usuario Normal 3
-- Username: usuario3
-- Password: usuario123
-- Email: usuario3@redima.edu.pe
-- DNI: 22345680
-- Nombre: Usuario Tres

-- ============================================================
-- NOTAS
-- ============================================================
-- Este script se ejecuta a través de la vista Django que:
-- 1. Hashea las contraseñas correctamente
-- 2. Valida los datos (DNI único, email válido, etc.)
-- 3. Maneja transacciones de base de datos
-- 4. Evita duplicados
-- ============================================================
