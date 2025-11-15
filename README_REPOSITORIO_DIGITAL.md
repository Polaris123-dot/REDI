# Esquema de Base de Datos - Repositorio Digital de Investigación

## Descripción General

Este es un esquema SQL completo y complejo para un sistema de repositorio digital de investigación. El esquema está diseñado para soportar todas las funcionalidades necesarias de un repositorio institucional moderno, incluyendo gestión de documentos, metadatos, versiones, revisiones, estadísticas, y más.

## Características Principales

### 1. **Gestión de Usuarios y Autenticación**
- **Integración con Django Auth**: Utiliza el sistema de autenticación nativo de Django (`auth_user`, `auth_group`, `auth_permission`)
- **Modelo Persona**: Extiende el User de Django con información adicional del repositorio
  - Información institucional (institución, departamento, cargo)
  - Identificadores académicos (ORCID, Google Scholar, ResearchGate, LinkedIn)
  - Biografía y foto de perfil
  - Preferencias de notificaciones
- **Roles y Permisos**: Gestionados mediante los Groups y Permissions de Django

### 2. **Estructura Jerárquica**
- **Comunidades**: Organización de alto nivel (ej: Facultades, Institutos)
- **Colecciones**: Agrupación dentro de comunidades (ej: Departamentos, Líneas de investigación)
- Soporte para jerarquías anidadas

### 3. **Gestión de Documentos**
- Soporte para múltiples tipos de recursos (artículos, tesis, libros, datasets, etc.)
- Sistema de versiones completo
- Estados del documento (borrador, en revisión, publicado, etc.)
- Handles persistentes y DOIs
- Metadatos Dublin Core y otros esquemas

### 4. **Gestión de Archivos**
- Múltiples archivos por versión
- Checksums (MD5, SHA256) para integridad
- Metadatos de archivos (tipo MIME, tamaño, formato, etc.)
- Soporte para archivos multimedia

### 5. **Autores y Colaboradores**
- Relación entre usuarios y autores
- Soporte para autores externos
- Orden de autores y autor correspondiente
- Colaboradores con roles específicos

### 6. **Sistema de Metadatos Avanzado**
- Múltiples esquemas de metadatos (Dublin Core, MARC, BibTeX)
- Campos personalizables
- Metadatos en múltiples idiomas
- Campos obligatorios y repetibles

### 7. **Categorización y Etiquetado**
- Sistema de categorías jerárquico
- Etiquetas libres
- Palabras clave
- Temas y clasificaciones

### 8. **Sistema de Revisión y Aprobación**
- Procesos de revisión configurables
- Revisión por pares (peer review)
- Criterios de evaluación personalizables
- Múltiples revisores por documento
- Comentarios públicos y privados

### 9. **Licencias y Derechos**
- Soporte para licencias Creative Commons
- Gestión de derechos de autor
- Información de titularidad

### 10. **Estadísticas y Analytics**
- Visitas y descargas detalladas
- Estadísticas agregadas por período
- Geolocalización de accesos
- Tiempo de lectura
- Seguimiento de IPs y user agents

### 11. **Citas y Referencias**
- Sistema de citas entre documentos
- Referencias bibliográficas
- Integración con DOIs
- Contexto de citación

### 12. **Interacción Social**
- Comentarios en documentos
- Sistema de valoraciones (1-5 estrellas)
- Comentarios anidados (respuestas)
- Moderación de comentarios

### 13. **Notificaciones**
- Sistema de notificaciones completo
- Tipos de notificación configurables
- Plantillas de notificación
- Notificaciones leídas/no leídas

### 14. **Búsqueda Avanzada**
- Índices de búsqueda full-text
- Búsquedas guardadas
- Filtros avanzados
- Logs de búsquedas para analytics

### 15. **Relaciones entre Documentos**
- Versiones anteriores/posteriores
- Documentos relacionados
- Partes y contenedores
- Enlaces externos

### 16. **Sistema y Configuración**
- Configuración del sistema centralizada
- Logs del sistema
- Categorización de configuraciones

## Estructura de Tablas

### Tablas Principales (16 secciones):

1. **Persona (Extensión de Django Auth)** (1 tabla)
   - `usuarios_persona` - Información adicional del usuario
   - **Nota**: Las tablas `auth_user`, `auth_group`, `auth_permission` son gestionadas por Django

2. **Comunidades y Colecciones** (2 tablas)
   - `comunidades`
   - `colecciones`

3. **Documentos y Recursos** (3 tablas)
   - `tipos_recurso`
   - `estados_documento`
   - `documentos`

4. **Versiones y Archivos** (2 tablas)
   - `versiones_documento`
   - `archivos`

5. **Autores y Colaboradores** (2 tablas)
   - `autores`
   - `colaboradores`

6. **Metadatos y Categorización** (7 tablas)
   - `esquemas_metadatos`
   - `campos_metadatos`
   - `metadatos_documento`
   - `categorias`
   - `documento_categorias`
   - `etiquetas`
   - `documento_etiquetas`

