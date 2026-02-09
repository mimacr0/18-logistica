# Proceso de Traslados Internos - Stock Internal

## Índice
1. [Prerequisitos](#prerequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Proceso de Traslado Interno - Flujo Completo](#proceso-de-traslado-interno---flujo-completo)
4. [Pasos Detallados](#pasos-detallados)
5. [Pasos Opcionales vs Necesarios](#pasos-opcionales-vs-necesarios)
6. [Gestión de Ubicaciones](#gestión-de-ubicaciones)
7. [Gestión de Propietarios (Owners)](#gestión-de-propietarios-owners)
8. [Validaciones y Restricciones](#validaciones-y-restricciones)
9. [Casos Especiales](#casos-especiales)

---

## Prerequisitos

### Módulos Requeridos
El módulo `stock_internal` depende de los siguientes módulos:
- `stock` - Gestión básica de inventario
- `hr` - Recursos humanos (para gestión de empleados)

### Configuraciones del Sistema
No se requieren configuraciones especiales del sistema. El módulo funciona con la configuración estándar de Odoo.

### Configuración de Almacén
No se requiere configuración especial del almacén. Los traslados internos funcionan con cualquier configuración de almacén.

### Configuración de Tipos de Operación

#### Tipo de Operación: Traslado Interno (Internal)
- **Código**: `internal`
- **Secuencia**: `INT` (para traslados internos estándar)
- **Configuración por defecto** (aplicada automáticamente):
  - `restrict_scan_source_location`: **mandatory** - Escaneo obligatorio de ubicación origen
  - `restrict_scan_dest_location`: **mandatory** - Escaneo obligatorio de ubicación destino
- **Configuración opcional**:
  - `use_custom_partner_domain`: **False** - Filtrar contactos (solo empresas, no empleados)
  - `allowed_location_ids`: Lista de ubicaciones origen permitidas (vacío = todas)
  - `allowed_location_dest_ids`: Lista de ubicaciones destino permitidas (vacío = todas)

**Propósito**: Mover productos entre ubicaciones internas del almacén manteniendo el propietario (owner).

### Datos Requeridos

#### Productos
- Los productos deben tener:
  - Stock disponible en la ubicación de origen
  - Tracking opcional (sin tracking, lot, o serial)

#### Ubicaciones
- Las ubicaciones deben ser:
  - De tipo `internal` (ubicaciones internas del almacén)
  - Configuradas en el sistema
  - Accesibles según los permisos del usuario

#### Propietarios (Owners)
- Los productos pueden tener:
  - `owner_id` - Propietario del stock (cuenta de cliente)
  - Si no tiene owner, se considera stock propio de la empresa

---

## Configuración Inicial

### 1. Configuración de Tipos de Operación

#### Restricción de Ubicaciones
Para restringir las ubicaciones disponibles en un tipo de operación:

1. Ir a **Inventario → Configuración → Tipos de Operación**
2. Seleccionar el tipo de operación de traslado interno
3. En la sección **"Dominios Personalizados"**:
   - **Ubicaciones origen permitidas**: Seleccionar ubicaciones que pueden ser origen
   - **Ubicaciones destino permitidas**: Seleccionar ubicaciones que pueden ser destino
   - Si se dejan vacías, se permiten todas las ubicaciones internas

#### Filtro de Contactos
Para filtrar contactos (solo empresas, no empleados):

1. Activar **"Dominio personalizado de contactos"**
2. Esto restringe la selección de contactos a solo empresas, excluyendo empleados

### 2. Configuración de Escaneo con Código de Barras

Los tipos de operación con secuencia `INT` se configuran automáticamente con:
- **Escaneo obligatorio de ubicación origen**: `restrict_scan_source_location = 'mandatory'`
- **Escaneo obligatorio de ubicación destino**: `restrict_scan_dest_location = 'mandatory'`

Esto asegura el flujo: **Escanear Origen → Escanear Producto → Escanear Destino**

---

## Proceso de Traslado Interno - Flujo Completo

El proceso de traslado interno es un **proceso de 1 paso** que mueve productos entre ubicaciones internas:

```
Crear Picking → Confirmar → Asignar Stock → Validar → Productos Movidos
```

### Resumen del Flujo

1. **FASE 1: Creación de Traslado** (Backend)
   - Crear picking de tipo `internal`
   - Seleccionar ubicación origen y destino
   - Agregar productos y cantidades

2. **FASE 2: Confirmación** (Backend)
   - Confirmar picking
   - Verificar disponibilidad de stock

3. **FASE 3: Asignación de Stock** (Backend)
   - Asignar stock desde ubicación origen
   - Reservar productos específicos

4. **FASE 4: Validación** (Backend)
   - Completar cantidades en `stock.move.line`
   - Especificar ubicaciones y productos
   - Validar el picking
   - → Productos movidos a ubicación destino

---

## Pasos Detallados

### **FASE 1: Creación de Traslado**

**Método**: Crear `stock.picking` con `picking_type_id.code = 'internal'`

**Acceso**: Backend Odoo → Inventario → Operaciones → Traslados Internos

**Pasos**:
1. Crear nuevo picking de tipo "Traslado Interno"
2. Completar información:
   - **OBLIGATORIO**: `location_id` - Ubicación origen
     - Si hay `allowed_location_ids` configurado, solo se muestran esas ubicaciones
   - **OBLIGATORIO**: `location_dest_id` - Ubicación destino
     - Si hay `allowed_location_dest_ids` configurado, solo se muestran esas ubicaciones
   - **OPCIONAL**: `owner_id` - Propietario del stock
     - Si no se especifica, se propaga automáticamente desde el quant de origen
   - **OPCIONAL**: `account_partner_id` - Cuenta de cliente
     - Si se especifica, se usa su `partner_id` como `owner_id`

3. Agregar productos:
   - **OBLIGATORIO**: Al menos un producto con cantidad > 0
   - **OPCIONAL**: Especificar lote/serial si el producto tiene tracking
   - **OPCIONAL**: Especificar paquete si el producto está empaquetado

**Validaciones**:
- Las ubicaciones deben ser de tipo `internal`
- Debe haber al menos un producto
- Las ubicaciones deben estar permitidas según la configuración del tipo de operación

**Nota**: El propietario (`owner_id`) se propaga automáticamente desde el quant de origen si no se especifica.

---

### **FASE 2: Confirmación**

**Método**: `stock.picking.action_confirm()`

**Acceso**: Backend Odoo → Inventario → Operaciones → Traslados Internos

**Pasos**:
1. Abrir el picking en estado `draft`
2. Revisar información:
   - Ubicación origen y destino
   - Productos y cantidades
   - Propietario (si aplica)
3. Confirmar el picking (`action_confirm()`) - Botón **"Mark as Todo"**

**Lo que sucede automáticamente al confirmar**:
- El picking cambia a estado `waiting` o `assigned`
- Se crean `stock.move` para cada producto
- Se crean `stock.move.line` iniciales
- Si hay stock disponible, se puede asignar automáticamente

**Validaciones**:
- Las ubicaciones deben ser válidas
- Los productos deben existir
- Las cantidades deben ser mayores que 0

---

### **FASE 3: Asignación de Stock**

**Método**: `stock.picking.action_assign()`

**Acceso**: Backend Odoo → Inventario → Operaciones → Traslados Internos

**Pasos**:
1. Abrir el picking en estado `waiting` o `assigned`
2. Asignar stock (`action_assign()`) - Botón **"Check Availability"**
   - El sistema busca stock disponible en la ubicación origen
   - Reserva productos específicos (considerando lote/serial/paquete si aplica)
   - Si hay stock, cambia a estado `assigned`
   - Si no hay stock, queda en `waiting`

**Validaciones**:
- Debe haber stock disponible en la ubicación origen
- El stock debe coincidir con el propietario (si se especificó)
- Para productos con tracking, debe haber stock con el lote/serial especificado

**Nota**: Si no hay stock disponible, el picking queda en `waiting` hasta que haya stock.

---

### **FASE 4: Validación**

**Método**: `stock.picking.button_validate()`

**Acceso**: Backend Odoo → Inventario → Operaciones → Traslados Internos

**Pasos**:
1. Abrir el picking en estado `assigned`
2. Completar información en `stock.move.line`:
   - **OBLIGATORIO**: `location_id` - Ubicación origen (puede ser diferente a la del picking)
   - **OBLIGATORIO**: `location_dest_id` - Ubicación destino (puede ser diferente a la del picking)
   - **OBLIGATORIO**: `quantity` - Cantidad a mover (no puede exceder el disponible)
   - **OPCIONAL**: `lot_id` - Lote/serial (si el producto tiene tracking)
   - **OPCIONAL**: `package_id` - Paquete (si el producto está empaquetado)
   - **OPCIONAL**: `owner_id` - Propietario (se propaga automáticamente si no se especifica)

3. **Validación automática de cantidad disponible**:
   - El sistema valida que la cantidad no exceda el disponible
   - Considera lote/serial/paquete si se especifican
   - Muestra error si no hay suficiente stock

4. Validar el picking (`button_validate()`) - Botón **"Validate"**
   - → Productos movidos a ubicación destino
   - → Stock actualizado en ambas ubicaciones

**Resultado**:
- Productos movidos desde ubicación origen a ubicación destino
- Stock descontado de ubicación origen
- Stock agregado a ubicación destino
- Propietario (`owner_id`) preservado en el movimiento
- Estado del picking: `done`

**Validaciones**:
- Debe haber stock disponible suficiente
- Las cantidades no pueden exceder el disponible
- Las ubicaciones deben ser válidas
- Para productos con tracking, los lotes/seriales deben existir

---

## Pasos Opcionales vs Necesarios

| Fase | Paso | Necesario | Descripción |
|------|------|-----------|-------------|
| **FASE 1** | Crear picking | ✅ **NECESARIO** | Crear traslado interno |
| **FASE 1** | Seleccionar ubicación origen | ✅ **NECESARIO** | De dónde se mueven los productos |
| **FASE 1** | Seleccionar ubicación destino | ✅ **NECESARIO** | A dónde se mueven los productos |
| **FASE 1** | Agregar productos | ✅ **NECESARIO** | Al menos un producto |
| **FASE 1** | Especificar propietario | ⚠️ **OPCIONAL** | Se propaga automáticamente |
| **FASE 1** | Especificar lote/serial | ⚠️ **OPCIONAL** | Solo si producto tiene tracking |
| **FASE 1** | Especificar paquete | ⚠️ **OPCIONAL** | Solo si producto está empaquetado |
| **FASE 2** | Confirmar picking | ✅ **NECESARIO** | Inicia el proceso |
| **FASE 3** | Asignar stock | ✅ **NECESARIO** | Reserva productos |
| **FASE 4** | Completar ubicaciones en líneas | ⚠️ **OPCIONAL** | Si difieren del picking |
| **FASE 4** | Completar cantidades | ✅ **NECESARIO** | Especificar cantidad a mover |
| **FASE 4** | Especificar lote/serial | ⚠️ **OPCIONAL** | Solo si producto tiene tracking |
| **FASE 4** | Validar picking | ✅ **NECESARIO** | Completa el traslado |

---

## Gestión de Ubicaciones

### Restricción de Ubicaciones

#### Configuración en Tipo de Operación
- **Ubicaciones origen permitidas**: Lista de ubicaciones que pueden ser origen
  - Si está vacía, se permiten todas las ubicaciones internas
  - Si tiene ubicaciones, solo esas están disponibles en el formulario

- **Ubicaciones destino permitidas**: Lista de ubicaciones que pueden ser destino
  - Si está vacía, se permiten todas las ubicaciones internas
  - Si tiene ubicaciones, solo esas están disponibles en el formulario

#### Uso en Picking
- El picking hereda las restricciones del tipo de operación
- Los campos `location_id` y `location_dest_id` solo muestran ubicaciones permitidas
- Se puede especificar ubicaciones diferentes en `stock.move.line` si es necesario

### Validación de Ubicaciones
- Las ubicaciones deben ser de tipo `internal`
- No se pueden usar ubicaciones de tipo `supplier`, `customer`, `inventory`, etc.
- Las ubicaciones deben estar en el mismo almacén (o ser compatibles)

---

## Gestión de Propietarios (Owners)

### Propagación Automática

El sistema propaga automáticamente el `owner_id` (propietario) en el siguiente orden de prioridad:

1. **Prioridad 1**: `picking.account_partner_id.partner_id`
   - Si el picking tiene `account_partner_id`, se usa su `partner_id` como owner

2. **Prioridad 2**: `picking.owner_id`
   - Si el picking tiene `owner_id` configurado, se usa ese

3. **Prioridad 3**: Owner del quant de origen
   - Se busca en los quants de la ubicación origen
   - Si todos los quants tienen el mismo owner, se usa ese
   - Si hay múltiples owners, se usa el del quant con mayor cantidad

### Validación de Stock Disponible

El sistema valida que haya stock disponible considerando:
- Ubicación origen
- Producto
- Lote/serial (si aplica)
- Paquete (si aplica)
- Owner (si se especifica)

**Importante**: La validación usa `strict=False` para permitir matching de quants con cualquier owner, pero luego se propaga el owner correcto.

### Casos Especiales

#### Sin Owner
- Si el producto no tiene owner, se considera stock propio de la empresa
- Se puede mover sin problemas

#### Con Owner
- El owner se preserva en el movimiento
- El stock en la ubicación destino mantiene el mismo owner
- Esto es importante para productos de clientes (account_partner_id)

---

## Validaciones y Restricciones

### 1. Validación de Cantidad Disponible

**Cuándo se valida**: Al crear `stock.move.line` para traslados internos

**Qué valida**:
- Cantidad disponible en ubicación origen
- Considera lote/serial si se especifica
- Considera paquete si se especifica
- No permite crear quants negativos

**Mensaje de error**:
```
Insufficient quantity for 'Product Name' in 'Location Name' (Package: XXX, Lot/Serial: YYY).
Available: X.XX, Requested: Y.YY
```

### 2. Restricción de Ubicaciones

**Cuándo se aplica**: Si el tipo de operación tiene `allowed_location_ids` o `allowed_location_dest_ids` configurados

**Qué restringe**:
- Solo se pueden seleccionar ubicaciones permitidas en el formulario
- Se puede especificar ubicaciones diferentes en `stock.move.line` si es necesario

### 3. Restricción de Contactos

**Cuándo se aplica**: Si el tipo de operación tiene `use_custom_partner_domain = True`

**Qué restringe**:
- Solo se pueden seleccionar contactos de tipo empresa
- Se excluyen empleados (`hr.employee`)

### 4. Escaneo Obligatorio (Código de Barras)

**Cuándo se aplica**: Para tipos de operación con secuencia `INT`

**Qué requiere**:
- Escaneo obligatorio de ubicación origen (`restrict_scan_source_location = 'mandatory'`)
- Escaneo obligatorio de ubicación destino (`restrict_scan_dest_location = 'mandatory'`)

**Flujo**:
1. Escanear ubicación origen
2. Escanear producto
3. Escanear ubicación destino
4. Validar

---

## Casos Especiales

### 1. Productos sin Stock Disponible

**Situación**: Se intenta mover más cantidad de la disponible.

**Comportamiento**:
- El sistema valida la cantidad al crear `stock.move.line`
- Muestra error si la cantidad excede el disponible
- No permite crear el movimiento

**Solución**:
- Verificar stock disponible en la ubicación origen
- Ajustar la cantidad a mover
- O esperar a que haya más stock disponible

### 2. Productos con Tracking (Serial/Lot)

**Situación**: Productos que requieren números de serie o lotes.

**Comportamiento**:
- Se debe especificar el lote/serial en `stock.move.line`
- El sistema valida que el lote/serial exista en la ubicación origen
- Se preserva el lote/serial en el movimiento

**Solución**:
- Escanear o introducir el número de serie/lote
- Validar que existe en la ubicación origen
- El sistema preserva el tracking en la ubicación destino

### 3. Productos Empaquetados

**Situación**: Productos que están en paquetes.

**Comportamiento**:
- Se puede especificar el paquete en `stock.move.line`
- El sistema valida que el paquete exista en la ubicación origen
- Se puede mover el paquete completo o productos individuales

**Solución**:
- Escanear el paquete o especificarlo manualmente
- Validar que el paquete existe en la ubicación origen
- El sistema preserva la relación con el paquete si es necesario

### 4. Múltiples Propietarios en la Misma Ubicación

**Situación**: Hay stock del mismo producto con diferentes owners en la ubicación origen.

**Comportamiento**:
- El sistema busca quants con owner en la ubicación origen
- Si hay múltiples owners, usa el del quant con mayor cantidad
- Se puede especificar el owner manualmente si es necesario

**Solución**:
- Especificar el owner en el picking o en `stock.move.line`
- El sistema usa el owner correcto automáticamente
- Validar que el owner sea correcto antes de validar

### 5. Traslados Parciales

**Situación**: Se mueve solo una parte del stock disponible.

**Comportamiento**:
- Se puede mover cualquier cantidad disponible
- El stock restante permanece en la ubicación origen
- No se crean backorders (solo para recepciones/expediciones)

**Solución**:
- Especificar la cantidad exacta a mover
- El stock restante queda disponible en la ubicación origen

### 6. Cancelación de Traslado

**Situación**: Se cancela un traslado después de crearlo.

**Comportamiento**:
- El picking se cancela
- El stock reservado se libera
- No se pueden validar pickings cancelados

**Solución**:
- Cancelar el picking desde el backend
- El stock vuelve a estar disponible

### 7. Modificación de Traslado Después de Confirmar

**Situación**: Se modifica un traslado ya confirmado.

**Comportamiento**:
- Si el picking está en `draft` o `assigned`, se pueden modificar productos
- Si el picking está validado (`done`), no se puede modificar
- Se deben cancelar y recrear si es necesario

**Solución**:
- Modificar antes de validar
- O cancelar y recrear el traslado

---

## Resumen de Procesos que Pueden Fallar

### Tabla de Errores Comunes

| Fase | Proceso | Error Posible | Causa | Solución |
|------|---------|---------------|-------|----------|
| **FASE 1** | Crear traslado | Ubicación no permitida | Ubicación no está en `allowed_location_ids` | Seleccionar ubicación permitida |
| **FASE 1** | Crear traslado | Sin productos | No se agregaron productos | Agregar al menos un producto |
| **FASE 2** | Confirmar picking | Ubicaciones inválidas | Ubicaciones no son tipo `internal` | Verificar tipo de ubicación |
| **FASE 3** | Asignar stock | Stock insuficiente | No hay stock disponible | Verificar stock disponible |
| **FASE 3** | Asignar stock | Owner incorrecto | Owner no coincide | Verificar owner del stock |
| **FASE 4** | Validar picking | Cantidad excede disponible | Se intenta mover más de lo disponible | Ajustar cantidad |
| **FASE 4** | Validar picking | Lote/serial no existe | Lote/serial no está en ubicación origen | Verificar lote/serial |
| **FASE 4** | Validar picking | Ubicaciones no escaneadas | `restrict_scan_*_location = mandatory` | Escanear ubicaciones |
| **General** | Error de validación | Quant negativo | Se intenta crear quant negativo | Verificar cantidad disponible |

### Errores en la Creación de Traslado

**Situación**: Errores al crear un traslado interno.

**Errores Posibles**:

1. **Ubicación origen no permitida**:
   - **Error**: Ubicación no aparece en el selector
   - **Causa**: Ubicación no está en `allowed_location_ids` del tipo de operación
   - **Solución**: 
     - Seleccionar una ubicación permitida
     - O configurar `allowed_location_ids` en el tipo de operación

2. **Ubicación destino no permitida**:
   - **Error**: Ubicación no aparece en el selector
   - **Causa**: Ubicación no está en `allowed_location_dest_ids` del tipo de operación
   - **Solución**: 
     - Seleccionar una ubicación permitida
     - O configurar `allowed_location_dest_ids` en el tipo de operación

3. **Sin productos agregados**:
   - **Error**: Validación falla al intentar confirmar
   - **Causa**: No se agregó ningún producto
   - **Solución**: Agregar al menos un producto con cantidad > 0

4. **Ubicación no es tipo internal**:
   - **Error**: Validación falla
   - **Causa**: Se seleccionó ubicación de tipo `supplier`, `customer`, etc.
   - **Solución**: Seleccionar solo ubicaciones de tipo `internal`

### Errores en la Confirmación

**Situación**: Errores al confirmar un picking de traslado interno.

**Errores Posibles**:

1. **Ubicaciones inválidas**:
   - **Error**: Validación falla
   - **Causa**: Las ubicaciones no son válidas o no son tipo `internal`
   - **Solución**: Verificar que las ubicaciones sean de tipo `internal`

2. **Productos no válidos**:
   - **Error**: Validación falla
   - **Causa**: Los productos no existen o no son válidos
   - **Solución**: Verificar que los productos existen y son válidos

3. **Cantidades inválidas**:
   - **Error**: Validación falla
   - **Causa**: Las cantidades son 0 o negativas
   - **Solución**: Especificar cantidades mayores que 0

### Errores en la Asignación de Stock

**Situación**: Errores al asignar stock en un picking de traslado interno.

**Errores Posibles**:

1. **Stock insuficiente**:
   - **Error**: El picking queda en estado `waiting`
   - **Causa**: No hay stock disponible en la ubicación origen
   - **Solución**: 
     - Verificar stock disponible en la ubicación origen
     - Esperar a que haya stock disponible
     - O cancelar el picking

2. **Owner incorrecto**:
   - **Error**: No se puede asignar stock
   - **Causa**: El owner del stock no coincide con el especificado
   - **Solución**: 
     - Verificar owner del stock en la ubicación origen
     - O especificar el owner correcto en el picking

3. **Lote/serial no existe**:
   - **Error**: No se puede asignar stock
   - **Causa**: El lote/serial especificado no existe en la ubicación origen
   - **Solución**: 
     - Verificar que el lote/serial existe
     - O especificar un lote/serial válido

### Errores en la Validación

**Situación**: Errores al validar un picking de traslado interno.

**Errores Posibles**:

1. **Cantidad excede disponible**:
   - **Error**: `"Insufficient quantity for 'Product Name' in 'Location Name' (Package: XXX, Lot/Serial: YYY). Available: X.XX, Requested: Y.YY"`
   - **Causa**: Se intenta mover más cantidad de la disponible
   - **Solución**: 
     - Ajustar la cantidad a mover
     - Verificar stock disponible en la ubicación origen
     - Considerar lote/serial/paquete si se especifican

2. **Lote/serial no existe en ubicación origen**:
   - **Error**: Validación falla
   - **Causa**: El lote/serial especificado no está en la ubicación origen
   - **Solución**: 
     - Verificar que el lote/serial existe en la ubicación origen
     - O especificar un lote/serial válido

3. **Ubicación origen no escaneada**:
   - **Error**: Validación falla si `restrict_scan_source_location = 'mandatory'`
   - **Causa**: No se escaneó la ubicación origen
   - **Solución**: Escanear la ubicación origen antes de validar

4. **Ubicación destino no escaneada**:
   - **Error**: Validación falla si `restrict_scan_dest_location = 'mandatory'`
   - **Causa**: No se escaneó la ubicación destino
   - **Solución**: Escanear la ubicación destino antes de validar

5. **Ubicaciones inválidas en líneas**:
   - **Error**: Validación falla
   - **Causa**: Las ubicaciones en `stock.move.line` no son válidas
   - **Solución**: 
     - Verificar que las ubicaciones son de tipo `internal`
     - Verificar que las ubicaciones existen

6. **Quant negativo**:
   - **Error**: No se puede crear quant negativo
   - **Causa**: Se intenta mover más cantidad de la disponible
   - **Solución**: 
     - Ajustar la cantidad
     - Verificar stock disponible
     - El sistema valida automáticamente antes de crear el movimiento

### Errores en la Propagación de Owner

**Situación**: Errores relacionados con el propietario (owner) del stock.

**Errores Posibles**:

1. **Owner no se propaga**:
   - **Causa**: No hay quants con owner en la ubicación origen
   - **Comportamiento**: El owner no se propaga automáticamente
   - **Solución**: 
     - Especificar el owner manualmente en el picking
     - O verificar que hay quants con owner en la ubicación origen

2. **Múltiples owners en la misma ubicación**:
   - **Causa**: Hay stock del mismo producto con diferentes owners
   - **Comportamiento**: El sistema usa el owner del quant con mayor cantidad
   - **Solución**: 
     - Especificar el owner manualmente si es necesario
     - Verificar que el owner sea correcto antes de validar

### Guía Rápida de Solución de Problemas

1. **No se pueden seleccionar ubicaciones**: Verificar que las ubicaciones estén en `allowed_location_ids` o `allowed_location_dest_ids`
2. **Error de cantidad insuficiente**: Verificar stock disponible en la ubicación origen, considerando lote/serial/paquete
3. **Owner no se propaga**: Verificar que hay quants con owner en la ubicación origen, o especificar manualmente
4. **No se puede validar**: Verificar que todas las líneas tienen cantidades y ubicaciones válidas, y que se escanearon las ubicaciones si es obligatorio
5. **Stock negativo**: Esto no debería ocurrir gracias a la validación, pero si ocurre, verificar configuración de ubicaciones
6. **Ubicaciones no escaneadas**: Escanear ubicación origen y destino si `restrict_scan_*_location = 'mandatory'`

---

## Resumen de Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CREAR TRASLADO                                           │
│    - Seleccionar ubicación origen                          │
│    - Seleccionar ubicación destino                         │
│    - Agregar productos y cantidades                        │
│    - Especificar propietario (opcional)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CONFIRMAR - NECESARIO                                    │
│    - Confirmar picking                                      │
│    → Crea movimientos de stock                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. ASIGNAR STOCK - NECESARIO                                │
│    - Asignar stock desde ubicación origen                   │
│    - Reservar productos específicos                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. VALIDAR - NECESARIO                                      │
│    - Completar cantidades en líneas                         │
│    - Especificar ubicaciones (si difieren)                  │
│    - Validar picking                                        │
│    → Productos movidos a ubicación destino                  │
│    → Propietario preservado                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Notas Importantes

### Diferencias con Recepción y Expedición

1. **Propósito**: Traslados internos mueven productos **dentro del almacén**, no hacia/desde clientes/proveedores
2. **Pasos**: Traslados internos son **1 paso** (no 3 como recepción/expedición)
3. **Propietario**: Traslados internos **preservan el owner** automáticamente
4. **Validación**: Traslados internos **validan stock disponible** antes de crear movimientos
5. **Ubicaciones**: Traslados internos solo usan ubicaciones **internas**

### Mejores Prácticas

1. **Configurar restricciones de ubicaciones**: Limitar ubicaciones permitidas para evitar errores
2. **Verificar stock antes de crear**: Asegurar que hay stock disponible antes de crear el traslado
3. **Especificar propietario si es necesario**: Aunque se propaga automáticamente, es mejor especificarlo explícitamente
4. **Usar código de barras**: Aprovechar el escaneo obligatorio para mayor precisión
5. **Validar antes de confirmar**: Revisar toda la información antes de confirmar el picking
6. **Documentar traslados**: Usar notas para documentar el motivo del traslado

### Troubleshooting

1. **No se pueden seleccionar ubicaciones**: Verificar que las ubicaciones estén en `allowed_location_ids` o `allowed_location_dest_ids`
2. **Error de cantidad insuficiente**: Verificar stock disponible en la ubicación origen
3. **Owner no se propaga**: Verificar que hay quants con owner en la ubicación origen, o especificar manualmente
4. **No se puede validar**: Verificar que todas las líneas tienen cantidades y ubicaciones válidas
5. **Stock negativo**: Esto no debería ocurrir gracias a la validación, pero si ocurre, verificar configuración de ubicaciones

---

## Referencias

- **Módulo**: `stock_internal`
- **Modelos principales**:
  - `stock.picking` - Picking de traslado interno
  - `stock.picking.type` - Tipo de operación (con restricciones)
  - `stock.move` - Movimiento de stock
  - `stock.move.line` - Línea de movimiento (con validación)
  - `stock.quant` - Cantidad de stock
  - `stock.location` - Ubicaciones

---

**Última actualización**: 2025-01-XX
**Versión del módulo**: 18.0.1.0.0
