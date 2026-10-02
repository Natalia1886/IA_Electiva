# HISTORIAS DE USUARIO

## HU01 – Inicio de sesión con control de roles

**Prioridad:** Alta  
**Historia de Usuario:** Como usuario del sistema (administrador o vendedor), quiero iniciar sesión con mi usuario y contraseña, para acceder solo a las funcionalidades permitidas por mi rol.  
**Característica:** Inicio de sesión con control de roles

---

### Escenario 1: Login exitoso de un administrador
* **Dado:** Existe un usuario "admin" con rol administrador y contraseña válida.
* **Cuando:** El usuario ingresa sus credenciales correctas.
* **Entonces:** El sistema concede el acceso y muestra el menú completo, incluyendo Usuarios y Recomendaciones.

---

### Escenario 2: Login exitoso de un vendedor
* **Dado:** Existe un usuario "vendedor1" con rol vendedor y contraseña válida.
* **Cuando:** El usuario ingresa sus credenciales correctas.
* **Entonces:** El sistema concede el acceso y no muestra las opciones de Usuarios ni Recomendaciones.

---

### Escenario 3: Credenciales inválidas
* **Dado:** Existe un usuario registrado en el sistema.
* **Cuando:** Ingresa una contraseña incorrecta.
* **Entonces:** El sistema rechaza el acceso y muestra un mensaje de error sin especificar cuál dato fue incorrecto.

---

## HU02 – Registro de productos

**Prioridad:** Alta  
**Historia de Usuario:** Como administrador, quiero registrar un nuevo producto con categoría, precio y stock inicial, para tenerlo disponible para la venta y el control de inventario.  
**Característica:** Registro de productos

---

### Escenario 1: Registrar un producto válido
* **Dado:** Soy administrador autenticado.
* **Cuando:** Completo nombre, categoría, precio y stock inicial válidos y confirmo el registro.
* **Entonces:** El producto queda creado y visible en el listado y su stock inicial coincide con el ingresado.

---

### Escenario 2: Intentar registrar un producto con precio negativo
* **Dado:** Soy administrador autenticado.
* **Cuando:** Ingreso un precio negativo.
* **Entonces:** El sistema rechaza el registro y muestra un mensaje indicando que el precio no puede ser negativo.

---

### Escenario 3: Vendedor intenta registrar un producto
* **Dado:** Soy un usuario con rol vendedor.
* **Cuando:** Intento acceder al formulario de creación de productos.
* **Entonces:** El sistema me niega el acceso.

---

## HU03 – Registro de ventas

**Prioridad:** Alta  
**Historia de Usuario:** Como vendedor o administrador, quiero registrar una venta con uno o varios productos, para que el inventario se actualice automáticamente y quede el registro del día.  
**Característica:** Registro de ventas

---

### Escenario 1: Venta exitosa con stock suficiente
* **Dado:** Existe un producto "Vela religiosa" con stock de 20 unidades.
* **Cuando:** Registro una venta de 5 unidades.
* **Entonces:** La venta queda registrada con su detalle, total y vendedor, y el stock se actualiza a 15 unidades y se genera un movimiento de inventario de tipo "salida".

---

## HU05 – Alertas de inventario

**Prioridad:** Alta  
**Historia de Usuario:** Como administrador, quiero ver alertas de productos con stock bajo o agotado, para anticipar quiebres de stock antes de que ocurran.  
**Característica:** Alertas de inventario

---

### Escenario 1: Producto con stock bajo
* **Dado:** Un producto tiene stock mínimo de 10 unidades y stock actual de 8 unidades.
* **Cuando:** El administrador consulta las alertas.
* **Entonces:** El producto aparece listado con estado "Stock bajo".

---

### Escenario 2: Producto agotado
* **Dado:** Un producto tiene stock actual de 0 unidades.
* **Cuando:** El administrador consulta las alertas.
* **Entonces:** El producto aparece listado con estado "Agotado".

---

## HU06 – Gestión de festividades religiosas

**Prioridad:** Media  
**Historia de Usuario:** Como administrador, quiero registrar festividades religiosas con sus fechas y productos asociados, para que el sistema pueda anticipar la demanda en esas fechas.  
**Característica:** Gestión de festividades religiosas

---

### Escenario 1: Registrar una festividad con productos asociados
* **Dado:** Soy administrador autenticado.
* **Cuando:** Registro "Semana Santa" con fecha de inicio, fecha de fin y productos como "Velas" y "Crucifijos".
* **Entonces:** La festividad queda creada y disponible para el módulo de recomendaciones.

---

## HU07 – Recomendación de compras con IA

**Prioridad:** Alta  
**Historia de Usuario:** Como administrador, quiero recibir una recomendación de qué comprar, cuánto y por qué, para tomar decisiones de compra informadas sin interpretar tablas técnicas.  
**Característica:** Recomendación de compras con IA

---

### Escenario 1: Recomendación antes de una festividad
* **Dado:** "Semana Santa" es una festividad próxima con productos asociados y el histórico muestra aumento de ventas de "Velas religiosas" en fechas similares.
* **Cuando:** El administrador consulta las recomendaciones.
* **Entonces:** El sistema muestra el producto, stock actual y cantidad recomendada y explica el motivo en lenguaje natural basado en el comportamiento histórico.