# Relaciones: Documento, Proyecto y Publicación

## 📋 Resumen de Arquitectura

El sistema REDI tiene una arquitectura en capas donde:

1. **Publicación** → Agrupa múltiples proyectos (lo que ve el público)
2. **Proyecto** → Contiene los datos del proyecto (título, descripción, autores, campos dinámicos)
3. **Documento** → Almacena el archivo PDF y metadatos opcionales
4. **Archivo** → El archivo físico (PDF) asociado a una versión del documento

---

## 🔗 Relaciones Detalladas

### 1. Publicación ↔ Proyecto

**Tipo de Relación:** ManyToMany (a través de `PublicacionProyecto`)

```python
# publicaciones/models.py
class Publicacion(models.Model):
    proyectos = models.ManyToManyField(
        'proyectos.Proyecto',
        through='PublicacionProyecto',
        related_name='publicaciones'
    )

class PublicacionProyecto(models.Model):
    publicacion = models.ForeignKey(Publicacion, ...)
    proyecto = models.ForeignKey('proyectos.Proyecto', ...)
    orden = models.PositiveIntegerField(default=0)
    rol_en_publicacion = models.CharField(...)  # "artículo principal", "capítulo", etc.
```

**Características:**
- Una publicación puede tener múltiples proyectos
- Un proyecto puede estar en múltiples publicaciones
- Se puede especificar el orden y el rol de cada proyecto en la publicación

**Ejemplo de uso:**
```python
# Crear una publicación
publicacion = Publicacion.objects.create(titulo="Revista Científica 2024", ...)

# Agregar proyectos a la publicación
proyecto1 = Proyecto.objects.get(id=1)
proyecto2 = Proyecto.objects.get(id=2)

PublicacionProyecto.objects.create(
    publicacion=publicacion,
    proyecto=proyecto1,
    orden=1,
    rol_en_publicacion="artículo principal"
)

PublicacionProyecto.objects.create(
    publicacion=publicacion,
    proyecto=proyecto2,
    orden=2,
    rol_en_publicacion="artículo secundario"
)
```

---

### 2. Proyecto ↔ Documento

**Tipo de Relación:** OneToOne (opcional)

```python
# repositorio/models.py
class Documento(models.Model):
    proyecto = models.OneToOneField(
        'proyectos.Proyecto',
        on_delete=models.CASCADE,
        related_name='documento',
        null=True,
        blank=True
    )
```

**Características:**
- Un proyecto puede tener UN documento (PDF)
- Un documento puede estar asociado a UN proyecto
- La relación es opcional (un documento puede existir sin proyecto)
- Si hay proyecto, el título y descripción del documento vienen del proyecto

**Métodos del Documento:**
```python
def get_titulo(self):
    """Retorna el título del proyecto si existe, sino el título del documento"""
    if self.proyecto:
        return self.proyecto.titulo
    return self.titulo or f"Documento #{self.id}"

def get_resumen(self):
    """Retorna el resumen del proyecto si existe, sino el resumen del documento"""
    if self.proyecto:
        return self.proyecto.resumen
    return self.resumen
```

**Ejemplo de uso:**
```python
# Crear un proyecto
proyecto = Proyecto.objects.create(
    titulo="Análisis de Machine Learning",
    resumen="Este proyecto analiza...",
    ...
)

# Crear el documento asociado
documento = Documento.objects.create(
    proyecto=proyecto,  # Relación OneToOne
    creador=user,
    ...
)

# Acceder desde el proyecto
proyecto.documento  # Retorna el Documento asociado
documento.proyecto  # Retorna el Proyecto asociado
```

---

### 3. Documento → VersionDocumento → Archivo

**Tipo de Relación:** ForeignKey (cascada)

```python
# repositorio/models.py
class VersionDocumento(models.Model):
    documento = models.ForeignKey(
        Documento,
        on_delete=models.CASCADE,
        related_name='versiones'
    )
    numero_version = models.PositiveIntegerField()
    es_version_actual = models.BooleanField(default=False)

class Archivo(models.Model):
    version = models.ForeignKey(
        VersionDocumento,
        on_delete=models.CASCADE,
        related_name='archivos'
    )
    archivo = models.FileField(upload_to=archivo_upload_path)
    nombre_original = models.CharField(max_length=500)
    es_archivo_principal = models.BooleanField(default=False)
```

**Características:**
- Un documento puede tener múltiples versiones
- Una versión puede tener múltiples archivos
- Solo una versión puede ser la versión actual
- Solo un archivo por versión puede ser el archivo principal

