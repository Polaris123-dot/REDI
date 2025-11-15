# Sistema de Campos Dinámicos para Proyectos

## Descripción General

Este sistema implementa un patrón **EAV (Entity-Attribute-Value)** que permite definir campos dinámicos y personalizados para cada tipo de proyecto. Esto significa que:

- Cada tipo de proyecto (Tesis, Monografía, Artículo, etc.) puede tener campos diferentes
- Los campos se definen dinámicamente en la base de datos, no están hardcodeados
- Puedes agregar, modificar o eliminar campos sin cambiar el código
- Cada proyecto almacena sus valores en una tabla flexible (EAV)

## Arquitectura del Sistema

### 1. **Tipos de Proyecto** (`tipos_proyecto`)
Define los diferentes tipos de proyectos que el sistema puede manejar.

**Ejemplo:**
- Tesis
- Monografía
- Artículo Científico
- Proyecto de Investigación

**Campos principales:**
- `nombre`: Nombre del tipo (ej: "Tesis")
- `slug`: Identificador único (ej: "tesis")
- `descripcion`: Descripción del tipo
- `icono`: Icono para mostrar en la UI
- `plantilla_vista`: Template personalizado (opcional)

### 2. **Campos por Tipo de Proyecto** (`campos_tipo_proyecto`)
Define qué campos debe tener cada tipo de proyecto.

**Características:**
- **Tipo de dato**: texto, textarea, numero, fecha, booleano, select, multiselect, archivo, url, email, json
- **Validaciones**: Campo obligatorio, repetible, validadores personalizados
- **Búsqueda**: Campos indexables y buscables
- **Categorías**: Agrupa campos en secciones (ej: "Información General", "Publicación")
- **Valores posibles**: Para campos select/multiselect (almacenados en JSON)

**Ejemplo para Tesis:**
```
Campo: "Director"
- Tipo: texto
- Obligatorio: Sí
- Categoría: "Información General"
- Orden: 4

Campo: "Nivel Académico"
- Tipo: select
- Obligatorio: Sí
- Valores: ["Pregrado", "Maestría", "Doctorado", "Especialización"]
- Categoría: "Información General"
```

### 3. **Proyectos** (`proyectos`)
Tabla principal que almacena los proyectos.

**Campos estándar:**
- `titulo`, `slug`, `resumen`, `descripcion`
- `tipo_proyecto_id`: Relación con el tipo de proyecto
- `creador_id`: Usuario que creó el proyecto
- `estado`: borrador, en_revision, aprobado, publicado, archivado, rechazado
- `visibilidad`: publico, privado, restringido

**Campos dinámicos:** Se almacenan en `valores_campo_proyecto`

### 4. **Valores de Campos Dinámicos** (`valores_campo_proyecto`)
Almacena los valores de los campos dinámicos (patrón EAV).

**Estructura:**
- `proyecto_id`: Proyecto al que pertenece
- `campo_tipo_proyecto_id`: Campo que se está llenando
- Valores según tipo de dato:
  - `valor_texto`: Para texto, textarea, url, email
  - `valor_numero`: Para números
  - `valor_fecha`: Para fechas
  - `valor_datetime`: Para fecha y hora
  - `valor_booleano`: Para booleanos
  - `valor_json`: Para datos complejos (select múltiple, etc.)
  - `valor_archivo`: Ruta al archivo
- `orden`: Para campos repetibles

## Ejemplo de Uso

### Crear un Proyecto de Tipo "Tesis"

1. **Seleccionar tipo**: Tesis
2. **Sistema carga los campos definidos** para Tesis:
   - Objetivos (textarea, obligatorio)
   - Hipótesis (textarea, opcional)
   - Metodología (textarea, obligatorio)
   - Director (texto, obligatorio)
   - Fecha de Defensa (fecha, opcional)
   - Jurado (textarea, opcional)
   - Nivel Académico (select, obligatorio)
   - Programa (texto, obligatorio)
   - Línea de Investigación (texto, opcional)
   - Palabras Clave (multiselect, obligatorio)

3. **El usuario llena los campos** según el tipo de dato
4. **Los valores se guardan** en `valores_campo_proyecto`

### Crear un Proyecto de Tipo "Monografía"

