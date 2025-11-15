-- ============================================================================
-- ESQUEMA COMPLETO DE REPOSITORIO DIGITAL DE INVESTIGACIÓN
-- Sistema complejo para gestión de documentos académicos, metadatos,
-- versiones, revisiones, estadísticas, y más
-- ============================================================================

-- Configuración inicial
SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

-- ============================================================================
-- NOTA IMPORTANTE: 
-- Este esquema utiliza el sistema de autenticación de Django (auth_user, 
-- auth_group, auth_permission). Las tablas de usuarios, roles y permisos
-- están gestionadas por Django. Solo creamos la tabla 'persona' que extiende
-- el modelo User de Django con información adicional.
-- ============================================================================

-- ============================================================================
-- 1. TABLA PERSONA (Extensión del User de Django)
-- ============================================================================
-- Esta tabla se relaciona con auth_user de Django mediante una relación
-- uno a uno. Django creará automáticamente la tabla auth_user.

CREATE TABLE IF NOT EXISTS `usuarios_persona` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` INT(11) NOT NULL UNIQUE,
    `telefono` VARCHAR(20) DEFAULT NULL,
    `institucion` VARCHAR(255) DEFAULT NULL,
    `departamento` VARCHAR(255) DEFAULT NULL,
    `cargo` VARCHAR(100) DEFAULT NULL,
    `biografia` TEXT DEFAULT NULL,
    `foto_perfil` VARCHAR(500) DEFAULT NULL,
    `orcid_id` VARCHAR(19) DEFAULT NULL UNIQUE,
    `google_scholar_id` VARCHAR(100) DEFAULT NULL,
    `researchgate_id` VARCHAR(100) DEFAULT NULL,
    `linkedin_url` VARCHAR(500) DEFAULT NULL,
    `email_verificado` BOOLEAN DEFAULT FALSE,
    `ultimo_acceso` DATETIME(6) DEFAULT NULL,
    `preferencias_notificaciones` JSON DEFAULT NULL,
    `fecha_creacion` DATETIME(6) NOT NULL,
    `fecha_actualizacion` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `usuarios_persona_user_id_key` (`user_id`),
    INDEX `idx_persona_user` (`user_id`),
    INDEX `idx_persona_orcid` (`orcid_id`),
    INDEX `idx_persona_institucion` (`institucion`),
    FOREIGN KEY (`user_id`) REFERENCES `auth_user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 2. TABLAS DE COMUNIDADES Y COLECCIONES
-- ============================================================================

