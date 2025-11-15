# Arquitectura: Publicaciones, Proyectos y Documentos

## Resumen de Cambios

Se ha reestructurado la arquitectura del sistema para que:

1. **Publicación** → agrupa **Proyectos** (lo que ve el público general)
2. **Proyecto** → tiene título, descripción, autores y un **Documento** (PDF)
3. **Documento** → almacena principalmente el archivo PDF y metadatos opcionales (NO título/descripción)

## Nueva Arquitectura

```
Publicacion (visibilidad: público/privado/restringido)
    ↓ (ManyToMany through PublicacionProyecto)
Proyecto (título, descripción, estado, visibilidad)
    ↓ (OneToOne)
Documento (solo archivo PDF y metadatos opcionales)
    ↓ (ForeignKey)
VersionDocumento
    ↓ (ForeignKey)
Archivo (FileField para PDF)
```

## Cambios en los Modelos

### 1. Publicacion (`publicaciones/models.py`)
- ✅ **Agregado campo `visibilidad`**: Controla si la publicación es visible para el público general
  - Opciones: `publico`, `privado`, `restringido`
  - Por defecto: `publico`

### 2. Proyecto (`proyectos/models.py`)
- ✅ **Agregado modelo `ProyectoAutor`**: Autores del proyecto (NO del documento)
  - Campos: nombre, apellidos, email, afiliación, ORCID, orden_autor, es_correspondiente, es_autor_principal
  - Relación opcional con User
- ✅ **Relación OneToOne con Documento**: Cada proyecto puede tener un documento (PDF)
  - Se define en `repositorio/models.py` para evitar dependencia circular

### 3. Documento (`repositorio/models.py`)
- ✅ **Agregado campo `proyecto`** (OneToOneField): Relación con Proyecto
  - Opcional (`null=True, blank=True`)
  - Si hay proyecto, el título y descripción vienen del proyecto
- ✅ **Campos simplificados**: `titulo` y `resumen` ahora son opcionales
  - Si hay proyecto asociado, se usan `get_titulo()` y `get_resumen()` que retornan los del proyecto
- ✅ **Métodos agregados**:
  - `get_titulo()`: Retorna título del proyecto si existe, sino del documento
  - `get_resumen()`: Retorna resumen del proyecto si existe, sino del documento

### 4. Archivo (`repositorio/models.py`)
- ✅ **Agregado `FileField`**: Campo real de Django para subir PDFs
  - Función `archivo_upload_path()`: Genera rutas organizadas por proyecto
  - Ruta: `documentos/proyectos/{proyecto_slug}/{version}/{filename}`
- ✅ **Campos legacy mantenidos**: `nombre_almacenado`, `ruta_completa` (deprecated, para compatibilidad)
- ✅ **Métodos agregados**:
  - `get_url_archivo()`: Retorna la URL del archivo
  - `get_tamaño_formateado()`: Retorna el tamaño formateado (KB, MB, etc.)

### 5. Autor (`repositorio/models.py`)
- ⚠️ **Mantenido para documentos independientes**: Si un documento no tiene proyecto, puede tener autores propios
- ⚠️ **Para proyectos, usar `ProyectoAutor`**: Los autores del proyecto están en `proyectos.ProyectoAutor`

## Configuración

### Media Files (`redima/settings.py`)
- ✅ **Agregado `MEDIA_URL = '/media/'`**
- ✅ **Agregado `MEDIA_ROOT = BASE_DIR / 'media'`**

### URLs (`redima/urls.py`)
- ✅ **Agregado servido de archivos media en desarrollo**:
  ```python
  if settings.DEBUG:
      urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
  ```

## Flujo de Trabajo

### Para Publicar un Proyecto:

1. **Crear Proyecto**:
   - Título, descripción, tipo, estado, visibilidad
   - Agregar autores (`ProyectoAutor`)
   - Agregar categorías y etiquetas

2. **Crear Documento** (asociado al proyecto):
   - Asociar el proyecto
   - Subir archivo PDF (se crea `VersionDocumento` y `Archivo`)
   - Metadatos opcionales (DOI, ISBN, etc.)

3. **Crear Publicación**:
   - Agregar proyectos a la publicación
   - Establecer visibilidad (`publico` para que sea visible)
   - Establecer estado (`publicada`)

### Para el Público General:

- Ver publicaciones con `visibilidad='publico'` y `estado='publicada'`
- Ver proyectos dentro de esas publicaciones
- Descargar PDF del documento asociado al proyecto
- Ver autores del proyecto (no del documento)

## Migraciones

Se han creado las siguientes migraciones:

1. **`proyectos/migrations/0002_proyectoautor.py`**: Crea el modelo `ProyectoAutor`
2. **`repositorio/migrations/0002_archivo_archivo_documento_proyecto_and_more.py`**:
   - Agrega campo `proyecto` a `Documento`
   - Agrega campo `archivo` (FileField) a `Archivo`
   - Hace opcionales varios campos de `Documento`
3. **`publicaciones/migrations/0003_publicacion_visibilidad_and_more.py`**:
   - Agrega campo `visibilidad` a `Publicacion`

## Próximos Pasos

1. ✅ Aplicar migraciones: `python manage.py migrate`
2. ⏳ Actualizar vistas de `Proyecto` para manejar autores y documento
3. ⏳ Actualizar vistas de `Documento` para manejar archivos (upload)
4. ⏳ Actualizar vistas de `Publicacion` para filtrar por visibilidad
5. ⏳ Crear vista pública para mostrar publicaciones al público general

## Preguntas Resueltas

### ¿Qué ve el público general?
- **Publicaciones** con `visibilidad='publico'` y `estado='publicada'`
- Dentro de cada publicación, los **Proyectos** asociados
- Cada proyecto tiene un enlace para descargar el **PDF** (Documento → Archivo)

### ¿Dónde se almacenan los PDFs?
- En el modelo `Archivo` usando `FileField` de Django
- Ruta: `media/documentos/proyectos/{proyecto_slug}/{version}/{filename}`
- Se sirven mediante `MEDIA_URL` en desarrollo y producción

### ¿Dónde están los autores?
- **Autores del proyecto**: En `ProyectoAutor` (modelo en `proyectos/models.py`)
- **Autores del documento**: En `Autor` (solo para documentos sin proyecto)

### ¿Cómo se relacionan Proyecto y Documento?
- **OneToOne**: Un proyecto tiene un documento (opcional)
- El documento obtiene título/descripción del proyecto mediante `get_titulo()` y `get_resumen()`



