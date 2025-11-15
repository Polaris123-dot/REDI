# Guía de Creación de Modelos Django

## 📋 Mapeo Completo: Tablas SQL → Apps → Modelos Django

### 📁 **usuarios** ✅
**Tabla SQL:** `usuarios_persona`  
**Modelo Django:** `Persona`  
**Estado:** ✅ Creado

---

### 📁 **proyectos**
**Responsabilidad:** Sistema de proyectos con campos dinámicos (EAV)

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `tipos_proyecto` | `TipoProyecto` | Modelo principal |
| `campos_tipo_proyecto` | `CampoTipoProyecto` | FK → TipoProyecto |
| `proyectos` | `Proyecto` | FK → TipoProyecto, User |
| `valores_campo_proyecto` | `ValorCampoProyecto` | FK → Proyecto, CampoTipoProyecto |

**Dependencias:** `catalogacion` (ManyToMany con Etiqueta, Categoria)

---

### 📁 **publicaciones**
**Responsabilidad:** Modelo de publicación

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `publicaciones` | `Publicacion` | FK → User (editor) |
| `publicacion_proyectos` | `PublicacionProyecto` | FK → Publicacion, Proyecto |
| `publicacion_etiquetas` | `PublicacionEtiqueta` | FK → Publicacion, Etiqueta |
| `publicacion_categorias` | `PublicacionCategoria` | FK → Publicacion, Categoria |

**Dependencias:** `proyectos`, `catalogacion`

---

### 📁 **repositorio**
**Responsabilidad:** Gestión de documentos del repositorio

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `comunidades` | `Comunidad` | FK → User (administrador), Self (padre) |
| `colecciones` | `Coleccion` | FK → Comunidad, User (administrador), Self (padre) |
| `tipos_recurso` | `TipoRecurso` | Modelo principal |
| `estados_documento` | `EstadoDocumento` | Modelo principal |
| `documentos` | `Documento` | FK → TipoRecurso, Coleccion, User, EstadoDocumento, Licencia |
| `versiones_documento` | `VersionDocumento` | FK → Documento, User |
| `archivos` | `Archivo` | FK → VersionDocumento |
| `autores` | `Autor` | FK → Documento, User (opcional) |
| `colaboradores` | `Colaborador` | FK → Documento, User |
| `relaciones_documentos` | `RelacionDocumento` | FK → Documento (origen, destino) |
| `enlaces_externos` | `EnlaceExterno` | FK → Documento |
| `licencias` | `Licencia` | Modelo principal |
| `derechos_documento` | `DerechoDocumento` | FK → Documento |

**Dependencias:** `catalogacion` (ManyToMany con Etiqueta, Categoria)

---

### 📁 **catalogacion**
**Responsabilidad:** Sistema de categorización y etiquetado (compartido)

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `categorias` | `Categoria` | FK → Self (padre) |
| `etiquetas` | `Etiqueta` | Modelo principal |
| `proyecto_etiquetas` | `ProyectoEtiqueta` | FK → Proyecto, Etiqueta |
| `proyecto_categorias` | `ProyectoCategoria` | FK → Proyecto, Categoria |
| `documento_etiquetas` | `DocumentoEtiqueta` | FK → Documento, Etiqueta |
| `documento_categorias` | `DocumentoCategoria` | FK → Documento, Categoria |
| `publicacion_etiquetas` | `PublicacionEtiqueta` | FK → Publicacion, Etiqueta |
| `publicacion_categorias` | `PublicacionCategoria` | FK → Publicacion, Categoria |

**Dependencias:** Ninguna (compartida)

---

### 📁 **metadatos**
**Responsabilidad:** Esquemas y campos de metadatos

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `esquemas_metadatos` | `EsquemaMetadatos` | Modelo principal |
| `campos_metadatos` | `CampoMetadatos` | FK → EsquemaMetadatos |
| `metadatos_documento` | `MetadatoDocumento` | FK → Documento, CampoMetadatos |

**Dependencias:** `repositorio` (Documento)

---