CREATE TABLE IF NOT EXISTS `comunidades` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL UNIQUE,
    `descripcion` TEXT DEFAULT NULL,
    `logo` VARCHAR(500) DEFAULT NULL,
    `banner` VARCHAR(500) DEFAULT NULL,
    `comunidad_padre_id` INT(11) UNSIGNED DEFAULT NULL,
    `administrador_id` INT(11) NOT NULL,
    `es_publica` BOOLEAN DEFAULT TRUE,
    `estado` ENUM('activa', 'inactiva', 'archivada') DEFAULT 'activa',
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_slug` (`slug`),
    INDEX `idx_comunidad_padre` (`comunidad_padre_id`),
    INDEX `idx_administrador` (`administrador_id`),
    FOREIGN KEY (`comunidad_padre_id`) REFERENCES `comunidades`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`administrador_id`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `colecciones` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `comunidad_id` INT(11) UNSIGNED NOT NULL,
    `coleccion_padre_id` INT(11) UNSIGNED DEFAULT NULL,
    `administrador_id` INT(11) NOT NULL,
    `politica_ingreso` ENUM('abierto', 'cerrado', 'revision') DEFAULT 'abierto',
    `es_publica` BOOLEAN DEFAULT TRUE,
    `plantilla_metadatos` JSON DEFAULT NULL,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_slug_comunidad` (`slug`, `comunidad_id`),
    INDEX `idx_comunidad` (`comunidad_id`),
    INDEX `idx_coleccion_padre` (`coleccion_padre_id`),
    INDEX `idx_administrador` (`administrador_id`),
    FOREIGN KEY (`comunidad_id`) REFERENCES `comunidades`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`coleccion_padre_id`) REFERENCES `colecciones`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`administrador_id`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. TABLAS DE DOCUMENTOS Y RECURSOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS `tipos_recurso` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(100) NOT NULL UNIQUE,
    `descripcion` TEXT DEFAULT NULL,
    `icono` VARCHAR(100) DEFAULT NULL,
    `categoria` VARCHAR(50) DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `estados_documento` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(50) NOT NULL UNIQUE,
    `descripcion` TEXT DEFAULT NULL,
    `orden` INT(11) DEFAULT 0,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `documentos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `handle` VARCHAR(255) NOT NULL UNIQUE,
    `titulo` VARCHAR(500) NOT NULL,
    `resumen` TEXT DEFAULT NULL,
    `tipo_recurso_id` INT(11) UNSIGNED NOT NULL,
    `coleccion_id` INT(11) UNSIGNED NOT NULL,
    `creador_id` INT(11) NOT NULL,
    `estado_id` INT(11) UNSIGNED NOT NULL,
    `idioma` VARCHAR(10) DEFAULT 'es',
    `fecha_publicacion` DATE DEFAULT NULL,
    `fecha_aceptacion` DATE DEFAULT NULL,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `fecha_publicacion_disponible` TIMESTAMP NULL DEFAULT NULL,
    `visibilidad` ENUM('publico', 'privado', 'restringido') DEFAULT 'publico',
    `version_actual` INT(11) UNSIGNED DEFAULT 1,
    `numero_acceso` VARCHAR(50) DEFAULT NULL,
    `doi` VARCHAR(255) DEFAULT NULL UNIQUE,
    `isbn` VARCHAR(20) DEFAULT NULL,
    `issn` VARCHAR(20) DEFAULT NULL,
    `licencia_id` INT(11) UNSIGNED DEFAULT NULL,
    `palabras_clave` TEXT DEFAULT NULL,
    `temas` JSON DEFAULT NULL,
    `campos_personalizados` JSON DEFAULT NULL,
    `metadata_completa` JSON DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_handle` (`handle`),
    INDEX `idx_titulo` (`titulo`(255)),
    INDEX `idx_tipo_recurso` (`tipo_recurso_id`),
    INDEX `idx_coleccion` (`coleccion_id`),
    INDEX `idx_creador` (`creador_id`),
    INDEX `idx_estado` (`estado_id`),
    INDEX `idx_doi` (`doi`),
    INDEX `idx_fecha_publicacion` (`fecha_publicacion`),
    FULLTEXT INDEX `ft_titulo_resumen` (`titulo`, `resumen`),
    FOREIGN KEY (`tipo_recurso_id`) REFERENCES `tipos_recurso`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`coleccion_id`) REFERENCES `colecciones`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`creador_id`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`estado_id`) REFERENCES `estados_documento`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. TABLAS DE VERSIONES Y ARCHIVOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS `versiones_documento` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `numero_version` INT(11) UNSIGNED NOT NULL,
    `notas_version` TEXT DEFAULT NULL,
    `creado_por` INT(11) NOT NULL,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `es_version_actual` BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_doc_version` (`documento_id`, `numero_version`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_creado_por` (`creado_por`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`creado_por`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `archivos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `version_id` INT(11) UNSIGNED NOT NULL,
    `nombre_original` VARCHAR(500) NOT NULL,
    `nombre_almacenado` VARCHAR(500) NOT NULL,
    `ruta_completa` VARCHAR(1000) NOT NULL,
    `tipo_mime` VARCHAR(100) DEFAULT NULL,
    `tamaño_bytes` BIGINT UNSIGNED NOT NULL,
    `checksum_md5` VARCHAR(32) DEFAULT NULL,
    `checksum_sha256` VARCHAR(64) DEFAULT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `es_archivo_principal` BOOLEAN DEFAULT FALSE,
    `formato` VARCHAR(50) DEFAULT NULL,
    `numero_paginas` INT(11) UNSIGNED DEFAULT NULL,
    `resolucion` VARCHAR(50) DEFAULT NULL,
    `duracion` INT(11) UNSIGNED DEFAULT NULL COMMENT 'en segundos',
    `bitrate` INT(11) UNSIGNED DEFAULT NULL,
    `fecha_subida` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_version` (`version_id`),
    INDEX `idx_checksum_md5` (`checksum_md5`),
    INDEX `idx_tipo_mime` (`tipo_mime`),
    FOREIGN KEY (`version_id`) REFERENCES `versiones_documento`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. TABLAS DE AUTORES Y COLABORADORES
-- ============================================================================

CREATE TABLE IF NOT EXISTS `autores` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `usuario_id` INT(11) DEFAULT NULL,
    `nombre` VARCHAR(200) NOT NULL,
    `apellidos` VARCHAR(200) NOT NULL,
    `email` VARCHAR(255) DEFAULT NULL,
    `afiliacion` VARCHAR(500) DEFAULT NULL,
    `orcid_id` VARCHAR(19) DEFAULT NULL,
    `orden_autor` INT(11) UNSIGNED DEFAULT 1,
    `es_correspondiente` BOOLEAN DEFAULT FALSE,
    `es_autor_principal` BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_usuario` (`usuario_id`),
    INDEX `idx_orden` (`orden_autor`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `colaboradores` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `usuario_id` INT(11) DEFAULT NULL,
    `rol` ENUM('editor', 'revisor', 'colaborador', 'supervisor', 'patrocinador') NOT NULL,
    `permisos` JSON DEFAULT NULL,
    `fecha_asignacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_usuario` (`usuario_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 6. TABLAS DE METADATOS Y CATEGORIZACIÓN
-- ============================================================================

CREATE TABLE IF NOT EXISTS `esquemas_metadatos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(100) NOT NULL UNIQUE,
    `prefijo` VARCHAR(50) NOT NULL UNIQUE,
    `namespace` VARCHAR(500) NOT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `version` VARCHAR(20) DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `campos_metadatos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `esquema_id` INT(11) UNSIGNED NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `etiqueta` VARCHAR(255) NOT NULL,
    `tipo_dato` ENUM('texto', 'numero', 'fecha', 'booleano', 'lista', 'json') DEFAULT 'texto',
    `es_obligatorio` BOOLEAN DEFAULT FALSE,
    `es_repetible` BOOLEAN DEFAULT FALSE,
    `valores_posibles` JSON DEFAULT NULL,
    `descripcion` TEXT DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_esquema_campo` (`esquema_id`, `nombre`),
    INDEX `idx_esquema` (`esquema_id`),
    FOREIGN KEY (`esquema_id`) REFERENCES `esquemas_metadatos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `metadatos_documento` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `campo_metadato_id` INT(11) UNSIGNED NOT NULL,
    `valor_texto` TEXT DEFAULT NULL,
    `valor_numero` DECIMAL(20,6) DEFAULT NULL,
    `valor_fecha` DATE DEFAULT NULL,
    `valor_booleano` BOOLEAN DEFAULT NULL,
    `valor_json` JSON DEFAULT NULL,
    `idioma` VARCHAR(10) DEFAULT NULL,
    `orden` INT(11) UNSIGNED DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_campo` (`campo_metadato_id`),
    INDEX `idx_valor_texto` (`valor_texto`(255)),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`campo_metadato_id`) REFERENCES `campos_metadatos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `categorias` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL UNIQUE,
    `descripcion` TEXT DEFAULT NULL,
    `categoria_padre_id` INT(11) UNSIGNED DEFAULT NULL,
    `nivel` INT(11) UNSIGNED DEFAULT 0,
    `ruta_completa` VARCHAR(1000) DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_slug` (`slug`),
    INDEX `idx_padre` (`categoria_padre_id`),
    FOREIGN KEY (`categoria_padre_id`) REFERENCES `categorias`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `documento_categorias` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `categoria_id` INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_doc_categoria` (`documento_id`, `categoria_id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_categoria` (`categoria_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`categoria_id`) REFERENCES `categorias`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `etiquetas` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(100) NOT NULL UNIQUE,
    `slug` VARCHAR(100) NOT NULL UNIQUE,
    `descripcion` TEXT DEFAULT NULL,
    `color` VARCHAR(7) DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `documento_etiquetas` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `etiqueta_id` INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_doc_etiqueta` (`documento_id`, `etiqueta_id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_etiqueta` (`etiqueta_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`etiqueta_id`) REFERENCES `etiquetas`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 7. TABLAS DE REVISIÓN Y APROBACIÓN
-- ============================================================================

CREATE TABLE IF NOT EXISTS `procesos_revision` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `tipo_revision` ENUM('peer_review', 'editorial', 'administrativa') NOT NULL,
    `estado` ENUM('pendiente', 'en_revision', 'aprobado', 'rechazado', 'requiere_cambios') DEFAULT 'pendiente',
    `iniciado_por` INT(11) NOT NULL,
    `fecha_inicio` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_finalizacion` TIMESTAMP NULL DEFAULT NULL,
    `notas_generales` TEXT DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_estado` (`estado`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`iniciado_por`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `revisiones` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `proceso_revision_id` INT(11) UNSIGNED NOT NULL,
    `revisor_id` INT(11) NOT NULL,
    `estado` ENUM('asignado', 'en_progreso', 'completado', 'rechazado') DEFAULT 'asignado',
    `calificacion_general` INT(11) UNSIGNED DEFAULT NULL COMMENT '1-5',
    `comentarios_publicos` TEXT DEFAULT NULL,
    `comentarios_privados` TEXT DEFAULT NULL,
    `recomendacion` ENUM('aprobar', 'aprobar_con_cambios', 'rechazar', 'requiere_revision') DEFAULT NULL,
    `fecha_asignacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_completacion` TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_proceso` (`proceso_revision_id`),
    INDEX `idx_revisor` (`revisor_id`),
    FOREIGN KEY (`proceso_revision_id`) REFERENCES `procesos_revision`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`revisor_id`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `criterios_revision` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `tipo` ENUM('numerico', 'texto', 'booleano', 'opcion') DEFAULT 'numerico',
    `es_obligatorio` BOOLEAN DEFAULT TRUE,
    `orden` INT(11) UNSIGNED DEFAULT 0,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `evaluaciones_criterios` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `revision_id` INT(11) UNSIGNED NOT NULL,
    `criterio_id` INT(11) UNSIGNED NOT NULL,
    `valor_numerico` DECIMAL(5,2) DEFAULT NULL,
    `valor_texto` TEXT DEFAULT NULL,
    `valor_booleano` BOOLEAN DEFAULT NULL,
    `comentarios` TEXT DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_revision_criterio` (`revision_id`, `criterio_id`),
    INDEX `idx_revision` (`revision_id`),
    INDEX `idx_criterio` (`criterio_id`),
    FOREIGN KEY (`revision_id`) REFERENCES `revisiones`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`criterio_id`) REFERENCES `criterios_revision`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 8. TABLAS DE LICENCIAS Y DERECHOS
-- ============================================================================

CREATE TABLE IF NOT EXISTS `licencias` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL,
    `codigo` VARCHAR(100) NOT NULL UNIQUE,
    `version` VARCHAR(20) DEFAULT NULL,
    `url` VARCHAR(500) DEFAULT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `permite_comercial` BOOLEAN DEFAULT FALSE,
    `permite_modificacion` BOOLEAN DEFAULT FALSE,
    `requiere_attribucion` BOOLEAN DEFAULT TRUE,
    `texto_completo` TEXT DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `derechos_documento` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `tipo_derecho` ENUM('copyright', 'patente', 'marca', 'privacidad', 'otros') NOT NULL,
    `titular` VARCHAR(500) NOT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `fecha_inicio` DATE DEFAULT NULL,
    `fecha_fin` DATE DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 9. TABLAS DE ESTADÍSTICAS Y ANALYTICS
-- ============================================================================

CREATE TABLE IF NOT EXISTS `visitas_documento` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `usuario_id` INT(11) DEFAULT NULL,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `user_agent` VARCHAR(500) DEFAULT NULL,
    `pais` VARCHAR(2) DEFAULT NULL,
    `ciudad` VARCHAR(100) DEFAULT NULL,
    `referer` VARCHAR(1000) DEFAULT NULL,
    `tipo_acceso` ENUM('vista', 'descarga', 'preview') DEFAULT 'vista',
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_usuario` (`usuario_id`),
    INDEX `idx_fecha` (`fecha`),
    INDEX `idx_tipo_acceso` (`tipo_acceso`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `descargas_archivo` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `archivo_id` INT(11) UNSIGNED NOT NULL,
    `usuario_id` INT(11) DEFAULT NULL,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_archivo` (`archivo_id`),
    INDEX `idx_usuario` (`usuario_id`),
    INDEX `idx_fecha` (`fecha`),
    FOREIGN KEY (`archivo_id`) REFERENCES `archivos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `estadisticas_agregadas` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `periodo` ENUM('diario', 'semanal', 'mensual', 'anual') NOT NULL,
    `fecha_inicio` DATE NOT NULL,
    `total_visitas` INT(11) UNSIGNED DEFAULT 0,
    `total_descargas` INT(11) UNSIGNED DEFAULT 0,
    `visitas_unicas` INT(11) UNSIGNED DEFAULT 0,
    `descargas_unicas` INT(11) UNSIGNED DEFAULT 0,
    `tiempo_promedio_lectura` INT(11) UNSIGNED DEFAULT NULL COMMENT 'en segundos',
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_doc_periodo_fecha` (`documento_id`, `periodo`, `fecha_inicio`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_fecha` (`fecha_inicio`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 10. TABLAS DE CITAS Y REFERENCIAS
-- ============================================================================

CREATE TABLE IF NOT EXISTS `citas` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_citado_id` INT(11) UNSIGNED NOT NULL,
    `documento_que_cita_id` INT(11) UNSIGNED NOT NULL,
    `contexto` TEXT DEFAULT NULL,
    `fecha_citacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_citacion` (`documento_citado_id`, `documento_que_cita_id`),
    INDEX `idx_citado` (`documento_citado_id`),
    INDEX `idx_que_cita` (`documento_que_cita_id`),
    FOREIGN KEY (`documento_citado_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`documento_que_cita_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `referencias_bibliograficas` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `tipo` ENUM('articulo', 'libro', 'capitulo', 'tesis', 'congreso', 'patente', 'web', 'otros') DEFAULT 'otros',
    `titulo` VARCHAR(500) NOT NULL,
    `autores` TEXT DEFAULT NULL,
    `año` INT(11) UNSIGNED DEFAULT NULL,
    `doi` VARCHAR(255) DEFAULT NULL,
    `url` VARCHAR(1000) DEFAULT NULL,
    `cita_completa` TEXT DEFAULT NULL,
    `orden` INT(11) UNSIGNED DEFAULT 0,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 11. TABLAS DE COMENTARIOS Y DISCUSIONES
-- ============================================================================

CREATE TABLE IF NOT EXISTS `comentarios` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `usuario_id` INT(11) NOT NULL,
    `comentario_padre_id` INT(11) UNSIGNED DEFAULT NULL,
    `contenido` TEXT NOT NULL,
    `es_moderado` BOOLEAN DEFAULT FALSE,
    `es_publico` BOOLEAN DEFAULT TRUE,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_usuario` (`usuario_id`),
    INDEX `idx_padre` (`comentario_padre_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`comentario_padre_id`) REFERENCES `comentarios`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `valoraciones` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `usuario_id` INT(11) NOT NULL,
    `calificacion` INT(11) UNSIGNED NOT NULL COMMENT '1-5',
    `comentario` TEXT DEFAULT NULL,
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_doc_usuario` (`documento_id`, `usuario_id`),
    INDEX `idx_documento` (`documento_id`),
    INDEX `idx_usuario` (`usuario_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 12. TABLAS DE NOTIFICACIONES
-- ============================================================================

CREATE TABLE IF NOT EXISTS `tipos_notificacion` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `codigo` VARCHAR(100) NOT NULL UNIQUE,
    `nombre` VARCHAR(255) NOT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `plantilla` TEXT DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `notificaciones` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `usuario_id` INT(11) NOT NULL,
    `tipo_notificacion_id` INT(11) UNSIGNED NOT NULL,
    `titulo` VARCHAR(500) NOT NULL,
    `mensaje` TEXT NOT NULL,
    `url_relacionada` VARCHAR(1000) DEFAULT NULL,
    `documento_id` INT(11) UNSIGNED DEFAULT NULL,
    `es_leida` BOOLEAN DEFAULT FALSE,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_usuario` (`usuario_id`),
    INDEX `idx_tipo` (`tipo_notificacion_id`),
    INDEX `idx_leida` (`es_leida`),
    INDEX `idx_fecha` (`fecha_creacion`),
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tipo_notificacion_id`) REFERENCES `tipos_notificacion`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 13. TABLAS DE BÚSQUEDA Y FULL-TEXT
-- ============================================================================

CREATE TABLE IF NOT EXISTS `indices_busqueda` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `contenido_indexado` LONGTEXT NOT NULL,
    `palabras_clave_indexadas` TEXT DEFAULT NULL,
    `fecha_indexacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_documento` (`documento_id`),
    FULLTEXT INDEX `ft_contenido` (`contenido_indexado`),
    FULLTEXT INDEX `ft_palabras_clave` (`palabras_clave_indexadas`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `busquedas` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `usuario_id` INT(11) DEFAULT NULL,
    `termino_busqueda` VARCHAR(500) NOT NULL,
    `filtros_aplicados` JSON DEFAULT NULL,
    `resultados_encontrados` INT(11) UNSIGNED DEFAULT 0,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_usuario` (`usuario_id`),
    INDEX `idx_fecha` (`fecha`),
    FULLTEXT INDEX `ft_termino` (`termino_busqueda`),
    FOREIGN KEY (`usuario_id`) REFERENCES `auth_user`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 14. TABLAS DE CONFIGURACIÓN Y SISTEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS `configuracion_sistema` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `clave` VARCHAR(255) NOT NULL UNIQUE,
    `valor` TEXT DEFAULT NULL,
    `tipo` ENUM('texto', 'numero', 'booleano', 'json', 'fecha') DEFAULT 'texto',
    `categoria` VARCHAR(100) DEFAULT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `es_editable` BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (`id`),
    INDEX `idx_clave` (`clave`),
    INDEX `idx_categoria` (`categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `logs_sistema` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `nivel` ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL,
    `modulo` VARCHAR(100) DEFAULT NULL,
    `mensaje` TEXT NOT NULL,
    `usuario_id` INT(11) DEFAULT NULL,
    `ip_address` VARCHAR(45) DEFAULT NULL,
    `datos_adicionales` JSON DEFAULT NULL,
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_nivel` (`nivel`),
    INDEX `idx_modulo` (`modulo`),
    INDEX `idx_usuario` (`usuario_id`),
    INDEX `idx_fecha` (`fecha`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 15. TABLAS DE PROYECTOS Y SISTEMA DE CAMPOS DINÁMICOS (EAV)
-- ============================================================================

-- Tipos de proyecto (Monografía, Tesis, Artículo, etc.)
CREATE TABLE IF NOT EXISTS `tipos_proyecto` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL UNIQUE,
    `slug` VARCHAR(255) NOT NULL UNIQUE,
    `descripcion` TEXT DEFAULT NULL,
    `icono` VARCHAR(100) DEFAULT NULL,
    `color` VARCHAR(7) DEFAULT NULL,
    `plantilla_vista` VARCHAR(500) DEFAULT NULL,
    `es_activo` BOOLEAN DEFAULT TRUE,
    `orden` INT(11) UNSIGNED DEFAULT 0,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_slug` (`slug`),
    INDEX `idx_activo` (`es_activo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Campos definidos para cada tipo de proyecto (configuración de campos dinámicos)
CREATE TABLE IF NOT EXISTS `campos_tipo_proyecto` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `tipo_proyecto_id` INT(11) UNSIGNED NOT NULL,
    `nombre` VARCHAR(255) NOT NULL,
    `slug` VARCHAR(255) NOT NULL,
    `etiqueta` VARCHAR(255) NOT NULL,
    `descripcion` TEXT DEFAULT NULL,
    `tipo_dato` ENUM('texto', 'textarea', 'numero', 'fecha', 'booleano', 'select', 'multiselect', 'archivo', 'url', 'email', 'json') NOT NULL DEFAULT 'texto',
    `es_obligatorio` BOOLEAN DEFAULT FALSE,
    `es_repetible` BOOLEAN DEFAULT FALSE,
    `es_buscable` BOOLEAN DEFAULT TRUE,
    `es_indexable` BOOLEAN DEFAULT TRUE,
    `orden` INT(11) UNSIGNED DEFAULT 0,
    `valores_posibles` JSON DEFAULT NULL COMMENT 'Opciones para select/multiselect',
    `validador` VARCHAR(255) DEFAULT NULL COMMENT 'Regex o validación',
    `valor_por_defecto` TEXT DEFAULT NULL,
    `ayuda` TEXT DEFAULT NULL,
    `categoria` VARCHAR(100) DEFAULT NULL COMMENT 'Agrupa campos en secciones',
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_tipo_slug` (`tipo_proyecto_id`, `slug`),
    INDEX `idx_tipo_proyecto` (`tipo_proyecto_id`),
    INDEX `idx_orden` (`orden`),
    FOREIGN KEY (`tipo_proyecto_id`) REFERENCES `tipos_proyecto`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla principal de proyectos
CREATE TABLE IF NOT EXISTS `proyectos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `titulo` VARCHAR(500) NOT NULL,
    `slug` VARCHAR(500) NOT NULL,
    `tipo_proyecto_id` INT(11) UNSIGNED NOT NULL,
    `creador_id` INT(11) NOT NULL,
    `resumen` TEXT DEFAULT NULL,
    `descripcion` LONGTEXT DEFAULT NULL,
    `estado` ENUM('borrador', 'en_revision', 'aprobado', 'publicado', 'archivado', 'rechazado') DEFAULT 'borrador',
    `visibilidad` ENUM('publico', 'privado', 'restringido') DEFAULT 'publico',
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `fecha_publicacion` TIMESTAMP NULL DEFAULT NULL,
    `version` INT(11) UNSIGNED DEFAULT 1,
    `metadata_adicional` JSON DEFAULT NULL COMMENT 'Metadata adicional en formato JSON',
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_slug` (`slug`),
    INDEX `idx_titulo` (`titulo`(255)),
    INDEX `idx_tipo_proyecto` (`tipo_proyecto_id`),
    INDEX `idx_creador` (`creador_id`),
    INDEX `idx_estado` (`estado`),
    INDEX `idx_fecha_publicacion` (`fecha_publicacion`),
    FULLTEXT INDEX `ft_titulo_resumen` (`titulo`, `resumen`),
    FOREIGN KEY (`tipo_proyecto_id`) REFERENCES `tipos_proyecto`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`creador_id`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Valores de campos dinámicos (EAV - Entity-Attribute-Value)
CREATE TABLE IF NOT EXISTS `valores_campo_proyecto` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `proyecto_id` INT(11) UNSIGNED NOT NULL,
    `campo_tipo_proyecto_id` INT(11) UNSIGNED NOT NULL,
    `valor_texto` TEXT DEFAULT NULL,
    `valor_numero` DECIMAL(20,6) DEFAULT NULL,
    `valor_fecha` DATE DEFAULT NULL,
    `valor_datetime` TIMESTAMP NULL DEFAULT NULL,
    `valor_booleano` BOOLEAN DEFAULT NULL,
    `valor_json` JSON DEFAULT NULL,
    `valor_archivo` VARCHAR(1000) DEFAULT NULL,
    `orden` INT(11) UNSIGNED DEFAULT 0 COMMENT 'Para campos repetibles',
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_proyecto` (`proyecto_id`),
    INDEX `idx_campo` (`campo_tipo_proyecto_id`),
    INDEX `idx_valor_texto` (`valor_texto`(255)),
    INDEX `idx_valor_numero` (`valor_numero`),
    INDEX `idx_valor_fecha` (`valor_fecha`),
    FULLTEXT INDEX `ft_valor_texto` (`valor_texto`),
    FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`campo_tipo_proyecto_id`) REFERENCES `campos_tipo_proyecto`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Relación entre proyectos y etiquetas
CREATE TABLE IF NOT EXISTS `proyecto_etiquetas` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `proyecto_id` INT(11) UNSIGNED NOT NULL,
    `etiqueta_id` INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_proyecto_etiqueta` (`proyecto_id`, `etiqueta_id`),
    INDEX `idx_proyecto` (`proyecto_id`),
    INDEX `idx_etiqueta` (`etiqueta_id`),
    FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`etiqueta_id`) REFERENCES `etiquetas`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Relación entre proyectos y categorías
CREATE TABLE IF NOT EXISTS `proyecto_categorias` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `proyecto_id` INT(11) UNSIGNED NOT NULL,
    `categoria_id` INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_proyecto_categoria` (`proyecto_id`, `categoria_id`),
    INDEX `idx_proyecto` (`proyecto_id`),
    INDEX `idx_categoria` (`categoria_id`),
    FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`categoria_id`) REFERENCES `categorias`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 16. TABLAS DE PUBLICACIONES
-- ============================================================================

-- Modelo de publicación (agrupa proyectos/documentos para publicar)
CREATE TABLE IF NOT EXISTS `publicaciones` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `titulo` VARCHAR(500) NOT NULL,
    `slug` VARCHAR(500) NOT NULL UNIQUE,
    `descripcion` TEXT DEFAULT NULL,
    `tipo_publicacion` ENUM('revista', 'libro', 'congreso', 'repositorio', 'otro') DEFAULT 'repositorio',
    `editor_id` INT(11) NOT NULL COMMENT 'Usuario que gestiona la publicación',
    `estado` ENUM('borrador', 'en_proceso', 'publicada', 'archivada') DEFAULT 'borrador',
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `fecha_publicacion` TIMESTAMP NULL DEFAULT NULL,
    `issn` VARCHAR(20) DEFAULT NULL,
    `isbn` VARCHAR(20) DEFAULT NULL,
    `doi` VARCHAR(255) DEFAULT NULL UNIQUE,
    `url_externa` VARCHAR(1000) DEFAULT NULL,
    `metadata` JSON DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_slug` (`slug`),
    INDEX `idx_editor` (`editor_id`),
    INDEX `idx_estado` (`estado`),
    INDEX `idx_doi` (`doi`),
    FOREIGN KEY (`editor_id`) REFERENCES `auth_user`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Relación muchos a muchos entre publicaciones y proyectos
CREATE TABLE IF NOT EXISTS `publicacion_proyectos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `publicacion_id` INT(11) UNSIGNED NOT NULL,
    `proyecto_id` INT(11) UNSIGNED NOT NULL,
    `orden` INT(11) UNSIGNED DEFAULT 0,
    `rol_en_publicacion` VARCHAR(100) DEFAULT NULL COMMENT 'artículo principal, capítulo, etc.',
    `fecha_incorporacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_publicacion_proyecto` (`publicacion_id`, `proyecto_id`),
    INDEX `idx_publicacion` (`publicacion_id`),
    INDEX `idx_proyecto` (`proyecto_id`),
    FOREIGN KEY (`publicacion_id`) REFERENCES `publicaciones`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`proyecto_id`) REFERENCES `proyectos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Relación entre publicaciones y etiquetas
CREATE TABLE IF NOT EXISTS `publicacion_etiquetas` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `publicacion_id` INT(11) UNSIGNED NOT NULL,
    `etiqueta_id` INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_publicacion_etiqueta` (`publicacion_id`, `etiqueta_id`),
    INDEX `idx_publicacion` (`publicacion_id`),
    INDEX `idx_etiqueta` (`etiqueta_id`),
    FOREIGN KEY (`publicacion_id`) REFERENCES `publicaciones`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`etiqueta_id`) REFERENCES `etiquetas`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Relación entre publicaciones y categorías
CREATE TABLE IF NOT EXISTS `publicacion_categorias` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `publicacion_id` INT(11) UNSIGNED NOT NULL,
    `categoria_id` INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_publicacion_categoria` (`publicacion_id`, `categoria_id`),
    INDEX `idx_publicacion` (`publicacion_id`),
    INDEX `idx_categoria` (`categoria_id`),
    FOREIGN KEY (`publicacion_id`) REFERENCES `publicaciones`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`categoria_id`) REFERENCES `categorias`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 17. TABLAS DE RELACIONES Y ENLACES
-- ============================================================================

CREATE TABLE IF NOT EXISTS `relaciones_documentos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_origen_id` INT(11) UNSIGNED NOT NULL,
    `documento_destino_id` INT(11) UNSIGNED NOT NULL,
    `tipo_relacion` ENUM('version_anterior', 'version_posterior', 'parte_de', 'contiene', 'relacionado', 'suplementa', 'cita') NOT NULL,
    `descripcion` TEXT DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_relacion` (`documento_origen_id`, `documento_destino_id`, `tipo_relacion`),
    INDEX `idx_origen` (`documento_origen_id`),
    INDEX `idx_destino` (`documento_destino_id`),
    FOREIGN KEY (`documento_origen_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`documento_destino_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `enlaces_externos` (
    `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
    `documento_id` INT(11) UNSIGNED NOT NULL,
    `tipo` ENUM('repositorio', 'preprint', 'versión_publisher', 'datos', 'código', 'multimedia', 'otros') DEFAULT 'otros',
    `url` VARCHAR(1000) NOT NULL,
    `titulo` VARCHAR(500) DEFAULT NULL,
    `descripcion` TEXT DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_documento` (`documento_id`),
    FOREIGN KEY (`documento_id`) REFERENCES `documentos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 18. INSERCIÓN DE DATOS INICIALES
-- ============================================================================

-- Tipos de recurso comunes
INSERT INTO `tipos_recurso` (`nombre`, `descripcion`, `categoria`) VALUES
('Artículo', 'Artículo científico o académico', 'publicacion'),
('Tesis', 'Tesis de grado o posgrado', 'tesis'),
('Libro', 'Libro completo', 'libro'),
('Capítulo', 'Capítulo de libro', 'libro'),
('Ponencia', 'Ponencia en congreso', 'congreso'),
('Póster', 'Póster científico', 'congreso'),
('Reporte', 'Reporte técnico o de investigación', 'reporte'),
('Dataset', 'Conjunto de datos', 'datos'),
('Software', 'Código fuente o software', 'software'),
('Multimedia', 'Video, audio o imagen', 'multimedia'),
('Otro', 'Otro tipo de recurso', 'otros');

-- Estados de documento
INSERT INTO `estados_documento` (`nombre`, `descripcion`, `orden`) VALUES
('borrador', 'Documento en proceso de creación', 1),
('en_revision', 'Documento enviado para revisión', 2),
('requiere_cambios', 'Documento requiere modificaciones', 3),
('aprobado', 'Documento aprobado para publicación', 4),
('publicado', 'Documento publicado', 5),
('archivado', 'Documento archivado', 6),
('rechazado', 'Documento rechazado', 7);

-- Esquemas de metadatos comunes
INSERT INTO `esquemas_metadatos` (`nombre`, `prefijo`, `namespace`, `version`) VALUES
('Dublin Core', 'dc', 'http://purl.org/dc/elements/1.1/', '1.1'),
('Dublin Core Terms', 'dcterms', 'http://purl.org/dc/terms/', ''),
('MARC', 'marc', 'http://www.loc.gov/MARC21/slim', '21'),
('BibTeX', 'bibtex', 'http://bibtex.org/', '');

-- Licencias comunes
INSERT INTO `licencias` (`nombre`, `codigo`, `version`, `url`, `permite_comercial`, `permite_modificacion`, `requiere_attribucion`) VALUES
('Creative Commons Attribution', 'CC-BY', '4.0', 'https://creativecommons.org/licenses/by/4.0/', FALSE, TRUE, TRUE),
('Creative Commons Attribution-ShareAlike', 'CC-BY-SA', '4.0', 'https://creativecommons.org/licenses/by-sa/4.0/', FALSE, TRUE, TRUE),
('Creative Commons Attribution-NonCommercial', 'CC-BY-NC', '4.0', 'https://creativecommons.org/licenses/by-nc/4.0/', FALSE, TRUE, TRUE),
('Creative Commons Attribution-NonCommercial-ShareAlike', 'CC-BY-NC-SA', '4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', FALSE, TRUE, TRUE),
('Creative Commons Zero', 'CC0', '1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', TRUE, TRUE, FALSE),
('All Rights Reserved', 'ALL_RIGHTS', NULL, NULL, FALSE, FALSE, FALSE);

-- NOTA: Los roles y permisos se gestionan mediante Django (auth_group, auth_permission)
-- No es necesario insertar datos iniciales aquí ya que Django los gestiona.

-- Tipos de notificación
INSERT INTO `tipos_notificacion` (`codigo`, `nombre`, `descripcion`) VALUES
('documento_publicado', 'Documento Publicado', 'Notificación cuando un documento es publicado'),
('revision_asignada', 'Revisión Asignada', 'Notificación cuando se asigna una revisión'),
('revision_completada', 'Revisión Completada', 'Notificación cuando se completa una revisión'),
('comentario_nuevo', 'Nuevo Comentario', 'Notificación de nuevo comentario en documento'),
('cita_recibida', 'Cita Recibida', 'Notificación cuando otro documento cita el tuyo'),
('documento_aprobado', 'Documento Aprobado', 'Notificación de aprobación de documento');

-- Configuración inicial del sistema
INSERT INTO `configuracion_sistema` (`clave`, `valor`, `tipo`, `categoria`, `descripcion`) VALUES
('nombre_repositorio', 'Repositorio Digital de Investigación', 'texto', 'general', 'Nombre del repositorio'),
('descripcion_repositorio', 'Sistema de repositorio digital para la gestión de documentos de investigación', 'texto', 'general', 'Descripción del repositorio'),
('email_contacto', 'admin@repositorio.edu', 'texto', 'general', 'Email de contacto'),
('items_por_pagina', '20', 'numero', 'interfaz', 'Número de items por página'),
('habilitar_registro', 'true', 'booleano', 'usuarios', 'Permitir registro de nuevos usuarios'),
('requiere_aprobacion', 'true', 'booleano', 'publicacion', 'Requiere aprobación para publicar'),
('habilitar_comentarios', 'true', 'booleano', 'interaccion', 'Habilitar comentarios en documentos'),
('habilitar_descargas', 'true', 'booleano', 'acceso', 'Permitir descarga de archivos');

-- Tipos de proyecto iniciales
INSERT INTO `tipos_proyecto` (`nombre`, `slug`, `descripcion`, `orden`) VALUES
('Tesis', 'tesis', 'Tesis de grado o posgrado', 1),
('Monografía', 'monografia', 'Monografía académica', 2),
('Artículo Científico', 'articulo-cientifico', 'Artículo científico o académico', 3),
('Proyecto de Investigación', 'proyecto-investigacion', 'Proyecto de investigación', 4),
('Informe Técnico', 'informe-tecnico', 'Informe técnico o de investigación', 5),
('Ponencia', 'ponencia', 'Ponencia en congreso o evento', 6),
('Póster', 'poster', 'Póster científico', 7),
('Capítulo de Libro', 'capitulo-libro', 'Capítulo de libro', 8),
('Libro', 'libro', 'Libro completo', 9),
('Otro', 'otro', 'Otro tipo de proyecto', 10);

-- Campos para tipo Tesis
INSERT INTO `campos_tipo_proyecto` (`tipo_proyecto_id`, `nombre`, `slug`, `etiqueta`, `tipo_dato`, `es_obligatorio`, `orden`, `categoria`) VALUES
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Objetivos', 'objetivos', 'Objetivos', 'textarea', TRUE, 1, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Hipótesis', 'hipotesis', 'Hipótesis', 'textarea', FALSE, 2, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Metodología', 'metodologia', 'Metodología', 'textarea', TRUE, 3, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Director', 'director', 'Director de Tesis', 'texto', TRUE, 4, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Fecha de Defensa', 'fecha_defensa', 'Fecha de Defensa', 'fecha', FALSE, 5, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Jurado', 'jurado', 'Jurado', 'textarea', FALSE, 6, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Nivel Académico', 'nivel_academico', 'Nivel Académico', 'select', TRUE, 7, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Programa', 'programa', 'Programa Académico', 'texto', TRUE, 8, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Línea de Investigación', 'linea_investigacion', 'Línea de Investigación', 'texto', FALSE, 9, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'tesis'), 'Palabras Clave', 'palabras_clave', 'Palabras Clave', 'multiselect', TRUE, 10, 'Clasificación');

-- Actualizar valores_posibles para nivel_academico
UPDATE `campos_tipo_proyecto` 
SET `valores_posibles` = JSON_ARRAY('Pregrado', 'Maestría', 'Doctorado', 'Especialización')
WHERE `slug` = 'nivel_academico' AND `tipo_proyecto_id` = (SELECT id FROM tipos_proyecto WHERE slug = 'tesis');

-- Campos para tipo Monografía
INSERT INTO `campos_tipo_proyecto` (`tipo_proyecto_id`, `nombre`, `slug`, `etiqueta`, `tipo_dato`, `es_obligatorio`, `orden`, `categoria`) VALUES
((SELECT id FROM tipos_proyecto WHERE slug = 'monografia'), 'Objetivo General', 'objetivo_general', 'Objetivo General', 'textarea', TRUE, 1, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'monografia'), 'Objetivos Específicos', 'objetivos_especificos', 'Objetivos Específicos', 'textarea', TRUE, 2, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'monografia'), 'Metodología', 'metodologia', 'Metodología', 'textarea', TRUE, 3, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'monografia'), 'Asesor', 'asesor', 'Asesor', 'texto', TRUE, 4, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'monografia'), 'Fecha de Entrega', 'fecha_entrega', 'Fecha de Entrega', 'fecha', FALSE, 5, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'monografia'), 'Programa', 'programa', 'Programa Académico', 'texto', TRUE, 6, 'Información General');

-- Campos para tipo Artículo Científico
INSERT INTO `campos_tipo_proyecto` (`tipo_proyecto_id`, `nombre`, `slug`, `etiqueta`, `tipo_dato`, `es_obligatorio`, `orden`, `categoria`) VALUES
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Abstract', 'abstract', 'Abstract', 'textarea', TRUE, 1, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Keywords', 'keywords', 'Keywords', 'multiselect', TRUE, 2, 'Información General'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Revista', 'revista', 'Revista', 'texto', TRUE, 3, 'Publicación'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Volumen', 'volumen', 'Volumen', 'numero', FALSE, 4, 'Publicación'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Número', 'numero', 'Número', 'texto', FALSE, 5, 'Publicación'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Páginas', 'paginas', 'Páginas', 'texto', FALSE, 6, 'Publicación'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'DOI', 'doi', 'DOI', 'url', FALSE, 7, 'Publicación'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Fecha de Aceptación', 'fecha_aceptacion', 'Fecha de Aceptación', 'fecha', FALSE, 8, 'Publicación'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Fecha de Publicación', 'fecha_publicacion', 'Fecha de Publicación', 'fecha', FALSE, 9, 'Publicación'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Metodología', 'metodologia', 'Metodología', 'textarea', TRUE, 10, 'Contenido'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Resultados', 'resultados', 'Resultados', 'textarea', TRUE, 11, 'Contenido'),
((SELECT id FROM tipos_proyecto WHERE slug = 'articulo-cientifico'), 'Conclusiones', 'conclusiones', 'Conclusiones', 'textarea', TRUE, 12, 'Contenido');

COMMIT;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- FIN DEL ESQUEMA
-- ============================================================================