**Estructura de almacenamiento:**
```
media/
  documentos/
    proyectos/
      {proyecto_slug}/
        {numero_version}/
          archivo.pdf
    {documento_handle}/
      {numero_version}/
        archivo.pdf
```

**Ejemplo de uso:**
```python
# Crear documento
documento = Documento.objects.create(...)

# Crear versión 1
version1 = VersionDocumento.objects.create(
    documento=documento,
    numero_version=1,
    es_version_actual=True,
    creado_por=user
)

# Subir archivo PDF a la versión 1
archivo = Archivo.objects.create(
    version=version1,
    archivo=uploaded_file,  # FileField
    nombre_original=uploaded_file.name,
    es_archivo_principal=True,
    tipo_mime='application/pdf',
    tamaño_bytes=uploaded_file.size
)

# Crear versión 2 (actualizar)
version2 = VersionDocumento.objects.create(
    documento=documento,
    numero_version=2,
    es_version_actual=True,
    creado_por=user
)
# Marcar versión 1 como no actual
version1.es_version_actual = False
version1.save()
```

---

## 📊 Diagrama de Relaciones

```
┌─────────────────────────────────────────────────────────────┐
│                    PUBLICACION                              │
│  - título, descripción, estado, visibilidad                 │
│  - editor (User)                                            │
└────────────────────┬────────────────────────────────────────┘
                      │
                      │ ManyToMany (through PublicacionProyecto)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROYECTO                                  │
│  - título, descripción, resumen                             │
│  - tipo_proyecto, estado, visibilidad                       │
│  - creador (User)                                           │
│  - campos dinámicos (EAV)                                   │
│  - autores (ProyectoAutor)                                  │
└────────────────────┬────────────────────────────────────────┘
                      │
                      │ OneToOne (opcional)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENTO                                 │
│  - handle, DOI, ISBN, ISSN                                  │
│  - tipo_recurso, estado, coleccion                          │
│  - creador (User)                                           │
│  - licencia                                                 │
│  - metadatos opcionales                                     │
└────────────────────┬────────────────────────────────────────┘
                      │
                      │ ForeignKey (CASCADE)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              VERSIONDOCUMENTO                               │
│  - numero_version                                           │
│  - notas_version                                            │
│  - creado_por (User)                                        │
│  - es_version_actual                                        │
└────────────────────┬────────────────────────────────────────┘
                      │
                      │ ForeignKey (CASCADE)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    ARCHIVO                                  │
│  - archivo (FileField - PDF)                               │
│  - nombre_original                                         │
│  - tipo_mime, tamaño_bytes                                 │
│  - checksum_md5, checksum_sha256                           │
│  - es_archivo_principal                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Trabajo Típico

### 1. Crear Documento con PDF (en repositorio)

**IMPORTANTE:** Los documentos se crean primero en la app `repositorio`, independientemente de los proyectos.

```python
# 1. Crear el documento en repositorio (con o sin PDF)
# Opción A: Crear documento con PDF
formData = new FormData();
formData.append('titulo', 'Mi Documento');
formData.append('tipo_recurso_id', tipoRecursoId);
formData.append('coleccion_id', coleccionId);
formData.append('archivo', pdfFile);  # PDF

fetch('/repositorio/documentos/crear/', {
    method: 'POST',
    body: formData
})

# Opción B: Crear documento sin PDF (se puede agregar después)
documento = Documento.objects.create(
    titulo="Mi Documento",
    creador=user,
    tipo_recurso=tipo_recurso,
    coleccion=coleccion
)

# Si se subió PDF, se crea automáticamente:
# - VersionDocumento (versión 1)
# - Archivo (con checksums MD5 y SHA256)
```

### 2. Crear Proyecto y Relacionar Documento Existente

```python
# 1. Crear el proyecto (sin documento)
proyecto = Proyecto.objects.create(
    titulo="Mi Proyecto de Investigación",
    tipo_proyecto=tipo_proyecto,
    creador=user,
    estado='borrador',
    documento_id=documento_id  # Seleccionar documento existente
)

# El documento se relaciona automáticamente con el proyecto
# El proyecto hereda título y resumen del documento si no los tiene
```

### 2. Agrupar Proyectos en Publicación

```python
# 1. Crear publicación
publicacion = Publicacion.objects.create(
    titulo="Revista Científica 2024",
    editor=user,
    estado='publicada',
    visibilidad='publico'
)

