# Proceso de Expedición de Productos - Stock Expedition

## Índice
1. [Prerequisitos](#prerequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Proceso de Expedición - Flujo Completo](#proceso-de-expedición---flujo-completo)
4. [Pasos Detallados](#pasos-detallados)
5. [Pasos Opcionales vs Necesarios](#pasos-opcionales-vs-necesarios)
6. [Gestión de Direcciones de Envío](#gestión-de-direcciones-de-envío)
7. [Gestión de Transportistas](#gestión-de-transportistas)
8. [Casos Especiales](#casos-especiales)

---

## Prerequisitos

### Módulos Requeridos
El módulo `stock_expedition` depende de los siguientes módulos:
- `sale` - Gestión de órdenes de venta
- `product_sales_by_location` - Ventas por ubicación
- `portal_expedition` - Portal para creación de expediciones (opcional pero recomendado)

### Configuraciones del Sistema
Al instalar el módulo, se configuran automáticamente:
- ✅ **Lotes de producción habilitados** (`group_stock_production_lot`)
- ✅ **Múltiples ubicaciones** (`group_stock_multi_locations`)
- ✅ **Rutas avanzadas** (`group_stock_adv_location`) - Multi-Step Routes
- ✅ **Lotes en albarán de entrega** (`group_lot_on_delivery_slip`)
- ✅ **Variantes de producto** (`group_product_variant`)

### Configuración de Almacén
**OBLIGATORIO**: El almacén debe estar configurado con **expedición en 3 pasos**:
- **Expedición en 3 pasos** (`delivery_steps = 'pick_pack_ship'`)
  - Paso 1: **Pick** (Recogida) - Recoger productos del almacén
  - Paso 2: **Pack** (Embalaje) - Embalar productos para envío
  - Paso 3: **Ship** (Envío) - Enviar productos al cliente

### Configuración de Tipos de Operación

#### 1. Tipo de Operación: Pick (Recogida)
- **Código**: `outgoing` (tipo base)
- **Barcode**: `NV1PICK`
- **Configuración**:
  - `use_delivery_address_domain`: **True** - Solo permite seleccionar direcciones de envío (type='delivery')
- **Propósito**: Recoger productos del almacén para preparar el pedido

#### 2. Tipo de Operación: Pack (Embalaje)
- **Barcode**: `NV1PACK`
- **Configuración**:
  - `use_delivery_address_domain`: **True** - Solo permite seleccionar direcciones de envío (type='delivery')
- **Propósito**: Embalar productos en paquetes para envío

#### 3. Tipo de Operación: Ship (Envío)
- **Barcode**: `NV1OUT`
- **Configuración**:
  - `use_delivery_address_domain`: **True** - Solo permite seleccionar direcciones de envío (type='delivery')
- **Propósito**: Enviar productos al cliente final

### Datos Requeridos

#### Órdenes de Venta (Sale Order)
- Las órdenes de venta deben tener:
  - `account_partner_id` - Cuenta de cliente propietaria (obligatorio)
  - `partner_id` - Cliente comercial
  - `partner_shipping_id` - Dirección de envío (obligatorio, debe ser tipo 'delivery')
  - `partner_invoice_id` - Dirección de facturación
  - `carrier_id` - Transportista (opcional)
  - `transport_insurance` - Seguro de transporte (opcional)
  - `client_order_ref` - Referencia del cliente (opcional)
  - `order_line` - Al menos una línea con productos

#### Productos
- Los productos deben tener:
  - Stock disponible suficiente para cumplir la orden
  - `account_partner_id` asociado (heredado de la orden de venta)

#### Direcciones de Envío
- Las direcciones de envío deben ser de tipo `delivery` (`type = 'delivery'`)
- Se crean automáticamente desde el portal o se pueden usar existentes

---

## Configuración Inicial

### 1. Filtro de Direcciones de Envío
Los tipos de operación Pick, Pack y Ship están configurados para:
- Solo permitir seleccionar direcciones de envío (`type='delivery'`)
- Esto se controla mediante el campo `use_delivery_address_domain` en `stock.picking.type`

### 2. Configuración de Transportistas
- Los transportistas se configuran en `delivery.carrier`
- Se pueden asignar a las órdenes de venta desde el portal

---

## Proceso de Expedición - Flujo Completo

El proceso de expedición sigue un flujo de **3 pasos** que se ejecuta automáticamente cuando se confirma una orden de venta:

```
Portal Cliente → Crear Orden → Confirmar Orden → Pick → Pack → Ship → Cliente
```

### Resumen del Flujo

1. **FASE 1: Creación de Expedición** (Portal Cliente)
   - Cliente crea orden de venta desde el portal
   - Selecciona productos, dirección de envío, transportista
   - Orden queda en estado `draft`

2. **FASE 2: Confirmación de Orden** (Backend o Portal)
   - Se confirma la orden de venta (`action_confirm()`)
   - Odoo crea automáticamente los pickings de expedición
   - Se generan los movimientos de stock

3. **FASE 3: Pick (Recogida)** (Almacén)
   - Confirmar picking
   - Asignar stock
   - Validar picking
   - → Crea automáticamente picking de Pack

4. **FASE 4: Pack (Embalaje)** (Almacén)
   - Confirmar picking
   - Asignar stock
   - Embalar productos (opcional)
   - Validar picking
   - → Crea automáticamente picking de Ship

5. **FASE 5: Ship (Envío)** (Almacén)
   - Confirmar picking
   - Asignar stock
   - Validar picking
   - → Productos enviados al cliente

---

## Pasos Detallados

### **FASE 1: Creación de Expedición**

**⚠️ IMPORTANTE**: Esta fase debe realizarse **directamente desde el portal del cliente**, no desde el backend de Odoo.

**Método**: Controlador `portal_expedition` - Ruta `/account/expedition/create`

**Acceso**: Portal del cliente → Sección de expediciones

**Pasos**:
1. **Desde el portal del cliente**: Seleccionar productos desde el catálogo
2. **Desde el portal del cliente**: Completar información de envío:
   - **OBLIGATORIO**: Dirección de envío (se crea automáticamente si no existe)
     - Nombre del destinatario
     - Calle, número
     - Código postal, ciudad
     - Estado/Provincia, País
     - Teléfono, email
   - **OBLIGATORIO**: Al menos un producto con cantidad
   - **OPCIONAL**: `carrier_id` - Transportista
   - **OPCIONAL**: `client_order_ref` - Referencia del cliente
   - **OPCIONAL**: `transport_insurance` - Seguro de transporte

3. **Desde el portal del cliente**: Crear orden de venta
   - El sistema crea automáticamente:
     - Un `sale.order` en estado `draft`
     - Una dirección de envío (`res.partner` con `type='delivery'`)
     - Líneas de orden (`sale.order.line`) para cada producto

**Validaciones**:
- Debe haber al menos un producto en la orden
- La cantidad debe ser mayor que 0
- El producto debe existir y estar disponible
- La dirección de envío se crea automáticamente si no existe

**Nota**: El cliente crea la orden desde su portal, y luego el almacén procesa los siguientes pasos (Confirmación → Pick → Pack → Ship).

---

### **FASE 2: Confirmación de Orden**

**⚠️ IMPORTANTE**: Esta fase puede realizarse desde el **backend de Odoo** o desde el **portal del cliente** (si está habilitado).

**Método**: `sale.order.action_confirm()`

**Acceso**: Backend Odoo → Ventas → Órdenes de Venta

**Pasos**:
1. Abrir la orden de venta en estado `draft`
2. Revisar información:
   - Productos y cantidades
   - Dirección de envío
   - Transportista
   - Precios y condiciones
3. Confirmar la orden (`action_confirm()`) - Botón **"Confirm"**

**Lo que sucede automáticamente al confirmar**:
- La orden cambia a estado `sale` (confirmada)
- Odoo crea automáticamente:
  - `stock.picking` de tipo **Pick** (recogida)
  - `stock.move` para cada producto
  - `stock.move.line` asociadas
- Si hay stock disponible, se reserva automáticamente
- Se generan los pickings siguientes (Pack, Ship) según la configuración de rutas

**Validaciones**:
- Debe haber stock disponible suficiente (o se crea en estado `waiting`)
- Los productos deben ser de tipo `product` (no `service` o `consu` sin stock)
- La dirección de envío debe ser válida

**Nota**: Si no hay stock disponible, los pickings se crean pero quedan en estado `waiting` hasta que haya stock.

---

### **FASE 3: Pick (Recogida) - NECESARIO**

**Método**: `stock.picking` con `picking_type_id.code = 'outgoing'` y `barcode = 'NV1PICK'`

**Acceso**: Backend Odoo → Inventario → Operaciones → Pick

**Pasos**:
1. **Confirmar picking** (`action_confirm()`) - Botón **"Mark as Todo"**
   - Cambia estado de `draft` a `waiting` o `assigned`
   - Verifica disponibilidad de stock

2. **Asignar stock** (`action_assign()`) - Botón **"Check Availability"**
   - Reserva productos en ubicaciones específicas
   - Si hay stock, cambia a estado `assigned`
   - Si no hay stock, queda en `waiting`

3. **Validar picking** (`button_validate()`) - Botón **"Validate"**
   - **OBLIGATORIO**: Completar cantidades en `stock.move.line`
   - **OBLIGATORIO**: Especificar ubicaciones de origen y destino
   - Validar el picking
   - → Crea automáticamente picking de **Pack**

**Resultado**:
- Productos movidos desde ubicación de stock a ubicación de preparación
- Picking de Pack creado automáticamente
- Estado del picking: `done`

**Validaciones**:
- Debe haber stock disponible
- Las cantidades deben coincidir con la orden
- Las ubicaciones deben ser válidas

---

### **FASE 4: Pack (Embalaje) - NECESARIO**

**Método**: `stock.picking` con `barcode = 'NV1PACK'`

**Acceso**: Backend Odoo → Inventario → Operaciones → Pack

**Pasos**:
1. **Confirmar picking** (`action_confirm()`) - Botón **"Mark as Todo"**
   - Cambia estado de `draft` a `waiting` o `assigned`

2. **Asignar stock** (`action_assign()`) - Botón **"Check Availability"**
   - Reserva productos en ubicación de preparación

3. **Embalar productos** (OPCIONAL)
   - Crear paquetes (`stock.quant.package`)
   - Asignar productos a paquetes
   - Etiquetar paquetes

4. **Validar picking** (`button_validate()`) - Botón **"Validate"**
   - **OBLIGATORIO**: Completar cantidades en `stock.move.line`
   - **OBLIGATORIO**: Especificar ubicaciones de origen y destino
   - Validar el picking
   - → Crea automáticamente picking de **Ship**

**Resultado**:
- Productos movidos desde ubicación de preparación a ubicación de envío
- Productos embalados (si se crearon paquetes)
- Picking de Ship creado automáticamente
- Estado del picking: `done`

**Validaciones**:
- Debe haber productos en ubicación de preparación
- Las cantidades deben coincidir con el picking anterior

---

### **FASE 5: Ship (Envío) - NECESARIO**

**Método**: `stock.picking` con `barcode = 'NV1OUT'`

**Acceso**: Backend Odoo → Inventario → Operaciones → Ship

**Pasos**:
1. **Confirmar picking** (`action_confirm()`) - Botón **"Mark as Todo"**
   - Cambia estado de `draft` a `waiting` o `assigned`

2. **Asignar stock** (`action_assign()`) - Botón **"Check Availability"**
   - Reserva productos en ubicación de envío

3. **Asignar transportista** (OPCIONAL pero recomendado)
   - Seleccionar `carrier_id`
   - Generar etiqueta de envío (si está configurado)
   - Obtener número de seguimiento

4. **Validar picking** (`button_validate()`) - Botón **"Validate"**
   - **OBLIGATORIO**: Completar cantidades en `stock.move.line`
   - **OBLIGATORIO**: Especificar ubicaciones de origen y destino
   - Validar el picking
   - → Productos enviados al cliente

**Resultado**:
- Productos movidos desde ubicación de envío a cliente (ubicación externa)
- Stock descontado del inventario
- Orden de venta marcada como entregada (parcial o completa)
- Estado del picking: `done`

**Validaciones**:
- Debe haber productos en ubicación de envío
- Las cantidades deben coincidir con el picking anterior
- La dirección de envío debe ser válida

---

## Pasos Opcionales vs Necesarios

| Fase | Paso | Necesario | Descripción |
|------|------|-----------|-------------|
| **FASE 1** | Crear orden desde portal | ✅ **NECESARIO** | Cliente crea orden de venta |
| **FASE 1** | Seleccionar transportista | ⚠️ **OPCIONAL** | Puede asignarse después |
| **FASE 1** | Seguro de transporte | ⚠️ **OPCIONAL** | Solo si se requiere |
| **FASE 1** | Referencia del cliente | ⚠️ **OPCIONAL** | Para tracking interno |
| **FASE 2** | Confirmar orden | ✅ **NECESARIO** | Genera pickings automáticamente |
| **FASE 3** | Confirmar picking Pick | ✅ **NECESARIO** | Inicia proceso de recogida |
| **FASE 3** | Asignar stock Pick | ✅ **NECESARIO** | Reserva productos |
| **FASE 3** | Validar picking Pick | ✅ **NECESARIO** | Crea picking Pack |
| **FASE 4** | Confirmar picking Pack | ✅ **NECESARIO** | Inicia proceso de embalaje |
| **FASE 4** | Asignar stock Pack | ✅ **NECESARIO** | Reserva productos |
| **FASE 4** | Embalar productos | ⚠️ **OPCIONAL** | Crear paquetes físicos |
| **FASE 4** | Validar picking Pack | ✅ **NECESARIO** | Crea picking Ship |
| **FASE 5** | Confirmar picking Ship | ✅ **NECESARIO** | Inicia proceso de envío |
| **FASE 5** | Asignar stock Ship | ✅ **NECESARIO** | Reserva productos |
| **FASE 5** | Asignar transportista | ⚠️ **OPCIONAL** | Para tracking de envío |
| **FASE 5** | Generar etiqueta envío | ⚠️ **OPCIONAL** | Si transportista lo requiere |
| **FASE 5** | Validar picking Ship | ✅ **NECESARIO** | Completa expedición |

---

## Gestión de Direcciones de Envío

### Creación Automática
- Las direcciones de envío se crean automáticamente desde el portal
- Se crean como `res.partner` con `type='delivery'`
- Se asocian al `partner_id` comercial del cliente

### Restricciones
- En los pickings de tipo Pick, Pack y Ship solo se pueden seleccionar direcciones de tipo `delivery`
- Esto se controla mediante `use_delivery_address_domain = True` en los tipos de operación

### Validación
- Las direcciones deben tener:
  - Nombre del destinatario
  - Calle (obligatorio)
  - Ciudad (obligatorio)
  - País (obligatorio)
  - Código postal (recomendado)

---

## Gestión de Transportistas

### Asignación
- Los transportistas se pueden asignar:
  - Al crear la orden desde el portal
  - Al confirmar la orden
  - En el picking de Ship

### Funcionalidades
- **Tracking**: Número de seguimiento (`carrier_tracking_ref`)
- **Etiquetas**: Generación de etiquetas de envío (si el transportista lo soporta)
- **Costos**: Cálculo automático de costos de envío

### Seguro de Transporte
- Se puede activar `transport_insurance` en la orden de venta
- Se hereda al picking mediante el campo relacionado `transport_insurance`

---

## Casos Especiales

### 1. Productos sin Stock Disponible

**Situación**: La orden se confirma pero no hay stock suficiente.

**Comportamiento**:
- Los pickings se crean pero quedan en estado `waiting`
- Cuando haya stock disponible, se puede asignar (`action_assign()`)
- El proceso continúa normalmente

**Solución**:
- Esperar a que haya stock disponible
- O cancelar/modificar la orden

### 2. Productos con Tracking (Serial/Lot)

**Situación**: Productos que requieren números de serie o lotes.

**Comportamiento**:
- En el picking Pick, se deben especificar los números de serie/lotes
- Los números de serie/lotes se validan en cada paso
- Se mantiene la trazabilidad completa

**Solución**:
- Escanear o introducir números de serie/lotes en cada picking
- Validar que los números sean únicos y válidos

### 3. Órdenes Parciales

**Situación**: No hay stock suficiente para toda la orden.

**Comportamiento**:
- Se puede validar el picking con cantidades parciales
- Se crea un backorder para las cantidades restantes
- El proceso continúa con las cantidades disponibles

**Solución**:
- Validar con cantidades parciales
- Completar el backorder cuando haya stock

### 4. Cancelación de Orden

**Situación**: Se cancela una orden después de crear pickings.

**Comportamiento**:
- Los pickings se cancelan automáticamente
- El stock reservado se libera
- No se pueden validar pickings cancelados

**Solución**:
- Cancelar la orden desde el backend
- Los pickings se cancelan en cascada

### 5. Modificación de Orden Después de Confirmar

**Situación**: Se modifica una orden ya confirmada.

**Comportamiento**:
- Si los pickings ya están validados, no se pueden modificar
- Si los pickings están en `draft` o `assigned`, se pueden modificar
- Se deben cancelar y recrear los pickings si es necesario

**Solución**:
- Modificar la orden antes de validar pickings
- O cancelar y recrear la orden

### 6. Importación Masiva de Órdenes

**Situación**: Se importan múltiples órdenes desde Excel/CSV.

**Comportamiento**:
- Se crean múltiples órdenes de venta en estado `draft`
- Cada orden debe confirmarse individualmente
- Los pickings se crean al confirmar cada orden

**Solución**:
- Usar la funcionalidad de importación masiva desde el portal
- Confirmar órdenes individualmente o en lote (si está habilitado)

---

## Resumen de Procesos que Pueden Fallar

### Tabla de Errores Comunes

| Fase | Proceso | Error Posible | Causa | Solución |
|------|---------|---------------|-------|----------|
| **FASE 1** | Crear orden desde portal | Sin productos | No se seleccionaron productos | Seleccionar al menos un producto |
| **FASE 1** | Crear orden desde portal | Cantidad inválida | Cantidad <= 0 | Especificar cantidad > 0 |
| **FASE 1** | Crear orden desde portal | Dirección inválida | Datos de dirección incompletos | Completar todos los campos obligatorios |
| **FASE 2** | Confirmar orden | Sin stock disponible | No hay stock suficiente | Esperar stock o modificar orden |
| **FASE 2** | Confirmar orden | Productos no válidos | Productos de tipo service sin stock | Verificar tipo de producto |
| **FASE 3** | Validar picking Pick | Líneas no escaneadas | `require_scan_confirmation = True` | Escanear todos los productos |
| **FASE 3** | Validar picking Pick | Faltan seriales | Productos con tracking sin serial | Generar o introducir seriales |
| **FASE 3** | Validar picking Pick | Stock insuficiente | No hay stock en ubicación origen | Verificar stock disponible |
| **FASE 4** | Validar picking Pack | Productos no en preparación | No se validó Pick anteriormente | Validar Pick primero |
| **FASE 4** | Validar picking Pack | Cantidades incorrectas | No coinciden con Pick | Verificar cantidades |
| **FASE 5** | Validar picking Ship | Productos no en envío | No se validó Pack anteriormente | Validar Pack primero |
| **FASE 5** | Validar picking Ship | Dirección inválida | Dirección no es tipo delivery | Verificar tipo de dirección |
| **General** | Dirección no aparece | Tipo incorrecto | No es tipo `delivery` | Crear dirección tipo delivery |

### Errores en la Creación de Expedición (Portal)

**Situación**: Errores al crear una expedición desde el portal.

**Errores Posibles**:

1. **Sin productos seleccionados**:
   - **Error**: Validación falla al intentar crear orden
   - **Causa**: No se seleccionó ningún producto
   - **Solución**: Seleccionar al menos un producto antes de crear la orden

2. **Cantidad inválida**:
   - **Error**: Validación falla si cantidad <= 0
   - **Causa**: Se especificó cantidad 0 o negativa
   - **Solución**: Especificar cantidad mayor que 0

3. **Dirección de envío incompleta**:
   - **Error**: Validación falla si faltan campos obligatorios
   - **Causa**: Campos obligatorios de dirección no completados
   - **Solución**: Completar todos los campos obligatorios (nombre, calle, ciudad, país)

4. **Producto no disponible**:
   - **Error**: Producto no aparece en catálogo
   - **Causa**: Producto sin stock disponible (filtro aplicado)
   - **Solución**: Verificar stock disponible o esperar a que haya stock

### Errores en la Confirmación de Orden

**Situación**: Errores al confirmar una orden de venta.

**Errores Posibles**:

1. **Sin stock disponible**:
   - **Causa**: No hay stock suficiente para cumplir la orden
   - **Comportamiento**: Los pickings se crean pero quedan en estado `waiting`
   - **Solución**: 
     - Esperar a que haya stock disponible
     - O cancelar/modificar la orden
     - Asignar stock cuando esté disponible (`action_assign()`)

2. **Productos de tipo service**:
   - **Causa**: Productos de tipo `service` no generan pickings
   - **Comportamiento**: No se crean pickings para productos service
   - **Solución**: Verificar tipo de producto antes de confirmar

3. **Dirección de envío inválida**:
   - **Causa**: Dirección no es de tipo `delivery`
   - **Comportamiento**: Error al crear pickings
   - **Solución**: Verificar que la dirección sea de tipo `delivery`

### Errores en la Validación de Pickings

**Situación**: Errores al validar pickings de expedición.

**Errores Posibles**:

1. **Líneas no escaneadas** (si `require_scan_confirmation = True`):
   - **Error**: `"The following products have not been scanned/confirmed: [lista]... Please scan or confirm all products before validating."`
   - **Causa**: Hay líneas con demanda pero que no han sido escaneadas/confirmadas
   - **Solución**: 
     - Escanear todos los productos requeridos
     - Confirmar todas las líneas antes de validar

2. **Faltan números de serie** (para productos con `tracking = 'serial'`):
   - **Error**: Se muestra wizard de generación de seriales
   - **Causa**: Hay líneas con productos `tracking = 'serial'` que no tienen `lot_id` ni `lot_name`
   - **Solución**: 
     - Generar seriales automáticamente usando el wizard
     - O introducir manualmente los números de serie

3. **Stock insuficiente**:
   - **Error**: No hay stock disponible en la ubicación origen
   - **Causa**: El stock fue movido o reservado por otro picking
   - **Solución**: 
     - Verificar stock disponible
     - Asignar stock nuevamente (`action_assign()`)
     - O cancelar y recrear el picking

4. **Cantidades incorrectas**:
   - **Error**: Las cantidades en `stock.move.line` no coinciden con las esperadas
   - **Causa**: Se modificaron cantidades incorrectamente
   - **Solución**: 
     - Revisar y corregir las cantidades
     - Verificar que coinciden con el picking anterior

5. **Ubicaciones inválidas**:
   - **Error**: Las ubicaciones origen/destino no son válidas
   - **Causa**: Ubicaciones no configuradas correctamente
   - **Solución**: 
     - Verificar configuración de ubicaciones
     - Verificar que las ubicaciones son del tipo correcto

### Errores en Pickings Siguientes

**Situación**: Errores al crear o validar pickings siguientes (Pack, Ship).

**Errores Posibles**:

1. **Picking anterior no validado**:
   - **Causa**: Se intenta validar Pack sin validar Pick primero
   - **Comportamiento**: No hay productos en ubicación de preparación
   - **Solución**: Validar pickings en orden (Pick → Pack → Ship)

2. **Productos no en ubicación esperada**:
   - **Causa**: Los productos no están en la ubicación correcta
   - **Comportamiento**: No se puede asignar stock
   - **Solución**: 
     - Verificar que el picking anterior está validado
     - Verificar ubicaciones de los productos

3. **Dirección no aparece en picking**:
   - **Causa**: Dirección no es de tipo `delivery`
   - **Comportamiento**: No se puede seleccionar en el picking
   - **Solución**: 
     - Verificar que la dirección es de tipo `delivery`
     - O crear una nueva dirección de tipo `delivery`

### Guía Rápida de Solución de Problemas

1. **Pickings no se crean**: Verificar que la orden esté confirmada y que los productos sean de tipo `product`
2. **No se puede asignar stock**: Verificar que haya stock disponible en las ubicaciones correctas
3. **Dirección no aparece**: Verificar que la dirección sea de tipo `delivery`
4. **Picking siguiente no se crea**: Verificar que el picking anterior esté validado y en estado `done`
5. **Error al validar**: Verificar que todas las líneas están escaneadas (si aplica) y que los productos con tracking tienen seriales
6. **Stock insuficiente**: Verificar stock disponible y cancelar reservas de otros pickings si es necesario

---

## Resumen de Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CREAR EXPEDICIÓN (Portal Cliente)                       │
│    - Seleccionar productos desde portal                    │
│    - Completar dirección de envío                          │
│    - Seleccionar transportista (opcional)                 │
│    - Crear orden de venta (draft)                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CONFIRMAR ORDEN - NECESARIO                              │
│    - Confirmar orden de venta                              │
│    → Crea automáticamente picking Pick                     │
│    → Crea automáticamente movimientos de stock             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PICK (Recogida) - NECESARIO                              │
│    - Confirmar picking                                      │
│    - Asignar stock                                          │
│    - Validar picking                                        │
│    → Crea automáticamente picking Pack                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PACK (Embalaje) - NECESARIO                              │
│    - Confirmar picking                                      │
│    - Asignar stock                                          │
│    - Embalar productos (opcional)                          │
│    - Validar picking                                        │
│    → Crea automáticamente picking Ship                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. SHIP (Envío) - NECESARIO                                 │
│    - Confirmar picking                                      │
│    - Asignar stock                                          │
│    - Asignar transportista (opcional)                       │
│    - Validar picking                                        │
│    → Productos enviados al cliente                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Notas Importantes

### Diferencias con Recepción

1. **Dirección**: Expedición va **del almacén al cliente** (outgoing), recepción va **del proveedor al almacén** (incoming)
2. **Origen**: Expedición se crea desde **orden de venta**, recepción se crea desde **wizard de recepción**
3. **Pasos**: Expedición usa **Pick → Pack → Ship**, recepción usa **Input → QC → Store**
4. **Control de Calidad**: Expedición **NO tiene control de calidad**, recepción **SÍ tiene QC**
5. **Paquetes**: En expedición los paquetes son **opcionales** (embalaje), en recepción son **obligatorios** (recepción física)

### Mejores Prácticas

1. **Confirmar órdenes en lote**: Si hay múltiples órdenes, confirmarlas en lote para optimizar
2. **Validar pickings en orden**: Siempre validar Pick → Pack → Ship en ese orden
3. **Embalar en Pack**: Crear paquetes físicos en la fase Pack para mejor organización
4. **Asignar transportista temprano**: Asignar transportista en la orden o en Pack para mejor tracking
5. **Verificar direcciones**: Validar direcciones de envío antes de confirmar órdenes
6. **Stock disponible**: Verificar stock antes de confirmar órdenes para evitar retrasos

### Troubleshooting

1. **Pickings no se crean**: Verificar que la orden esté confirmada y que los productos sean de tipo `product`
2. **No se puede asignar stock**: Verificar que haya stock disponible en las ubicaciones correctas
3. **Dirección no aparece**: Verificar que la dirección sea de tipo `delivery`
4. **Picking siguiente no se crea**: Verificar que el picking anterior esté validado y en estado `done`
5. **Transportista no funciona**: Verificar configuración del transportista y credenciales API (si aplica)

---

## Referencias

- **Módulo**: `stock_expedition`
- **Módulo Portal**: `portal_expedition`
- **Modelos principales**:
  - `sale.order` - Orden de venta
  - `stock.picking` - Picking de expedición
  - `stock.move` - Movimiento de stock
  - `stock.move.line` - Línea de movimiento
  - `res.partner` - Direcciones de envío
  - `delivery.carrier` - Transportistas

---

**Última actualización**: 2025-01-XX
**Versión del módulo**: 18.0.1.0.0
