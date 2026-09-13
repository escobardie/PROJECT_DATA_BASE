"use strict";


(() => {

    const SELECTOR_CLASS = (
        "proyecto-detalle-origen-selector"
    );


    // ======================================================
    // CONFIGURACIÓN
    // ======================================================

    const METADATA_URL = (
        window.PROYECTO_DETALLE_METADATA_URL
        || ""
    );

    // ======================================================
    // CONFIGURACIÓN MONETARIA
    // ======================================================

    const DECIMALES_MONETARIOS = 2;

    // ======================================================
    // HELPERS
    // ======================================================

    function obtenerWrapper(select) {

        if (!select) {
            return null;
        }

        return (
            select.closest(
                ".related-widget-wrapper"
            )
            || select
        );
    }


    function mostrarSelect(
        select,
        mostrar,
    ) {

        const wrapper = obtenerWrapper(
            select
        );

        if (!wrapper) {
            return;
        }

        wrapper.style.display = (
            mostrar
                ? ""
                : "none"
        );
    }


    function limpiarSelect(
        select,
    ) {

        if (!select) {
            return;
        }

        if (
            window.django
            && window.django.jQuery
        ) {

            window.django
                .jQuery(select)
                .val(null)
                .trigger("change");

            return;
        }

        select.value = "";

        select.dispatchEvent(
            new Event(
                "change",
                {
                    bubbles: true,
                }
            )
        );
    }


    function registrarCambioSelect(
        select,
        callback,
    ) {

        if (
            window.django
            && window.django.jQuery
        ) {

            window.django
                .jQuery(select)
                .off(
                    "change.proyectoDetalle"
                )
                .on(
                    "change.proyectoDetalle",
                    callback
                );

            return;
        }

        select.addEventListener(
            "change",
            callback
        );
    }


    function crearRadio(
        {
            name,
            value,
            texto,
        }
    ) {

        const label = (
            document.createElement(
                "label"
            )
        );

        label.style.display = "inline-flex";
        label.style.alignItems = "center";
        label.style.gap = "5px";
        label.style.marginRight = "14px";
        label.style.cursor = "pointer";
        label.style.whiteSpace = "nowrap";


        const input = (
            document.createElement(
                "input"
            )
        );

        input.type = "radio";
        input.name = name;
        input.value = value;


        label.appendChild(
            input
        );

        label.appendChild(
            document.createTextNode(
                texto
            )
        );


        return {
            label,
            input,
        };
    }


    // ======================================================
    // CAMPOS DE LA FILA
    // ======================================================

    function obtenerCamposFila(
        fila,
    ) {

        return {

            // ==================================================
            // ORIGEN
            // ==================================================

            dispositivo: (
                fila.querySelector(
                    'select[name$="-dispositivo"]'
                )
            ),

            itemCatalogo: (
                fila.querySelector(
                    'select[name$="-item_catalogo"]'
                )
            ),

            // ==================================================
            // INFORMACIÓN
            // ==================================================

            descripcion: (
                fila.querySelector(
                    'textarea[name$="-descripcion"],'
                    + 'input[name$="-descripcion"]'
                )
            ),

            // ==================================================
            // CÁLCULO
            // ==================================================

            cantidad: (
                fila.querySelector(
                    'input[name$="-cantidad"]'
                )
            ),

            precioUnitario: (
                fila.querySelector(
                    'input[name$="-precio_unitario"]'
                )
            ),

            descuentoImporte: (
                fila.querySelector(
                    'input[name$="-descuento_importe"]'
                )
            ),

            impuestosImporte: (
                fila.querySelector(
                    'input[name$="-impuestos_importe"]'
                )
            ),

            // ==================================================
            // READONLY
            // ==================================================

            tipoReadonly: (
                fila.querySelector(
                    ".field-tipo .readonly,"
                    + ".field-tipo p"
                )
            ),

            unidadReadonly: (
                fila.querySelector(
                    ".field-unidad .readonly,"
                    + ".field-unidad p"
                )
            ),

            subtotalCelda: (
                fila.querySelector(
                    ".field-subtotal"
                )
            ),

            totalCelda: (
                fila.querySelector(
                    ".field-total"
                )
            ),
        };
    }

    // ======================================================
    // CONVERSIÓN NUMÉRICA
    // ======================================================

    function obtenerNumero(
        campo,
    ) {

        if (!campo) {
            return 0;
        }

        let valor = String(
            campo.value || ""
        ).trim();

        if (!valor) {
            return 0;
        }

        /*
        * Casos admitidos:
        *
        * 125000.50
        * 125000,50
        * 125.000,50
        */

        if (
            valor.includes(".")
            && valor.includes(",")
        ) {

            /*
            * Formato argentino:
            * 125.000,50
            */

            valor = valor
                .replace(/\./g, "")
                .replace(",", ".");

        } else if (
            valor.includes(",")
        ) {

            valor = valor.replace(
                ",",
                "."
            );
        }

        const numero = Number(
            valor
        );

        if (!Number.isFinite(numero)) {
            return 0;
        }

        return numero;
    }

    // ======================================================
    // EVENTOS DE CÁLCULO
    // ======================================================

    function registrarCalculosFila(
        campos,
    ) {

        const camposCalculo = [
            campos.cantidad,
            campos.precioUnitario,
            campos.descuentoImporte,
            campos.impuestosImporte,
        ];

        camposCalculo.forEach(
            (campo) => {

                if (!campo) {
                    return;
                }

                campo.addEventListener(
                    "input",
                    () => {

                        recalcularImportes(
                            campos
                        );
                    }
                );

                campo.addEventListener(
                    "change",
                    () => {

                        recalcularImportes(
                            campos
                        );
                    }
                );
            }
        );
    }

    // ======================================================
    // REDONDEO MONETARIO
    // ======================================================

    function redondearImporte(
        valor,
    ) {

        const factor = (
            10 ** DECIMALES_MONETARIOS
        );

        return (
            Math.round(
                (
                    valor
                    + Number.EPSILON
                )
                * factor
            )
            / factor
        );
    }


    // ======================================================
    // FORMATO VISUAL
    // ======================================================

    function formatearImporte(
        valor,
    ) {

        return new Intl.NumberFormat(
            "es-AR",
            {
                minimumFractionDigits: (
                    DECIMALES_MONETARIOS
                ),
                maximumFractionDigits: (
                    DECIMALES_MONETARIOS
                ),
            }
        ).format(
            valor
        );
    }

    // ======================================================
    // ACTUALIZAR CAMPO READONLY
    // ======================================================

    function actualizarReadonly(
        celda,
        valor,
    ) {

        if (!celda) {
            return;
        }

        const elemento = (
            celda.querySelector(
                ".readonly, p, div"
            )
        );

        if (elemento) {

            elemento.textContent = valor;

            return;
        }

        /*
        * Fallback para cambios futuros
        * en el HTML del Admin.
        */

        celda.textContent = valor;
    }

    // ======================================================
    // RECALCULAR FILA
    // ======================================================

    function recalcularImportes(
        campos,
    ) {

        if (!campos) {
            return;
        }

        const cantidad = obtenerNumero(
            campos.cantidad
        );

        const precioUnitario = obtenerNumero(
            campos.precioUnitario
        );

        const descuento = obtenerNumero(
            campos.descuentoImporte
        );

        const impuestos = obtenerNumero(
            campos.impuestosImporte
        );


        // ==================================================
        // SUBTOTAL
        // ==================================================

        const subtotal = redondearImporte(
            cantidad
            * precioUnitario
        );


        // ==================================================
        // TOTAL
        // ==================================================

        const total = redondearImporte(
            subtotal
            - descuento
            + impuestos
        );


        // ==================================================
        // MOSTRAR RESULTADOS
        // ==================================================

        actualizarReadonly(
            campos.subtotalCelda,
            formatearImporte(
                subtotal
            )
        );

        actualizarReadonly(
            campos.totalCelda,
            formatearImporte(
                total
            )
        );

        // ==================================================
        // RESUMEN DEL PROYECTO
        // ==================================================

        recalcularResumenEconomico();

    }


    // ======================================================
    // CAMBIOS MANUALES
    // ======================================================

    function registrarCambiosManuales(
        campos,
    ) {

        if (campos.descripcion) {

            campos.descripcion.addEventListener(
                "input",
                () => {

                    campos.descripcion.dataset
                        .usuarioEdito = "1";
                }
            );
        }


        if (campos.precioUnitario) {

            campos.precioUnitario.addEventListener(
                "input",
                () => {

                    campos.precioUnitario.dataset
                        .usuarioEdito = "1";
                }
            );
        }
    }


    // ======================================================
    // ACTUALIZAR CAMPOS VISUALES
    // ======================================================

    function aplicarMetadata(
        campos,
        data,
    ) {

        // ==================================================
        // DESCRIPCIÓN
        // ==================================================

        if (
            campos.descripcion
            && (
                campos.descripcion.dataset
                    .usuarioEdito !== "1"
            )
        ) {

            campos.descripcion.value = (
                data.descripcion
                || ""
            );
        }


        // ==================================================
        // PRECIO
        // ==================================================

        if (
            campos.precioUnitario
            && (
                campos.precioUnitario.dataset
                    .usuarioEdito !== "1"
            )
        ) {

            campos.precioUnitario.value = (
                data.precio_unitario
                || "0.00"
            );
        }


        // ==================================================
        // TIPO
        // ==================================================

        if (campos.tipoReadonly) {

            campos.tipoReadonly.textContent = (
                data.tipo_label
                || "—"
            );
        }


        // ==================================================
        // UNIDAD
        // ==================================================

        if (campos.unidadReadonly) {

            campos.unidadReadonly.textContent = (
                data.unidad_label
                || "—"
            );
        }

        // ==================================================
        // RECALCULAR IMPORTES
        // ==================================================

        recalcularImportes(
            campos
        );

    }


    // ======================================================
    // CONSULTAR ORIGEN
    // ======================================================

    async function cargarMetadata(
        fila,
        origen,
        objetoId,
    ) {

        if (
            !METADATA_URL
            || !objetoId
        ) {
            return;
        }

        const url = (
            new URL(
                METADATA_URL,
                window.location.origin
            )
        );

        url.searchParams.set(
            "origen",
            origen
        );

        url.searchParams.set(
            "id",
            objetoId
        );


        try {

            const response = await fetch(
                url.toString(),
                {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "X-Requested-With": (
                            "XMLHttpRequest"
                        ),
                    },
                }
            );

            if (!response.ok) {

                console.error(
                    "No fue posible obtener "
                    + "los datos del origen."
                );

                return;
            }

            const data = (
                await response.json()
            );

            const campos = (
                obtenerCamposFila(
                    fila
                )
            );

            aplicarMetadata(
                campos,
                data
            );

        } catch (error) {

            console.error(
                "Error consultando los datos "
                + "del detalle:",
                error
            );
        }
    }


    // ======================================================
    // LIMPIAR CAMPOS DERIVADOS
    // ======================================================

    function limpiarCamposDerivados(
        campos,
    ) {

        if (
            campos.descripcion
            && (
                campos.descripcion.dataset
                    .usuarioEdito !== "1"
            )
        ) {
            campos.descripcion.value = "";
        }

        if (
            campos.precioUnitario
            && (
                campos.precioUnitario.dataset
                    .usuarioEdito !== "1"
            )
        ) {
            campos.precioUnitario.value = "0.00";
        }

        if (campos.tipoReadonly) {
            campos.tipoReadonly.textContent = "—";
        }

        if (campos.unidadReadonly) {
            campos.unidadReadonly.textContent = "—";
        }

        // ==================================================
        // RECALCULAR
        // ==================================================

        recalcularImportes(
            campos
        );
    }


    // ======================================================
    // INICIALIZAR FILA
    // ======================================================

    function inicializarFila(
        fila,
    ) {

        if (!fila) {
            return;
        }

        if (
            fila.classList.contains(
                "empty-form"
            )
        ) {
            return;
        }


        const campos = (
            obtenerCamposFila(
                fila
            )
        );


        if (
            !campos.dispositivo
            || !campos.itemCatalogo
        ) {
            return;
        }


        if (
            fila.querySelector(
                `.${SELECTOR_CLASS}`
            )
        ) {
            return;
        }


        registrarCambiosManuales(
            campos
        );

        registrarCalculosFila(
            campos
        );
        
        registrarEliminacionFila(
            fila
        );
        
        /*
        * Calcula inmediatamente con los valores
        * que ya están presentes en la fila.
        */
        recalcularImportes(
            campos
        );

        // ==================================================
        // SELECTOR VISUAL
        // ==================================================

        const celdaDispositivo = (
            campos.dispositivo.closest(
                ".field-dispositivo"
            )
        );

        if (!celdaDispositivo) {
            return;
        }


        const selector = (
            document.createElement(
                "div"
            )
        );

        selector.className = (
            SELECTOR_CLASS
        );

        selector.style.marginBottom = "8px";
        selector.style.padding = "7px 8px";
        selector.style.border = (
            "1px solid var(--hairline-color)"
        );
        selector.style.borderRadius = "4px";
        selector.style.background = (
            "var(--darkened-bg)"
        );


        const titulo = (
            document.createElement(
                "div"
            )
        );

        titulo.textContent = "Origen";

        titulo.style.marginBottom = "6px";
        titulo.style.fontSize = "11px";
        titulo.style.fontWeight = "600";
        titulo.style.textTransform = "uppercase";
        titulo.style.color = (
            "var(--body-quiet-color)"
        );


        selector.appendChild(
            titulo
        );


        const identificador = (
            campos.dispositivo.name
                .replace(
                    /[^a-zA-Z0-9_-]/g,
                    "_"
                )
        );

        const nombreRadio = (
            `ui_origen_${identificador}`
        );


        const radioDispositivo = (
            crearRadio(
                {
                    name: nombreRadio,
                    value: "dispositivo",
                    texto: "Dispositivo",
                }
            )
        );


        const radioCatalogo = (
            crearRadio(
                {
                    name: nombreRadio,
                    value: "catalogo",
                    texto: "Ítem de catálogo",
                }
            )
        );


        selector.appendChild(
            radioDispositivo.label
        );

        selector.appendChild(
            radioCatalogo.label
        );


        celdaDispositivo.prepend(
            selector
        );


        // ==================================================
        // APLICAR ORIGEN VISUAL
        // ==================================================

        function aplicarOrigen(
            origen,
            limpiarContrario = false,
        ) {

            if (
                origen === "dispositivo"
            ) {

                radioDispositivo.input.checked = true;
                radioCatalogo.input.checked = false;

                mostrarSelect(
                    campos.dispositivo,
                    true
                );

                mostrarSelect(
                    campos.itemCatalogo,
                    false
                );

                if (limpiarContrario) {

                    limpiarSelect(
                        campos.itemCatalogo
                    );

                    limpiarCamposDerivados(
                        campos
                    );
                }

                return;
            }


            if (
                origen === "catalogo"
            ) {

                radioDispositivo.input.checked = false;
                radioCatalogo.input.checked = true;

                mostrarSelect(
                    campos.dispositivo,
                    false
                );

                mostrarSelect(
                    campos.itemCatalogo,
                    true
                );

                if (limpiarContrario) {

                    limpiarSelect(
                        campos.dispositivo
                    );

                    limpiarCamposDerivados(
                        campos
                    );
                }

                return;
            }


            radioDispositivo.input.checked = false;
            radioCatalogo.input.checked = false;

            mostrarSelect(
                campos.dispositivo,
                false
            );

            mostrarSelect(
                campos.itemCatalogo,
                false
            );
        }


        // ==================================================
        // ESTADO INICIAL
        // ==================================================
        //
        // No consultamos metadata en la carga inicial,
        // porque los valores históricos del Proyecto
        // deben conservarse.
        // ==================================================

        if (campos.dispositivo.value) {

            aplicarOrigen(
                "dispositivo"
            );

        } else if (
            campos.itemCatalogo.value
        ) {

            aplicarOrigen(
                "catalogo"
            );

        } else {

            aplicarOrigen(
                null
            );
        }


        // ==================================================
        // RADIO DISPOSITIVO
        // ==================================================

        radioDispositivo
            .input
            .addEventListener(
                "change",
                () => {

                    if (
                        radioDispositivo
                            .input
                            .checked
                    ) {

                        aplicarOrigen(
                            "dispositivo",
                            true
                        );
                    }
                }
            );


        // ==================================================
        // RADIO CATÁLOGO
        // ==================================================

        radioCatalogo
            .input
            .addEventListener(
                "change",
                () => {

                    if (
                        radioCatalogo
                            .input
                            .checked
                    ) {

                        aplicarOrigen(
                            "catalogo",
                            true
                        );
                    }
                }
            );


        // ==================================================
        // CAMBIO DISPOSITIVO
        // ==================================================

        registrarCambioSelect(
            campos.dispositivo,
            () => {

                const valor = (
                    campos.dispositivo.value
                );

                if (!valor) {
                    return;
                }

                aplicarOrigen(
                    "dispositivo"
                );

                cargarMetadata(
                    fila,
                    "dispositivo",
                    valor
                );
            }
        );


        // ==================================================
        // CAMBIO CATÁLOGO
        // ==================================================

        registrarCambioSelect(
            campos.itemCatalogo,
            () => {

                const valor = (
                    campos.itemCatalogo.value
                );

                if (!valor) {
                    return;
                }

                aplicarOrigen(
                    "catalogo"
                );

                cargarMetadata(
                    fila,
                    "catalogo",
                    valor
                );
            }
        );
    }


    // ======================================================
    // FILAS EXISTENTES
    // ======================================================

    function inicializarFilasExistentes() {

        const filas = (
            document.querySelectorAll(
                ".inline-group tr.form-row,"
                + ".detalle-tabla tr.form-row"
            )
        );

        filas.forEach(
            inicializarFila
        );
    }


    // ======================================================
    // INICIO
    // ======================================================

    function inicializarPagina() {

        inicializarFilasExistentes();

        inicializarAgregarDetalle();

        actualizarOrdenesNuevos();

        recalcularResumenEconomico();
        
    }


    if (
        document.readyState
        === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            inicializarPagina
        );

    } else {

        inicializarPagina();
    }


    // ======================================================
    // NUEVAS FILAS DEL INLINE
    // ======================================================

    document.addEventListener(
        "formset:added",
        (event) => {

            inicializarFila(
                event.target
            );
        }
    );

    // ======================================================
    // AGREGAR DETALLE - PANTALLA PERSONALIZADA
    // ======================================================

    function inicializarAgregarDetalle() {

        const boton = (
            document.getElementById(
                "agregar-detalle-proyecto"
            )
        );

        const template = (
            document.getElementById(
                "detalle-proyecto-empty-form"
            )
        );

        const totalForms = (
            document.querySelector(
                'input[name$="-TOTAL_FORMS"]'
            )
        );

        const tablaBody = (
            document.querySelector(
                ".detalle-tabla tbody"
            )
        );


        if (
            !boton
            || !template
            || !totalForms
            || !tablaBody
        ) {
            return;
        }


        boton.addEventListener(
            "click",
            () => {

                // ==========================================
                // ÍNDICE DEL NUEVO FORM
                // ==========================================

                const indice = parseInt(
                    totalForms.value,
                    10
                );


                // ==========================================
                // CLONAR EMPTY FORM
                // ==========================================

                const html = (
                    template.innerHTML.replace(
                        /__prefix__/g,
                        String(indice)
                    )
                );


                const contenedor = (
                    document.createElement(
                        "tbody"
                    )
                );

                contenedor.innerHTML = (
                    html.trim()
                );


                const fila = (
                    contenedor.querySelector(
                        "tr"
                    )
                );

                if (!fila) {
                    return;
                }


                // ==========================================
                // AGREGAR
                // ==========================================

                tablaBody.appendChild(
                    fila
                );


                // ==========================================
                // ACTUALIZAR MANAGEMENT FORM
                // ==========================================

                totalForms.value = (
                    indice + 1
                );


                // ==========================================
                // INICIALIZAR SELECT2 DEL ADMIN
                // ==========================================

                if (
                    window.django
                    && window.django.jQuery
                ) {

                    const $ = (
                        window.django.jQuery
                    );

                    $(fila)
                        .find(
                            ".admin-autocomplete"
                        )
                        .each(
                            function () {

                                /*
                                * Django Admin proporciona
                                * djangoAdminSelect2().
                                */

                                if (
                                    typeof $(this)
                                        .djangoAdminSelect2
                                    === "function"
                                ) {

                                    $(this)
                                        .djangoAdminSelect2();
                                }
                            }
                        );
                }


                // ==========================================
                // NUESTRO COMPORTAMIENTO
                // ==========================================

                inicializarFila(
                    fila
                );


                // ==========================================
                // ORDEN VISUAL
                // ==========================================

                actualizarOrdenesNuevos();

                recalcularResumenEconomico();

            }
        );
    }

    // ======================================================
    // ORDEN AUTOMÁTICO VISUAL
    // ======================================================

    function actualizarOrdenesNuevos() {

        const filas = (
            document.querySelectorAll(
                ".detalle-tabla tbody tr.form-row"
            )
        );

        let mayorOrden = 0;


        // ==================================================
        // BUSCAR MAYOR ORDEN EXISTENTE
        // ==================================================

        filas.forEach(
            (fila) => {

                if (
                    fila.classList.contains(
                        "detalle-form-nuevo"
                    )
                ) {
                    return;
                }


                const campo = (
                    fila.querySelector(
                        'input[name$="-orden"]'
                    )
                );

                if (!campo) {
                    return;
                }


                const numero = parseInt(
                    campo.value,
                    10
                );


                if (
                    Number.isFinite(numero)
                    && numero > mayorOrden
                ) {

                    mayorOrden = numero;
                }
            }
        );


        // ==================================================
        // NUEVAS FILAS
        // ==================================================

        let siguiente = (
            mayorOrden + 1
        );


        document
            .querySelectorAll(
                ".detalle-tabla tbody "
                + "tr.detalle-form-nuevo"
            )
            .forEach(
                (fila) => {

                    const campo = (
                        fila.querySelector(
                            'input[name$="-orden"]'
                        )
                    );

                    if (!campo) {
                        return;
                    }


                    campo.value = (
                        siguiente
                    );

                    siguiente += 1;
                }
            );
    }

    // ======================================================
    // ELIMINAR FILA NUEVA
    // ======================================================

    document.addEventListener(
        "click",
        (event) => {

            const boton = (
                event.target.closest(
                    ".eliminar-detalle-nuevo"
                )
            );

            if (!boton) {
                return;
            }


            const fila = (
                boton.closest(
                    "tr.form-row"
                )
            );

            if (!fila) {
                return;
            }


            fila.remove();

            /*
            * No reducimos TOTAL_FORMS porque los índices
            * de formsets deben conservarse consecutivos.
            *
            * Después compactamos todos los forms nuevos.
            */

            compactarFormset();

            actualizarOrdenesNuevos();

            recalcularResumenEconomico();

        }
    );

    // ======================================================
    // COMPACTAR FORMSET
    // ======================================================

    function compactarFormset() {

        const totalForms = (
            document.querySelector(
                'input[name$="-TOTAL_FORMS"]'
            )
        );

        const filas = Array.from(
            document.querySelectorAll(
                ".detalle-tabla tbody tr.form-row"
            )
        );


        if (!totalForms) {
            return;
        }


        filas.forEach(
            (fila, indice) => {

                fila
                    .querySelectorAll(
                        "input, select, textarea, label"
                    )
                    .forEach(
                        (elemento) => {

                            if (
                                elemento.name
                            ) {

                                elemento.name = (
                                    elemento.name.replace(
                                        /-\d+-/,
                                        `-${indice}-`
                                    )
                                );
                            }


                            if (
                                elemento.id
                            ) {

                                elemento.id = (
                                    elemento.id.replace(
                                        /-\d+-/,
                                        `-${indice}-`
                                    )
                                );
                            }


                            if (
                                elemento.htmlFor
                            ) {

                                elemento.htmlFor = (
                                    elemento.htmlFor.replace(
                                        /-\d+-/,
                                        `-${indice}-`
                                    )
                                );
                            }
                        }
                    );
            }
        );


        totalForms.value = (
            filas.length
        );
    }

    // ======================================================
    // RESUMEN ECONÓMICO DEL PROYECTO
    // ======================================================

    function recalcularResumenEconomico() {

        const subtotalElemento = (
            document.getElementById(
                "resumen-proyecto-subtotal"
            )
        );

        const descuentosElemento = (
            document.getElementById(
                "resumen-proyecto-descuentos"
            )
        );

        const impuestosElemento = (
            document.getElementById(
                "resumen-proyecto-impuestos"
            )
        );

        const totalElemento = (
            document.getElementById(
                "resumen-proyecto-total"
            )
        );


        /*
        * Si el usuario no puede ver costos,
        * estos elementos no existen.
        */

        if (
            !subtotalElemento
            || !descuentosElemento
            || !impuestosElemento
            || !totalElemento
        ) {
            return;
        }


        let subtotalProyecto = 0;
        let descuentosProyecto = 0;
        let impuestosProyecto = 0;


        const filas = (
            document.querySelectorAll(
                ".detalle-tabla tbody tr.form-row"
            )
        );


        filas.forEach(
            (fila) => {

                // ==========================================
                // IGNORAR FILAS ELIMINADAS
                // ==========================================

                const eliminar = (
                    fila.querySelector(
                        'input[name$="-DELETE"]'
                    )
                );

                if (
                    eliminar
                    && eliminar.checked
                ) {
                    return;
                }


                // ==========================================
                // CAMPOS
                // ==========================================

                const campos = (
                    obtenerCamposFila(
                        fila
                    )
                );


                /*
                * Una fila completamente vacía no debe
                * participar del resumen.
                */

                const tieneOrigen = Boolean(
                    (
                        campos.dispositivo
                        && campos.dispositivo.value
                    )
                    ||
                    (
                        campos.itemCatalogo
                        && campos.itemCatalogo.value
                    )
                );

                if (!tieneOrigen) {
                    return;
                }


                // ==========================================
                // IMPORTES
                // ==========================================

                const cantidad = (
                    obtenerNumero(
                        campos.cantidad
                    )
                );

                const precio = (
                    obtenerNumero(
                        campos.precioUnitario
                    )
                );

                const descuento = (
                    obtenerNumero(
                        campos.descuentoImporte
                    )
                );

                const impuestos = (
                    obtenerNumero(
                        campos.impuestosImporte
                    )
                );


                const subtotalFila = (
                    redondearImporte(
                        cantidad * precio
                    )
                );


                subtotalProyecto += subtotalFila;
                descuentosProyecto += descuento;
                impuestosProyecto += impuestos;
            }
        );


        // ==================================================
        // REDONDEAR
        // ==================================================

        subtotalProyecto = (
            redondearImporte(
                subtotalProyecto
            )
        );

        descuentosProyecto = (
            redondearImporte(
                descuentosProyecto
            )
        );

        impuestosProyecto = (
            redondearImporte(
                impuestosProyecto
            )
        );


        const totalProyecto = (
            redondearImporte(
                subtotalProyecto
                - descuentosProyecto
                + impuestosProyecto
            )
        );


        // ==================================================
        // MOSTRAR
        // ==================================================

        subtotalElemento.textContent = (
            formatearImporte(
                subtotalProyecto
            )
        );

        descuentosElemento.textContent = (
            formatearImporte(
                descuentosProyecto
            )
        );

        impuestosElemento.textContent = (
            formatearImporte(
                impuestosProyecto
            )
        );

        totalElemento.textContent = (
            formatearImporte(
                totalProyecto
            )
        );
    }

    // ======================================================
    // ELIMINACIÓN DE DETALLES EXISTENTES
    // ======================================================

    function registrarEliminacionFila(
        fila,
    ) {

        const eliminar = (
            fila.querySelector(
                'input[name$="-DELETE"]'
            )
        );

        if (!eliminar) {
            return;
        }

        eliminar.addEventListener(
            "change",
            () => {

                if (eliminar.checked) {

                    fila.style.opacity = "0.45";

                } else {

                    fila.style.opacity = "";
                }

                recalcularResumenEconomico();
            }
        );
    }


})();