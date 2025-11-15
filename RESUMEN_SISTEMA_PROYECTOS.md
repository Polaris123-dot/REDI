# Resumen: Sistema de Proyectos con Campos Dinámicos

## ✅ Lo que se ha Implementado

### 1. **Sistema de Perfil de Usuario**
- ✅ Tabla `usuarios_persona` relacionada con `auth_user` de Django
- ✅ Información completa: institucional, académica, biografía
- ✅ Identificadores: ORCID, Google Scholar, ResearchGate, LinkedIn

### 2. **Sistema de Campos Dinámicos (EAV)**
- ✅ **Tipos de Proyecto**: Define los tipos (Tesis, Monografía, Artículo, etc.)
- ✅ **Campos por Tipo**: Define qué campos tiene cada tipo
- ✅ **Proyectos**: Tabla principal de proyectos
- ✅ **Valores Dinámicos**: Almacena valores según el tipo de dato

### 3. **Modelo de Publicación**
- ✅ Tabla `publicaciones` para agrupar proyectos
- ✅ Relación muchos a muchos: `publicacion_proyectos`
- ✅ Relación con etiquetas: `publicacion_etiquetas`
- ✅ Relación con categorías: `publicacion_categorias`

### 4. **Integración con Etiquetas y Categorías**
- ✅ Proyectos pueden tener múltiples etiquetas
- ✅ Proyectos pueden tener múltiples categorías
- ✅ Publicaciones también tienen etiquetas y categorías

## 🎯 Cómo Funciona el Sistema de Campos Dinámicos

### Ejemplo: Tesis vs Monografía

**Tesis tiene estos campos:**
- Objetivos (textarea, obligatorio)
- Hipótesis (textarea, opcional)
- Metodología (textarea, obligatorio)
- Director (texto, obligatorio)
- Fecha de Defensa (fecha, opcional)
- Jurado (textarea, opcional)
- Nivel Académico (select: Pregrado/Maestría/Doctorado, obligatorio)
- Programa (texto, obligatorio)
- Línea de Investigación (texto, opcional)
- Palabras Clave (multiselect, obligatorio)

**Monografía tiene estos campos (MENOS campos):**
- Objetivo General (textarea, obligatorio)
- Objetivos Específicos (textarea, obligatorio)
- Metodología (textarea, obligatorio)
- Asesor (texto, obligatorio)
- Fecha de Entrega (fecha, opcional)
- Programa (texto, obligatorio)

**Resultado:** Cada tipo muestra solo los campos que necesita.

## 📊 Estructura de Tablas

### Tablas Principales:

1. **`tipos_proyecto`**: Tipos de proyecto (Tesis, Monografía, etc.)
2. **`campos_tipo_proyecto`**: Campos definidos para cada tipo
3. **`proyectos`**: Tabla principal de proyectos
4. **`valores_campo_proyecto`**: Valores dinámicos (EAV)
5. **`proyecto_etiquetas`**: Relación proyectos ↔ etiquetas
6. **`proyecto_categorias`**: Relación proyectos ↔ categorías
7. **`publicaciones`**: Modelo de publicación
8. **`publicacion_proyectos`**: Relación publicaciones ↔ proyectos
9. **`publicacion_etiquetas`**: Relación publicaciones ↔ etiquetas
10. **`publicacion_categorias`**: Relación publicaciones ↔ categorías

## 🔄 Flujo de Trabajo

### 1. Administrador Configura Tipos

```sql
-- Crear nuevo tipo
INSERT INTO tipos_proyecto (nombre, slug, descripcion) 
VALUES ('Protocolo', 'protocolo', 'Protocolo de investigación');

-- Agregar campos para ese tipo
INSERT INTO campos_tipo_proyecto 
    (tipo_proyecto_id, nombre, slug, etiqueta, tipo_dato, es_obligatorio, orden)
VALUES
    (1, 'Objetivo', 'objetivo', 'Objetivo', 'textarea', TRUE, 1),
    (1, 'Duración', 'duracion', 'Duración (meses)', 'numero', TRUE, 2);
```

### 2. Usuario Crea Proyecto

1. Selecciona tipo de proyecto (ej: "Tesis")
2. Sistema carga automáticamente los campos definidos para Tesis
3. Usuario llena el formulario dinámico
4. Valores se guardan en `valores_campo_proyecto`

### 3. Visualización

- Sistema carga proyecto
- Carga campos definidos para ese tipo
- Carga valores almacenados
- Muestra formulario/vista con todos los datos

## 💡 Ventajas Clave

✅ **Flexibilidad Total**: Agregar tipos sin cambiar código  
✅ **Campos Personalizados**: Cada tipo tiene exactamente los campos que necesita  
✅ **No Estático**: Estructura completamente dinámica  
✅ **Escalable**: Fácil agregar nuevos tipos y campos  
✅ **Mantenible**: Configuración centralizada en BD  

## 📝 Tipos de Dato Soportados

- `texto`: Campo de texto corto
- `textarea`: Campo de texto largo
- `numero`: Números decimales
- `fecha`: Fechas
- `booleano`: Sí/No
- `select`: Lista desplegable
- `multiselect`: Selección múltiple
- `archivo`: Subida de archivos
- `url`: URLs
- `email`: Correos electrónicos
- `json`: Datos complejos en JSON

## 🔍 Consultas Útiles

### Obtener campos de un tipo de proyecto
```sql
SELECT * FROM campos_tipo_proyecto 
WHERE tipo_proyecto_id = (SELECT id FROM tipos_proyecto WHERE slug = 'tesis')
ORDER BY orden;
```

### Obtener valores de un proyecto
```sql
SELECT 
    ctp.etiqueta,
    ctp.tipo_dato,
    CASE 
        WHEN ctp.tipo_dato = 'texto' THEN vcp.valor_texto
        WHEN ctp.tipo_dato = 'numero' THEN CAST(vcp.valor_numero AS CHAR)
        WHEN ctp.tipo_dato = 'fecha' THEN CAST(vcp.valor_fecha AS CHAR)
        WHEN ctp.tipo_dato = 'booleano' THEN CAST(vcp.valor_booleano AS CHAR)
        ELSE 'N/A'
    END as valor
FROM valores_campo_proyecto vcp
JOIN campos_tipo_proyecto ctp ON vcp.campo_tipo_proyecto_id = ctp.id
WHERE vcp.proyecto_id = 1
ORDER BY ctp.orden;
```

## 🚀 Próximos Pasos para Implementar en Django

1. **Crear modelos Django** basados en el esquema SQL
2. **Crear vistas** para gestionar tipos de proyecto y campos
3. **Crear formularios dinámicos** que se generen según el tipo
4. **Crear vistas** para crear/editar proyectos
5. **Implementar sistema de publicación**

## 📚 Archivos Relacionados

- `esquema_repositorio_digital.sql` - Esquema completo
- `SISTEMA_CAMPOS_DINAMICOS.md` - Documentación detallada
- `DIAGRAMA_RELACIONES.txt` - Diagrama de relaciones
- `usuarios/models.py` - Modelo Persona (ya creado)





