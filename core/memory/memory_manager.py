"""API única de lectura/escritura de memoria que usan los agentes.

Ningún agente ni skill debe acceder a short_term/long_term directamente:
todo pasa por aquí para mantener trazabilidad y composabilidad.
"""
