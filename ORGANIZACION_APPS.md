# Organización de Apps del Sistema

## ✅ Apps Creadas

Todas las apps han sido creadas exitosamente:

1. ✅ **usuarios** (Ya existía)
2. ✅ **proyectos**
3. ✅ **publicaciones**
4. ✅ **repositorio**
5. ✅ **catalogacion**
6. ✅ **metadatos**
7. ✅ **revisiones**
8. ✅ **estadisticas**
9. ✅ **interaccion**
10. ✅ **notificaciones**
11. ✅ **busqueda**
12. ✅ **configuracion**

## 📋 Distribución de Modelos por App

### 1. **usuarios**
**Responsabilidad:** Gestión de usuarios y perfiles

**Modelos:**
- `Persona` - Extensión del User de Django

**Dependencias:** Ninguna (base)

---

### 2. **catalogacion**
**Responsabilidad:** Sistema de categorización y etiquetado (compartido)

**Modelos:**
- `Categoria` - Categorías jerárquicas
- `Etiqueta` - Etiquetas libres
- `ProyectoCategoria` - Relación proyectos ↔ categorías
- `ProyectoEtiqueta` - Relación proyectos ↔ etiquetas
- `DocumentoCategoria` - Relación documentos ↔ categorías
- `DocumentoEtiqueta` - Relación documentos ↔ etiquetas
- `PublicacionCategoria` - Relación publicaciones ↔ categorías
- `PublicacionEtiqueta` - Relación publicaciones ↔ etiquetas

**Dependencias:** Ninguna (compartida)

---

### 3. **proyectos**
**Responsabilidad:** Sistema de proyectos con campos dinámicos (EAV)

**Modelos:**
- `TipoProyecto` - Tipos de proyecto (Tesis, Monografía, etc.)
- `CampoTipoProyecto` - Campos definidos para cada tipo
- `Proyecto` - Tabla principal de proyectos
- `ValorCampoProyecto` - Valores de campos dinámicos (EAV)

**Dependencias:** `catalogacion` (para etiquetas y categorías)

---

### 4. **repositorio**
**Responsabilidad:** Gestión de documentos del repositorio

**Modelos:**
- `Comunidad` - Comunidades del repositorio
- `Coleccion` - Colecciones dentro de comunidades
- `TipoRecurso` - Tipos de recurso
- `EstadoDocumento` - Estados de documento
- `Documento` - Documentos del repositorio
- `VersionDocumento` - Versiones de documentos
- `Archivo` - Archivos asociados a versiones
- `Autor` - Autores de documentos
- `Colaborador` - Colaboradores de documentos
- `RelacionDocumento` - Relaciones entre documentos
- `EnlaceExterno` - Enlaces externos
- `Licencia` - Licencias (Creative Commons, etc.)
- `DerechoDocumento` - Derechos de documentos

**Dependencias:** `catalogacion` (para etiquetas y categorías)

---

### 5. **publicaciones**
**Responsabilidad:** Modelo de publicación

**Modelos:**
- `Publicacion` - Modelo de publicación
- `PublicacionProyecto` - Relación publicaciones ↔ proyectos

**Dependencias:** `proyectos`, `catalogacion`

---

### 6. **metadatos**
**Responsabilidad:** Esquemas y campos de metadatos

**Modelos:**
- `EsquemaMetadatos` - Esquemas (Dublin Core, MARC, etc.)
- `CampoMetadatos` - Campos de metadatos
- `MetadatoDocumento` - Valores de metadatos para documentos

**Dependencias:** `repositorio` (para documentos)

---

### 7. **revisiones**
**Responsabilidad:** Procesos de revisión y aprobación

**Modelos:**
- `ProcesoRevision` - Procesos de revisión
- `Revision` - Revisiones individuales
- `CriterioRevision` - Criterios de evaluación
- `EvaluacionCriterio` - Evaluaciones de criterios

**Dependencias:** `repositorio` (para documentos)

---

### 8. **estadisticas**
**Responsabilidad:** Analytics y estadísticas

**Modelos:**
- `VisitaDocumento` - Visitas a documentos
- `DescargaArchivo` - Descargas de archivos
- `EstadisticaAgregada` - Estadísticas agregadas

**Dependencias:** `repositorio` (para documentos y archivos)

---

### 9. **interaccion**
**Responsabilidad:** Comentarios, valoraciones y citas

**Modelos:**
- `Comentario` - Comentarios en documentos
- `Valoracion` - Valoraciones de documentos
- `Cita` - Citas entre documentos
- `ReferenciaBibliografica` - Referencias bibliográficas

**Dependencias:** `repositorio` (para documentos)

---

### 10. **notificaciones**
**Responsabilidad:** Sistema de notificaciones

**Modelos:**
- `TipoNotificacion` - Tipos de notificación
- `Notificacion` - Notificaciones a usuarios

**Dependencias:** `usuarios` (para usuarios)

---

### 11. **busqueda**
**Responsabilidad:** Índices de búsqueda y full-text

**Modelos:**
- `IndiceBusqueda` - Índices de búsqueda full-text
- `Busqueda` - Historial de búsquedas

**Dependencias:** `repositorio`, `proyectos` (para indexar)

---

### 12. **configuracion**
**Responsabilidad:** Configuración del sistema y logs

**Modelos:**
- `ConfiguracionSistema` - Configuración del sistema
- `LogSistema` - Logs del sistema

**Dependencias:** Ninguna (independiente)

---

## 🔄 Orden de Instalación (settings.py)

El orden en `INSTALLED_APPS` es importante debido a las dependencias:

```python
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps del sistema
    'usuarios',          # Base
    'catalogacion',     # Compartida
    'proyectos',         # Depende de catalogacion
    'repositorio',       # Depende de catalogacion
    'publicaciones',    # Depende de proyectos, catalogacion
    'metadatos',         # Depende de repositorio
    'revisiones',        # Depende de repositorio
    'estadisticas',      # Depende de repositorio
    'interaccion',       # Depende de repositorio
    'notificaciones',    # Depende de usuarios
    'busqueda',          # Depende de repositorio, proyectos
    'configuracion',     # Independiente
]
```

## 📊 Resumen

- **Total de Apps:** 12
- **Total de Modelos:** ~48 modelos
- **Apps Base:** usuarios, catalogacion, configuracion
- **Apps Principales:** proyectos, repositorio, publicaciones
- **Apps de Soporte:** metadatos, revisiones, estadisticas, interaccion, notificaciones, busqueda

## ✅ Estado Actual

- ✅ Todas las apps creadas
- ✅ Apps registradas en `settings.py`
- ⏳ Modelos pendientes de crear (siguiente paso)





