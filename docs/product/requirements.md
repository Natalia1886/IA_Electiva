# REQUERIMIENTOS FUNCIONALES

| 

| **ID** | **REQUERIMIENTO** | **MODULO** | 
| RF0 | El sistema debe permitir iniciar sesión con usuario y contraseña. | Autenticación | 
| RF02 | El sistema debe distinguir dos roles: Administrador y Vendedor, con permisos diferenciados. | Autenticación | 
| RF03 | El administrador debe poder crear, consultar, editar y desactivar productos. | Productos | 
| RF04 | El sistema debe permitir asociar cada producto a una categoría y a un precio. | Productos | 
| RF05 | Ambos roles deben poder consultar el listado de productos con búsqueda y filtro por categoría. | Productos | 
| RF06 | El sistema debe permitir registrar una venta con uno o más productos, cantidades y total calculado. | Ventas | 
| RF07 | Toda venta registrada debe descontar automáticamente el stock de los productos vendidos. | Ventas | 
| RF08 | El sistema debe generar un resumen diario con ventas, total vendido, transacciones y productos con mayor movimiento. | Ventas | 
| RF09 | El sistema debe mostrar stock actual, stock mínimo y el historial de entradas/salidas de cada producto. | Inventario | 
| RF10 | El administrador debe poder registrar festividades religiosas con fechas, productos y factor de demanda. | Festividades | 
| RF11 | El sistema debe entrenar y usar un modelo de segmentación de productos basado en frecuencia, recencia, varianza y festividades. | ML/Recomendaciones | 
| RF12 | El sistema debe generar recomendaciones de compra (producto, cantidad y motivo) cruzando inventario, historial y festividades. | Recomendaciones | 
| RF13 | Las recomendaciones deben presentarse en lenguaje natural comprensible para un usuario no técnico. | Recomendaciones | 
| RF14 | Solo el administrador debe poder ver las recomendaciones de compra. | Recomendaciones | 
| RF15 | El sistema debe mostrar un dashboard con ventas, inventario, alertas, productos más vendidos y recomendaciones. | Dashboard | 

# REQUERIMIENTOS NO FUNCIONALES

| **ID** | **REQUERIMIENTO** | **MODULO** | 
| RNF01 | La interfaz debe ser utilizable por personas sin formación técnica, con lenguaje simple. | Usabilidad | 
| RNF02 | Las pantallas principales deben cargar en menos de 3 segundos bajo condiciones normales de red. | Rendimiento | 
| RNF03 | Las contraseñas deben almacenarse cifradas (hash), nunca en texto plano. | Seguridad | 
| RNF04 | El acceso a cada funcionalidad debe validarse tanto en frontend como en backend según el rol. | Seguridad | 
| RNF05 | El descuento de stock por venta debe ser una operación atómica (transaccional). | Confiabilidad | 
| RNF06 | El modelo de segmentación debe poder reentrenarse sin rediseñar el sistema. | Mantenibilidad | 
| RNF07 | El código de backend, frontend e IA/ML debe estar versionado y documentado. | Mantenibilidad | 
| RNF08 | El sistema debe mantener un histórico auditable de movimientos de inventario. | Auditabilidad | 
