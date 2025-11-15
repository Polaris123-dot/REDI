# Estructura de Apps del Sistema

## Organización de Apps y Modelos

### 1. **usuarios** (Ya existe)
**Modelos:**
- `Persona` - Extensión del User de Django

**Responsabilidad:**
- Gestión de perfiles de usuario
- Información adicional de usuarios

---

### 2. **proyectos**
**Modelos:**
- `TipoProyecto` - Tipos de proyecto (Tesis, Monografía, etc.)
- `CampoTipoProyecto` - Campos definidos para cada tipo
- `Proyecto` - Tabla principal de proyectos
- `ValorCampoProyecto` - Valores de campos dinámicos (EAV)

**Responsabilidad:**
- Sistema de proyectos con campos dinámicos
- Gestión de tipos de proyecto
- Almacenamiento de valores dinámicos

---

### 3. **publicaciones**
**Modelos:**
- `Publicacion` - Modelo de publicación
- `PublicacionProyecto` - Relación publicaciones ↔ proyectos

**Responsabilidad:**
- Agrupar proyectos para publicar
- Gestión de publicaciones (revistas, libros, congresos)

---

### 4. **repositorio**
**Modelos:**
- `Comunidad` - Comunidades del repositorio
- `Coleccion` - Colecciones dentro de comunidades
- `TipoRecurso` - Tipos de recurso (Artículo, Tesis, etc.)
- `EstadoDocumento` - Estados de documento
- `Documento` - Documentos del repositorio
- `VersionDocumento` - Versiones de documentos
- `Archivo` - Archivos asociados a versiones
- `Autor` - Autores de documentos
- `Colaborador` - Colaboradores de documentos
- `RelacionDocumento` - Relaciones entre documentos
- `EnlaceExterno` - Enlaces externos de documentos

**Responsabilidad:**
- Gestión de documentos del repositorio
- Versiones y archivos
- Autores y colaboradores
- Estructura jerárquica (comunidades → colecciones → documentos)

---

### 5. **catalogacion**
**Modelos:**
- `Categoria` - Categorías jerárquicas
- `Etiqueta` - Etiquetas libres
- `ProyectoCategoria` - Relación proyectos ↔ categorías
- `ProyectoEtiqueta` - Relación proyectos ↔ etiquetas
- `DocumentoCategoria` - Relación documentos ↔ categorías
- `DocumentoEtiqueta` - Relación documentos ↔ etiquetas
- `PublicacionCategoria` - Relación publicaciones ↔ categorías
- `PublicacionEtiqueta` - Relación publicaciones ↔ etiquetas

**Responsabilidad:**
- Sistema de categorización y etiquetado
- Compartido entre proyectos, documentos y publicaciones

---

### 6. **metadatos**
**Modelos:**
- `EsquemaMetadatos` - Esquemas (Dublin Core, MARC, etc.)
- `CampoMetadatos` - Campos de metadatos
- `MetadatoDocumento` - Valores de metadatos para documentos

**Responsabilidad:**
- Gestión de esquemas de metadatos
- Campos de metadatos configurables
- Valores de metadatos para documentos

---

### 7. **revisiones**
**Modelos:**
- `ProcesoRevision` - Procesos de revisión
- `Revision` - Revisiones individuales
- `CriterioRevision` - Criterios de evaluación
- `EvaluacionCriterio` - Evaluaciones de criterios

**Responsabilidad:**
- Sistema de revisión por pares
- Criterios de evaluación
- Procesos de aprobación

---

### 8. **estadisticas**
**Modelos:**
- `VisitaDocumento` - Visitas a documentos
- `DescargaArchivo` - Descargas de archivos
- `EstadisticaAgregada` - Estadísticas agregadas

**Responsabilidad:**
- Tracking de visitas y descargas
- Analytics y estadísticas
- Reportes de uso

---

### 9. **interaccion**
**Modelos:**
- `Comentario` - Comentarios en documentos
- `Valoracion` - Valoraciones de documentos
- `Cita` - Citas entre documentos
- `ReferenciaBibliografica` - Referencias bibliográficas

**Responsabilidad:**
- Comentarios y discusiones
- Sistema de valoraciones
- Citas y referencias

---

### 10. **notificaciones**
**Modelos:**
- `TipoNotificacion` - Tipos de notificación
- `Notificacion` - Notificaciones a usuarios

**Responsabilidad:**
- Sistema de notificaciones
- Alertas y avisos

---

### 11. **busqueda**
**Modelos:**
- `IndiceBusqueda` - Índices de búsqueda full-text
- `Busqueda` - Historial de búsquedas

**Responsabilidad:**
- Índices de búsqueda
- Full-text search
- Historial de búsquedas

---

### 12. **configuracion**
**Modelos:**
- `ConfiguracionSistema` - Configuración del sistema
- `LogSistema` - Logs del sistema

**Responsabilidad:**
- Configuración centralizada
- Logging y auditoría

---

### 13. **licencias** (Opcional, puede ir en repositorio)
**Modelos:**
- `Licencia` - Licencias (Creative Commons, etc.)
- `DerechoDocumento` - Derechos de documentos

**Responsabilidad:**
- Gestión de licencias
- Derechos de autor

---

## Dependencias entre Apps

```
usuarios (base)
    ↓
proyectos ──→ catalogacion
    ↓              ↓
publicaciones ──→ catalogacion
    ↓
repositorio ──→ catalogacion
    ↓              ↓
metadatos ──→ repositorio
    ↓
revisiones ──→ repositorio
    ↓
estadisticas ──→ repositorio
    ↓
interaccion ──→ repositorio
    ↓
notificaciones ──→ usuarios
    ↓
busqueda ──→ repositorio, proyectos
    ↓
configuracion (independiente)
```

## Orden de Instalación en INSTALLED_APPS

1. `usuarios` - Base de usuarios
2. `catalogacion` - Categorías y etiquetas (compartidas)
3. `proyectos` - Sistema de proyectos
4. `repositorio` - Documentos y estructura
5. `publicaciones` - Modelo de publicación
6. `metadatos` - Esquemas de metadatos
7. `revisiones` - Procesos de revisión
8. `estadisticas` - Analytics
9. `interaccion` - Comentarios y valoraciones
10. `notificaciones` - Sistema de notificaciones
11. `busqueda` - Índices de búsqueda
12. `configuracion` - Configuración del sistema





