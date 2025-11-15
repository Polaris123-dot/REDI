# Mapeo de Tablas SQL a Modelos Django

## Guía de Mapeo: Tablas SQL → Apps → Modelos

### 📁 **usuarios** (Ya existe)
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `usuarios_persona` | `Persona` | ✅ Creado |

---

### 📁 **proyectos**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `tipos_proyecto` | `TipoProyecto` | ⏳ Pendiente |
| `campos_tipo_proyecto` | `CampoTipoProyecto` | ⏳ Pendiente |
| `proyectos` | `Proyecto` | ⏳ Pendiente |
| `valores_campo_proyecto` | `ValorCampoProyecto` | ⏳ Pendiente |

---

### 📁 **publicaciones**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `publicaciones` | `Publicacion` | ⏳ Pendiente |
| `publicacion_proyectos` | `PublicacionProyecto` | ⏳ Pendiente |
| `publicacion_etiquetas` | `PublicacionEtiqueta` | ⏳ Pendiente |
| `publicacion_categorias` | `PublicacionCategoria` | ⏳ Pendiente |

---

### 📁 **repositorio**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `comunidades` | `Comunidad` | ⏳ Pendiente |
| `colecciones` | `Coleccion` | ⏳ Pendiente |
| `tipos_recurso` | `TipoRecurso` | ⏳ Pendiente |
| `estados_documento` | `EstadoDocumento` | ⏳ Pendiente |
| `documentos` | `Documento` | ⏳ Pendiente |
| `versiones_documento` | `VersionDocumento` | ⏳ Pendiente |
| `archivos` | `Archivo` | ⏳ Pendiente |
| `autores` | `Autor` | ⏳ Pendiente |
| `colaboradores` | `Colaborador` | ⏳ Pendiente |
| `relaciones_documentos` | `RelacionDocumento` | ⏳ Pendiente |
| `enlaces_externos` | `EnlaceExterno` | ⏳ Pendiente |

---

### 📁 **catalogacion**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `categorias` | `Categoria` | ⏳ Pendiente |
| `etiquetas` | `Etiqueta` | ⏳ Pendiente |
| `proyecto_etiquetas` | `ProyectoEtiqueta` | ⏳ Pendiente |
| `proyecto_categorias` | `ProyectoCategoria` | ⏳ Pendiente |
| `documento_etiquetas` | `DocumentoEtiqueta` | ⏳ Pendiente |
| `documento_categorias` | `DocumentoCategoria` | ⏳ Pendiente |
| `publicacion_etiquetas` | `PublicacionEtiqueta` | ⏳ Pendiente |
| `publicacion_categorias` | `PublicacionCategoria` | ⏳ Pendiente |

---

### 📁 **metadatos**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `esquemas_metadatos` | `EsquemaMetadatos` | ⏳ Pendiente |
| `campos_metadatos` | `CampoMetadatos` | ⏳ Pendiente |
| `metadatos_documento` | `MetadatoDocumento` | ⏳ Pendiente |

---

### 📁 **revisiones**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `procesos_revision` | `ProcesoRevision` | ⏳ Pendiente |
| `revisiones` | `Revision` | ⏳ Pendiente |
| `criterios_revision` | `CriterioRevision` | ⏳ Pendiente |
| `evaluaciones_criterios` | `EvaluacionCriterio` | ⏳ Pendiente |

---

### 📁 **estadisticas**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `visitas_documento` | `VisitaDocumento` | ⏳ Pendiente |
| `descargas_archivo` | `DescargaArchivo` | ⏳ Pendiente |
| `estadisticas_agregadas` | `EstadisticaAgregada` | ⏳ Pendiente |

---

### 📁 **interaccion**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `comentarios` | `Comentario` | ⏳ Pendiente |
| `valoraciones` | `Valoracion` | ⏳ Pendiente |
| `citas` | `Cita` | ⏳ Pendiente |
| `referencias_bibliograficas` | `ReferenciaBibliografica` | ⏳ Pendiente |

---

### 📁 **notificaciones**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `tipos_notificacion` | `TipoNotificacion` | ⏳ Pendiente |
| `notificaciones` | `Notificacion` | ⏳ Pendiente |

---

### 📁 **busqueda**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `indices_busqueda` | `IndiceBusqueda` | ⏳ Pendiente |
| `busquedas` | `Busqueda` | ⏳ Pendiente |

---

### 📁 **configuracion**
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `configuracion_sistema` | `ConfiguracionSistema` | ⏳ Pendiente |
| `logs_sistema` | `LogSistema` | ⏳ Pendiente |

---

### 📁 **repositorio** (Licencias - puede ir aquí)
| Tabla SQL | Modelo Django | Estado |
|-----------|---------------|--------|
| `licencias` | `Licencia` | ⏳ Pendiente |
| `derechos_documento` | `DerechoDocumento` | ⏳ Pendiente |

---

## Resumen por App

- **usuarios**: 1 modelo
- **proyectos**: 4 modelos
- **publicaciones**: 4 modelos
- **repositorio**: 11 modelos
- **catalogacion**: 8 modelos
- **metadatos**: 3 modelos
- **revisiones**: 4 modelos
- **estadisticas**: 3 modelos
- **interaccion**: 4 modelos
- **notificaciones**: 2 modelos
- **busqueda**: 2 modelos
- **configuracion**: 2 modelos

**Total: 48 modelos**