### 📁 **revisiones**
**Responsabilidad:** Procesos de revisión y aprobación

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `procesos_revision` | `ProcesoRevision` | FK → Documento, User (iniciado_por) |
| `revisiones` | `Revision` | FK → ProcesoRevision, User (revisor) |
| `criterios_revision` | `CriterioRevision` | Modelo principal |
| `evaluaciones_criterios` | `EvaluacionCriterio` | FK → Revision, CriterioRevision |

**Dependencias:** `repositorio` (Documento)

---

### 📁 **estadisticas**
**Responsabilidad:** Analytics y estadísticas

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `visitas_documento` | `VisitaDocumento` | FK → Documento, User (opcional) |
| `descargas_archivo` | `DescargaArchivo` | FK → Archivo, User (opcional) |
| `estadisticas_agregadas` | `EstadisticaAgregada` | FK → Documento |

**Dependencias:** `repositorio` (Documento, Archivo)

---

### 📁 **interaccion**
**Responsabilidad:** Comentarios, valoraciones y citas

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `comentarios` | `Comentario` | FK → Documento, User, Self (padre) |
| `valoraciones` | `Valoracion` | FK → Documento, User |
| `citas` | `Cita` | FK → Documento (citado, que_cita) |
| `referencias_bibliograficas` | `ReferenciaBibliografica` | FK → Documento |

**Dependencias:** `repositorio` (Documento)

---

### 📁 **notificaciones**
**Responsabilidad:** Sistema de notificaciones

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `tipos_notificacion` | `TipoNotificacion` | Modelo principal |
| `notificaciones` | `Notificacion` | FK → User, TipoNotificacion, Documento (opcional) |

**Dependencias:** `usuarios` (User)

---

### 📁 **busqueda**
**Responsabilidad:** Índices de búsqueda y full-text

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `indices_busqueda` | `IndiceBusqueda` | FK → Documento |
| `busquedas` | `Busqueda` | FK → User (opcional) |

**Dependencias:** `repositorio` (Documento)

---

### 📁 **configuracion**
**Responsabilidad:** Configuración del sistema y logs

| Tabla SQL | Modelo Django | Tipo de Relación |
|-----------|---------------|------------------|
| `configuracion_sistema` | `ConfiguracionSistema` | Modelo principal |
| `logs_sistema` | `LogSistema` | FK → User (opcional) |

**Dependencias:** Ninguna (independiente)

---

## 📊 Resumen por App

| App | Modelos | Estado |
|-----|---------|--------|
| usuarios | 1 | ✅ Creado |
| proyectos | 4 | ⏳ Pendiente |
| publicaciones | 4 | ⏳ Pendiente |
| repositorio | 13 | ⏳ Pendiente |
| catalogacion | 8 | ⏳ Pendiente |
| metadatos | 3 | ⏳ Pendiente |
| revisiones | 4 | ⏳ Pendiente |
| estadisticas | 3 | ⏳ Pendiente |
| interaccion | 4 | ⏳ Pendiente |
| notificaciones | 2 | ⏳ Pendiente |
| busqueda | 2 | ⏳ Pendiente |
| configuracion | 2 | ⏳ Pendiente |
| **TOTAL** | **48** | **1 ✅ / 47 ⏳** |

---

## 🎯 Orden Recomendado para Crear Modelos

1. **catalogacion** (sin dependencias)
2. **configuracion** (sin dependencias)
3. **proyectos** (depende de catalogacion)
4. **repositorio** (depende de catalogacion)
5. **publicaciones** (depende de proyectos, catalogacion)
6. **metadatos** (depende de repositorio)
7. **revisiones** (depende de repositorio)
8. **estadisticas** (depende de repositorio)
9. **interaccion** (depende de repositorio)
10. **notificaciones** (depende de usuarios)
11. **busqueda** (depende de repositorio, proyectos)

---

## ✅ Estado Actual

- ✅ 12 apps creadas
- ✅ Apps registradas en `settings.py`
- ✅ Estructura de directorios lista
- ⏳ 47 modelos pendientes de crear

**Siguiente paso:** Crear los modelos Django basados en el esquema SQL.





