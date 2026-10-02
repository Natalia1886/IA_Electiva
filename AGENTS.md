## 🤖 Comandos Personalizados de Automatización

### Comando: "CREAR COMMIT"

Cuando el usuario te dé la instrucción exacta **"CREAR COMMIT"**, debes ejecutar estrictamente el siguiente flujo de trabajo secuencial en el repositorio actual:

---

#### Paso 1 — Aplicar Skill de Formato (Conventional Commits)

Antes de generar el mensaje, lee y aplica el skill de commits ubicado en `.agents/skills/committer/skill.md`.

Formatea el commit usando la siguiente estructura obligatoria:

| Tipo | Cuándo usarlo |
| :--- | :--- |
| `feat:` | Nueva característica |
| `fix:` | Solución de errores |
| `docs:` | Cambios en documentación |
| `style:` | Cambios de formato que no afectan el código |
| `refactor:` | Reestructuración de código |

> **Regla:** El mensaje debe ser corto, en tiempo presente y completamente en minúsculas.
> **Formato del título:** `<tipo>(<alcance opcional>): <descripción corta máx 50 caracteres>`

---

#### Paso 2 — Detectar Cambios Locales

Ejecuta los siguientes comandos de terminal para analizar detalladamente qué archivos han sido modificados, añadidos o eliminados:

```bash
git status
git diff --stat
```

Analiza el resultado para determinar el tipo de commit más adecuado y redactar un cuerpo descriptivo.

---

#### Paso 3 — Ejecutar mediante Git (stage + commit + push)

Realiza las siguientes acciones de forma automática sobre la rama activa:

1. Hacer **stage** de todos los archivos modificados:
   ```bash
   git add .
   ```
2. Crear el **commit** con el mensaje formateado en el Paso 1:
   ```bash
   git commit -m "<tipo>(<alcance>): <descripción>" -m "<cuerpo detallado>"
   ```
3. Hacer **push** del commit a la rama activa:
   ```bash
   git push
   ```

---

#### Paso 4 — Actualizar Documentación (`docs/`)

Después del commit, revisa si los cambios realizados requieren nueva documentación.

- **NO modifiques archivos que ya existen** en `docs/`.
- Crea archivos nuevos o subcarpetas únicamente si los cambios introducen funcionalidades, módulos o flujos no documentados aún.
- Ejemplos de cuándo crear documentación nueva:
  - Se añadió un nuevo agente → crear `docs/agents/<nombre_agente>.md`
  - Se añadió una nueva skill → crear `docs/skills/<nombre_skill>.md`
  - Se añadió una nueva ruta de API → crear `docs/api/<nombre_ruta>.md`

---

#### Paso 5 — Confirmación Final

Muestra al usuario un resumen con:

- ✅ Rama donde se hizo el push
- 📝 Mensaje de commit completo (título + cuerpo)
- 📁 Archivos incluidos en el commit
- 📄 Documentación nueva creada (si aplica)