1. **Seleccionar tipo**: Monografía
2. **Sistema carga los campos definidos** para Monografía (diferentes a Tesis):
   - Objetivo General (textarea, obligatorio)
   - Objetivos Específicos (textarea, obligatorio)
   - Metodología (textarea, obligatorio)
   - Asesor (texto, obligatorio)
   - Fecha de Entrega (fecha, opcional)
   - Programa (texto, obligatorio)

3. **Nota**: Monografía tiene menos campos que Tesis (no tiene Director, Jurado, Nivel Académico, etc.)

## Ventajas del Sistema

### 1. **Flexibilidad Total**
- Agregar nuevos tipos de proyecto sin cambiar código
- Agregar/modificar/eliminar campos sin migraciones complejas
- Cada tipo tiene exactamente los campos que necesita

### 2. **Escalabilidad**
- Fácil agregar nuevos tipos (ej: "Protocolo de Investigación")
- Fácil agregar campos a tipos existentes
- No requiere modificar la estructura de la tabla principal

### 3. **Mantenibilidad**
- Configuración centralizada en base de datos
- Cambios sin deploy de código
- Fácil de entender y documentar

### 4. **Búsqueda y Filtrado**
- Campos marcados como `es_buscable` e `es_indexable`
- Búsqueda full-text en valores de texto
- Filtrado por cualquier campo dinámico

## Modelo de Publicación

### Tabla `publicaciones`
Agrupa proyectos/documentos para publicar. Una publicación puede contener:
- Múltiples proyectos (ej: revista con varios artículos)
- Un solo proyecto (ej: tesis publicada)

**Características:**
- Relación muchos a muchos con proyectos (`publicacion_proyectos`)
- Relación con etiquetas (`publicacion_etiquetas`)
- Relación con categorías (`publicacion_categorias`)
- Información de publicación (ISSN, ISBN, DOI)
- Estados de publicación (borrador, en_proceso, publicada, archivada)

**Ejemplo:**
- Publicación: "Revista Científica 2024, Vol. 10"
- Proyectos asociados: Múltiples artículos científicos
- Cada artículo puede tener su propio tipo de proyecto

## Consultas SQL Útiles

### Obtener todos los campos de un tipo de proyecto
```sql
SELECT * FROM campos_tipo_proyecto 
WHERE tipo_proyecto_id = (SELECT id FROM tipos_proyecto WHERE slug = 'tesis')
ORDER BY orden;
```

### Obtener los valores de un proyecto
```sql
SELECT 
    ctp.etiqueta,
    ctp.tipo_dato,
    vcp.valor_texto,
    vcp.valor_numero,
    vcp.valor_fecha,
    vcp.valor_booleano
FROM valores_campo_proyecto vcp
JOIN campos_tipo_proyecto ctp ON vcp.campo_tipo_proyecto_id = ctp.id
WHERE vcp.proyecto_id = 1
ORDER BY ctp.orden;
```

### Crear un nuevo tipo de proyecto con campos
```sql
-- 1. Insertar tipo
INSERT INTO tipos_proyecto (nombre, slug, descripcion) 
VALUES ('Protocolo', 'protocolo', 'Protocolo de investigación');

-- 2. Insertar campos
INSERT INTO campos_tipo_proyecto 
    (tipo_proyecto_id, nombre, slug, etiqueta, tipo_dato, es_obligatorio, orden, categoria)
VALUES
    ((SELECT id FROM tipos_proyecto WHERE slug = 'protocolo'), 
     'Objetivo', 'objetivo', 'Objetivo del Protocolo', 'textarea', TRUE, 1, 'General'),
    ((SELECT id FROM tipos_proyecto WHERE slug = 'protocolo'), 
     'Duración', 'duracion', 'Duración (meses)', 'numero', TRUE, 2, 'General');
```

### Obtener proyectos con sus valores dinámicos
```sql
SELECT 
    p.id,
    p.titulo,
    tp.nombre as tipo_proyecto,
    GROUP_CONCAT(
        CONCAT(ctp.etiqueta, ': ', 
            COALESCE(vcp.valor_texto, CAST(vcp.valor_numero AS CHAR), 
            CAST(vcp.valor_fecha AS CHAR), 'N/A'))
        SEPARATOR ' | '
    ) as valores_campos
FROM proyectos p
JOIN tipos_proyecto tp ON p.tipo_proyecto_id = tp.id
LEFT JOIN valores_campo_proyecto vcp ON p.id = vcp.proyecto_id
LEFT JOIN campos_tipo_proyecto ctp ON vcp.campo_tipo_proyecto_id = ctp.id
GROUP BY p.id;
```

