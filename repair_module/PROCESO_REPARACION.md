# Proceso de Reparación de Productos - Repair Module

## Índice
1. [Prerequisitos](#prerequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Proceso de Reparación - Flujo Completo](#proceso-de-reparación---flujo-completo)
4. [Pasos Detallados](#pasos-detallados)
5. [Pasos Opcionales vs Necesarios](#pasos-opcionales-vs-necesarios)
6. [Gestión de Alertas de Calidad](#gestión-de-alertas-de-calidad)
7. [Gestión de Órdenes de Reparación](#gestión-de-órdenes-de-reparación)
8. [Estados y Transiciones](#estados-y-transiciones)
9. [Casos Especiales](#casos-especiales)

---

## Prerequisitos

### Módulos Requeridos
El módulo `repair_module` depende de los siguientes módulos:
- `base` - Base de Odoo
- `client_account` - Gestión de cuentas de cliente
- `repair` - Módulo base de reparaciones de Odoo
- `stock_expedition` - Módulo de expediciones
- `stock_reception` - Módulo de recepciones
- `logistics_security` - Seguridad logística
- `stock_internal` - Movimientos internos

### Configuraciones del Sistema
No se requieren configuraciones especiales del sistema. El módulo funciona con la configuración estándar.

### Configuración de Ubicaciones
El módulo crea automáticamente las siguientes ubicaciones:
- **Repairs** (`repair_module.stock_location_repairs`) - Ubicación para productos en reparación
- **Stock to Relocate** (`repair_module.stock_location_to_relocate`) - Ubicación para productos reparados pendientes de reubicación
- **Scrap** (`repair_module.stock_location_scrap`) - Ubicación para productos desechados

### Configuración de Tipos de Operación

#### 1. Tipo de Operación: Move to Repair
- **Código**: `internal`
- **Secuencia**: `MVREP`
- **Barcode**: `move_repair`
- **Ubicación origen**: Stock (`stock.stock_location_stock`)
- **Ubicación destino**: Repairs (`repair_module.stock_location_repairs`)
- **Configuración**:
  - `use_create_lots`: **False** - No crear lotes
  - `allowed_location_dest_ids`: Solo ubicación Repairs
  - `create_backorder`: **never** - No crear backorders

**Propósito**: Mover productos desde Stock a la ubicación de Reparaciones.

#### 2. Tipo de Operación: Return from Repair
- **Código**: `internal`
- **Secuencia**: `RETREP`
- **Barcode**: `return_repair`
- **Ubicación origen**: Repairs (`repair_module.stock_location_repairs`)
- **Ubicación destino**: Stock to Relocate (`repair_module.stock_location_to_relocate`)
- **Configuración**:
  - `use_create_lots`: **False** - No crear lotes
  - `restrict_scan_tracking_number`: **mandatory** - Escaneo obligatorio de número de tracking
  - `restrict_scan_dest_location`: **mandatory** - Escaneo obligatorio de ubicación destino
  - `allowed_location_ids`: Solo ubicación Repairs
  - `create_backorder`: **never** - No crear backorders

**Propósito**: Devolver productos desde Reparaciones a Stock después de completar la reparación.

#### 3. Tipo de Operación: Review
- **Código**: `repair_operation`
- **Secuencia**: `REV` (RVW)
- **Barcode**: `review_operation`
- **Ubicación producto origen**: Repairs
- **Ubicación producto destino**: Stock
- **Ubicación componentes origen**: Stock
- **Ubicación componentes destino**: Stock

**Propósito**: Revisión de productos (no reparación completa).

#### 4. Tipo de Operación: Repair (modificado)
- **Código**: `repair_operation`
- **Secuencia**: `REP`
- **Ubicación producto origen**: Repairs
- **Ubicación componentes origen**: Stock
- **Ubicación componentes destino**: Stock

**Propósito**: Reparación completa de productos.

### Datos Requeridos

#### Alertas de Calidad (Quality Alert)
- Las alertas deben tener:
  - `product_id` - Producto a reparar
  - `account_partner_id` - Cuenta del cliente (obligatorio)
  - `quantity` - Cantidad (debe ser > 0)
  - `lot_id` - Lote/Serial (si el producto tiene tracking)
  - `is_repair` - Marcado como True para reparaciones
  - `maintenance_type` - Tipo de mantenimiento (repair, review, warranty, renew)

#### Productos
- Los productos pueden tener:
  - `tracking = 'none'` - Sin seguimiento de lote/serial
  - `tracking = 'serial'` - Con seguimiento de número de serie
  - **NO se usa** `tracking = 'lot'` en este sistema

#### Órdenes de Reparación (Repair Order)
- Las órdenes deben tener:
  - `product_id` - Producto a reparar
  - `account_partner_id` - Cuenta del cliente
  - `repair_alert_id` - Alerta de calidad asociada
  - `technician_id` - Técnico asignado (obligatorio para validar)
  - `maintenance_type` - Tipo de mantenimiento
  - `lifecycle_state` - Estado del ciclo de vida (obligatorio para productos con serial)

---

## Configuración Inicial

### 1. Etapas de Alerta de Calidad
Se crean automáticamente las siguientes etapas:
- **In Transit (Reception)** - En tránsito desde recepción
- **In Warehouse** - En almacén (estado inicial)
- **Sent for Review / Repair** - Enviado para revisión/reparación
- **Repairing** - En reparación
- **Return to After-Sales** - Devuelto a postventa
- **Sent to client** - Enviado al cliente
- **Sent for Recycling** - Enviado para reciclaje
- **Repair Cancelled** - Reparación cancelada

### 2. Equipos de Calidad
- Se debe configurar un equipo de calidad (`quality.alert.team`)
- El líder del equipo se asigna automáticamente como responsable si no se especifica `user_id`

### 3. Usuarios y Permisos
- **Técnicos de reparación**: Deben pertenecer al grupo `logistics_security.group_repair_user`
- **Gestores de reparación**: Deben pertenecer al grupo `logistics_security.group_repair_manager`
- **Responsables**: Solo usuarios del departamento de After Sales pueden ser asignados

---

## Proceso de Reparación - Flujo Completo

El proceso de reparación sigue un flujo que comienza con una alerta de calidad y termina con la devolución del producto al stock.

```
Alerta de Calidad → Mover a Reparación → Crear Orden → Asignar Técnico → Reparar → Finalizar → Devolver a Stock
```

### Resumen del Flujo

1. **FASE 1: Creación de Alerta de Calidad** (Portal o QC)
   - Se crea `quality.alert` desde el portal o por fallo en QC
   - Estado inicial: "In Warehouse"

2. **FASE 2: Mover a Reparación** (Backend)
   - Crear picking de traslado interno
   - Mover producto desde Stock a Repairs
   - Validar picking
   - → Cambia estado de alerta a "Sent for Review / Repair"
   - → Crea automáticamente `repair.order`

3. **FASE 3: Asignar Técnico y Validar Orden** (Backend)
   - Asignar técnico a la orden
   - Validar orden
   - → Cambia estado de alerta a "Confirmed"

4. **FASE 4: Iniciar Reparación** (Backend)
   - Iniciar reparación
   - → Cambia estado de alerta a "Repairing"
   - → Cambia estado de orden a "Under Repair"

5. **FASE 5: Completar Reparación** (Backend)
   - Registrar diagnóstico y resultados
   - Asignar estado de ciclo de vida
   - Finalizar reparación
   - → Cambia estado de alerta a "Return to After-Sales"
   - → Crea picking de retorno desde Repairs a Stock

6. **FASE 6: Devolver a Stock** (Backend)
   - Validar picking de retorno
   - → Producto devuelto a Stock to Relocate

---

## Pasos Detallados

### **FASE 1: Creación de Alerta de Calidad**

**⚠️ IMPORTANTE**: Esta fase puede realizarse desde el **portal del cliente** (`portal_repair`) o automáticamente cuando **falla el control de calidad** en recepción.

**Método 1: Desde Portal del Cliente**
- **Acceso**: Portal del cliente → Menú **"SAT"** → Botón **"Crear Alerta de Reparación"**
- **Ruta**: `/account/repair-alert/create` (JSON)
- Se crea `quality.alert` con `is_repair = True`

**Método 2: Desde Fallo en Control de Calidad**
- **Acceso**: Automático cuando falla QC en recepción
- Se crea `quality.alert` con estado "QC Failed"
- Se notifica al cliente automáticamente

**Información Requerida**:
- **OBLIGATORIO**: `product_id` - Producto a reparar
- **OBLIGATORIO**: `account_partner_id` - Cuenta del cliente
- **OBLIGATORIO**: `quantity` - Cantidad (debe ser > 0)
- **OBLIGATORIO**: Para productos con `tracking = 'serial'`: `lot_id` - Lote/Serial
- **OBLIGATORIO**: Para productos con `tracking = 'none'`: `location_id` - Ubicación con stock
- **OPCIONAL**: `title` - Título de la alerta
- **OPCIONAL**: `description` - Descripción del problema
- **OPCIONAL**: `maintenance_type` - Tipo de mantenimiento

**Estado Inicial**: "In Warehouse" (`repair_module.quality_alert_stage_received`)

**Nota**: Si no se especifica `user_id`, se asigna automáticamente el líder del equipo de calidad.

---

### **FASE 2: Mover a Reparación**

**⚠️ IMPORTANTE**: Esta fase debe realizarse desde el **backend de Odoo**.

**Método**: `quality.alert.action_create_move_to_repair()`

**Acceso**: Backend Odoo → Calidad → Alertas de Calidad → Seleccionar alerta → Botón **"Create Move to Repair"**

**Pasos**:
1. Abrir la alerta de calidad en estado "In Warehouse"
2. Verificar información:
   - Producto
   - Cantidad
   - Lote/Serial (si aplica)
   - Ubicación con stock disponible
3. Crear movimiento a reparación (`action_create_move_to_repair()`)
   - El sistema crea automáticamente:
     - `stock.picking` de tipo "Move to Repair"
     - `stock.move` para el producto
     - `stock.move.line` con cantidad reservada
     - Asocia el picking a la alerta

4. **Confirmar picking** (`action_confirm()`) - Botón **"Mark as Todo"**
   - Reserva el stock en la ubicación origen

5. **Asignar stock** (`action_assign()`) - Botón **"Check Availability"**
   - Reserva productos específicos

6. **Validar picking** (`button_validate()`) - Botón **"Validate"**
   - Mueve productos desde Stock a Repairs
   - → Cambia estado de alerta a **"Sent for Review / Repair"**
   - → Crea automáticamente `repair.order` si `maintenance_type` está configurado

**Validaciones**:
- La cantidad debe ser > 0
- Debe haber stock disponible en la ubicación origen
- Para productos con tracking, debe existir el lote/serial
- Debe haber `account_partner_id` asociado

**Nota**: Si el picking tiene `maintenance_type` configurado, se crea automáticamente el `repair.order` al validar el picking.

---

### **FASE 3: Asignar Técnico y Validar Orden**

**⚠️ IMPORTANTE**: Esta fase debe realizarse desde el **backend de Odoo**.

**Método**: `repair.order.action_validate()`

**Acceso**: Backend Odoo → Reparaciones → Órdenes de Reparación

**Pasos**:
1. Abrir la orden de reparación en estado `draft`
2. **OBLIGATORIO**: Asignar técnico (`technician_id`)
   - Solo usuarios del grupo `logistics_security.group_repair_user` o `logistics_security.group_repair_manager`
   - Se puede asignar individualmente o en lote usando wizard
3. **OPCIONAL**: Completar información adicional:
   - `maintenance_type` - Tipo de mantenimiento (si no está configurado)
   - `description` - Descripción del problema
   - `schedule_date` - Fecha programada
4. Validar orden (`action_validate()`) - Botón **"Confirm Repair"**
   - **Validación**: Debe haber técnico asignado
   - → Cambia estado de orden a `confirmed`
   - → Cambia estado de alerta a "Confirmed" (`quality.quality_alert_stage_2`)
   - → Registra fecha y usuario de asignación
   - → Publica mensaje en el chatter

**Validaciones**:
- El técnico es obligatorio antes de validar
- El técnico debe pertenecer al grupo de reparaciones

**Nota**: Se puede asignar técnico en lote usando el wizard `repair.technician.set` desde la vista de lista.

---

### **FASE 4: Iniciar Reparación**

**⚠️ IMPORTANTE**: Esta fase debe realizarse desde el **backend de Odoo**.

**Método**: `repair.order.action_repair_start()`

**Acceso**: Backend Odoo → Reparaciones → Órdenes de Reparación

**Pasos**:
1. Abrir la orden de reparación en estado `confirmed`
2. **OPCIONAL**: Agregar componentes/piezas necesarias
3. Iniciar reparación (`action_repair_start()`) - Botón **"Start Repair"**
   - → Cambia estado de orden a `under_repair`
   - → Cambia estado de alerta a **"Repairing"** (`repair_module.quality_alert_stage_repairing`)
   - → Registra fecha y usuario de inicio

**Nota**: El técnico puede agregar componentes y realizar la reparación física en este estado.

---

### **FASE 5: Completar Reparación**

**⚠️ IMPORTANTE**: Esta fase debe realizarse desde el **backend de Odoo**.

**Método**: `repair.order.action_repair_end()`

**Acceso**: Backend Odoo → Reparaciones → Órdenes de Reparación

**Pasos**:
1. Abrir la orden de reparación en estado `under_repair`
2. **OPCIONAL**: Registrar diagnóstico (`diagnosis_ids`)
   - Seleccionar diagnósticos desde la lista disponible
   - Se pueden seleccionar múltiples diagnósticos
3. **OPCIONAL**: Registrar resultados (`result_ids`)
   - Seleccionar resultados desde la lista disponible
   - Se pueden seleccionar múltiples resultados
4. **OBLIGATORIO** (para productos con `tracking = 'serial'`): Asignar estado de ciclo de vida (`lifecycle_state`)
   - Estados disponibles:
     - `E` - E-Standby
     - `A` - A-New
     - `B` - B-Seminew
     - `C` - C-Repair
     - `D` - D-Scrap
     - `CR` - CR-Repair in review
5. Finalizar reparación (`action_repair_end()`) - Botón **"End Repair"**
   - **Validación**: Para productos con `tracking = 'serial'`, el `lifecycle_state` no puede ser `E` (debe ser diferente)
   - → Cambia estado de orden a `ready`
   - → Cambia estado de alerta a **"Return to After-Sales"** (`repair_module.quality_alert_stage_sent_to_postsale`)
   - → Registra fecha y usuario de finalización
   - → Si hay `lot_id`, actualiza el lote:
     - `diagnosis_ids` - Diagnósticos
     - `result_ids` - Resultados
     - `lifecycle_state` - Estado de ciclo de vida

**Validaciones**:
- Para productos con `tracking = 'serial'`, el `lifecycle_state` es obligatorio y no puede ser `E`
- El `lifecycle_state` se propaga al lote/serial asociado

**Nota**: Los diagnósticos y resultados se guardan tanto en la orden como en el lote/serial (si aplica).

---

### **FASE 6: Completar Orden y Devolver a Stock**

**⚠️ IMPORTANTE**: Esta fase debe realizarse desde el **backend de Odoo**.

**Método**: `repair.order.action_repair_done()`

**Acceso**: Backend Odoo → Reparaciones → Órdenes de Reparación

**Pasos**:
1. Abrir la orden de reparación en estado `ready`
2. Completar orden (`action_repair_done()`) - Botón **"End Repair"** (segunda vez)
   - El sistema crea automáticamente:
     - `stock.picking` de tipo "Return from Repair"
     - `stock.move` para devolver el producto
     - `stock.move.line` con cantidad y lote/serial
     - Asocia el picking a la alerta
   - → Cambia estado de orden a `done`
   - → Actualiza líneas de venta si existen

3. **Confirmar picking de retorno** (`action_confirm()`) - Botón **"Mark as Todo"**
   - Reserva el stock en ubicación Repairs

4. **Asignar stock** (`action_assign()`) - Botón **"Check Availability"**
   - Reserva productos en ubicación Repairs

5. **Validar picking de retorno** (`button_validate()`) - Botón **"Validate"**
   - **OBLIGATORIO**: Escanear número de tracking (`restrict_scan_tracking_number = mandatory`)
   - **OBLIGATORIO**: Escanear ubicación destino (`restrict_scan_dest_location = mandatory`)
   - → Mueve productos desde Repairs a Stock to Relocate
   - → Producto disponible para reubicación

**Validaciones**:
- Para productos con `tracking = 'serial'`, debe existir `lot_id`
- Debe haber stock disponible en ubicación Repairs
- El escaneo de tracking y ubicación destino son obligatorios

**Nota**: El producto queda en "Stock to Relocate" para ser reubicado a su ubicación final.

---

## Pasos Opcionales vs Necesarios

| Fase | Paso | Necesario | Descripción |
|------|------|-----------|-------------|
| **FASE 1** | Crear alerta desde portal | ⚠️ **OPCIONAL** | Si se crea desde portal |
| **FASE 1** | Crear alerta desde QC fallido | ⚠️ **OPCIONAL** | Si falla control de calidad |
| **FASE 1** | Especificar tipo de mantenimiento | ⚠️ **OPCIONAL** | Se puede especificar después |
| **FASE 2** | Crear movimiento a reparación | ✅ **NECESARIO** | Mover producto a Repairs |
| **FASE 2** | Confirmar picking | ✅ **NECESARIO** | Botón **"Mark as Todo"** |
| **FASE 2** | Asignar stock | ✅ **NECESARIO** | Botón **"Check Availability"** |
| **FASE 2** | Validar picking | ✅ **NECESARIO** | Botón **"Validate"** - Crea orden |
| **FASE 3** | Asignar técnico | ✅ **NECESARIO** | Obligatorio antes de validar |
| **FASE 3** | Validar orden | ✅ **NECESARIO** | Botón **"Confirm Repair"** |
| **FASE 4** | Agregar componentes | ⚠️ **OPCIONAL** | Si se necesitan piezas |
| **FASE 4** | Iniciar reparación | ✅ **NECESARIO** | Botón **"Start Repair"** |
| **FASE 5** | Registrar diagnóstico | ⚠️ **OPCIONAL** | Para documentación |
| **FASE 5** | Registrar resultados | ⚠️ **OPCIONAL** | Para documentación |
| **FASE 5** | Asignar lifecycle_state | ✅ **NECESARIO** | Para productos con serial |
| **FASE 5** | Finalizar reparación | ✅ **NECESARIO** | Botón **"End Repair"** |
| **FASE 6** | Completar orden | ✅ **NECESARIO** | Botón **"End Repair"** - Crea picking |
| **FASE 6** | Confirmar picking retorno | ✅ **NECESARIO** | Botón **"Mark as Todo"** |
| **FASE 6** | Asignar stock retorno | ✅ **NECESARIO** | Botón **"Check Availability"** |
| **FASE 6** | Validar picking retorno | ✅ **NECESARIO** | Botón **"Validate"** |

---

## Gestión de Alertas de Calidad

### Creación de Alerta

**Desde Portal**:
- Cliente crea alerta desde `portal_repair`
- Se especifica producto, cantidad, lote/ubicación, descripción del problema

**Desde Fallo en QC**:
- Se crea automáticamente cuando falla control de calidad
- Estado inicial: "QC Failed"
- Se notifica al cliente automáticamente

### Crear Movimiento a Reparación

**Método**: `quality.alert.action_create_move_to_repair(location_id=None)`

**Validaciones**:
- `quantity > 0`
- `product_id` debe existir
- `account_partner_id` debe existir
- Para productos con tracking: `lot_id` debe existir
- Debe haber stock disponible

**Resultado**:
- Crea `stock.picking` de tipo "Move to Repair"
- Reserva stock en ubicación origen
- Asocia picking a la alerta

### Actualización de Pickings

**Situación**: Se modifica producto, lote o cantidad en la alerta.

**Comportamiento**:
- Si hay pickings en estado `done` o `cancel`, no se puede modificar
- Si los pickings son editables, se actualizan automáticamente:
  - `stock.move.product_id`
  - `stock.move.product_uom_qty`
  - `stock.move.line.product_id`
  - `stock.move.line.quantity`
  - `stock.move.line.lot_id` (si aplica)

### Cancelación de Alerta

**Método**: `quality.alert.action_cancel()`

**Comportamiento**:
- Si hay pickings completados o reparaciones, se abre wizard para pedir motivo
- Si no hay pickings/reparaciones, se cancela directamente
- **Acciones automáticas**:
  - Cancela pickings no completados
  - Crea picking de retorno si hay pickings completados (producto ya en Repairs)
  - Cancela reparaciones asociadas
  - Cambia estado a "Repair Cancelled"
  - Publica motivo en el chatter

---

## Gestión de Órdenes de Reparación

### Creación Automática

**Cuándo se crea**:
- Automáticamente al validar picking "Move to Repair" si tiene `maintenance_type` configurado
- O manualmente desde la alerta de calidad

**Información heredada**:
- `account_partner_id` - De la alerta o picking
- `repair_alert_id` - Alerta asociada
- `product_id` - Del picking
- `maintenance_type` - Del picking o alerta
- `description` - De la alerta
- `schedule_date` - De la alerta o fecha por defecto (+7 días)

### Asignación de Técnico

**Método Individual**:
- Seleccionar `technician_id` en el formulario de la orden
- Solo usuarios del grupo de reparaciones

**Método en Lote**:
- Seleccionar múltiples órdenes en la vista de lista
- Usar acción "Set Technician" (wizard `repair.technician.set`)
- Asigna el mismo técnico a todas las órdenes seleccionadas

### Estados de la Orden

1. **Draft** - Borrador (recién creada)
2. **Confirmed** - Confirmada (técnico asignado y validada)
3. **Under Repair** - En reparación (iniciada)
4. **Ready** - Lista (reparación completada, pendiente de finalizar)
5. **Done** - Completada (orden finalizada, picking de retorno creado)
6. **Cancel** - Cancelada

### Transiciones de Estado

- **Draft → Confirmed**: `action_validate()` - Botón **"Confirm Repair"**
- **Confirmed → Under Repair**: `action_repair_start()` - Botón **"Start Repair"**
- **Under Repair → Ready**: `action_repair_end()` - Botón **"End Repair"** (primera vez)
- **Ready → Done**: `action_repair_done()` - Botón **"End Repair"** (segunda vez)

---

## Estados y Transiciones

### Estados de Alerta de Calidad

| Estado | Secuencia | Descripción | Cuándo se Asigna |
|--------|-----------|-------------|------------------|
| **In Transit (Reception)** | 10 | En tránsito desde recepción | Al crear desde recepción |
| **In Warehouse** | 20 | En almacén | Estado inicial por defecto |
| **Sent for Review / Repair** | 30 | Enviado para revisión/reparación | Al validar picking "Move to Repair" |
| **Repairing** | 40 | En reparación | Al iniciar reparación |
| **Return to After-Sales** | 50 | Devuelto a postventa | Al finalizar reparación |
| **Sent to client** | 60 | Enviado al cliente | Manual |
| **Sent for Recycling** | 70 | Enviado para reciclaje | Manual |
| **Repair Cancelled** | 80 | Reparación cancelada | Al cancelar alerta |

### Estados de Ciclo de Vida

| Código | Nombre | Descripción |
|--------|--------|-------------|
| **E** | E-Standby | Standby (estado inicial) |
| **A** | A-New | Nuevo |
| **B** | B-Seminew | Semi-nuevo |
| **C** | C-Repair | Reparado |
| **D** | D-Scrap | Desechado |
| **CR** | CR-Repair in review | Reparación en revisión |

### Tipos de Mantenimiento

| Código | Nombre | Descripción |
|--------|--------|-------------|
| **repair** | Repair | Reparación completa |
| **review** | Review | Revisión |
| **warranty** | Warranty | Garantía |
| **renew** | Renew | Renovación |

---

## Casos Especiales

### 1. Productos sin Tracking

**Situación**: Producto con `tracking = 'none'`.

**Comportamiento**:
- Se debe especificar `location_id` al crear la alerta desde el portal
- El sistema busca stock disponible en esa ubicación
- No se requiere `lot_id`
- No se requiere `lifecycle_state` al finalizar

**Solución**:
- Seleccionar ubicación con stock disponible
- El sistema maneja automáticamente el movimiento

### 2. Productos con Tracking Serial

**Situación**: Producto con `tracking = 'serial'`.

**Comportamiento**:
- Se debe especificar `lot_id` al crear la alerta
- Se requiere `lifecycle_state` al finalizar (no puede ser `E`)
- El `lifecycle_state` se propaga al lote/serial
- Los diagnósticos y resultados se guardan en el lote

**Solución**:
- Seleccionar serial desde la lista disponible
- Asignar estado de ciclo de vida al finalizar
- El sistema preserva toda la información en el lote

### 3. Creación Automática de Orden

**Situación**: El picking "Move to Repair" tiene `maintenance_type` configurado.

**Comportamiento**:
- Al validar el picking, se crea automáticamente `repair.order`
- La orden hereda información del picking y alerta
- Se asocia automáticamente a la alerta

**Solución**:
- Configurar `maintenance_type` en el picking antes de validar
- O crear la orden manualmente después

### 4. Cancelación de Alerta con Pickings Completados

**Situación**: Se cancela una alerta que ya tiene pickings validados (producto en Repairs).

**Comportamiento**:
- Se abre wizard para pedir motivo de cancelación
- Se crea automáticamente picking de retorno desde Repairs a Stock
- Se cancelan reparaciones asociadas
- Se cambia estado a "Repair Cancelled"

**Solución**:
- Proporcionar motivo de cancelación
- El sistema maneja automáticamente el retorno del producto

### 5. Cancelación de Alerta sin Pickings

**Situación**: Se cancela una alerta que no tiene pickings completados.

**Comportamiento**:
- Se cancela directamente sin wizard
- Se cancelan pickings pendientes
- Se cambia estado a "Repair Cancelled"
- No se crea picking de retorno (producto no está en Repairs)

**Solución**:
- Cancelar directamente desde la alerta
- El sistema maneja automáticamente la limpieza

### 6. Modificación de Alerta con Pickings Completados

**Situación**: Se intenta modificar producto, lote o cantidad en una alerta con pickings `done`.

**Comportamiento**:
- Se muestra error: `"No se puede modificar porque hay pickings en estado finalizado o cancelado"`
- No se permite la modificación

**Solución**:
- Cancelar y recrear la alerta si es necesario
- O crear una nueva alerta con la información correcta

### 7. Múltiples Quants Disponibles

**Situación**: Hay múltiples quants del mismo producto en diferentes ubicaciones.

**Comportamiento**:
- Para productos sin tracking: se pueden especificar múltiples ubicaciones
- El sistema toma quants de las ubicaciones especificadas
- Se valida que haya suficiente cantidad total

**Solución**:
- Especificar ubicaciones con stock disponible
- El sistema agrupa automáticamente los quants

### 8. Falta de Stock Disponible

**Situación**: No hay suficiente stock disponible para mover a reparación.

**Comportamiento**:
- Error: `"Not enough quantity available. Remaining: X"`
- No se crea el picking

**Solución**:
- Verificar stock disponible en las ubicaciones
- Ajustar la cantidad solicitada
- O esperar a que haya más stock disponible

### 9. Orden sin Técnico

**Situación**: Se intenta validar una orden sin técnico asignado.

**Comportamiento**:
- Error: `"Please assign a technitian first"`
- No se puede validar la orden

**Solución**:
- Asignar técnico antes de validar
- Usar wizard de asignación en lote si hay múltiples órdenes

### 10. Producto Serial sin Lifecycle State

**Situación**: Se intenta finalizar reparación de producto serial sin `lifecycle_state`.

**Comportamiento**:
- Error: `"Please assign a new lifecycle state"`
- No se puede finalizar la reparación

**Solución**:
- Asignar `lifecycle_state` antes de finalizar
- El estado no puede ser `E` (debe ser diferente)

### 11. Actualización de Lote al Finalizar

**Situación**: Se finaliza una reparación con `lot_id` asociado.

**Comportamiento**:
- Se actualizan automáticamente en el lote:
  - `diagnosis_ids` - Diagnósticos de la reparación
  - `result_ids` - Resultados de la reparación
  - `lifecycle_state` - Estado de ciclo de vida

**Solución**:
- El sistema maneja automáticamente la actualización
- La información queda disponible en el lote para futuras referencias

---

## Resumen de Procesos que Pueden Fallar

### Tabla de Errores Comunes

| Fase | Proceso | Error Posible | Causa | Solución |
|------|---------|---------------|-------|----------|
| **FASE 1** | Crear alerta | Producto sin account_partner_id | Producto no asociado | Asociar producto a account.partner |
| **FASE 1** | Crear alerta | Sin lote/serial (tracking) | Producto serial sin lote | Seleccionar lote/serial válido |
| **FASE 1** | Crear alerta | Sin ubicación (no tracking) | Producto sin ubicación con stock | Seleccionar ubicación con stock |
| **FASE 2** | Crear movimiento | Cantidad <= 0 | Cantidad inválida | Especificar cantidad > 0 |
| **FASE 2** | Crear movimiento | Sin account_partner_id | Falta cuenta de cliente | Asociar account.partner |
| **FASE 2** | Crear movimiento | Sin lote (tracking) | Producto serial sin lote | Seleccionar lote válido |
| **FASE 2** | Crear movimiento | Stock insuficiente | No hay stock disponible | Verificar stock disponible |
| **FASE 3** | Validar orden | Sin técnico | No se asignó técnico | Asignar técnico antes de validar |
| **FASE 5** | Finalizar reparación | Sin lifecycle_state (serial) | Estado no asignado | Asignar lifecycle_state |
| **FASE 5** | Finalizar reparación | Lifecycle_state = E | Estado no puede ser E | Asignar estado diferente |
| **FASE 6** | Completar orden | Ubicaciones no encontradas | Repairs/Stock to Relocate no configuradas | Verificar configuración |
| **FASE 6** | Validar picking retorno | Tracking no escaneado | `restrict_scan_tracking_number = mandatory` | Escanear tracking |
| **FASE 6** | Validar picking retorno | Destino no escaneado | `restrict_scan_dest_location = mandatory` | Escanear destino |
| **General** | Cancelar alerta | Pickings completados | Hay pickings done | Proporcionar motivo |

### Errores en la Creación de Alerta

**Situación**: Errores al crear una alerta de calidad desde el portal o por fallo en QC.

**Errores Posibles**:

1. **Producto sin `account_partner_id`**:
   - **Error**: Validación falla
   - **Causa**: El producto no tiene `account_partner_id` asociado
   - **Solución**: Asociar el producto a un `account.partner` antes de crear la alerta

2. **Producto serial sin lote**:
   - **Error**: Validación falla
   - **Causa**: Producto con `tracking = 'serial'` pero no se seleccionó `lot_id`
   - **Solución**: Seleccionar un lote/serial válido desde la lista disponible

3. **Producto sin tracking sin ubicación**:
   - **Error**: Validación falla
   - **Causa**: Producto con `tracking = 'none'` pero no se seleccionó `location_id`
   - **Solución**: Seleccionar una ubicación con stock disponible

4. **Cantidad <= 0**:
   - **Error**: Validación falla
   - **Causa**: Se especificó cantidad 0 o negativa
   - **Solución**: Especificar cantidad mayor que 0

### Errores en la Creación de Movimiento a Reparación

**Situación**: Errores al crear el movimiento desde Stock a Repairs.

**Errores Posibles**:

1. **Cantidad <= 0**:
   - **Error**: `"Quantity must be greater than 0."`
   - **Causa**: La cantidad de la alerta es 0 o negativa
   - **Solución**: Verificar que la cantidad es mayor que 0

2. **Sin producto seleccionado**:
   - **Error**: `"A product must be selected."`
   - **Causa**: No se especificó `product_id` en la alerta
   - **Solución**: Seleccionar un producto válido

3. **Sin account_partner_id**:
   - **Error**: `"An account partner must be selected."`
   - **Causa**: No se especificó `account_partner_id` en la alerta
   - **Solución**: Asociar un `account.partner` a la alerta

4. **Producto serial sin lote**:
   - **Error**: `"A lot/serial must be selected for this product."`
   - **Causa**: Producto con `tracking = 'serial'` o `'lot'` pero no se especificó `lot_id`
   - **Solución**: Seleccionar un lote/serial válido

5. **Stock insuficiente**:
   - **Error**: `"Not enough quantity available. Remaining: X"`
   - **Causa**: No hay suficiente stock disponible en la ubicación origen
   - **Solución**: 
     - Verificar stock disponible
     - Ajustar la cantidad solicitada
     - O esperar a que haya más stock disponible

### Errores en la Validación de Orden

**Situación**: Errores al validar una orden de reparación.

**Errores Posibles**:

1. **Sin técnico asignado**:
   - **Error**: `"Please assign a technitian first"`
   - **Causa**: No se asignó `technician_id` antes de validar
   - **Solución**: 
     - Asignar técnico antes de validar
     - Usar wizard de asignación en lote si hay múltiples órdenes

2. **Técnico no válido**:
   - **Error**: Técnico no aparece en el selector
   - **Causa**: El usuario no pertenece al grupo `logistics_security.group_repair_user` o `group_repair_manager`
   - **Solución**: Asignar el usuario al grupo correcto

### Errores en la Finalización de Reparación

**Situación**: Errores al finalizar una reparación.

**Errores Posibles**:

1. **Producto serial sin lifecycle_state**:
   - **Error**: `"Please assign a new lifecycle state"`
   - **Causa**: Producto con `tracking = 'serial'` pero no se asignó `lifecycle_state`
   - **Solución**: Asignar un `lifecycle_state` antes de finalizar (no puede ser `E`)

2. **Lifecycle_state = E**:
   - **Error**: `"Please assign a new lifecycle state"`
   - **Causa**: Se intenta finalizar con `lifecycle_state = 'E'` (no permitido)
   - **Solución**: Asignar un estado diferente (`A`, `B`, `C`, `D`, `CR`)

### Errores en la Completación de Orden

**Situación**: Errores al completar una orden de reparación (crear picking de retorno).

**Errores Posibles**:

1. **Ubicación Repairs no encontrada**:
   - **Error**: `"Locations 'Repairs' or 'Stock to relocate' not found. Please update the repair_module."`
   - **Causa**: No se encuentra la ubicación `repair_module.stock_location_repairs`
   - **Solución**: Verificar que el módulo está correctamente instalado y configurado

2. **Ubicación Stock to Relocate no encontrada**:
   - **Error**: `"Locations 'Repairs' or 'Stock to relocate' not found. Please update the repair_module."`
   - **Causa**: No se encuentra la ubicación `repair_module.stock_location_to_relocate`
   - **Solución**: Verificar que el módulo está correctamente instalado y configurado

3. **Tipo de operación no encontrado**:
   - **Error**: `"Operation type 'Return from Repair' not found. Please update the repair_module."`
   - **Causa**: No se encuentra el tipo de operación `repair_module.stock_picking_type_return_from_repair`
   - **Solución**: Verificar que el módulo está correctamente instalado y configurado

4. **Producto serial sin lote**:
   - **Error**: `"Serial number is required for product to repair : [product]"`
   - **Causa**: Producto con `tracking = 'serial'` pero no tiene `lot_id` en la orden
   - **Solución**: Verificar que el producto tiene lote/serial asociado

### Errores en la Validación de Picking de Retorno

**Situación**: Errores al validar el picking de retorno desde Repairs a Stock.

**Errores Posibles**:

1. **Tracking no escaneado**:
   - **Error**: Validación falla si `restrict_scan_tracking_number = 'mandatory'`
   - **Causa**: No se escaneó el número de tracking
   - **Solución**: Escanear el número de tracking antes de validar

2. **Ubicación destino no escaneada**:
   - **Error**: Validación falla si `restrict_scan_dest_location = 'mandatory'`
   - **Causa**: No se escaneó la ubicación destino
   - **Solución**: Escanear la ubicación destino antes de validar

3. **Stock insuficiente en Repairs**:
   - **Error**: No se puede asignar stock
   - **Causa**: No hay stock disponible en ubicación Repairs
   - **Solución**: 
     - Verificar que el producto está en Repairs
     - Verificar que el picking de "Move to Repair" fue validado

### Errores en la Actualización de Pickings

**Situación**: Errores al modificar producto, lote o cantidad en una alerta con pickings.

**Errores Posibles**:

1. **Pickings completados**:
   - **Error**: `"No se puede modificar porque hay pickings en estado finalizado o cancelado: [lista]"`
   - **Causa**: Hay pickings en estado `done` o `cancel` asociados a la alerta
   - **Solución**: 
     - Cancelar y recrear la alerta si es necesario
     - O crear una nueva alerta con la información correcta

### Errores en la Cancelación de Alerta

**Situación**: Errores al cancelar una alerta de calidad.

**Errores Posibles**:

1. **Pickings completados sin motivo**:
   - **Causa**: Hay pickings completados o reparaciones, se requiere motivo
   - **Comportamiento**: Se abre wizard para pedir motivo
   - **Solución**: Proporcionar motivo de cancelación

2. **Error al crear picking de retorno**:
   - **Causa**: No se encuentra ubicación Stock o tipo de operación
   - **Comportamiento**: El picking de retorno no se crea
   - **Solución**: Verificar configuración del módulo

### Guía Rápida de Solución de Problemas

1. **No se crea orden automáticamente**: Verificar que el picking tiene `maintenance_type` configurado
2. **Error al crear movimiento**: Verificar stock disponible, `account_partner_id`, y lote/ubicación según tracking
3. **No se puede validar orden**: Verificar que hay técnico asignado y que pertenece al grupo correcto
4. **Error al finalizar reparación**: Verificar que `lifecycle_state` está asignado (para serial) y no es `E`
5. **No se puede modificar alerta**: Verificar que no hay pickings completados
6. **Error al cancelar**: Verificar si hay pickings completados (requiere motivo)
7. **Ubicaciones no encontradas**: Verificar que el módulo está correctamente instalado
8. **Tracking/destino no escaneado**: Escanear tracking y destino si son obligatorios

---

## Resumen de Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CREAR ALERTA DE CALIDAD                                 │
│    - Desde portal o fallo en QC                           │
│    - Especificar producto, cantidad, lote/ubicación       │
│    → Crea quality.alert (estado: In Warehouse)            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. MOVER A REPARACIÓN - NECESARIO                           │
│    - Crear movimiento a reparación                        │
│    - Confirmar picking                                      │
│    - Asignar stock                                          │
│    - Validar picking                                        │
│    → Producto movido a Repairs                             │
│    → Alerta cambia a "Sent for Review / Repair"            │
│    → Crea automáticamente repair.order                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. ASIGNAR TÉCNICO Y VALIDAR - NECESARIO                    │
│    - Asignar técnico                                        │
│    - Validar orden                                          │
│    → Orden en estado Confirmed                             │
│    → Alerta cambia a "Confirmed"                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. INICIAR REPARACIÓN - NECESARIO                           │
│    - Agregar componentes (opcional)                        │
│    - Iniciar reparación                                     │
│    → Orden en estado Under Repair                          │
│    → Alerta cambia a "Repairing"                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. COMPLETAR REPARACIÓN - NECESARIO                         │
│    - Registrar diagnóstico (opcional)                       │
│    - Registrar resultados (opcional)                         │
│    - Asignar lifecycle_state (obligatorio para serial)    │
│    - Finalizar reparación                                   │
│    → Orden en estado Ready                                 │
│    → Alerta cambia a "Return to After-Sales"               │
│    → Actualiza lote con diagnóstico/resultados/estado      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. DEVOLVER A STOCK - NECESARIO                             │
│    - Completar orden (crea picking retorno)                │
│    - Confirmar picking retorno                             │
│    - Asignar stock                                          │
│    - Validar picking retorno (escanear tracking y destino) │
│    → Producto devuelto a Stock to Relocate                 │
│    → Orden en estado Done                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Notas Importantes

### Diferencias con Módulos Estándar

1. **Alertas de Calidad**: Se usan `quality.alert` en lugar de `repair.order` directamente para gestión desde portal
2. **Ubicaciones Específicas**: Se usan ubicaciones dedicadas (Repairs, Stock to Relocate, Scrap)
3. **Estados de Ciclo de Vida**: Se gestiona el estado del ciclo de vida del producto
4. **Creación Automática**: Las órdenes se crean automáticamente al validar pickings
5. **Integración con Lotes**: Los diagnósticos y resultados se guardan en los lotes/seriales

### Mejores Prácticas

1. **Asignar técnico temprano**: Asignar técnico tan pronto como se cree la orden
2. **Documentar diagnóstico**: Registrar diagnósticos para trazabilidad
3. **Documentar resultados**: Registrar resultados para historial
4. **Actualizar lifecycle_state**: Siempre actualizar el estado de ciclo de vida para productos serial
5. **Validar pickings en orden**: Validar pickings en el orden correcto (Move to Repair → Return from Repair)
6. **Usar cancelación con motivo**: Proporcionar motivo al cancelar alertas con pickings completados

### Troubleshooting

1. **No se crea orden automáticamente**: Verificar que el picking tiene `maintenance_type` configurado
2. **Error al crear movimiento**: Verificar stock disponible y datos válidos
3. **No se puede validar orden**: Verificar que hay técnico asignado
4. **Error al finalizar reparación**: Verificar que `lifecycle_state` está asignado (para serial)
5. **No se puede modificar alerta**: Verificar que no hay pickings completados
6. **Error al cancelar**: Verificar si hay pickings completados (requiere motivo)

---

## Referencias

- **Módulo**: `repair_module`
- **Modelos principales**:
  - `quality.alert` - Alerta de calidad/reparación
  - `repair.order` - Orden de reparación
  - `stock.picking` - Pickings de movimiento
  - `stock.lot` - Lotes/Seriales (con diagnóstico/resultados)
  - `repair.diagnosis` - Diagnósticos de reparación
  - `repair.result` - Resultados de reparación

---

**Última actualización**: 2025-01-XX
**Versión del módulo**: 18.0.1.0.0