# 2. Agregar proyectos
proyecto1 = Proyecto.objects.get(id=1)
proyecto2 = Proyecto.objects.get(id=2)

PublicacionProyecto.objects.create(
    publicacion=publicacion,
    proyecto=proyecto1,
    orden=1,
    rol_en_publicacion="artículo principal"
)

PublicacionProyecto.objects.create(
    publicacion=publicacion,
    proyecto=proyecto2,
    orden=2,
    rol_en_publicacion="artículo secundario"
)
```

### 3. Actualizar Versión del Documento

```python
# 1. Obtener documento y versión actual
documento = Documento.objects.get(id=1)
version_actual = documento.versiones.filter(es_version_actual=True).first()

# 2. Crear nueva versión
nueva_version = VersionDocumento.objects.create(
    documento=documento,
    numero_version=version_actual.numero_version + 1,
    creado_por=user,
    es_version_actual=True,
    notas_version="Corrección de errores tipográficos"
)

# 3. Marcar versión anterior como no actual
version_actual.es_version_actual = False
version_actual.save()

# 4. Subir nuevo archivo
nuevo_archivo = Archivo.objects.create(
    version=nueva_version,
    archivo=nuevo_pdf,
    nombre_original=nuevo_pdf.name,
    es_archivo_principal=True
)
```

---

## 📝 Notas Importantes

1. **Separación de Responsabilidades:**
   - **Proyecto**: Datos del proyecto (título, descripción, autores, campos dinámicos)
   - **Documento**: Archivo PDF y metadatos del repositorio
   - **Publicación**: Agrupación de proyectos para publicación

2. **Relación OneToOne Proyecto-Documento:**
   - Es opcional: un documento puede existir sin proyecto
   - Si hay proyecto, el documento hereda título y resumen
   - Un proyecto solo puede tener un documento

3. **Sistema de Versiones:**
   - Cada documento puede tener múltiples versiones
   - Solo una versión puede ser la "versión actual"
   - Cada versión puede tener múltiples archivos
   - Solo un archivo por versión puede ser el "archivo principal"

4. **Almacenamiento de Archivos:**
   - Los archivos se almacenan en `media/documentos/`
   - Si hay proyecto: `media/documentos/proyectos/{proyecto_slug}/{version}/{archivo}`
   - Si no hay proyecto: `media/documentos/{documento_handle}/{version}/{archivo}`

---

## ✅ Flujo Correcto Implementado

### 1. Crear Documento en Repositorio

**Los documentos se crean PRIMERO en la app `repositorio`:**

```javascript
// Crear documento con PDF
const formData = new FormData();
formData.append('titulo', 'Mi Documento');
formData.append('tipo_recurso_id', tipoRecursoId);
formData.append('coleccion_id', coleccionId);
formData.append('archivo', pdfFile);  // PDF opcional

fetch('/repositorio/documentos/crear/', {
    method: 'POST',
    body: formData
})
```

**Si se sube PDF, se crea automáticamente:**
- `VersionDocumento` (versión 1)
- `Archivo` (con checksums MD5 y SHA256)

### 2. Listar Documentos Disponibles

```javascript
// Obtener documentos sin proyecto asociado
fetch('/repositorio/documentos/disponibles/')
    .then(response => response.json())
    .then(data => {
        // Mostrar en select para seleccionar al crear proyecto
        console.log(data.data);
    });
```

### 3. Crear Proyecto y Seleccionar Documento

```javascript
// Crear proyecto y relacionar documento existente
const data = {
    titulo: 'Mi Proyecto',
    tipo_proyecto_id: tipoProyectoId,
    documento_id: documentoId,  // Seleccionar documento existente
    // ... otros campos
};

fetch('/proyectos/crear/', {
    method: 'POST',
    body: JSON.stringify(data)
});
```

### 4. CRUD Completo de Archivos

**Todas las operaciones están disponibles:**
- `GET /repositorio/archivos/` - Listar todos los archivos
- `GET /repositorio/archivos/por-version/<version_id>/` - Archivos de una versión
- `POST /repositorio/archivos/crear/` - Subir nuevo archivo PDF
- `GET /repositorio/archivos/<archivo_id>/` - Detalle de archivo
- `PUT /repositorio/archivos/<archivo_id>/editar/` - Actualizar metadatos
- `DELETE /repositorio/archivos/<archivo_id>/eliminar/` - Eliminar archivo
- `GET /repositorio/archivos/<archivo_id>/descargar/` - Descargar archivo

