# 📋 Manual de Pruebas de Usuario - Módulos 18-Logística

**Versión:** 1.0  
**Fecha:** 8 de Enero de 2026  
**Autor:** Equipo de Desarrollo  

---

## 📑 Índice

1. [client_account](#1-client_account---gestión-de-cuentas-de-clientes)
2. [dev_attendance_dashboard_advanced](#2-dev_attendance_dashboard_advanced---dashboard-de-asistencia)
3. [logistics_security](#3-logistics_security---grupos-de-seguridad-logística)
4. [product_menu](#4-product_menu---gestión-de-productos)
5. [package_menu](#5-package_menu---gestión-de-paquetes)
6. [product_sales_by_location](#6-product_sales_by_location---ventas-por-ubicación)
7. [quality_control_imei](#7-quality_control_imei---control-de-calidad-imei)
8. [repair_module](#8-repair_module---módulo-de-reparaciones)
9. [rpc_client_api / rpc_server_api / rpc_sync_api](#9-apis-rpc)
10. [stock_barcode_picking_batch](#10-stock_barcode_picking_batch---batch-picking-con-código-de-barras)
11. [stock_expedition](#11-stock_expedition---expediciones)
12. [stock_menu](#12-stock_menu---menú-de-stock)
13. [stock_reception](#13-stock_reception---recepción-de-paquetes)

---

## 1. client_account - Gestión de Cuentas de Clientes

### 1.1 Descripción
Módulo para la gestión de clientes, cuentas y créditos en el sistema y portal.

### 1.2 Prerrequisitos
- Usuario con permisos de Ventas
- Módulos `account` y `sale_management` instalados
- Usuarios de tipo empresa creados previamente (para poder asociarlos a las cuentas)

### 1.3 Casos de Prueba

#### CP-CA-001: Crear nueva cuenta de partner
| Campo | Valor |
|-------|-------|
| **ID** | CP-CA-001 |
| **Título** | Crear nueva cuenta de partner |
| **Prioridad** | Alta |

**Pasos:**
1. Ir al **Menú Principal**
2. Navegar a **Cuentas**
3. Clic en el botón **Agregar Cuenta**
4. En el formulario que se abre, completar:
   - **Nombre de la cuenta**
   - **Empresa** (asociar a una empresa)
   - **Idioma** (seleccionar idioma)
   - **Comercial** (asignar un comercial)
5. Clic en **Guardar**

**Resultado Esperado:**
- Se crea la cuenta usando el nombre como identificador
- La cuenta aparece vinculada a la empresa seleccionada
- El comercial queda asignado correctamente

**Criterios de Aceptación:**
- [ ] Nombre de cuenta guardado (usado como identificador)
- [ ] Empresa asociada correctamente
- [ ] Idioma configurado
- [ ] Comercial asignado
- [ ] Visible en la lista de cuentas

---

#### CP-CA-002: Añadir contactos a una cuenta
| Campo | Valor |
|-------|-------|
| **ID** | CP-CA-002 |
| **Título** | Añadir contactos desde una cuenta |
| **Prioridad** | Alta |

**Pasos:**
1. Ir al **Menú Principal**
2. Navegar a **Cuentas**
3. Seleccionar una cuenta existente
4. En la vista formulario, ir a la página **Contactos**
5. Clic en el botón **Añadir**
6. En el formulario que se abre, completar:
   - **Nombre** (obligatorio)
   - **Correo electrónico** (obligatorio)
   - Otros campos opcionales según necesidad
7. Guardar y cerrar

**Resultado Esperado:**
- El contacto se crea y queda asociado a la cuenta
- El contacto aparece en la lista de contactos de la cuenta

**Criterios de Aceptación:**
- [ ] Formulario de contacto se abre correctamente
- [ ] Nombre guardado
- [ ] Correo electrónico guardado
- [ ] Contacto visible en la lista de la cuenta
- [ ] Relación cuenta-contacto establecida

---

#### CP-CA-003: Invitar contactos al portal
| Campo | Valor |
|-------|-------|
| **ID** | CP-CA-003 |
| **Título** | Invitar contactos al portal |
| **Prioridad** | Alta |

**Prerrequisitos:**
- Haber creado un contacto para la cuenta (ver CP-CA-002)

**Pasos:**
1. Ir al **Menú Principal**
2. Navegar a **Cuentas**
3. Seleccionar una cuenta existente
4. En la vista formulario, pulsar el botón **Invitar**
5. Se muestra una lista con los contactos y sus correos electrónicos
6. Pulsar el botón **Otorgar Acceso** en el contacto deseado

**Resultado Esperado:**
- Se envía una invitación al correo del contacto
- El contacto recibe acceso al portal

**Criterios de Aceptación:**
- [ ] Lista de contactos visible
- [ ] Correos electrónicos mostrados
- [ ] Botón "Otorgar Acceso" funcional
- [ ] Invitación enviada correctamente

---

#### CP-CA-004: Revocar acceso al portal
| Campo | Valor |
|-------|-------|
| **ID** | CP-CA-004 |
| **Título** | Revocar acceso al portal de un contacto |
| **Prioridad** | Alta |

**Prerrequisitos:**
- Haber otorgado acceso al portal a un contacto (ver CP-CA-003)

**Pasos:**
1. Ir al **Menú Principal**
2. Navegar a **Cuentas**
3. Seleccionar una cuenta existente
4. En la vista formulario, pulsar el botón **Gestionar Cuenta**
5. Se muestra una lista solo con los usuarios que tienen acceso al portal
6. Pulsar el botón **Revocar Acceso** en el contacto deseado

**Resultado Esperado:**
- El contacto pierde acceso al portal
- Ya no puede iniciar sesión en el portal

**Criterios de Aceptación:**
- [ ] Solo se muestran usuarios con acceso
- [ ] Botón "Revocar Acceso" funcional
- [ ] Acceso revocado correctamente
- [ ] Contacto ya no puede acceder al portal

---

#### CP-CA-005: Reenviar invitación al portal
| Campo | Valor |
|-------|-------|
| **ID** | CP-CA-005 |
| **Título** | Reenviar invitación al portal |
| **Prioridad** | Media |

**Prerrequisitos:**
- El contacto ya tiene acceso al portal previamente otorgado (ver CP-CA-003)

**Pasos:**
1. Ir al **Menú Principal**
2. Navegar a **Cuentas**
3. Seleccionar una cuenta existente
4. En la vista formulario, pulsar el botón **Gestionar Cuenta**
5. Se muestra una lista con los usuarios que ya tienen acceso al portal
6. Pulsar el botón **Volver a Invitar** en el contacto deseado

**Resultado Esperado:**
- Se reenvía la invitación al correo del contacto
- El contacto recibe un nuevo email con acceso al portal

**Criterios de Aceptación:**
- [ ] Solo se muestran usuarios con acceso previo
- [ ] Botón "Volver a Invitar" funcional
- [ ] Email reenviado correctamente

---

#### CP-CA-006: Gestión de créditos de cliente
| Campo | Valor |
|-------|-------|
| **ID** | CP-CA-006 |
| **Título** | Crear y gestionar créditos |
| **Prioridad** | Alta |

**Prerrequisitos:**
- Cuenta existente a la que se quiere añadir el crédito

**Pasos:**
1. Ir al **Menú Principal**
2. Navegar a **Cuentas**
3. En el menú superior, buscar **Crédito**
4. Pulsar **Nuevo**
5. En el formulario que se abre, completar:
   - **Cuenta** (seleccionar la cuenta)
   - **Concepto**
   - **Fecha**
   - **Cantidad**
6. Guardar
7. El crédito puede ser **Aceptado** o **Rechazado**

**Resultado Esperado:**
- El crédito se crea correctamente asociado a la cuenta
- Se puede gestionar el estado (aceptar/rechazar)

**Criterios de Aceptación:**
- [ ] Formulario de crédito abre correctamente
- [ ] Cuenta asociada
- [ ] Concepto, fecha y cantidad guardados
- [ ] Botón Aceptar funcional
- [ ] Botón Rechazar funcional

---

#### CP-CA-007: Rechazar solicitud de crédito
| Campo | Valor |
|-------|-------|
| **ID** | CP-CA-007 |
| **Título** | Usar wizard de rechazo de crédito |
| **Prioridad** | Media |

**Pasos:**
1. Abrir una solicitud de crédito pendiente
2. Clic en **Rechazar**
3. En el wizard, ingresar **motivo de rechazo**
4. Confirmar

**Resultado Esperado:**
- La solicitud pasa a estado "Rechazado"
- Se guarda el motivo de rechazo
- Se notifica al cliente (si aplica)

**Criterios de Aceptación:**
- [ ] Estado cambiado a "Rechazado"
- [ ] Motivo registrado
- [ ] Email enviado (si configurado)

---

## 2. dev_attendance_dashboard_advanced - Dashboard de Asistencia

### 2.1 Descripción
Dashboard avanzado para visualización de asistencias de empleados con calendario mensual.

### 2.2 Prerrequisitos
- Usuario con permisos de HR
- Módulos `hr_attendance` y `hr_holidays` instalados
- Empleados con registros de asistencia

### 2.3 Casos de Prueba

#### CP-AD-001: Visualizar dashboard mensual
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-001 |
| **Título** | Ver dashboard de asistencia mensual |
| **Prioridad** | Alta |

**Pasos:**
1. Navegar a **Asistencias → Dashboard Mensual**
2. Observar el calendario de asistencias
3. Verificar que se muestran todos los empleados

**Resultado Esperado:**
- Se muestra el calendario del mes actual
- Cada empleado tiene una fila
- Los días muestran el estado (asistencia, ausencia, festivo)

**Criterios de Aceptación:**
- [ ] Dashboard carga correctamente
- [ ] Empleados visibles
- [ ] Estados de días correctos

---

#### CP-AD-002: Filtrar por empresa
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-002 |
| **Título** | Aplicar filtro de empresa |
| **Prioridad** | Media |

**Pasos:**
1. En el dashboard, localizar el filtro de **Empresa**
2. Seleccionar una empresa específica
3. Observar los resultados

**Resultado Esperado:**
- Solo se muestran empleados de la empresa seleccionada
- Los datos se actualizan inmediatamente

**Criterios de Aceptación:**
- [ ] Filtro funciona
- [ ] Datos filtrados correctamente
- [ ] Sin empleados de otras empresas

---

#### CP-AD-003: Cambiar período (mes/año)
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-003 |
| **Título** | Navegación entre meses y años |
| **Prioridad** | Media |

**Pasos:**
1. Usar los controles de navegación para cambiar al mes anterior
2. Verificar que los datos cambian
3. Cambiar de año
4. Verificar datos históricos

**Resultado Esperado:**
- El calendario muestra el período seleccionado
- Los datos de asistencia corresponden al período

**Criterios de Aceptación:**
- [ ] Navegación fluida
- [ ] Datos históricos correctos
- [ ] Sin errores de carga

---

#### CP-AD-004: Ver detalle de asistencia
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-004 |
| **Título** | Consultar detalle de un día |
| **Prioridad** | Alta |

**Pasos:**
1. En el calendario, hacer clic en un día con asistencia
2. Observar el popup/modal de detalle
3. Verificar la información mostrada

**Resultado Esperado:**
- Se muestra hora de check-in
- Se muestra hora de check-out
- Se muestra total de horas trabajadas

**Criterios de Aceptación:**
- [ ] Popup/modal se abre
- [ ] Horas correctas
- [ ] Cálculo de horas trabajadas correcto

---

#### CP-AD-005: Resumen de ausencias mensual
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-005 |
| **Título** | Ver resumen lateral de ausencias |
| **Prioridad** | Media |

**Pasos:**
1. Observar el panel lateral del dashboard
2. Verificar el resumen de ausencias
3. Revisar los detalles por empleado

**Resultado Esperado:**
- Se muestra resumen de ausencias del mes
- Incluye nombre del empleado, fechas y motivos
- Botón para ver más detalles

**Criterios de Aceptación:**
- [ ] Panel visible
- [ ] Datos de ausencias correctos
- [ ] Enlaces a registros funcionales

---

#### CP-AD-006: Generar informe PDF
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-006 |
| **Título** | Exportar asistencias a PDF |
| **Prioridad** | Baja |

**Pasos:**
1. Aplicar los filtros deseados
2. Clic en **Exportar PDF** o **Imprimir**
3. Descargar el documento

**Resultado Esperado:**
- Se genera un PDF con el resumen de asistencias
- El documento incluye los filtros aplicados
- Formato legible y profesional

**Criterios de Aceptación:**
- [ ] PDF generado
- [ ] Contenido correcto
- [ ] Formato adecuado

---

#### CP-AD-007: Visibilidad menú Vista General (Seguridad)
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-007 |
| **Título** | Verificar ocultamiento de menú para empleados |
| **Prioridad** | Alta |

**Pasos:**
1. Iniciar sesión como empleado raso (solo `base.group_user`)
2. Navegar a **Asistencias**
3. Verificar que el menú "Vista general" NO está visible
4. Cerrar sesión
5. Iniciar sesión como oficial de HR (`hr_holidays.group_hr_holidays_user`)
6. Verificar que el menú "Vista general" SÍ está visible

**Resultado Esperado:**
- Empleados rasos: menú oculto
- Oficiales HR: menú visible

**Criterios de Aceptación:**
- [ ] Menú oculto para empleados
- [ ] Menú visible para HR
- [ ] Sin errores de acceso

---

#### CP-AD-008: Acceso a datos de empleados
| Campo | Valor |
|-------|-------|
| **ID** | CP-AD-008 |
| **Título** | Verificar permisos de lectura hr.employee |
| **Prioridad** | Alta |

**Pasos:**
1. Iniciar sesión como empleado básico
2. Intentar acceder a datos de `hr.employee` (ej: desde dashboard)
3. Verificar que el campo `tracking_required` es legible

**Resultado Esperado:**
- El empleado puede ver datos básicos de hr.employee
- No puede modificar, crear ni eliminar

**Criterios de Aceptación:**
- [ ] Lectura permitida
- [ ] Escritura denegada
- [ ] Sin errores de acceso

---

## 3. logistics_security - Grupos de Seguridad Logística

### 3.1 Descripción
Módulo que define grupos de seguridad compartidos para los módulos de logística.

### 3.2 Prerrequisitos
- Usuario administrador
- Módulo base instalado

### 3.3 Casos de Prueba

#### CP-LS-001: Verificar existencia de grupos
| Campo | Valor |
|-------|-------|
| **ID** | CP-LS-001 |
| **Título** | Comprobar grupos de seguridad creados |
| **Prioridad** | Alta |

**Pasos:**
1. Navegar a **Configuración → Usuarios y Compañías → Grupos**
2. Buscar "After Sales Department"
3. Buscar "Repair Department"
4. Verificar que ambos existen

**Resultado Esperado:**
- Grupo "After Sales Department" existe
- Grupo "Repair Department" existe
- Ambos tienen la categoría correcta

**Criterios de Aceptación:**
- [ ] Grupos creados
- [ ] Categorías correctas
- [ ] Accesibles desde configuración

---

#### CP-LS-002: Asignar usuarios a grupos
| Campo | Valor |
|-------|-------|
| **ID** | CP-LS-002 |
| **Título** | Añadir usuarios a los grupos |
| **Prioridad** | Alta |

**Pasos:**
1. Abrir el grupo "After Sales Department"
2. En la pestaña "Usuarios", añadir un usuario
3. Guardar
4. Verificar que el usuario aparece en el grupo

**Resultado Esperado:**
- Usuario añadido al grupo
- El usuario hereda los permisos del grupo

**Criterios de Aceptación:**
- [ ] Usuario asignado
- [ ] Visible en lista de usuarios del grupo
- [ ] Permisos aplicados

---

#### CP-LS-003: Verificar permisos del grupo
| Campo | Valor |
|-------|-------|
| **ID** | CP-LS-003 |
| **Título** | Comprobar acceso según grupo |
| **Prioridad** | Alta |

**Pasos:**
1. Iniciar sesión como usuario del grupo "After Sales"
2. Verificar acceso a funciones de postventa
3. Intentar acceder a funciones no permitidas

**Resultado Esperado:**
- Acceso permitido a funciones del departamento
- Acceso denegado a funciones restringidas

**Criterios de Aceptación:**
- [ ] Acceso correcto a funciones permitidas
- [ ] Denegación correcta de funciones restringidas

---

## 4. product_menu - Gestión de Productos

### 4.1 Descripción
Módulo para la gestión avanzada de productos con wizards de importación.

### 4.2 Prerrequisitos
- Usuario con permisos de Inventario
- Módulos `stock` y `client_account` instalados

### 4.3 Casos de Prueba

#### CP-PRM-001: Acceder al menú de productos
| Campo | Valor |
|-------|-------|
| **ID** | CP-PRM-001 |
| **Título** | Verificar menú personalizado de productos |
| **Prioridad** | Media |

**Pasos:**
1. Navegar a **Inventario → Productos**
2. Verificar que las vistas personalizadas están disponibles

**Resultado Esperado:**
- Menú de productos visible
- Vistas personalizadas cargadas

**Criterios de Aceptación:**
- [ ] Menú visible
- [ ] Vistas personalizadas

---

#### CP-PRM-002: Añadir productos con wizard
| Campo | Valor |
|-------|-------|
| **ID** | CP-PRM-002 |
| **Título** | Usar wizard de añadir productos a cuenta |
| **Prioridad** | Alta |

**Pasos:**
1. Abrir una cuenta de partner
2. Usar la acción **Añadir Productos**
3. En el wizard, seleccionar los productos a añadir
4. Confirmar

**Resultado Esperado:**
- Los productos se asocian a la cuenta
- Se crea la relación correctamente

**Criterios de Aceptación:**
- [ ] Wizard abre correctamente
- [ ] Selección de productos funcional
- [ ] Productos asociados

---

#### CP-PRM-003: Importar imágenes de productos
| Campo | Valor |
|-------|-------|
| **ID** | CP-PRM-003 |
| **Título** | Usar wizard de importación de imágenes |
| **Prioridad** | Media |

**Pasos:**
1. Ir a **Inventario → Productos → Importar Imágenes** (o acción similar)
2. Seleccionar archivo(s) de imagen
3. Mapear imágenes con productos (por código, nombre, etc.)
4. Ejecutar importación

**Resultado Esperado:**
- Las imágenes se importan correctamente
- Cada imagen se asocia al producto correspondiente

**Criterios de Aceptación:**
- [ ] Wizard funcional
- [ ] Imágenes importadas
- [ ] Asociación correcta

---

#### CP-PRM-004: Gestionar atributos de productos
| Campo | Valor |
|-------|-------|
| **ID** | CP-PRM-004 |
| **Título** | Configurar atributos y valores |
| **Prioridad** | Media |

**Pasos:**
1. Abrir un producto template
2. Ir a la sección de Atributos
3. Añadir un nuevo atributo con valores
4. Guardar

**Resultado Esperado:**
- Los atributos se crean correctamente
- Se generan las variantes correspondientes

**Criterios de Aceptación:**
- [ ] Atributos creados
- [ ] Valores asignados
- [ ] Variantes generadas

---

## 5. package_menu - Gestión de Paquetes

### 5.1 Descripción
Módulo para la gestión de paquetes de stock con secuencias automáticas.

### 5.2 Prerrequisitos
- Usuario con permisos de Inventario
- Módulos `stock` y `client_account` instalados

### 5.3 Casos de Prueba

#### CP-PM-001: Acceder al menú de paquetes
| Campo | Valor |
|-------|-------|
| **ID** | CP-PM-001 |
| **Título** | Verificar menú de paquetes |
| **Prioridad** | Media |

**Pasos:**
1. Navegar a **Inventario → Paquetes**
2. Verificar que el menú está visible
3. Verificar que la lista de paquetes carga

**Resultado Esperado:**
- Menú visible y accesible
- Lista de paquetes cargada

**Criterios de Aceptación:**
- [ ] Menú visible
- [ ] Lista funcional
- [ ] Sin errores

---

#### CP-PM-002: Crear nuevo paquete desde portal
| Campo | Valor |
|-------|-------|
| **ID** | CP-PM-002 |
| **Título** | Crear paquete desde el portal |
| **Prioridad** | Alta |

**Pasos:**
1. Acceder al **Portal**
2. Navegar a la sección de **Paquetes**
3. Clic en **Crear Nuevo Paquete**
4. Completar los datos del paquete
5. Guardar

**Resultado Esperado:**
- Se genera un número de paquete automático (secuencia)
- El paquete se guarda correctamente
- El paquete queda asociado a la cuenta del usuario del portal

**Criterios de Aceptación:**
- [ ] Secuencia generada automáticamente
- [ ] Formato correcto del número de paquete
- [ ] Paquete visible en el portal
- [ ] Paquete visible en el backend (Inventario → Paquetes)

---

#### CP-PM-003: Verificar paquete en backend
| Campo | Valor |
|-------|-------|
| **ID** | CP-PM-003 |
| **Título** | Verificar paquete creado desde portal en backend |
| **Prioridad** | Media |

**Prerrequisitos:**
- Paquete creado desde el portal (ver CP-PM-002)

**Pasos:**
1. Ir a **Inventario → Paquetes**
2. Buscar el paquete creado desde el portal
3. Verificar que tiene la cuenta (account_partner) asociada
4. Verificar los datos del paquete

**Resultado Esperado:**
- El paquete aparece en la lista del backend
- La cuenta del cliente está correctamente vinculada
- Los datos coinciden con lo ingresado en el portal

**Criterios de Aceptación:**
- [ ] Paquete visible en backend
- [ ] Account partner asociado correctamente
- [ ] Datos consistentes entre portal y backend

---

## 6. product_sales_by_location - Ventas por Ubicación

### 6.1 Descripción
Permite seleccionar la ubicación de origen en líneas de pedido de venta.

### 6.2 Prerrequisitos
- Usuario con permisos de Ventas e Inventario
- Módulo `sale_stock` instalado
- Ubicaciones de stock configuradas

### 6.3 Casos de Prueba

#### CP-PSL-001: Crear pedido con ubicación específica
| Campo | Valor |
|-------|-------|
| **ID** | CP-PSL-001 |
| **Título** | Asignar ubicación a línea de pedido |
| **Prioridad** | Alta |

**Pasos:**
1. Crear un nuevo **Pedido de Venta**
2. Añadir un producto a la línea
3. En el campo **Ubicación**, seleccionar una ubicación específica
4. Guardar y confirmar el pedido

**Resultado Esperado:**
- La línea guarda la ubicación seleccionada
- El pedido se puede confirmar

**Criterios de Aceptación:**
- [ ] Campo ubicación visible
- [ ] Ubicación guardada
- [ ] Pedido confirmable

---

#### CP-PSL-002: Validar entrega desde ubicación
| Campo | Valor |
|-------|-------|
| **ID** | CP-PSL-002 |
| **Título** | Entrega sale de ubicación correcta |
| **Prioridad** | Alta |

**Pasos:**
1. Con un pedido confirmado (CP-PSL-001), ir a la entrega
2. Verificar que la ubicación de origen es la seleccionada
3. Validar la entrega

**Resultado Esperado:**
- El picking tiene como origen la ubicación seleccionada
- El stock se descuenta de esa ubicación

**Criterios de Aceptación:**
- [ ] Ubicación origen correcta
- [ ] Stock descontado correctamente
- [ ] Entrega validada

---

#### CP-PSL-003: Múltiples ubicaciones en un pedido
| Campo | Valor |
|-------|-------|
| **ID** | CP-PSL-003 |
| **Título** | Pedido con líneas de diferentes ubicaciones |
| **Prioridad** | Alta |

**Pasos:**
1. Crear un nuevo **Pedido de Venta**
2. Añadir línea 1: Producto A - Ubicación X
3. Añadir línea 2: Producto B - Ubicación Y
4. Confirmar el pedido
5. Verificar las entregas generadas

**Resultado Esperado:**
- Se crean entregas separadas por ubicación
- Cada entrega tiene los productos correctos

**Criterios de Aceptación:**
- [ ] Múltiples entregas creadas
- [ ] Productos correctamente asignados
- [ ] Ubicaciones correctas

---

## 7. quality_control_imei - Control de Calidad IMEI

### 7.1 Descripción
Control de calidad con validación de IMEI mediante API externa.

### 7.2 Prerrequisitos
- Módulos `stock` y `quality_control` instalados
- Acceso a API de validación IMEI
- Productos con tracking por serial

### 7.3 Casos de Prueba

#### CP-QCI-001: Configurar credenciales API
| Campo | Valor |
|-------|-------|
| **ID** | CP-QCI-001 |
| **Título** | Configurar conexión API IMEI |
| **Prioridad** | Alta |

**Pasos:**
1. Ir a **Configuración → Ajustes Generales**
2. Buscar la sección de **IMEI API**
3. Ingresar las credenciales (API Key, URL, etc.)
4. Guardar

**Resultado Esperado:**
- Las credenciales se guardan correctamente
- Se puede probar la conexión

**Criterios de Aceptación:**
- [ ] Campos de configuración visibles
- [ ] Credenciales guardadas
- [ ] Test de conexión funcional

---

#### CP-QCI-002: Validar IMEI en check de calidad
| Campo | Valor |
|-------|-------|
| **ID** | CP-QCI-002 |
| **Título** | Validar IMEI durante control de calidad |
| **Prioridad** | Alta |

**Pasos:**
1. Abrir un **Check de Calidad** para un producto con IMEI
2. Ingresar el número IMEI
3. Clic en **Validar IMEI**
4. Observar el resultado

**Resultado Esperado:**
- La API responde con el estado del IMEI
- Se muestra si es válido o inválido
- Se registra el resultado

**Criterios de Aceptación:**
- [ ] Llamada a API exitosa
- [ ] Resultado mostrado
- [ ] Estado registrado

---

#### CP-QCI-003: Generar números de serie con wizard
| Campo | Valor |
|-------|-------|
| **ID** | CP-QCI-003 |
| **Título** | Generar seriales automáticamente |
| **Prioridad** | Media |

**Pasos:**
1. Ir a **Inventario → Operaciones** o usar acción de generación
2. Abrir el wizard **Generar Números de Serie**
3. Configurar el prefijo, cantidad y formato
4. Ejecutar

**Resultado Esperado:**
- Se generan los números de serie según la configuración
- La secuencia es correcta

**Criterios de Aceptación:**
- [ ] Wizard funcional
- [ ] Seriales generados
- [ ] Formato correcto

---

## 8. repair_module - Módulo de Reparaciones

### 8.1 Descripción
Módulo integral para gestión de reparaciones, incluyendo alertas de calidad, movimientos de stock y órdenes de reparación.

### 8.2 Prerrequisitos
- Módulos `quality`, `quality_control`, `repair`, `stock_expedition`, `logistics_security` instalados
- Configurar equipos de calidad con líderes
- Usuarios en grupo "After Sales Department"
- Ubicaciones de reparación configuradas

### 8.3 Casos de Prueba

#### CP-RM-001: Crear alerta de calidad desde portal
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-001 |
| **Título** | Crear alerta de reparación desde portal |
| **Prioridad** | Alta |

**Pasos:**
1. Acceder al **Portal de Reparaciones**
2. Clic en **Crear Nueva Alerta**
3. Seleccionar productos del catálogo
4. Para productos sin lote: seleccionar ubicación
5. Guardar

**Resultado Esperado:**
- Se crea la alerta de calidad
- Los productos quedan asociados
- Las ubicaciones se guardan correctamente

**Criterios de Aceptación:**
- [ ] Alerta creada
- [ ] Productos asociados
- [ ] Ubicaciones correctas

---

#### CP-RM-002: Stock.picking automático al crear alerta
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-002 |
| **Título** | Verificar creación automática de picking |
| **Prioridad** | Alta |

**Pasos:**
1. Crear una alerta de calidad (CP-RM-001)
2. Ir al backend y abrir la alerta
3. Verificar el campo **Pickings Relacionados**

**Resultado Esperado:**
- Se crea automáticamente un stock.picking
- El picking tiene los productos correctos
- La ubicación origen viene del tipo de operación

**Criterios de Aceptación:**
- [ ] Picking creado
- [ ] Productos correctos
- [ ] Ubicaciones correctas

---

#### CP-RM-003: Asignación automática de líder
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-003 |
| **Título** | Verificar asignación de líder del equipo |
| **Prioridad** | Alta |

**Prerrequisitos adicionales:**
- Configurar un equipo de calidad con `leader_id` asignado

**Pasos:**
1. Crear una alerta de calidad
2. Verificar el campo **Responsable (user_id)**

**Resultado Esperado:**
- El user_id se asigna automáticamente al líder del equipo
- Si no hay líder, el campo queda vacío

**Criterios de Aceptación:**
- [ ] Líder asignado automáticamente
- [ ] Campo vacío si no hay líder

---

#### CP-RM-004: Dominio de usuarios en alerta
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-004 |
| **Título** | Verificar dominio del campo user_id |
| **Prioridad** | Media |

**Pasos:**
1. Abrir una alerta de calidad en el backend
2. Hacer clic en el campo **Responsable (user_id)**
3. Verificar las opciones disponibles

**Resultado Esperado:**
- Solo aparecen usuarios del grupo "After Sales Department"
- No se pueden seleccionar usuarios fuera del grupo

**Criterios de Aceptación:**
- [ ] Dominio aplicado
- [ ] Solo usuarios After Sales

---

#### CP-RM-005: Cancelar picking → Cancelar alerta
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-005 |
| **Título** | Cancelación automática de alerta al cancelar picking |
| **Prioridad** | Alta |

**Pasos:**
1. Crear una alerta con su picking asociado
2. Ir al picking y cancelarlo
3. Volver a la alerta

**Resultado Esperado:**
- La alerta pasa automáticamente a estado "Cancelado"
- Se registra el cambio en el chatter

**Criterios de Aceptación:**
- [ ] Estado cambiado a Cancelado
- [ ] Mensaje en chatter

---

#### CP-RM-006: Confirmar picking → Crear repair.order
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-006 |
| **Título** | Crear orden de reparación al confirmar picking |
| **Prioridad** | Alta |

**Pasos:**
1. Crear una alerta con su picking asociado
2. Ir al picking y validarlo (completar qty_done con PDA o manualmente)
3. Volver a la alerta

**Resultado Esperado:**
- La alerta pasa a estado "Enviado para Revisión/Reparación"
- Se crea automáticamente una orden de reparación (repair.order)

**Criterios de Aceptación:**
- [ ] Estado cambiado a Enviado
- [ ] Repair.order creada
- [ ] Productos correctos en la orden

---

#### CP-RM-007: Escanear lote con PDA
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-007 |
| **Título** | Validar picking con escaneo de lote |
| **Prioridad** | Alta |

**Pasos:**
1. Crear una alerta con producto que tiene lote/serial
2. Ir al picking desde la app de código de barras
3. Escanear el número de serie/lote del producto
4. Verificar que se asigna correctamente

**Resultado Esperado:**
- El lote se escanea y asigna correctamente
- qty_done se actualiza (inicialmente era 0)
- Sin error de "serial ya asignado"

**Criterios de Aceptación:**
- [ ] Escaneo funcional
- [ ] qty_done actualizado
- [ ] Sin errores de validación

---

#### CP-RM-008: Iniciar reparación
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-008 |
| **Título** | Acción action_repair_start |
| **Prioridad** | Alta |

**Pasos:**
1. Abrir una orden de reparación validada
2. Ejecutar **Iniciar Reparación**
3. Verificar el estado de la alerta de calidad relacionada

**Resultado Esperado:**
- La orden de reparación pasa a estado "En Reparación"
- La alerta de calidad pasa a estado "Reparando"

**Criterios de Aceptación:**
- [ ] Estado repair.order correcto
- [ ] Estado quality.alert correcto

---

#### CP-RM-009: Finalizar reparación
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-009 |
| **Título** | Acción action_repair_done |
| **Prioridad** | Alta |

**Pasos:**
1. Tener una orden de reparación en estado "En Reparación"
2. Ejecutar **Finalizar Reparación**
3. Verificar los movimientos de stock generados

**Resultado Esperado:**
- Se crea un movimiento interno
- Origen: "Stock Reparaciones" (`repair_module.stock_location_repairs`)
- Destino: "Stock a reubicar" (`repair_module.stock_location_to_relocate`)

**Criterios de Aceptación:**
- [ ] Movimiento creado
- [ ] Ubicación origen correcta
- [ ] Ubicación destino correcta

---

#### CP-RM-010: Cambiar técnico con wizard
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-010 |
| **Título** | Usar wizard de cambio de técnico |
| **Prioridad** | Media |

**Pasos:**
1. Abrir una orden de reparación
2. Usar la acción **Cambiar Técnico**
3. Seleccionar nuevo técnico
4. Confirmar

**Resultado Esperado:**
- El técnico se actualiza
- Se registra mensaje en el chatter con el cambio

**Criterios de Aceptación:**
- [ ] Técnico cambiado
- [ ] Mensaje en chatter

---

#### CP-RM-011: Mensaje de asignación al validar
| Campo | Valor |
|-------|-------|
| **ID** | CP-RM-011 |
| **Título** | Verificar mensaje de asignación en chatter |
| **Prioridad** | Baja |

**Pasos:**
1. Validar una orden de reparación
2. Verificar el chatter de la orden

**Resultado Esperado:**
- Se publica un mensaje indicando el técnico asignado

**Criterios de Aceptación:**
- [ ] Mensaje visible
- [ ] Nombre del técnico correcto

---

## 9. APIs RPC

### 9.1 Descripción
Conjunto de módulos para comunicación RPC entre sistemas (cliente, servidor, sincronización).

### 9.2 Prerrequisitos
- Dependencias Python: `jwt`, `marshmallow`, `cryptography`
- Configuración de parámetros del sistema

### 9.3 Casos de Prueba

#### CP-RPC-001: Configurar servidor RPC
| Campo | Valor |
|-------|-------|
| **ID** | CP-RPC-001 |
| **Título** | Crear y configurar servidor RPC |
| **Prioridad** | Alta |

**Pasos:**
1. Ir a **Configuración → RPC → Servidores**
2. Crear nuevo servidor
3. Configurar URL, credenciales, etc.
4. Guardar

**Resultado Esperado:**
- Servidor configurado correctamente
- Conexión establecida

**Criterios de Aceptación:**
- [ ] Servidor creado
- [ ] Conexión funcional

---

#### CP-RPC-002: Autenticación JWT
| Campo | Valor |
|-------|-------|
| **ID** | CP-RPC-002 |
| **Título** | Verificar generación de tokens JWT |
| **Prioridad** | Alta |

**Pasos:**
1. Ejecutar endpoint de autenticación
2. Verificar que se genera un token JWT
3. Usar el token para una petición autenticada

**Resultado Esperado:**
- Token generado correctamente
- Peticiones autenticadas funcionan

**Criterios de Aceptación:**
- [ ] Token generado
- [ ] Autenticación funcional

---

#### CP-RPC-003: Sincronización de datos
| Campo | Valor |
|-------|-------|
| **ID** | CP-RPC-003 |
| **Título** | Ejecutar sincronización entre sistemas |
| **Prioridad** | Alta |

**Pasos:**
1. Configurar la acción de sincronización
2. Ejecutar manualmente o por cron
3. Verificar los datos sincronizados

**Resultado Esperado:**
- Datos sincronizados correctamente
- Sin errores ni duplicados

**Criterios de Aceptación:**
- [ ] Sincronización exitosa
- [ ] Datos correctos
- [ ] Sin duplicados

---

## 10. stock_barcode_picking_batch - Batch Picking con Código de Barras

### 10.1 Descripción
Extensión para procesar lotes de pickings desde la aplicación de código de barras.

### 10.2 Prerrequisitos
- Módulos `stock_barcode` y `stock_picking_batch` instalados
- Dispositivo con escáner o cámara

### 10.3 Casos de Prueba

#### CP-SBB-001: Crear batch de pickings
| Campo | Valor |
|-------|-------|
| **ID** | CP-SBB-001 |
| **Título** | Crear lote de pickings |
| **Prioridad** | Alta |

**Pasos:**
1. Ir a **Inventario → Operaciones → Lotes de Picking**
2. Crear nuevo batch
3. Añadir pickings al batch
4. Confirmar

**Resultado Esperado:**
- Batch creado con los pickings seleccionados
- Estado: Esperando

**Criterios de Aceptación:**
- [ ] Batch creado
- [ ] Pickings asociados
- [ ] Estado correcto

---

#### CP-SBB-002: Procesar batch con barcode
| Campo | Valor |
|-------|-------|
| **ID** | CP-SBB-002 |
| **Título** | Procesar batch desde app barcode |
| **Prioridad** | Alta |

**Pasos:**
1. Abrir la app de **Código de Barras**
2. Seleccionar el batch a procesar
3. Escanear productos/ubicaciones
4. Completar y validar

**Resultado Esperado:**
- Interfaz de batch en barcode funcional
- Todos los pickings se procesan
- Batch completado

**Criterios de Aceptación:**
- [ ] Interfaz funcional
- [ ] Escaneo correcto
- [ ] Batch completado

---

## 11. stock_expedition - Expediciones

### 11.1 Descripción
Módulo para gestión de expediciones de productos.

### 11.2 Prerrequisitos
- Módulos `sale` y `product_sales_by_location` instalados

### 11.3 Casos de Prueba

#### CP-SE-001: Crear expedición desde portal
| Campo | Valor |
|-------|-------|
| **ID** | CP-SE-001 |
| **Título** | Crear nueva expedición |
| **Prioridad** | Alta |

**Pasos:**
1. Acceder al **Portal de Expediciones**
2. Clic en **Crear Nueva Expedición**
3. Completar datos requeridos
4. Guardar

**Resultado Esperado:**
- Expedición creada correctamente
- Estado inicial correcto

**Criterios de Aceptación:**
- [ ] Expedición creada
- [ ] Datos guardados
- [ ] Estado correcto

---

#### CP-SE-002: Seleccionar lotes desde catálogo
| Campo | Valor |
|-------|-------|
| **ID** | CP-SE-002 |
| **Título** | Añadir productos desde catálogo |
| **Prioridad** | Alta |

**Pasos:**
1. En el modal de expedición, abrir el **Catálogo**
2. Buscar y seleccionar lotes/productos
3. Ajustar cantidades si es necesario
4. Volver al modal

**Resultado Esperado:**
- Los lotes seleccionados aparecen en el formulario
- Las cantidades son correctas

**Criterios de Aceptación:**
- [ ] Catálogo funcional
- [ ] Selección correcta
- [ ] Cantidades correctas

---

#### CP-SE-003: Sincronización catálogo-modal
| Campo | Valor |
|-------|-------|
| **ID** | CP-SE-003 |
| **Título** | Verificar sincronización de cambios |
| **Prioridad** | Alta |

**Pasos:**
1. Seleccionar varios productos del catálogo
2. Volver al modal
3. Volver al catálogo y modificar/eliminar algún producto
4. Volver al modal

**Resultado Esperado:**
- Los cambios se reflejan correctamente en el modal
- No hay productos duplicados ni incorrectos

**Criterios de Aceptación:**
- [ ] Sincronización correcta
- [ ] Sin duplicados
- [ ] Cambios reflejados

---

## 12. stock_menu - Menú de Stock

### 12.1 Descripción
Personalización del menú de inventario/stock.

### 12.2 Prerrequisitos
- Módulos `stock` y `client_account` instalados

### 12.3 Casos de Prueba

#### CP-SM-001: Verificar menú de stock
| Campo | Valor |
|-------|-------|
| **ID** | CP-SM-001 |
| **Título** | Comprobar menú personalizado |
| **Prioridad** | Media |

**Pasos:**
1. Navegar a **Inventario**
2. Verificar que las opciones de menú personalizadas están visibles
3. Acceder a las diferentes opciones

**Resultado Esperado:**
- Menú personalizado visible
- Todas las opciones funcionales

**Criterios de Aceptación:**
- [ ] Menú visible
- [ ] Opciones funcionales
- [ ] Sin errores

---

## 13. stock_reception - Recepción de Paquetes

### 13.1 Descripción
Módulo para gestión de recepción de paquetes con control de calidad integrado.

### 13.2 Prerrequisitos
- Almacén configurado con recepción en 3 pasos
- Punto de control de calidad configurado para operación "Control de calidad"
- Módulos de calidad instalados

### 13.3 Casos de Prueba

#### CP-SR-001: Configurar recepción en 3 pasos
| Campo | Valor |
|-------|-------|
| **ID** | CP-SR-001 |
| **Título** | Configurar almacén con 3 pasos de recepción |
| **Prioridad** | Alta |

**Prerrequisitos:**
- Acceso de administrador

**Pasos:**
1. Ir a **Inventario → Configuración → Almacenes**
2. Abrir el almacén principal
3. En **Envíos entrantes**, seleccionar **Recibir mercancías en ubicación de entrada, luego stock (3 pasos)**
4. Guardar

**Resultado Esperado:**
- Se crean los tipos de operación: Recepción, Control de Calidad, Almacenar
- El flujo de 3 pasos está activo

**Criterios de Aceptación:**
- [ ] Configuración guardada
- [ ] Tipos de operación creados
- [ ] Flujo funcional

---

#### CP-SR-002: Punto de control de calidad
| Campo | Valor |
|-------|-------|
| **ID** | CP-SR-002 |
| **Título** | Verificar generación de checks de calidad |
| **Prioridad** | Alta |

**Pasos:**
1. Crear un picking de recepción con productos
2. Validar la recepción (paso 1)
3. Ir al picking de "Control de Calidad" (paso 2)
4. Verificar que se generan los checks de calidad

**Resultado Esperado:**
- Se generan checks de calidad automáticamente
- Cada producto tiene su check asociado

**Criterios de Aceptación:**
- [ ] Checks generados
- [ ] Asociados al picking correcto
- [ ] Tipo de test correcto (Aprueba/Falla)

---

#### CP-SR-003: Asignar account_partner en picking
| Campo | Valor |
|-------|-------|
| **ID** | CP-SR-003 |
| **Título** | Asignar cuenta de partner en recepción |
| **Prioridad** | Media |

**Pasos:**
1. Abrir un picking de recepción
2. Localizar el campo **Account Partner**
3. Seleccionar una cuenta de partner
4. Guardar

**Resultado Esperado:**
- El campo es visible y editable
- La cuenta se guarda correctamente

**Criterios de Aceptación:**
- [ ] Campo visible
- [ ] Selección funcional
- [ ] Datos guardados

---

#### CP-SR-004: Campo show_account_partner
| Campo | Valor |
|-------|-------|
| **ID** | CP-SR-004 |
| **Título** | Verificar visibilidad condicional del campo |
| **Prioridad** | Media |

**Pasos:**
1. Abrir un picking de tipo "entrante" (recepción)
2. Verificar que el campo account_partner es visible
3. Abrir un picking de tipo "interno"
4. Verificar la visibilidad del campo según configuración

**Resultado Esperado:**
- El campo `show_account_partner` controla la visibilidad
- Para recepciones: visible
- Para otros tipos: según configuración

**Criterios de Aceptación:**
- [ ] Visibilidad correcta en recepciones
- [ ] Comportamiento correcto en otros tipos

---

#### CP-SR-005: Validar control de calidad
| Campo | Valor |
|-------|-------|
| **ID** | CP-SR-005 |
| **Título** | Completar paso de control de calidad |
| **Prioridad** | Alta |

**Pasos:**
1. Tener un picking en paso de "Control de Calidad"
2. Completar todos los checks de calidad (Aprobar/Fallar)
3. Validar el picking

**Resultado Esperado:**
- Todos los checks deben estar completados para validar
- El picking pasa al siguiente paso

**Criterios de Aceptación:**
- [ ] Checks completables
- [ ] Validación exitosa
- [ ] Siguiente paso iniciado

---

## 📊 Resumen de Pruebas

| Módulo | Casos de Prueba | Prioridad Alta | Prioridad Media | Prioridad Baja |
|--------|-----------------|----------------|-----------------|----------------|
| client_account | 7 | 5 | 2 | 0 |
| dev_attendance_dashboard_advanced | 8 | 4 | 3 | 1 |
| logistics_security | 3 | 2 | 1 | 0 |
| package_menu | 3 | 1 | 2 | 0 |
| product_menu | 4 | 1 | 3 | 0 |
| product_sales_by_location | 3 | 3 | 0 | 0 |
| quality_control_imei | 3 | 2 | 1 | 0 |
| repair_module | 11 | 8 | 2 | 1 |
| APIs RPC | 3 | 3 | 0 | 0 |
| stock_barcode_picking_batch | 2 | 2 | 0 | 0 |
| stock_expedition | 3 | 3 | 0 | 0 |
| stock_menu | 1 | 0 | 1 | 0 |
| stock_reception | 5 | 3 | 2 | 0 |
| **TOTAL** | **56** | **37** | **17** | **2** |

---

## 📝 Notas Adicionales

### Orden Recomendado de Ejecución

1. **logistics_security** - Base de grupos de seguridad
2. **client_account** - Gestión de cuentas (dependencia común)
3. **product_menu** / **stock_menu** - Configuración de productos
4. **package_menu** - Gestión de paquetes
5. **product_sales_by_location** - Ventas con ubicación
6. **stock_reception** - Recepción de productos
7. **repair_module** - Flujo de reparaciones (más complejo)
8. **stock_expedition** - Expediciones
9. **dev_attendance_dashboard_advanced** - Dashboard HR
10. **quality_control_imei** - Control IMEI
11. **APIs RPC** - Integraciones

### Datos de Prueba Recomendados

- **Usuarios:** Crear al menos 3 usuarios con diferentes roles
- **Productos:** Productos con y sin tracking (lote/serial)
- **Ubicaciones:** Múltiples ubicaciones de stock
- **Equipos de calidad:** Con líderes asignados
- **Clientes:** Con cuentas de partner asociadas

---

*Documento generado automáticamente - Revisar y adaptar según necesidades específicas del proyecto*

