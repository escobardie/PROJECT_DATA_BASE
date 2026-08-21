# Checklist — Registro Clientes Star

## 🔴 Errores

* [ ] Revisar errores pendientes en Django Admin.
* [ ] Verificar relaciones `select_related()` después de modificar modelos.
* [ ] Revisar errores de migraciones.
* [ ] Comprobar restricciones y claves foráneas de MySQL.

---

## 🟠 Pendiente de revisar

### Orden de Trabajo

* [ ] Revisar modelo `OrdenTrabajo`.
* [ ] Revisar relación `OrdenTrabajo → Instalacion`.
* [ ] Verificar fechas de la OT.
* [ ] Revisar validaciones de estados.
* [ ] Revisar `admin.py`.

### Instalación

* [ ] Revisar modelo `Instalacion`.
* [ ] Verificar `InstalacionDispositivo`.
* [ ] Revisar técnicos asignados.
* [ ] Comprobar estados de instalación.

### Proyecto

* [ ] Revisar `Proyecto`.
* [ ] Revisar `ProyectoDetalle`.
* [ ] Revisar `ProyectoRequerimiento`.
* [ ] Comprobar cálculo de valores.
* [ ] Revisar estados del proyecto.

### Dispositivos

* [ ] Revisar `Dispositivo`.
* [ ] Revisar `ModeloDispositivo`.
* [ ] Verificar marcas y tipos.
* [ ] Revisar valores de mercado.

### Telecom

* [ ] Revisar zonas.
* [ ] Revisar factores.
* [ ] Revisar conceptos.
* [ ] Revisar recargos.
* [ ] Verificar cálculos.

---

## 🟡 Mejoras

* [ ] Optimizar consultas ORM.
* [ ] Revisar uso de `select_related()`.
* [ ] Revisar uso de `prefetch_related()`.
* [ ] Agregar índices donde corresponda.
* [ ] Mejorar validaciones de modelos.
* [ ] Mejorar mensajes del Django Admin.
* [ ] Revisar permisos de usuarios.

---

## 🔵 Ideas futuras

* [ ] Dashboard principal.
* [ ] Reportes de órdenes de trabajo.
* [ ] Historial de cambios.
* [ ] Exportación a Excel.
* [ ] Exportación a PDF.
* [ ] Notificaciones.
* [ ] Auditoría de modificaciones.

---

## ✅ Corregido

* [x] Relación OT → Instalación funcionando.
* [x] Eliminada referencia antigua a `servicio_contratado` en Instalación.
* [x] Corregido problema con `date_hierarchy`.
* [x] Proyecto funcionando antes de generar OT.

---

## 📝 Notas

Agregar aquí observaciones que todavía no tengan una tarea concreta.

### Ejemplo

**Fecha:** YYYY-MM-DD

**Módulo:** `orden_trabajo`

**Problema:**

Descripción del problema encontrado.

**Archivo:**

`apps/orden_trabajo/models/orden_trabajo.py`

**Posible solución:**

Descripción de lo que habría que revisar.

**Estado:** Pendiente
