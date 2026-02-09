# Proceso de Recepción de Paquetes - Stock Reception

## Índice
1. [Prerequisitos](#prerequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Proceso de Recepción - Flujo Completo](#proceso-de-recepción---flujo-completo)
4. [Pasos Detallados](#pasos-detallados)
5. [Pasos Opcionales vs Necesarios](#pasos-opcionales-vs-necesarios)
6. [Gestión de Paquetes](#gestión-de-paquetes)
7. [Control de Calidad](#control-de-calidad)
8. [Casos Especiales](#casos-especiales)

---

## Prerequisitos

### Módulos Requeridos
El módulo `stock_reception` depende de los siguientes módulos:
- `stock` - Gestión básica de inventario
- `delivery` - Gestión de transportistas
- `hr` - Recursos humanos (para asignar receptores)
- `contacts_menu` - Menú de contactos
- `product_menu` - Menú de productos
- `stock_menu` - Menú de stock
- `package_menu` - Menú de paquetes
- `logistics_security` - Seguridad logística
- `stock_internal` - Movimientos internos
- `stock_barcode_auto_serial` - Generación automática de números de serie

### Configuraciones del Sistema
Al instalar el módulo, se configuran automáticamente:
- ✅ **Lotes de producción habilitados** (`group_stock_production_lot`)
- ✅ **Múltiples ubicaciones** (`group_stock_multi_locations`)
- ✅ **Rutas avanzadas** (`group_stock_adv_location`) - Multi-Step Routes
- ✅ **Lotes en albarán de entrega** (`group_lot_on_delivery_slip`)
- ✅ **Variantes de producto** (`group_product_variant`)

### Configuración de Almacén
**OBLIGATORIO**: El almacén debe estar configurado con **recepción en 3 pasos**:
- **Recepción en 3 pasos** (`reception_steps = 'three_steps'`)
  - Paso 1: **Recepción** (Input) - Recibir mercancías en ubicación de entrada
  - Paso 2: **Control de Calidad** (QC) - Inspección en ubicación de control
  - Paso 3: **Almacenar** (Store) - Almacenar en ubicación de stock

### Configuración de Tipos de Operación

#### 1. Tipo de Operación: Recepción (Input)
- **Código**: `incoming`
- **Configuración**:
  - `use_create_lots`: **False** - No crear lotes en recepción
  - `use_existing_lots`: **False** - No usar lotes existentes
- **Propósito**: Recibir paquetes físicos en la ubicación de entrada

#### 2. Tipo de Operación: Control de Calidad (QC)
- **Código**: `NV1QC` (barcode)
- **Configuración**:
  - `use_create_lots`: **True** - Crear lotes/números de serie en QC
  - `use_existing_lots`: **False** - No usar lotes existentes
  - `require_scan_confirmation`: **True** - Requiere confirmación de escaneo
  - `show_print_lot_labels`: **True** - Mostrar impresión de etiquetas
  - `barcode_allow_extra_product`: **True** - Permitir productos extra
  - `barcode_validation_full`: **True** - Validación completa
  - `restrict_put_in_pack`: **optional** - Empaquetado opcional
  - `restrict_scan_dest_location`: **optional** - Escaneo de destino opcional
  - `restrict_scan_product`: **False** - No restringir escaneo de producto
  - `restrict_scan_source_location`: **no** - No restringir ubicación origen
  - `restrict_scan_tracking_number`: **optional** - Número de seguimiento opcional
  - `allowed_location_dest_ids`: Solo ubicación de QC
- **Propósito**: Inspeccionar productos y crear lotes/números de serie

#### 3. Tipo de Operación: Almacenar (Store)
- **Código**: `NV1STOR` (barcode)
- **Configuración**:
  - `require_scan_confirmation`: **True** - Requiere confirmación de escaneo
- **Propósito**: Almacenar productos en ubicación final de stock

### Datos Requeridos

#### Productos
- Los productos deben tener `account_partner_id` asociado (cuenta de cliente)
- Los productos pueden tener:
  - `tracking = 'none'` - Sin seguimiento de lote/serial
  - `tracking = 'serial'` - Con seguimiento de número de serie
  - **NO se usa** `tracking = 'lot'` en este sistema

#### Paquetes
- Los paquetes deben tener:
  - `name` - Nombre del paquete (generado automáticamente o manual)
  - `package_type_id` - Tipo de paquete (opcional pero recomendado)
  - `account_partner_id` - Cuenta de cliente propietaria
  - `global_tracking_ref` - Referencia de seguimiento internacional (obligatorio para crear recepción)
  - `carrier_tracking_ref` - Referencia de seguimiento del transportista (opcional)
  - `state` - Estado del paquete: `on_hold`, `planned`, `in_progress`, `done`

---

## Configuración Inicial

### 1. Punto de Control de Calidad
Se crea automáticamente un punto de control de calidad:
- **Nombre**: "Quality Control - Reception Inspection"
- **Tipo de operación**: Control de calidad (NV1QC)
- **Medición sobre**: `move_line` (líneas de movimiento)
- **Frecuencia**: Todos los movimientos (`all`)
- **Tipo de prueba**: Pass/Fail

### 2. Etapas de Alerta de Calidad
- **Etapa**: "QC Failed" - Para productos que fallan el control de calidad

---

## Proceso de Recepción - Flujo Completo

### Resumen del Flujo
```
1. Crear Recepción (Wizard)
   ↓
2. Picking de Recepción (Input) - Estado: draft → confirmed → assigned → done
   ↓
3. Picking de Control de Calidad (QC) - Estado: draft → confirmed → assigned → done
   ↓
4. Picking de Almacenamiento (Store) - Estado: draft → confirmed → assigned → done
```

### Flujo Detallado

#### **FASE 1: Creación de Recepción**

**⚠️ IMPORTANTE**: Esta fase debe realizarse **directamente desde el portal del cliente**, no desde el backend de Odoo.

**Método**: Wizard `create.stock.picking.wizard`

**Acceso**: Portal del cliente → Sección de recepciones

**Pasos**:
1. **Desde el portal del cliente**: Seleccionar productos desde la vista de productos
2. **Desde el portal del cliente**: Abrir wizard de creación de recepción
3. **Desde el portal del cliente**: Completar información:
   - **OBLIGATORIO**: `package_type_id` - Tipo de paquete
   - **OBLIGATORIO**: `global_tracking_ref` - Referencia de seguimiento internacional
   - **OBLIGATORIO**: `scheduled_date` - Fecha programada
   - **OBLIGATORIO**: `reception_line_ids` - Al menos una línea con productos
   - **OPCIONAL**: `carrier_name` - Nombre del transportista
   - **OPCIONAL**: `carrier_id` - Transportista
   - **OPCIONAL**: `optional_tracking_ref` - Referencia de seguimiento opcional
   - **OPCIONAL**: Dimensiones (height, width, packaging_length, packaging_weight)

4. El wizard crea:
   - Un `stock.picking` de tipo recepción (`incoming`)
   - Uno o más `stock.quant.package` (según `box_number` en líneas)
   - `stock.move` para cada producto
   - `stock.move.line` asociadas a los paquetes correspondientes

**Validaciones**:
- Todos los productos seleccionados deben tener el mismo `account_partner_id`
- Debe haber al menos una línea de recepción
- El tipo de paquete es obligatorio
- La referencia de seguimiento internacional es obligatoria

**Nota**: El cliente crea la recepción desde su portal, y luego el almacén procesa los siguientes pasos (Recepción → QC → Almacenamiento).

---

#### **FASE 2: Recepción de Paquetes (Input)**

**Tipo de Operación**: Recepción (`incoming`)

**Estado Inicial**: `draft` → `confirmed` → `assigned` → `done`

**Pasos Necesarios**:

1. **Confirmar Picking** (`action_confirm`) - Botón **"Mark as Todo"**
   - **NECESARIO**: Confirma el picking y prepara las reservas
   - Estado: `draft` → `confirmed`

2. **Asignar Stock** (`action_assign`) - Botón **"Check Availability"**
   - **NECESARIO**: Reserva el stock en la ubicación origen
   - Estado: `confirmed` → `assigned`
   - Nota: Para recepciones, el stock viene de `stock_location_customers`

3. **Validar Picking** (`button_validate`) - Botón **"Validate"**
   - **NECESARIO**: Valida la recepción
   - Estado: `assigned` → `done`
   - **Acciones automáticas al validar**:
     - Asigna el usuario actual como responsable si no hay uno (`user_id`)
     - Actualiza el estado de los paquetes a `done`
     - Desempaqueta los pickings de QC (si existen)
     - Marca los paquetes de QC como `done` (si aplica)

**Método Alternativo: Recepción por Escaneo de Código de Barras**

**Wizard**: `receive.package.wizard`

**Pasos**:
1. Escanear referencia de seguimiento (tracking ref) o nombre de paquete
2. El sistema busca el paquete en estados: `on_hold`, `planned`, `in_progress`
3. Se cargan automáticamente:
   - Información del paquete
   - Referencias de seguimiento
   - Peso
   - Dimensiones (si hay tipo de paquete)
4. **OPCIONAL**: Seleccionar receptor (`receiver_id`)
5. **OPCIONAL**: Capturar imágenes/videos del paquete (`media_ids`)
6. Confirmar recepción (`action_confirm`) - Botón **"Confirm"**
   - Busca la línea de movimiento asociada al paquete
   - Asigna el receptor como responsable del picking
   - Valida el picking automáticamente
   - Adjunta las imágenes al paquete
   - Vuelve a abrir el wizard para escanear otro paquete

**Resultado de la Fase 2**:
- El picking de recepción queda en estado `done`
- Los paquetes se mueven a la ubicación de entrada del almacén
- Se crea automáticamente el picking de Control de Calidad (QC) mediante push rules
- Los paquetes se desempaquetan automáticamente en el picking de QC

---

#### **FASE 3: Control de Calidad (QC)**

**Tipo de Operación**: Control de Calidad (`NV1QC`)

**Estado**: `draft` → `confirmed` → `assigned` → `done`

**Creación Automática**:
- Se crea automáticamente mediante push rules cuando se valida el picking de recepción
- Tiene el mismo `group_id` que el picking de recepción

**Desempaquetado Automático**:
Al validar el picking de recepción, se ejecuta `_unpack_qc_pickings_after_reception()`:
- Guarda `package_id` en `origin_package_id` (para trazabilidad)
- Limpia `package_id` y `result_package_id` (permite movimiento libre)
- Desempaqueta físicamente los paquetes (`package.unpack()`)

**Pasos Necesarios**:

1. **Confirmar Picking** (`action_confirm`) - Botón **"Mark as Todo"**
   - **NECESARIO**: Confirma el picking de QC
   - Estado: `draft` → `confirmed`

2. **Asignar Stock** (`action_assign`) - Botón **"Check Availability"**
   - **NECESARIO**: Reserva el stock
   - Estado: `confirmed` → `assigned`

3. **Procesar Productos con Código de Barras** (Opcional pero recomendado)
   - Escanear productos
   - Para productos con `tracking = 'serial'`:
     - **NECESARIO**: Crear números de serie
     - Se pueden generar automáticamente con `stock_barcode_auto_serial`
   - Para productos con `tracking = 'none'`:
     - No requiere lotes/seriales

4. **Control de Calidad** (Opcional pero recomendado)
   - Se generan checks de calidad automáticamente (según `quality_point`)
   - **OPCIONAL**: Realizar inspección visual
   - **OPCIONAL**: Verificar que el producto coincide con el albarán
   - **OPCIONAL**: Verificar números de serie/lotes
   - **OPCIONAL**: Documentar daños visibles
   - **OPCIONAL**: Marcar como Pass/Fail
   - **Si falla el control de calidad**:
     - Se crea automáticamente una `quality.alert` con estado **"QC Failed"**
     - La alerta incluye:
       - Información del picking asociado
       - Producto que falló
       - Lote/Serial (si aplica)
       - Cantidad fallida
       - Ubicación de fallo (si se especifica)
       - Notas del operador (`note` y `additional_note`)
       - Usuario que realizó el check
       - `account_partner_id` del cliente
     - Se envía mensaje automático al `partner_id` del cliente con:
       - Nombre del picking
       - Producto que falló
       - Lote/Serial
       - Cantidad fallida
       - Ubicación de fallo
     - Se envía notificación al sistema (si está instalado `portal.user.notification`) a todos los usuarios del portal asociados al cliente
     - **El proceso puede continuar**: Los productos que pasan QC continúan al almacenamiento, los que fallan se pueden mover a ubicación de fallo
     - La alerta queda disponible para seguimiento y gestión desde el módulo de reparaciones

5. **Validar Picking** (`button_validate`) - Botón **"Validate"**
   - **NECESARIO**: Valida el control de calidad
   - Estado: `assigned` → `done`
   - **Acciones automáticas**:
     - Marca los paquetes originales (de `origin_package_id`) como `done`
     - Se crea automáticamente el picking de Almacenamiento mediante push rules

**Configuración Especial de QC**:
- Permite productos extra (`barcode_allow_extra_product = True`)
- Validación completa requerida (`barcode_validation_full = True`)
- Empaquetado opcional (`restrict_put_in_pack = optional`)
- Solo permite destino a ubicación de QC

---

#### **FASE 4: Almacenamiento (Store)**

**Tipo de Operación**: Almacenar (`NV1STOR`)

**Estado**: `draft` → `confirmed` → `assigned` → `done`

**Creación Automática**:
- Se crea automáticamente mediante push rules cuando se valida el picking de QC
- Tiene el mismo `group_id` que los pickings anteriores

**Pasos Necesarios**:

1. **Confirmar Picking** (`action_confirm`) - Botón **"Mark as Todo"**
   - **NECESARIO**: Confirma el picking de almacenamiento
   - Estado: `draft` → `confirmed`

2. **Asignar Stock** (`action_assign`) - Botón **"Check Availability"**
   - **NECESARIO**: Reserva el stock
   - Estado: `confirmed` → `assigned`

3. **Validar Picking** (`button_validate`) - Botón **"Validate"**
   - **NECESARIO**: Valida el almacenamiento
   - Estado: `assigned` → `done`
   - Requiere confirmación de escaneo (`require_scan_confirmation = True`)

**Resultado Final**:
- Los productos quedan almacenados en la ubicación de stock final
- El proceso de recepción está completo

---

## Pasos Detallados

### Creación de Recepción

#### Paso 1.1: Selección de Productos
- **NECESARIO**: Seleccionar productos desde la vista de productos
- **Requisito**: Todos los productos deben tener el mismo `account_partner_id`
- **Validación**: Si hay productos con diferentes `account_partner_id`, se muestra error

#### Paso 1.2: Abrir Wizard de Creación
- Acción: Abrir wizard `create.stock.picking.wizard`
- Se pre-llenan automáticamente:
  - `account_partner_id` - Del primer producto seleccionado
  - `location_id` - `stock_location_customers`
  - `location_dest_id` - `stock_location_company`
  - `picking_type_id` - `stock.picking_type_in`
  - `reception_line_ids` - Líneas con productos seleccionados

#### Paso 1.3: Completar Información del Paquete
- **OBLIGATORIO**: `package_type_id` - Tipo de paquete
- **OBLIGATORIO**: `global_tracking_ref` - Referencia de seguimiento internacional
- **OBLIGATORIO**: `scheduled_date` - Fecha programada
- **OPCIONAL**: `carrier_name` - Nombre del transportista
- **OPCIONAL**: `carrier_id` - Transportista seleccionado
- **OPCIONAL**: `optional_tracking_ref` - Referencia adicional
- **OPCIONAL**: Dimensiones (se pueden pre-llenar desde `package_type_id`)

#### Paso 1.4: Configurar Líneas de Recepción
- Cada línea puede tener un `box_number` para agrupar productos en el mismo paquete
- **NECESARIO**: Al menos una línea con `product_uom_qty > 0`
- Se calcula automáticamente el peso total del paquete (productos + peso base del tipo)

#### Paso 1.5: Crear Recepción
- Acción: `action_new_reception()`
- **Validaciones**:
  - Tipo de paquete existe
  - Referencia de seguimiento internacional existe
  - Fecha programada existe
  - Hay al menos una línea de recepción
- **Crea**:
  - `stock.picking` en estado `confirmed`
  - `stock.quant.package` (uno por cada `box_number` único)
  - `stock.move` para cada producto
  - `stock.move.line` asociadas a paquetes según `box_number`

---

### Recepción de Paquetes (Input)

#### Paso 2.1: Confirmar Picking
- **NECESARIO**: `picking.action_confirm()`
- Prepara las reservas de stock
- Estado: `draft` → `confirmed`

#### Paso 2.2: Asignar Stock
- **NECESARIO**: `picking.action_assign()`
- Reserva el stock en la ubicación origen
- Estado: `confirmed` → `assigned`

#### Paso 2.3: Validar Picking
- **NECESARIO**: `picking.button_validate()`
- Valida la recepción
- Estado: `assigned` → `done`
- **Acciones automáticas**:
  - Asigna `user_id` si no está asignado
  - Actualiza estado de paquetes a `done`
  - Desempaqueta pickings de QC
  - Crea automáticamente picking de QC mediante push rules

**Alternativa: Recepción por Escaneo**

#### Paso 2A.1: Escanear Paquete
- Escanear `carrier_tracking_ref`, `global_tracking_ref` o `name` del paquete
- El sistema busca paquetes en estados: `on_hold`, `planned`, `in_progress`

#### Paso 2A.2: Revisar Información
- Se carga automáticamente información del paquete
- **OPCIONAL**: Seleccionar receptor
- **OPCIONAL**: Capturar imágenes

#### Paso 2A.3: Confirmar Recepción
- Acción: `action_confirm()`
- Valida automáticamente el picking asociado
- Adjunta imágenes al paquete
- Vuelve a abrir wizard para siguiente paquete

---

### Control de Calidad (QC)

#### Paso 3.1: Confirmar Picking de QC
- **NECESARIO**: `qc_picking.action_confirm()`
- Estado: `draft` → `confirmed`
- Nota: El picking se crea automáticamente al validar recepción

#### Paso 3.2: Asignar Stock
- **NECESARIO**: `qc_picking.action_assign()`
- Estado: `confirmed` → `assigned`

#### Paso 3.3: Procesar Productos
- **OPCIONAL pero RECOMENDADO**: Usar código de barras para escanear productos
- Para productos con `tracking = 'serial'`:
  - **NECESARIO**: Crear números de serie
  - Se pueden generar automáticamente con wizard de generación de seriales
  - Formato: `{package_name}-{sequence}` (ej: `ABC123-001`, `ABC123-002`)
  - Si no hay paquete: usa `default_code` o primeros 10 caracteres del nombre

#### Paso 3.4: Control de Calidad
- **OPCIONAL**: Se generan checks de calidad automáticamente
- **OPCIONAL**: Realizar inspección visual
- **OPCIONAL**: Verificar productos contra albarán
- **OPCIONAL**: Documentar daños
- Si falla:
  - Se crea alerta de calidad
  - Se notifica al cliente
  - Se puede especificar ubicación de fallo

#### Paso 3.5: Validar Picking de QC
- **NECESARIO**: `qc_picking.button_validate()`
- Estado: `assigned` → `done`
- Marca paquetes originales como `done`
- Crea automáticamente picking de almacenamiento

---

### Almacenamiento (Store)

#### Paso 4.1: Confirmar Picking de Almacenamiento
- **NECESARIO**: `store_picking.action_confirm()`
- Estado: `draft` → `confirmed`
- Nota: El picking se crea automáticamente al validar QC

#### Paso 4.2: Asignar Stock
- **NECESARIO**: `store_picking.action_assign()`
- Estado: `confirmed` → `assigned`

#### Paso 4.3: Validar Picking de Almacenamiento
- **NECESARIO**: `store_picking.button_validate()`
- Estado: `assigned` → `done`
- Requiere confirmación de escaneo
- Los productos quedan en ubicación de stock final

---

## Pasos Opcionales vs Necesarios

### Pasos OBLIGATORIOS (Necesarios)

#### Creación de Recepción
- ✅ Seleccionar productos con mismo `account_partner_id`
- ✅ Especificar `package_type_id`
- ✅ Especificar `global_tracking_ref`
- ✅ Especificar `scheduled_date`
- ✅ Tener al menos una línea de recepción con cantidad > 0

#### Recepción (Input)
- ✅ `action_confirm()` - Botón **"Mark as Todo"** - Confirmar picking
- ✅ `action_assign()` - Botón **"Check Availability"** - Asignar stock
- ✅ `button_validate()` - Botón **"Validate"** - Validar recepción

#### Control de Calidad (QC)
- ✅ `action_confirm()` - Botón **"Mark as Todo"** - Confirmar picking
- ✅ `action_assign()` - Botón **"Check Availability"** - Asignar stock
- ✅ Para productos `tracking = 'serial'`: Crear números de serie
- ✅ `button_validate()` - Botón **"Validate"** - Validar QC

#### Almacenamiento (Store)
- ✅ `action_confirm()` - Botón **"Mark as Todo"** - Confirmar picking
- ✅ `action_assign()` - Botón **"Check Availability"** - Asignar stock
- ✅ `button_validate()` - Botón **"Validate"** - Validar almacenamiento

### Pasos OPCIONALES (No Necesarios)

#### Creación de Recepción
- ⚪ `carrier_name` - Nombre del transportista
- ⚪ `carrier_id` - Transportista
- ⚪ `optional_tracking_ref` - Referencia adicional
- ⚪ Dimensiones del paquete (se pueden pre-llenar)

#### Recepción (Input)
- ⚪ Usar wizard de recepción por escaneo (alternativa a validación manual)
- ⚪ Seleccionar receptor específico
- ⚪ Capturar imágenes del paquete

#### Control de Calidad (QC)
- ⚪ Realizar inspección visual
- ⚪ Completar checks de calidad (se generan automáticamente pero son opcionales)
- ⚪ Verificar productos contra albarán
- ⚪ Documentar daños
- ⚪ Re-empaquetar productos (opcional según configuración)

#### Almacenamiento (Store)
- ⚪ No hay pasos opcionales adicionales

---

## Gestión de Paquetes

### Estados de Paquetes
- `on_hold` - En espera
- `planned` - Planificado
- `in_progress` - En proceso
- `done` - Completado

### Transiciones de Estado
1. **Creación**: Estado inicial según configuración (generalmente `planned` o `in_progress`)
2. **Recepción validada**: Estado → `done` (automático al validar picking de recepción)
3. **QC validado**: Paquetes originales marcados como `done` (desde `origin_package_id`)

### Desempaquetado
- **Cuándo**: Automáticamente al validar picking de recepción
- **Qué hace**:
  - Guarda `package_id` en `origin_package_id` (trazabilidad)
  - Limpia `package_id` y `result_package_id` (permite movimiento libre)
  - Desempaqueta físicamente los paquetes
- **Por qué**: Permite inspección individual de productos en QC

### Trazabilidad de Paquetes
- `package_id` - Paquete actual (se limpia en QC)
- `result_package_id` - Paquete de destino (se limpia en QC)
- `origin_package_id` - Paquete original (se mantiene para trazabilidad)

---

## Control de Calidad

### Punto de Control de Calidad
- **Nombre**: "Quality Control - Reception Inspection"
- **Tipo**: Pass/Fail
- **Frecuencia**: Todos los movimientos (`all`)
- **Medición sobre**: `move_line`

### Proceso de Control
1. Se generan checks automáticamente al procesar productos en QC
2. **OPCIONAL**: Realizar inspección
3. **OPCIONAL**: Marcar como Pass/Fail
4. **Si falla el control de calidad**:
   - Se ejecuta automáticamente el método `confirm_fail()` del wizard
   - Se crea `quality.alert` con estado **"QC Failed"** (`stock_reception.quality_alert_stage_qc_failed`)
   - La alerta se asocia automáticamente a:
     - `picking_id` - Picking de QC donde falló
     - `product_id` - Producto que falló
     - `product_tmpl_id` - Plantilla del producto
     - `lot_id` - Lote/Serial (si aplica)
     - `check_id` - Check de calidad que falló
     - `account_partner_id` - Cuenta del cliente
     - `partner_id` - Partner del cliente
     - `user_id` - Usuario que realizó el check
     - `team_id` - Equipo de calidad
     - `company_id` - Compañía
   - **Título de la alerta**: `"{check_name} failed - {account_name}"`
   - **Descripción**: Combina `note` y `additional_note` del wizard
   - Se notifica al `partner_id` del cliente mediante mensaje en el chatter con:
     - Asunto: "Quality check failed"
     - Detalles: picking, producto, lote/serial, cantidad fallida, ubicación de fallo
   - Se envía notificación al sistema (si está instalado `portal.user.notification`) a todos los usuarios activos del portal asociados al cliente con:
     - Icono: `exclamation-triangle`
     - Mensaje: "QC failed on {package} | {product} | Lot: {lot} | Qty: {qty} | Note: {note}"
   - **El proceso continúa**: Los productos que pasan QC se validan normalmente y continúan al almacenamiento
   - Los productos que fallan pueden moverse a una ubicación de fallo si se especifica en el wizard

### Alertas de Calidad
- Se crean automáticamente cuando un check falla mediante `quality.check.wizard.confirm_fail()`
- **Estado inicial**: "QC Failed" (`stock_reception.quality_alert_stage_qc_failed`)
- **Información incluida**:
  - Información del picking (`picking_id`)
  - Producto que falló (`product_id`, `product_tmpl_id`)
  - Lote/Serial (`lot_id`)
  - Cantidad fallida (del wizard: `qty_failed` o `qty_line`)
  - Ubicación de fallo (`failure_location_id` del wizard)
  - Notas del operador (`note` y `additional_note`)
  - Usuario que realizó el check (`user_id`)
  - Equipo de calidad (`team_id`)
  - Cuenta del cliente (`account_partner_id`)
- **Notificaciones automáticas**:
  - Mensaje en el chatter del partner del cliente
  - Notificación del sistema a usuarios del portal (si está instalado)
- **Seguimiento**: La alerta queda disponible para gestión desde el módulo de reparaciones (`portal_repair`)

---

## Casos Especiales

### Productos sin Tracking (`tracking = 'none'`)
- No requieren creación de lotes/seriales
- Se procesan directamente en QC
- No hay generación automática de números de serie

### Productos con Serial (`tracking = 'serial'`)
- **NECESARIO**: Crear números de serie en QC
- Se pueden generar automáticamente con wizard
- Formato: `{package_name}-{sequence}` o `{default_code}-{sequence}`
- Si no hay paquete: usa `default_code` o primeros 10 caracteres del nombre

### Recepción sin Paquete
- Si no hay paquete asociado, se usa `default_code` del producto
- Si no hay `default_code`, se usan los primeros 10 caracteres del nombre
- Formato de serial: `{default_code}-001`, `{default_code}-002`, etc.

### Fallo en Control de Calidad

**Situación**: Un producto falla el control de calidad durante la fase QC.

**Comportamiento**:
1. **Creación de Alerta**:
   - Se crea automáticamente una `quality.alert` con estado **"QC Failed"**
   - La alerta se asocia al picking, producto, lote/serial, y cuenta del cliente
   - Se incluyen todas las notas del operador

2. **Notificaciones**:
   - **Mensaje al cliente**: Se envía mensaje automático al `partner_id` del cliente en el chatter con todos los detalles del fallo
   - **Notificación del sistema**: Si está instalado `portal.user.notification`, se envía notificación a todos los usuarios activos del portal asociados al cliente

3. **Continuación del Proceso**:
   - **Los productos que pasan QC**: Se validan normalmente y continúan al almacenamiento
   - **Los productos que fallan**: Se pueden mover a una ubicación de fallo si se especifica en el wizard de calidad
   - El picking de QC se puede validar incluso si hay productos que fallan (solo los que pasan continúan)

4. **Gestión de la Alerta**:
   - La alerta queda disponible en el módulo de reparaciones (`portal_repair`)
   - El cliente puede ver la alerta desde su portal
   - Se puede gestionar el seguimiento y resolución de la alerta

**Solución**:
- Revisar la alerta creada para entender el problema
- El cliente recibe notificación automática del fallo
- Los productos que pasan QC continúan normalmente
- Los productos fallidos se pueden gestionar desde la alerta de calidad

### Errores en la Creación de Recepción (Wizard)

**Situación**: Errores al crear una recepción desde el wizard.

**Errores Posibles**:

1. **Productos sin `account_partner_id`**:
   - **Error**: `"No partners found associated with the selected products."`
   - **Causa**: Los productos seleccionados no tienen `account_partner_id` asociado
   - **Solución**: Asociar los productos a un `account.partner` antes de crear la recepción

2. **Productos con diferentes `account_partner_id`**:
   - **Error**: `"The selected products have different associated partners. They must be the same."`
   - **Causa**: Se seleccionaron productos de diferentes cuentas de cliente
   - **Solución**: Seleccionar solo productos del mismo `account.partner`

3. **Falta tipo de paquete**:
   - **Error**: `"Please select a package type."`
   - **Causa**: No se seleccionó `package_type_id` en el wizard
   - **Solución**: Seleccionar un tipo de paquete antes de crear la recepción

4. **Falta referencia de seguimiento**:
   - **Error**: `"Please introduce a carrier_tracking_ref."`
   - **Causa**: No se especificó `global_tracking_ref` en el wizard
   - **Solución**: Introducir la referencia de seguimiento internacional

5. **Falta fecha programada**:
   - **Error**: `"Please enter a scheduled date."`
   - **Causa**: No se especificó `scheduled_date` en el wizard
   - **Solución**: Introducir la fecha programada de recepción

6. **Sin líneas de recepción**:
   - **Error**: `"Please add at least one reception line."`
   - **Causa**: No hay líneas de recepción o todas fueron eliminadas
   - **Solución**: Agregar al menos una línea con cantidad > 0

**Validación**: Todas estas validaciones se ejecutan en `_check_reception_information()` antes de crear la recepción.

### Errores en la Recepción por Escaneo

**Situación**: Errores al recibir un paquete mediante el wizard de escaneo.

**Errores Posibles**:

1. **Paquete no encontrado**:
   - **Causa**: El código escaneado no coincide con ningún paquete en estados `on_hold`, `planned`, o `in_progress`
   - **Solución**: 
     - Verificar que el código escaneado es correcto
     - Verificar que el paquete existe y está en un estado válido
     - Verificar que se está buscando por `carrier_tracking_ref`, `global_tracking_ref`, o `name`

2. **Paquete ya recibido**:
   - **Causa**: El paquete está en estado `done` (ya fue recibido)
   - **Solución**: Verificar el estado del paquete antes de intentar recibirlo

3. **Picking no encontrado**:
   - **Causa**: No hay `stock.move.line` asociada al paquete
   - **Solución**: Verificar que el paquete está correctamente asociado a un picking de recepción

**Validación**: El wizard busca paquetes en estados válidos y carga automáticamente la información si se encuentra.

### Errores en la Validación de Pickings

**Situación**: Errores al validar un picking (botón **"Validate"**).

**Errores Posibles**:

1. **Líneas no escaneadas** (si `require_scan_confirmation = True`):
   - **Error**: `"The following products have not been scanned/confirmed: [lista de productos]... Please scan or confirm all products before validating."`
   - **Causa**: Hay líneas de movimiento con demanda pero que no han sido escaneadas/confirmadas (`picked = False`)
   - **Solución**: 
     - Escanear todos los productos requeridos
     - Confirmar todas las líneas antes de validar
     - Verificar que todas las líneas tienen `picked = True`

2. **Faltan números de serie** (para productos con `tracking = 'serial'`):
   - **Error**: Se muestra wizard de generación de seriales
   - **Causa**: Hay líneas con productos `tracking = 'serial'` que no tienen `lot_id` ni `lot_name`
   - **Solución**: 
     - Generar seriales automáticamente usando el wizard
     - O introducir manualmente los números de serie
     - Verificar que todos los productos con tracking tienen serial asignado

3. **Validaciones estándar de Odoo**:
   - **Cantidades incorrectas**: Las cantidades en `stock.move.line` no coinciden con las esperadas
   - **Ubicaciones inválidas**: Las ubicaciones origen/destino no son válidas
   - **Stock insuficiente**: No hay stock disponible en la ubicación origen (para movimientos internos/salidas)
   - **Solución**: Revisar y corregir las cantidades, ubicaciones y stock antes de validar

**Validación**: Estas validaciones se ejecutan en `_pre_action_done_hook()` y `_check_missing_lots()` antes de validar el picking.

### Errores en la Generación de Seriales

**Situación**: Errores al generar números de serie automáticamente.

**Errores Posibles**:

1. **Producto sin `default_code` ni nombre**:
   - **Causa**: El producto no tiene `default_code` y el nombre está vacío
   - **Solución**: Asignar `default_code` o nombre al producto antes de generar seriales

2. **Paquete sin nombre**:
   - **Causa**: No hay paquete asociado y el producto no tiene `default_code`
   - **Solución**: Asociar un paquete o asignar `default_code` al producto

3. **Productos excluidos** (si hay módulos que extienden):
   - **Causa**: Algunos productos pueden estar excluidos de generación automática (ej: productos IMEI)
   - **Solución**: Introducir manualmente los seriales para productos excluidos

**Validación**: El wizard solo genera seriales para productos con `tracking = 'serial'` que no tienen `lot_id` ni `lot_name` y no están excluidos.

### Errores en el Desempaquetado

**Situación**: Errores al desempaquetar productos después de la recepción.

**Errores Posibles**:

1. **Paquete no encontrado**:
   - **Causa**: El paquete asociado a las líneas de movimiento no existe
   - **Solución**: Verificar que los paquetes están correctamente asociados antes de validar la recepción

2. **Error al desempaquetar**:
   - **Causa**: Error al ejecutar `package.unpack()`
   - **Solución**: Verificar que el paquete existe y tiene estado válido

**Validación**: El desempaquetado se ejecuta automáticamente al validar el picking de recepción si hay paquetes asociados.

### Errores en la Creación de Pickings Siguientes

**Situación**: Errores al crear pickings de QC o Store automáticamente.

**Errores Posibles**:

1. **Push rules no configuradas**:
   - **Causa**: No hay push rules configuradas para crear pickings siguientes
   - **Solución**: Verificar configuración de rutas y push rules en el almacén

2. **Ubicaciones no configuradas**:
   - **Causa**: Las ubicaciones de QC o Store no están configuradas en el almacén
   - **Solución**: Verificar configuración de almacén con recepción en 3 pasos

3. **Grupo de procuración incorrecto**:
   - **Causa**: El `procurement.group` no está correctamente asociado
   - **Solución**: Verificar que el picking tiene un `group_id` válido

**Validación**: Los pickings siguientes se crean automáticamente mediante push rules cuando se valida el picking anterior.

### Múltiples Paquetes en una Recepción
- Se pueden crear múltiples paquetes usando `box_number` en las líneas
- Cada paquete se procesa independientemente
- Todos los paquetes deben validarse en recepción antes de pasar a QC

---

## Resumen de Procesos que Pueden Fallar

### Tabla de Errores Comunes

| Fase | Proceso | Error Posible | Causa | Solución |
|------|---------|---------------|-------|----------|
| **FASE 1** | Creación de recepción | Productos sin `account_partner_id` | Productos no asociados a cuenta | Asociar productos a `account.partner` |
| **FASE 1** | Creación de recepción | Productos con diferentes `account_partner_id` | Productos de diferentes cuentas | Seleccionar solo productos de la misma cuenta |
| **FASE 1** | Creación de recepción | Falta tipo de paquete | No se seleccionó `package_type_id` | Seleccionar tipo de paquete |
| **FASE 1** | Creación de recepción | Falta tracking ref | No se especificó `global_tracking_ref` | Introducir referencia de seguimiento |
| **FASE 1** | Creación de recepción | Falta fecha programada | No se especificó `scheduled_date` | Introducir fecha programada |
| **FASE 1** | Creación de recepción | Sin líneas de recepción | No hay líneas o todas fueron eliminadas | Agregar al menos una línea con cantidad > 0 |
| **FASE 2** | Recepción por escaneo | Paquete no encontrado | Código no coincide o paquete en estado incorrecto | Verificar código y estado del paquete |
| **FASE 2** | Recepción por escaneo | Paquete ya recibido | Paquete en estado `done` | Verificar estado del paquete |
| **FASE 2** | Recepción por escaneo | Picking no encontrado | No hay `stock.move.line` asociada | Verificar asociación del paquete |
| **FASE 3** | Validación de picking QC | Líneas no escaneadas | `require_scan_confirmation = True` y líneas sin escanear | Escanear todos los productos |
| **FASE 3** | Validación de picking QC | Faltan números de serie | Productos `tracking = 'serial'` sin serial | Generar o introducir seriales |
| **FASE 3** | Control de calidad | Fallo en QC | Producto no pasa inspección | Se crea alerta automáticamente |
| **FASE 4** | Validación de picking Store | Líneas no escaneadas | `require_scan_confirmation = True` y líneas sin escanear | Escanear todos los productos |
| **FASE 4** | Validación de picking Store | Validaciones estándar | Cantidades, ubicaciones o stock incorrectos | Revisar y corregir datos |
| **General** | Generación de seriales | Producto sin `default_code` | No hay código ni nombre para generar serial | Asignar `default_code` o nombre |
| **General** | Desempaquetado | Paquete no encontrado | Paquete no existe o estado inválido | Verificar paquetes asociados |
| **General** | Creación de pickings siguientes | Push rules no configuradas | No hay rutas configuradas | Verificar configuración de almacén |

### Guía Rápida de Solución de Problemas

1. **Error al crear recepción**: Verificar que todos los campos obligatorios están completos y que los productos tienen el mismo `account_partner_id`
2. **Error al escanear paquete**: Verificar que el código es correcto y que el paquete está en estado válido (`on_hold`, `planned`, `in_progress`)
3. **Error al validar picking**: Verificar que todas las líneas están escaneadas (si aplica) y que los productos con tracking tienen seriales
4. **Error en control de calidad**: Revisar la alerta creada automáticamente y notificar al cliente
5. **Error en generación de seriales**: Verificar que los productos tienen `default_code` o nombre para generar seriales

---

## Resumen de Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CREAR RECEPCIÓN (Portal Cliente)                         │
│    - Seleccionar productos desde portal                     │
│    - Completar wizard (tipo paquete, tracking ref, fecha)  │
│    - Crear picking + paquetes + movimientos                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. RECEPCIÓN (Input) - NECESARIO                           │
│    - Confirmar picking                                      │
│    - Asignar stock                                          │
│    - Validar picking                                        │
│    → Crea automáticamente picking de QC                     │
│    → Desempaqueta productos para QC                        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CONTROL DE CALIDAD (QC) - NECESARIO                     │
│    - Confirmar picking                                      │
│    - Asignar stock                                          │
│    - Crear seriales (si tracking='serial') - NECESARIO    │
│    - Control de calidad - OPCIONAL                          │
│    - Validar picking                                        │
│    → Crea automáticamente picking de almacenamiento         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ALMACENAMIENTO (Store) - NECESARIO                       │
│    - Confirmar picking                                      │
│    - Asignar stock                                          │
│    - Validar picking                                        │
│    → Productos en stock final                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Notas Importantes

1. **El proceso es secuencial**: Cada paso debe completarse antes del siguiente
2. **Los pickings se crean automáticamente**: Mediante push rules de Odoo
3. **Los paquetes se desempaquetan en QC**: Para permitir inspección individual
4. **La trazabilidad se mantiene**: A través de `origin_package_id`
5. **El control de calidad es opcional**: Pero recomendado para garantizar calidad
6. **Los seriales se crean en QC**: No en recepción inicial
7. **Todos los productos deben tener el mismo account_partner_id**: En una recepción

---

## Dependencias entre Módulos

- `stock_reception` depende de `stock_barcode_auto_serial` para generación automática de seriales
- `stock_reception` integra con `quality_control` para checks de calidad
- `stock_reception` usa `package_menu` para gestión de paquetes
- `stock_reception` requiere `logistics_security` para permisos

---

*Documento generado el: 2025-02-09*
*Versión del módulo: 18.0.1.0.0*
