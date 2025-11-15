/**
 * Script de gestión para Configuración
 * Usa jQuery, DataTables, SweetAlert2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tableConfiguraciones, tableLogs;
    
    // ========================================================================
    // FUNCIONES AUXILIARES
    // ========================================================================
    
    /**
     * Función auxiliar para escapar HTML
     */
    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
    
    // Hacer disponible escapeHtml globalmente
    window.escapeHtml = escapeHtml;
    
    /**
     * Obtiene el token CSRF
     */
    function getCSRFToken() {
        return $('[name=csrfmiddlewaretoken]').val() || $('input[name="csrfmiddlewaretoken"]').val() || '';
    }
    
    /**
     * Muestra el overlay de carga
     */
    function showLoading() {
        $('#loadingOverlay').addClass('show');
    }
    
    /**
     * Oculta el overlay de carga
     */
    function hideLoading() {
        $('#loadingOverlay').removeClass('show');
    }
    
    /**
     * Función genérica para hacer peticiones AJAX
     */
    function ajaxRequest(url, method, data, successCallback, errorCallback) {
        showLoading();
        
        const options = {
            url: url,
            method: method,
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            success: function(response) {
                hideLoading();
                if (successCallback) successCallback(response);
            },
            error: function(xhr, status, error) {
                hideLoading();
                let errorMessage = 'Error al procesar la solicitud';
                
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage = xhr.responseJSON.error;
                } else if (xhr.status === 403) {
                    errorMessage = 'No tiene permisos para realizar esta acción';
                } else if (xhr.status === 404) {
                    errorMessage = 'Recurso no encontrado';
                } else if (xhr.status >= 500) {
                    errorMessage = 'Error en el servidor. Por favor, intente nuevamente';
                }
                
                if (errorCallback) {
                    errorCallback(errorMessage);
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: errorMessage,
                        confirmButtonText: 'Aceptar'
                    });
                }
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.data = JSON.stringify(data);
        }
        
        $.ajax(options);
    }
    
    /**
     * Obtiene el badge class para nivel de log
     */
    function getLogBadgeClass(nivel) {
        const classes = {
            'DEBUG': 'badge-log-debug',
            'INFO': 'badge-log-info',
            'WARNING': 'badge-log-warning',
            'ERROR': 'badge-log-error',
            'CRITICAL': 'badge-log-critical'
        };
        return classes[nivel] || 'badge-secondary';
    }
    
    // ========================================================================
    // TABLAS DATATABLES
    // ========================================================================
    
    /**
     * Inicializa la tabla de Configuraciones
     */
    function initTableConfiguraciones() {
        const $table = $('#tableConfiguraciones');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableConfiguraciones')) {
            $('#tableConfiguraciones').DataTable().destroy();
        }
        
        tableConfiguraciones = $('#tableConfiguraciones').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: CONFIGURACION_URLS.configuracionesList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar configuraciones:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las configuraciones',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'clave' },
                { 
                    data: 'valor',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'tipo_display',
                    render: function(data) {
                        const badgeClass = {
                            'Texto': 'badge-primary',
                            'Número': 'badge-info',
                            'Booleano': 'badge-warning',
                            'JSON': 'badge-success',
                            'Fecha': 'badge-secondary'
                        };
                        const className = badgeClass[data] || 'badge-secondary';
                        return `<span class="badge ${className}">${escapeHtml(data)}</span>`;
                    }
                },
                { data: 'categoria' },
                { 
                    data: 'descripcion',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 50 ? data.substring(0, 50) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'es_editable',
                    render: function(data) {
                        return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const claveEscapado = escapeHtml(row.clave);
                        const editable = row.es_editable;
                        const btnEditar = editable 
                            ? `<button class="btn btn-info btn-sm btn-editar-configuracion" data-id="${row.id}" data-clave="${claveEscapado}" title="Editar"><i class="fas fa-edit"></i><span class="d-none d-md-inline ml-1">Editar</span></button>`
                            : `<button class="btn btn-info btn-sm" disabled title="No editable"><i class="fas fa-lock"></i><span class="d-none d-md-inline ml-1">Bloqueado</span></button>`;
                        
                        const btnEliminar = editable
                            ? `<button class="btn btn-danger btn-sm btn-eliminar-configuracion" data-id="${row.id}" data-clave="${claveEscapado}" title="Eliminar"><i class="fas fa-trash"></i><span class="d-none d-md-inline ml-1">Eliminar</span></button>`
                            : '';
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                ${btnEditar}
                                ${btnEliminar}
                            </div>
                        `;
                    }
                }
            ],
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json'
            },
            order: [[4, 'asc'], [1, 'asc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]],
            rowCallback: function(row, data) {
                if (!data.es_editable) {
                    $(row).addClass('config-no-editable');
                }
            }
        });
    }
    
    /**
     * Inicializa la tabla de Logs
     */
    function initTableLogs() {
        const $table = $('#tableLogs');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableLogs')) {
            $('#tableLogs').DataTable().destroy();
        }
        
        tableLogs = $('#tableLogs').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: CONFIGURACION_URLS.logsList,
                type: 'GET',
                data: function(d) {
                    // Obtener filtros actuales cada vez que se hace la petición
                    return {
                        nivel: $('#filtroNivel').val() || '',
                        modulo: $('#filtroModulo').val() || '',
                        limit: $('#filtroLimit').val() || '1000'
                    };
                },
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar logs:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los logs',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { 
                    data: 'nivel',
                    render: function(data) {
                        const badgeClass = getLogBadgeClass(data);
                        return `<span class="badge ${badgeClass}">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'modulo',
                    render: function(data) {
                        return data ? escapeHtml(data) : '-';
                    }
                },
                { 
                    data: 'mensaje',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'usuario_nombre',
                    render: function(data) {
                        return data ? escapeHtml(data) : '-';
                    }
                },
                { 
                    data: 'ip_address',
                    render: function(data) {
                        return data ? escapeHtml(data) : '-';
                    }
                },
                { 
                    data: 'fecha',
                    render: function(data) {
                        if (data) {
                            const date = new Date(data);
                            return date.toLocaleDateString('es-ES') + ' ' + date.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit', second: '2-digit'});
                        }
                        return '-';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '15%',
                    render: function(data, type, row) {
                        // Solo superusuarios pueden ver/eliminar logs
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-sm btn-ver-log" 
                                        data-id="${row.id}" 
                                        title="Ver Detalles">
                                    <i class="fas fa-eye"></i>
                                    <span class="d-none d-md-inline ml-1">Ver</span>
                                </button>
                                <button class="btn btn-danger btn-sm btn-eliminar-log" 
                                        data-id="${row.id}" 
                                        title="Eliminar">
                                    <i class="fas fa-trash"></i>
                                    <span class="d-none d-md-inline ml-1">Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json'
            },
            order: [[6, 'desc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 25,
            lengthMenu: [[25, 50, 100, 500, 1000, -1], [25, 50, 100, 500, 1000, "Todos"]]
        });
    }
    
    // ========================================================================
    // EVENTOS PARA CONFIGURACIONES
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva configuración
     */
    $(document).on('click', '#btnCrearConfiguracion', function() {
        $('#modalConfiguracionLabel').text('Nueva Configuración');
        $('#formConfiguracion')[0].reset();
        $('#configuracionId').val('');
        $('#configuracionTipo').val('texto');
        $('#configuracionEsEditable').prop('checked', true);
        $('#modalConfiguracion').modal('show');
    });
    
    /**
     * Cambia el tipo de input según el tipo de configuración
     */
    $(document).on('change', '#configuracionTipo', function() {
        const tipo = $(this).val();
        const $valor = $('#configuracionValor');
        
        if (tipo === 'booleano') {
            $valor.attr('placeholder', 'true o false');
        } else if (tipo === 'numero') {
            $valor.attr('placeholder', 'Número (ej: 123, 45.67)');
        } else if (tipo === 'fecha') {
            $valor.attr('placeholder', 'Fecha (formato: YYYY-MM-DD)');
        } else if (tipo === 'json') {
            $valor.attr('placeholder', 'JSON válido (ej: {"key": "value"})');
        } else {
            $valor.attr('placeholder', 'Valor de la configuración');
        }
    });
    
    /**
     * Edita una configuración
     */
    $(document).on('click', '.btn-editar-configuracion', function() {
        const configId = $(this).data('id');
        const url = CONFIGURACION_URLS.configuracionDetail(configId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const config = response.data;
                    $('#modalConfiguracionLabel').text('Editar Configuración');
                    $('#configuracionId').val(config.id);
                    $('#configuracionClave').val(config.clave);
                    $('#configuracionValor').val(config.valor || '');
                    $('#configuracionTipo').val(config.tipo);
                    $('#configuracionCategoria').val(config.categoria || '');
                    $('#configuracionDescripcion').val(config.descripcion || '');
                    $('#configuracionEsEditable').prop('checked', config.es_editable);
                    
                    // Deshabilitar campos si no es editable
                    if (!config.es_editable) {
                        $('#configuracionClave').prop('readonly', true);
                        $('#configuracionEsEditable').prop('disabled', true);
                    } else {
                        $('#configuracionClave').prop('readonly', false);
                        $('#configuracionEsEditable').prop('disabled', false);
                    }
                    
                    // Actualizar placeholder según tipo
                    $('#configuracionTipo').trigger('change');
                    
                    $('#modalConfiguracion').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina una configuración
     */
    $(document).on('click', '.btn-eliminar-configuracion', function() {
        const configId = $(this).data('id');
        const clave = $(this).data('clave');
        const url = CONFIGURACION_URLS.configuracionDelete(configId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la configuración "${clave}"?`,
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    url,
                    'POST',
                    { _method: 'DELETE' },
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Éxito',
                                text: response.message || 'Configuración eliminada correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableConfiguraciones.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Maneja el envío del formulario de configuración
     */
    $(document).on('submit', '#formConfiguracion', function(e) {
        e.preventDefault();
        
        const configId = $('#configuracionId').val();
        const formData = {
            clave: $('#configuracionClave').val().trim(),
            valor: $('#configuracionValor').val().trim() || null,
            tipo: $('#configuracionTipo').val(),
            categoria: $('#configuracionCategoria').val().trim() || null,
            descripcion: $('#configuracionDescripcion').val().trim() || null,
            es_editable: $('#configuracionEsEditable').is(':checked'),
        };
        
        if (!formData.clave) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'La clave es obligatoria',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (configId) {
            url = CONFIGURACION_URLS.configuracionUpdate(configId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = CONFIGURACION_URLS.configuracionCreate;
            method = 'POST';
            sendData = formData;
        }
        
        ajaxRequest(
            url,
            method,
            sendData,
            function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Operación realizada correctamente',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    $('#modalConfiguracion').modal('hide');
                    tableConfiguraciones.ajax.reload(null, false);
                }
            }
        );
    });
    
    // ========================================================================
    // EVENTOS PARA LOGS
    // ========================================================================
    
    /**
     * Aplica filtros a la tabla de logs
     */
    $(document).on('click', '#btnAplicarFiltros', function() {
        tableLogs.ajax.reload(null, false);
    });
    
    /**
     * Limpia los filtros
     */
    $(document).on('click', '#btnLimpiarFiltros', function() {
        $('#filtroNivel').val('');
        $('#filtroModulo').val('');
        $('#filtroLimit').val('1000');
        tableLogs.ajax.reload(null, false);
    });
    
    /**
     * Abre el modal para limpiar logs
     */
    $(document).on('click', '#btnLimpiarLogs', function() {
        $('#formLimpiarLogs')[0].reset();
        $('#limpiarNivel').val('');
        $('#limpiarNivelMinimo').val('');
        $('#modalLimpiarLogs').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de limpiar logs
     */
    $(document).on('submit', '#formLimpiarLogs', function(e) {
        e.preventDefault();
        
        const formData = {
            nivel: $('#limpiarNivel').val() || '',
            nivel_minimo: $('#limpiarNivelMinimo').val() || '',
            dias: $('#limpiarDias').val() ? parseInt($('#limpiarDias').val()) : null,
        };
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: 'Esta acción eliminará logs permanentemente y no se puede deshacer.',
            showCancelButton: true,
            confirmButtonText: 'Sí, limpiar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    CONFIGURACION_URLS.logsLimpiar,
                    'POST',
                    formData,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Éxito',
                                text: response.message || 'Logs limpiados correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            $('#modalLimpiarLogs').modal('hide');
                            tableLogs.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Ver detalles de un log
     */
    $(document).on('click', '.btn-ver-log', function() {
        const logId = $(this).data('id');
        const url = CONFIGURACION_URLS.logDetail(logId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const log = response.data;
                    let datosAdicionales = '';
                    if (log.datos_adicionales) {
                        datosAdicionales = `<pre>${escapeHtml(JSON.stringify(log.datos_adicionales, null, 2))}</pre>`;
                    } else {
                        datosAdicionales = '<p class="text-muted">No hay datos adicionales</p>';
                    }
                    
                    Swal.fire({
                        icon: 'info',
                        title: 'Detalles del Log',
                        html: `
                            <div class="text-left">
                                <p><strong>ID:</strong> ${log.id}</p>
                                <p><strong>Nivel:</strong> <span class="badge ${getLogBadgeClass(log.nivel)}">${escapeHtml(log.nivel_display)}</span></p>
                                <p><strong>Módulo:</strong> ${log.modulo ? escapeHtml(log.modulo) : '-'}</p>
                                <p><strong>Mensaje:</strong> ${escapeHtml(log.mensaje)}</p>
                                <p><strong>Usuario:</strong> ${log.usuario_nombre ? escapeHtml(log.usuario_nombre) : '-'}</p>
                                <p><strong>IP:</strong> ${log.ip_address ? escapeHtml(log.ip_address) : '-'}</p>
                                <p><strong>Fecha:</strong> ${log.fecha ? new Date(log.fecha).toLocaleString('es-ES') : '-'}</p>
                                <p><strong>Datos Adicionales:</strong></p>
                                ${datosAdicionales}
                            </div>
                        `,
                        width: '700px',
                        confirmButtonText: 'Cerrar'
                    });
                }
            }
        );
    });
    
    /**
     * Elimina un log
     */
    $(document).on('click', '.btn-eliminar-log', function() {
        const logId = $(this).data('id');
        const url = CONFIGURACION_URLS.logDelete(logId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: '¿Desea eliminar este log?',
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    url,
                    'POST',
                    { _method: 'DELETE' },
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Éxito',
                                text: response.message || 'Log eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableLogs.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    // Inicializar tablas cuando se muestran los tabs
    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function(e) {
        const target = $(e.target).attr('href');
        
        if (target === '#configuraciones' && !$.fn.DataTable.isDataTable('#tableConfiguraciones')) {
            initTableConfiguraciones();
        } else if (target === '#logs' && !$.fn.DataTable.isDataTable('#tableLogs')) {
            initTableLogs();
        }
    });
    
    // Inicializar la tabla del tab activo al cargar la página
    try {
        const $activeTab = $('.nav-tabs .nav-link.active');
        const activeTabHref = $activeTab.length > 0 ? $activeTab.attr('href') : null;
        
        if (activeTabHref === '#configuraciones') {
            initTableConfiguraciones();
        }
    } catch (error) {
        console.error('Error al inicializar tablas:', error);
    }
    
    // Limpiar campos cuando se cierra el modal de configuración
    $(document).on('hidden.bs.modal', '#modalConfiguracion', function() {
        $('#formConfiguracion')[0].reset();
        $('#configuracionId').val('');
        $('#configuracionClave').prop('readonly', false);
        $('#configuracionEsEditable').prop('disabled', false);
    });
});

