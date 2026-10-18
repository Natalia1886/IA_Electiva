# Diagrama Entidad-Relación — GovSST Lab (PostgreSQL)

> **Nota:** diseño objetivo de la capa de persistencia. El repositorio actual contiene el framework base real (MilanFramework: `core/agent_base`, `core/skill_base`, `core/llm_gateway`, `core/observability`) y PostgreSQL configurado en `config/environments/*.yaml` con `psycopg2-binary`. Las entidades GovSST / Resolución 0312 se modelan aquí por primera vez.

## Bloque Mermaid

```mermaid
erDiagram
    USUARIO ||--o{ PARTICIPACION : "participa"
    EMPRESA ||--o{ PARTICIPACION : "recibe"
    USUARIO ||--o{ AUTOEVALUACION : "evalua"
    EMPRESA ||--o{ CENTRO_TRABAJO : "agrupa"
    NIVEL_RIESGO ||--o{ CENTRO_TRABAJO : "clasifica"
    EMPRESA ||--o{ AUTOEVALUACION : "posee"
    CENTRO_TRABAJO ||--o{ AUTOEVALUACION : "evalua"
    AUTOEVALUACION ||--o{ AUTOEVALUACION_ITEM : "compone"
    ESTANDAR_MINIMO ||--o{ AUTOEVALUACION_ITEM : "define"
    AUTOEVALUACION_ITEM ||--o{ EVIDENCIA : "documenta"
    EVIDENCIA ||--o{ EVIDENCIA_HASH : "versiona"
    EMPRESA ||--o{ REPORTE_MINTRABAJO : "genera"
    AUTOEVALUACION ||--o{ REPORTE_MINTRABAJO : "origina"
    AUTOEVALUACION ||--o{ PLAN_MEJORAMIENTO : "requiere"
    USUARIO ||--o{ PLAN_MEJORAMIENTO : "lidera"
    PLAN_MEJORAMIENTO ||--o{ ACCION_MEJORA : "contiene"
    ESTANDAR_MINIMO ||--o{ ACCION_MEJORA : "orienta"
    USUARIO ||--o{ EVENTO_ANALITICA : "produce"

    USUARIO {
        uuid id PK
        string email
        string password_hash "PBKDF2-HMAC-SHA256"
        string rol "ESTUDIANTE | PROFESOR | ADMIN"
        string nombres
        string apellidos
        boolean activo
        datetime creado_en
    }
    PARTICIPACION {
        uuid id PK
        uuid usuario_id FK
        uuid empresa_id FK
        string curso_grado
        date fecha_asignacion
    }
    EMPRESA {
        uuid id PK
        string nit
        int digito_verificacion
        string razon_social
        string sector_economico
        string tamano_empresarial
        string actividad_economica
        datetime creado_en
    }
    CENTRO_TRABAJO {
        uuid id PK
        uuid empresa_id FK
        int nivel_riesgo_id FK
        string nombre
        string departamento
        string municipio
        string direccion
        int numero_trabajadores
    }
    NIVEL_RIESGO {
        int id PK
        string letra "I a V"
        string nombre
        string rango_salarios_uvt
        string color_hex
    }
    AUTOEVALUACION {
        uuid id PK
        uuid empresa_id FK
        uuid centro_trabajo_id FK
        uuid evaluador_id FK "usuario"
        int nivel_riesgo_asignado_id FK
        date fecha
        string estado "BORRADOR | FINALIZADA"
        decimal puntaje_total
        decimal pct_cumplimiento
    }
    ESTANDAR_MINIMO {
        int id PK
        string codigo "E01 a E46"
        string eje
        string titulo
        text descripcion
        string resolucion "0312 de 2019"
    }
    AUTOEVALUACION_ITEM {
        uuid id PK
        uuid autoevaluacion_id FK
        int estandar_minimo_id FK
        string estado_cumplimiento "CUMPLE | NO_CUMPLE | NO_APLICA"
        decimal puntuacion
        text observacion
    }
    EVIDENCIA {
        uuid id PK
        uuid item_id FK
        string nombre_archivo
        string mime_type
        bigint tamano_bytes
        uuid subido_por "FK usuario"
        datetime creado_en
    }
    EVIDENCIA_HASH {
        uuid id PK
        uuid evidencia_id FK
        string algoritmo "SHA-256"
        string hash_sha256
        boolean verificado
        datetime verificado_en
    }
    REPORTE_MINTRABAJO {
        uuid id PK
        uuid empresa_id FK
        uuid autoevaluacion_id FK
        string numero_radicado
        string tipo "AUTOEVALUACION | INSPECCION | DENUNCIA"
        string estado "RADICADO | EN_REVISION | ACEPTADO | OBSERVADO"
        date fecha_envio
        date fecha_respuesta
    }
    PLAN_MEJORAMIENTO {
        uuid id PK
        uuid autoevaluacion_id FK
        uuid responsable_id FK "usuario"
        string estado "ABIERTO | CERRADO"
        date fecha_creacion
        date fecha_limite
    }
    ACCION_MEJORA {
        uuid id PK
        uuid plan_id FK
        int estandar_minimo_id FK
        text descripcion
        string responsable
        string estado "PENDIENTE | EN_PROCESO | CUMPLE"
        date fecha_limite
    }
    EVENTO_ANALITICA {
        uuid id PK
        uuid usuario_id FK
        uuid sesion_id
        string agente
        string accion
        int duracion_ms
        boolean exito
        string codigo_error
        int tokens_llm
        datetime creado_en
    }
```

## Decisiones de modelado

- **Cardinalidades 1:N**: `EMPRESA → CENTRO_TRABAJO`, `EMPRESA → AUTOEVALUACION`, `AUTOEVALUACION → AUTOEVALUACION_ITEM`, `AUTOEVALUACION_ITEM → EVIDENCIA`, `EVIDENCIA → EVIDENCIA_HASH` (hash versionado), `PLAN_MEJORAMIENTO → ACCION_MEJORA`, `USUARIO → EVENTO_ANALITICA`.
- **Cardinalidad N:M (resuelta)**: `USUARIO ↔ EMPRESA` mediante `PARTICIPACION` (un estudiante evalúa varias empresas; una empresa recibe muchos estudiantes).
- **Catálogos**: `NIVEL_RIESGO` (I–V con rango salarial en UVT) y `ESTANDAR_MINIMO` (E01–E46, Resolución 0312 de 2019).
- **Integridad de evidencias**: `EVIDENCIA_HASH` guarda SHA-256 por evidencia para verificación posterior (`hash_validator`) sin perder historial.
- **Analítica educativa**: `EVENTO_ANALITICA` registra `duracion_ms`, `exito`, `codigo_error` y `tokens_llm` por sesión → tasas de error y tiempos.
- **Seguridad**: `password_hash` con PBKDF2-HMAC-SHA256 (consistente con `core/security/auth.py`).

## Archivos relacionados

- `govsst_diagrama_er.mmd` — fuente Mermaid.
- `govsst_diagrama_er.drawio` — Draw.io del DER (13 tablas PK/FK, relaciones crow's foot).