## Implementación en Django

### Modelos Sugeridos

```python
class TipoProyecto(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    es_activo = models.BooleanField(default=True)
    # ... otros campos

class CampoTipoProyecto(models.Model):
    TIPO_DATO_CHOICES = [
        ('texto', 'Texto'),
        ('textarea', 'Área de Texto'),
        ('numero', 'Número'),
        ('fecha', 'Fecha'),
        ('booleano', 'Booleano'),
        ('select', 'Selección'),
        ('multiselect', 'Selección Múltiple'),
        # ... más tipos
    ]
    
    tipo_proyecto = models.ForeignKey(TipoProyecto, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    slug = models.SlugField()
    etiqueta = models.CharField(max_length=255)
    tipo_dato = models.CharField(max_length=20, choices=TIPO_DATO_CHOICES)
    es_obligatorio = models.BooleanField(default=False)
    valores_posibles = models.JSONField(default=list, blank=True)
    # ... otros campos

class Proyecto(models.Model):
    titulo = models.CharField(max_length=500)
    slug = models.SlugField(unique=True)
    tipo_proyecto = models.ForeignKey(TipoProyecto, on_delete=models.PROTECT)
    creador = models.ForeignKey(User, on_delete=models.PROTECT)
    # ... campos estándar
    
    def get_campos_definidos(self):
        """Retorna los campos definidos para este tipo de proyecto"""
        return CampoTipoProyecto.objects.filter(
            tipo_proyecto=self.tipo_proyecto
        ).order_by('orden')
    
    def get_valor_campo(self, slug_campo):
        """Obtiene el valor de un campo dinámico"""
        campo = self.get_campos_definidos().get(slug=slug_campo)
        valor = ValoresCampoProyecto.objects.filter(
            proyecto=self,
            campo_tipo_proyecto=campo
        ).first()
        
        if valor:
            if campo.tipo_dato == 'texto':
                return valor.valor_texto
            elif campo.tipo_dato == 'numero':
                return valor.valor_numero
            # ... más tipos
        return None

class ValoresCampoProyecto(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    campo_tipo_proyecto = models.ForeignKey(CampoTipoProyecto, on_delete=models.CASCADE)
    valor_texto = models.TextField(blank=True, null=True)
    valor_numero = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    valor_fecha = models.DateField(blank=True, null=True)
    valor_booleano = models.BooleanField(blank=True, null=True)
    valor_json = models.JSONField(blank=True, null=True)
    # ... más campos de valor
```

## Flujo de Trabajo

### 1. Administrador define tipos de proyecto
1. Crear nuevo tipo (ej: "Tesis")
2. Agregar campos necesarios (Director, Metodología, etc.)
3. Configurar validaciones y opciones

### 2. Usuario crea proyecto
1. Selecciona tipo de proyecto
2. Sistema muestra formulario dinámico con los campos definidos
3. Usuario llena los campos
4. Valores se guardan en tabla EAV

### 3. Visualización
1. Sistema carga proyecto con su tipo
2. Carga campos definidos para ese tipo
3. Carga valores almacenados
4. Muestra formulario o vista con todos los datos

## Consideraciones

### Ventajas
✅ Flexibilidad total
✅ Sin cambios de código para nuevos tipos
✅ Campos personalizados por tipo
✅ Escalable y mantenible

### Desventajas
⚠️ Consultas más complejas (JOINs adicionales)
⚠️ Validaciones deben hacerse en código
⚠️ Rendimiento: más tablas involucradas

### Optimizaciones
- Índices en campos clave
- Caché de definiciones de campos
- Agregación de valores comunes en `metadata_adicional` JSON
- Full-text search en valores de texto

## Conclusión

Este sistema proporciona la máxima flexibilidad para manejar diferentes tipos de proyectos con estructuras diferentes, permitiendo que cada tipo tenga exactamente los campos que necesita, sin hardcodear nada en el código.





