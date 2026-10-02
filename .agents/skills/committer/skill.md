---
name: committer
description: Guía y estándares para realizar commits estructurados en el repositorio utilizando Conventional Commits.
---

# Guía de Commits (Conventional Commits)

Este documento define la estructura y el estándar para realizar commits en este repositorio utilizando **Conventional Commits**.

---

## Reglas Principales

1. **Título (Header):**
   - Debe seguir el formato: `<tipo>(<alcance opcional>): <descripción corta>`.
   - **Límite estricto de máximo 50 caracteres**.
   - En minúsculas y sin punto final `.`.
   - Utilizar el verbo en imperativo o presente claro (ej: `add`, `fix`, `refactor`).

2. **Cuerpo (Body):**
   - Separado por una línea en blanco tras el título.
   - **Explicación extensa y detallada** de los cambios realizados.
   - Responde a las preguntas:
     - ¿Por qué es necesario este cambio?
     - ¿Cómo aborda o resuelve el problema?
     - ¿Qué efectos secundarios o implicaciones tiene?

3. **Pie de página (Footer) - Opcional:**
   - Para indicar breaking changes (`BREAKING CHANGE: <descripción>`) o referenciar tareas e issues (ej: `Closes #123`, `Refs #456`).

---

## 🎨 Tipos de Commit (`<tipo>`)

| Tipo | Descripción |
| :--- | :--- |
| `feat` | Nueva característica para el usuario final. |
| `fix` | Corrección de un error o bug. |
| `docs` | Cambios únicamente en la documentación. |
| `style` | Cambios de formato/estilo que no afectan el significado del código (espacios, comas, etc.). |
| `refactor` | Cambio en el código que no corrige un bug ni añade una característica. |
| `perf` | Cambio en el código que mejora el rendimiento. |
| `test` | Añadir tests existentes o corregir tests preexistentes. |
| `build` | Cambios que afectan el sistema de construcción o dependencias externas (npm, pip, etc.). |
| `ci` | Cambios en los ficheros o scripts de configuración de CI (GitHub Actions, etc.). |
| `chore` | Tareas rutinarias de mantenimiento que no modifican archivos de código ni de tests. |

---

## 📝 Estructura del Mensaje de Commit

```text
<tipo>(<alcance>): <título corto máx 50 caracteres>

<Descripción extensa explicando detalladamente los cambios realizados.
Explicación del motivo del cambio, decisiones tomadas y cómo afecta
a los componentes involucrados.>

BREAKING CHANGE: <descripción si rompe compatibilidad>
Fixes #<número de issue>
```

---

## 💡 Ejemplos

### Ejemplo 1: Nueva funcionalidad (con alcance)
```text
feat(auth): agregar login con Google

Se implementó el flujo de autenticación mediante OAuth2 con Google.
- Se integró la librería oficial de Google Auth SDK.
- Se creó el endpoint backend /api/auth/google para validar el token.
- Se guardan las credenciales en la sesión activa del usuario.
```

### Ejemplo 2: Corrección de error
```text
fix(agenda): corregir solape de citas mecánicas

Se resolvió un bug en el módulo de agendas donde dos mecánicos podían
ser asignados al mismo turno de trabajo si se guardaban en paralelo.
- Se agregó un lock optimista en la tabla de asignaciones.
- Se añadieron validaciones de horario previo al guardado en DB.
```

### Ejemplo 3: Refactorización simple
```text
refactor: optimizar consulta SQL de vehículos

Se reemplazaron múltiples subconsultas redundantes por JOINs
optimizados en el listado principal de vehículos para reducir
el tiempo de respuesta del endpoint en un 35%.
```