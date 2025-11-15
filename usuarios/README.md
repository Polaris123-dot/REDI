# Sistema de Gestión de Usuarios y Roles

Este sistema permite a los superusuarios gestionar usuarios y asignarles roles (grupos) usando únicamente los modelos por defecto de Django.

## Características

- **Gestión de Usuarios:**
  - Listar todos los usuarios con búsqueda
  - Crear nuevos usuarios
  - Editar información de usuarios
  - Ver detalles de usuario
  - Asignar/remover roles a usuarios

- **Gestión de Roles (Grupos):**
  - Listar todos los roles
  - Crear nuevos roles
  - Ver detalles de rol y usuarios asignados
  - Asignar/remover usuarios a roles
  - Eliminar roles

## Requisitos

- Solo superusuarios pueden acceder al sistema
- Usa los modelos `User` y `Group` de Django (`django.contrib.auth`)

## URLs

- `/usuarios/` - Lista de usuarios
- `/usuarios/crear/` - Crear nuevo usuario
- `/usuarios/<id>/` - Detalle de usuario
- `/usuarios/<id>/editar/` - Editar usuario
- `/usuarios/grupos/` - Lista de roles
- `/usuarios/grupos/crear/` - Crear nuevo rol
- `/usuarios/grupos/<id>/` - Detalle de rol
- `/usuarios/grupos/<id>/eliminar/` - Eliminar rol

## Uso

1. Inicia sesión como superusuario
2. Accede a `/usuarios/` para ver la lista de usuarios
3. Usa el botón "Gestionar Roles" para crear y administrar roles
4. En el detalle de cada usuario, puedes asignar múltiples roles
5. En el detalle de cada rol, puedes asignar múltiples usuarios

## Notas

- Los roles en Django se implementan usando el modelo `Group`
- Un usuario puede tener múltiples roles
- Un rol puede tener múltiples usuarios
- Solo los superusuarios pueden gestionar usuarios y roles






