# CRUD de Catalogación - Documentación

## ✅ Implementación Completa

### Características Implementadas

1. ✅ **Modales Bootstrap** - Para crear y editar categorías y etiquetas
2. ✅ **JSON API** - Todas las vistas retornan JSON
3. ✅ **jQuery/Fetch** - Peticiones AJAX con jQuery
4. ✅ **URL Reverse** - Todas las URLs usan `{% url %}` de Django
5. ✅ **SweetAlert2** - Alertas elegantes para errores y confirmaciones
6. ✅ **DataTables** - Tablas interactivas y responsivas
7. ✅ **Validación** - Validación en frontend y backend
8. ✅ **CSRF Protection** - Manejo correcto de tokens CSRF

---

## 📋 Endpoints API

### Categorías

| Método | URL | Vista | Descripción |
|--------|-----|-------|-------------|
| GET | `/catalogacion/categorias/` | `categorias_list` | Lista todas las categorías |
| POST | `/catalogacion/categorias/crear/` | `categoria_create` | Crea una categoría |
| GET | `/catalogacion/categorias/<id>/` | `categoria_detail` | Obtiene detalles de una categoría |
| PUT/POST | `/catalogacion/categorias/<id>/editar/` | `categoria_update` | Actualiza una categoría |
| DELETE/POST | `/catalogacion/categorias/<id>/eliminar/` | `categoria_delete` | Elimina una categoría |

### Etiquetas

| Método | URL | Vista | Descripción |
|--------|-----|-------|-------------|
| GET | `/catalogacion/etiquetas/` | `etiquetas_list` | Lista todas las etiquetas |
| POST | `/catalogacion/etiquetas/crear/` | `etiqueta_create` | Crea una etiqueta |
| GET | `/catalogacion/etiquetas/<id>/` | `etiqueta_detail` | Obtiene detalles de una etiqueta |
| PUT/POST | `/catalogacion/etiquetas/<id>/editar/` | `etiqueta_update` | Actualiza una etiqueta |
| DELETE/POST | `/catalogacion/etiquetas/<id>/eliminar/` | `etiqueta_delete` | Elimina una etiqueta |

---

## 🎨 Interfaz de Usuario

### Pestañas (Tabs)

1. **Categorías** - Gestión de categorías jerárquicas
2. **Etiquetas** - Gestión de etiquetas simples

### Funcionalidades

- ✅ **Crear** - Botón "Nueva Categoría/Etiqueta" abre modal
- ✅ **Listar** - Tabla DataTables con búsqueda y ordenamiento
- ✅ **Editar** - Botón de edición por fila
- ✅ **Eliminar** - Botón de eliminación con confirmación
- ✅ **Responsive** - Botones adaptativos según tamaño de pantalla

---

## 🔧 Archivos Creados/Modificados

### Backend

1. **`catalogacion/views.py`**
   - Views JSON para CRUD completo
   - Manejo de errores
   - Validaciones

2. **`catalogacion/urls.py`**
   - URLs con nombres para URL reverse
   - Namespace `catalogacion`

### Frontend

1. **`Templates/catalogacion/index.html`**
   - Template principal con tabs
   - Modales Bootstrap
   - DataTables
   - Integración de scripts

2. **`static/js/catalogacion.js`**
   - Lógica AJAX completa
   - Manejo de eventos
   - Integración con SweetAlert2
   - URL reverse dinámico

---

## 📝 Formato de Respuesta JSON

### Respuesta Exitosa

```json
{
    "success": true,
    "message": "Categoría creada exitosamente",
    "data": {
        "id": 1,
        "nombre": "Categoría ejemplo",
        "slug": "categoria-ejemplo",
        "descripcion": "Descripción",
        "categoria_padre_id": null,
        "categoria_padre_nombre": null,
        "nivel": 0,
        "ruta_completa": "Categoría ejemplo",
        "subcategorias_count": 0
    }
}
```

### Respuesta de Error

```json
{
    "success": false,
    "error": "El nombre es obligatorio"
}
```

---

## 🚀 Uso

### Acceder al CRUD

1. Iniciar sesión en el sistema
2. Navegar a `/catalogacion/`
3. Seleccionar pestaña (Categorías o Etiquetas)
4. Usar botones para crear, editar o eliminar

### Crear Categoría

1. Click en "Nueva Categoría"
2. Llenar formulario en modal
3. Seleccionar categoría padre (opcional)
4. Guardar

### Editar Categoría

1. Click en botón de edición (ícono o texto según pantalla)
2. Modal se abre con datos precargados
3. Modificar campos
4. Guardar

### Eliminar Categoría

1. Click en botón de eliminación
2. Confirmar en SweetAlert2
3. Categoría se elimina (si no tiene subcategorías)

---

## ✅ Validaciones

### Categorías

- ✅ Nombre obligatorio
- ✅ Nombre único
- ✅ No puede ser padre de sí misma
- ✅ No se puede eliminar si tiene subcategorías
- ✅ Validación de referencias circulares

### Etiquetas

- ✅ Nombre obligatorio
- ✅ Nombre único
- ✅ Color en formato hexadecimal (auto-formato)

---

## 🎯 Próximos Pasos

1. ✅ CRUD de Catalogación completado
2. ⏳ Crear CRUD para Proyectos
3. ⏳ Crear CRUD para Repositorio
4. ⏳ Crear CRUD para Publicaciones

---

## 📚 Dependencias

- jQuery
- DataTables
- Bootstrap 4
- SweetAlert2
- AdminLTE 3





