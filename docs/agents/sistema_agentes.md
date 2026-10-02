# Agentes Especializados del Framework

Este documento describe la arquitectura y responsabilidades de los agentes inteligentes implementados en MilanFramework para la gestión del dominio de tienda de artículos religiosos.

## 1. Sales Agent (`agents/sales_agent`)
- **Propósito**: Gestión del flujo de ventas, registro de transacciones y cálculo de métricas financieras del día.
- **Rutas asociadas**: `/api/sales`

## 2. Inventory Agent (`agents/inventory_agent`)
- **Propósito**: Monitoreo y control de stock de productos, detección de insumos o artículos bajo el umbral mínimo y generación de alertas operativas.
- **Rutas asociadas**: `/api/inventory`

## 3. Purchase Advisor Agent (`agents/purchase_advisor_agent`)
- **Propósito**: Motor de recomendación inteligente de compras que combina pronóstico de demanda, festividades religiosas e inventario actual para sugerir abastecimiento optimizado.
- **Rutas asociadas**: `/api/recommendations`
