import re

# Leer el archivo
with open(r'c:\Users\Joen\Documents\GitHub\REDI\Templates\usuarios\panel.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar la etiqueta if dividida
pattern = r'{%\s*if\s+can_add_proyectos\s+or\s+can_add_repositorio\s+or\s+can_add_publicaciones\s+or\s+user\.is_superuser\s*%}'
replacement = '{% if can_add_proyectos or can_add_repositorio or can_add_publicaciones or user.is_superuser %}'

# Hacer el reemplazo considerando saltos de línea
content_fixed = re.sub(
    r'{%\s*if\s+can_add_proyectos\s+or\s+can_add_repositorio\s+or\s+can_add_publicaciones\s+or\s*\n\s*user\.is_superuser\s*%}',
    replacement,
    content,
    flags=re.MULTILINE
)

# Guardar el archivo
with open(r'c:\Users\Joen\Documents\GitHub\REDI\Templates\usuarios\panel.html', 'w', encoding='utf-8') as f:
    f.write(content_fixed)

print("Archivo corregido exitosamente")