7. **Revisión y Aprobación** (4 tablas)
   - `procesos_revision`
   - `revisiones`
   - `criterios_revision`
   - `evaluaciones_criterios`

8. **Licencias y Derechos** (2 tablas)
   - `licencias`
   - `derechos_documento`

9. **Estadísticas y Analytics** (3 tablas)
   - `visitas_documento`
   - `descargas_archivo`
   - `estadisticas_agregadas`

10. **Citas y Referencias** (2 tablas)
    - `citas`
    - `referencias_bibliograficas`

11. **Comentarios y Discusiones** (2 tablas)
    - `comentarios`
    - `valoraciones`

12. **Notificaciones** (2 tablas)
    - `tipos_notificacion`
    - `notificaciones`

13. **Búsqueda y Full-Text** (2 tablas)
    - `indices_busqueda`
    - `busquedas`

14. **Configuración y Sistema** (2 tablas)
    - `configuracion_sistema`
    - `logs_sistema`

15. **Relaciones y Enlaces** (2 tablas)
    - `relaciones_documentos`
    - `enlaces_externos`

## Características Técnicas

### Índices y Optimización
- Índices en campos clave para búsquedas rápidas
- Índices full-text para búsqueda de contenido
- Índices compuestos para consultas complejas
- Claves foráneas con cascadas apropiadas

### Integridad de Datos
- Restricciones de integridad referencial
- Valores únicos donde corresponde
- Checksums para archivos
- Validación de tipos de datos

### Escalabilidad
- Uso de BIGINT para IDs que pueden crecer mucho
- Particionamiento potencial en tablas grandes (visitas, logs)
- Índices optimizados para consultas frecuentes

### Seguridad
- Passwords hasheados
- Roles y permisos granulares
- Auditoría con logs
- Control de acceso por visibilidad

## Datos Iniciales

El esquema incluye datos iniciales para:
- Tipos de recursos comunes
- Estados de documento
- Esquemas de metadatos (Dublin Core, MARC, BibTeX)
- Licencias Creative Commons
- Roles del sistema
- Tipos de notificación
- Configuración básica del sistema

## Uso

### Instalación

```sql
-- Ejecutar el script completo
mysql -u usuario -p nombre_base_datos < esquema_repositorio_digital.sql

-- O desde MySQL
source esquema_repositorio_digital.sql;
```

### Personalización

1. **Ajustar tipos de recurso**: Modificar `tipos_recurso` según necesidades
2. **Configurar esquemas de metadatos**: Agregar campos a `campos_metadatos`
3. **Definir criterios de revisión**: Personalizar `criterios_revision`
4. **Configurar sistema**: Modificar valores en `configuracion_sistema`

## Ejemplos de Consultas

### Documentos más visitados
```sql
SELECT d.titulo, COUNT(v.id) as total_visitas
FROM documentos d
JOIN visitas_documento v ON d.id = v.documento_id
WHERE d.estado_id = (SELECT id FROM estados_documento WHERE nombre = 'publicado')
GROUP BY d.id
ORDER BY total_visitas DESC
LIMIT 10;
```

### Documentos por autor
```sql
SELECT u.nombre, u.apellidos, COUNT(DISTINCT a.documento_id) as total_documentos
FROM usuarios u
JOIN autores a ON u.id = a.usuario_id
GROUP BY u.id
ORDER BY total_documentos DESC;
```

### Estadísticas de colección
```sql
SELECT c.nombre, 
       COUNT(DISTINCT d.id) as total_documentos,
       COUNT(DISTINCT a.id) as total_autores,
       SUM(est.total_descargas) as total_descargas
FROM colecciones c
LEFT JOIN documentos d ON c.id = d.coleccion_id
LEFT JOIN autores a ON d.id = a.documento_id
LEFT JOIN estadisticas_agregadas est ON d.id = est.documento_id
GROUP BY c.id;
```

## Compatibilidad

- **MySQL**: 5.7+ / 8.0+
- **MariaDB**: 10.2+
- **PostgreSQL**: Requiere ajustes menores (tipos de datos JSON, ENUM)

## Notas

- El esquema utiliza `utf8mb4` para soporte completo de Unicode
- Se recomienda usar InnoDB para transacciones y claves foráneas
- Para producción, considerar particionamiento en tablas grandes
- Implementar backups regulares debido a la complejidad del sistema

## Extensiones Futuras

Posibles mejoras:
- Tabla de workflow personalizable
- Sistema de workflows visuales
- Integración con sistemas externos (ORCID API, CrossRef, etc.)
- Soporte para datasets grandes
- Sistema de preservación digital
- Integración con sistemas de gestión de referencias (Mendeley, Zotero)

## Licencia

Este esquema es proporcionado como referencia y puede ser modificado según necesidades específicas.

