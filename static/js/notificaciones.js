/**
 * Script de gestión para Notificaciones
 * Usa jQuery, DataTables, SweetAlert2, Select2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tableTipos, tableNotificaciones;
    let usuariosCache = [];
    let documentosCache = [];
    let tiposCache = [];
    
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
     * Carga los usuarios para los selects
     */
    function loadUsuariosForSelect(selectId, callback) {
        if (usuariosCache.length > 0) {
            populateSelect(selectId, usuariosCache, 'id', 'text');
            if (callback) callback();
            return;
        }
        
        ajaxRequest(
            NOTIFICACIONES_URLS.usuariosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    usuariosCache = response.data;
                    populateSelect(selectId, usuariosCache, 'id', 'text');
                    if (callback) callback();
                }
            }
        );
    }
    
    /**
     * Carga los documentos para los selects
     */
    function loadDocumentosForSelect(selectId, callback) {
        if (documentosCache.length > 0) {
            populateSelect(selectId, documentosCache, 'id', 'text');
            if (callback) callback();
            return;
        }
        
        ajaxRequest(
            NOTIFICACIONES_URLS.documentosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    documentosCache = response.data;
                    populateSelect(selectId, documentosCache, 'id', 'text');
                    if (callback) callback();
                }
            }
        );
    }
    
    /**
     * Carga los tipos de notificación para los selects
     */
    function loadTiposForSelect(selectId, callback) {
        if (tiposCache.length > 0) {
            populateSelect(selectId, tiposCache, 'id', 'text');
            if (callback) callback();
            return;
        }
        
        ajaxRequest(
            NOTIFICACIONES_URLS.tiposForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    tiposCache = response.data;
                    populateSelect(selectId, tiposCache, 'id', 'text');
                    if (callback) callback();
                }
            }
        );
    }
    
    /**
     * Pobla un select con datos
     */
    function populateSelect(selectId, data, valueKey, textKey) {
        const $select = $(selectId);
        const currentValue = $select.val();
        $select.empty();
        $select.append('<option value="">Seleccione...</option>');
        
        data.forEach(function(item) {
            const text = item[textKey] || '';
            const value = item[valueKey];
            $select.append(`<option value="${value}">${escapeHtml(text)}</option>`);
        });
        
        if (currentValue) {
            $select.val(currentValue);
        }
    }
    
    // ========================================================================
    // TABLAS DATATABLES
    // ========================================================================
    
    /**
     * Inicializa la tabla de Tipos de Notificación
     */
    function initTableTipos() {
        const $table = $('#tableTipos');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableTipos')) {
            $('#tableTipos').DataTable().destroy();
        }
        
        tableTipos = $('#tableTipos').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: NOTIFICACIONES_URLS.tiposList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar tipos:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los tipos de notificación',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'codigo' },
                { data: 'nombre' },
                { 
                    data: 'descripcion',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'plantilla',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'notificaciones_count',
                    render: function(data) {
                        return `<span class="badge badge-info">${data || 0}</span>`;
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const nombreEscapado = escapeHtml(row.nombre);
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-tipo" 
                                        data-id="${row.id}" 
                                        data-nombre="${nombreEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-tipo" 
                                        data-id="${row.id}" 
                                        data-nombre="${nombreEscapado}"
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
            order: [[1, 'asc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Inicializa la tabla de Notificaciones
     */
    function initTableNotificaciones() {
        const $table = $('#tableNotificaciones');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableNotificaciones')) {
            $('#tableNotificaciones').DataTable().destroy();
        }
        
        tableNotificaciones = $('#tableNotificaciones').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: NOTIFICACIONES_URLS.notificacionesList,
                type: 'GET',
                dataSrc: function(json) {
                    if (json && json.success && json.data) {
                        // Actualizar contador de no leídas
                        const noLeidas = json.data.filter(n => !n.es_leida).length;
                        $('#badgeNotificacionesNoLeidas').text(noLeidas);
                        return json.data;
                    } else {
                        console.error('Respuesta inválida del servidor:', json);
                        return [];
                    }
                },
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar notificaciones:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las notificaciones',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'usuario_nombre' },
                { data: 'tipo_notificacion_nombre' },
                { 
                    data: 'titulo',
                    render: function(data, type, row) {
                        const tituloEscapado = escapeHtml(data || '');
                        const clase = row.es_leida ? '' : 'font-weight-bold';
                        return `<span class="${clase}">${tituloEscapado}</span>`;
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
                    data: 'documento_titulo',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 50 ? data.substring(0, 50) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'es_leida',
                    render: function(data) {
                        if (data) {
                            return '<span class="badge badge-success">Leída</span>';
                        } else {
                            return '<span class="badge badge-warning badge-no-leida">No Leída</span>';
                        }
                    }
                },
                { 
                    data: 'fecha_creacion',
                    render: function(data) {
                        if (data) {
                            const date = new Date(data);
                            return date.toLocaleDateString('es-ES') + ' ' + date.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'});
                        }
                        return '-';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '25%',
                    render: function(data, type, row) {
                        const tituloEscapado = escapeHtml((row.titulo || '').substring(0, 50));
                        const btnLeida = row.es_leida 
                            ? `<button class="btn btn-warning btn-sm btn-marcar-no-leida" data-id="${row.id}" title="Marcar como no leída"><i class="fas fa-envelope"></i></button>`
                            : `<button class="btn btn-success btn-sm btn-marcar-leida" data-id="${row.id}" title="Marcar como leída"><i class="fas fa-envelope-open"></i></button>`;
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                ${btnLeida}
                                <button class="btn btn-info btn-editar-notificacion" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-notificacion" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
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
            order: [[7, 'desc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    // ========================================================================
    // EVENTOS PARA TIPOS DE NOTIFICACIÓN
    // ========================================================================
    
    /**
     * Abre el modal para crear un nuevo tipo
     */
    $(document).on('click', '#btnCrearTipo', function() {
        $('#modalTipoLabel').text('Nuevo Tipo de Notificación');
        $('#formTipo')[0].reset();
        $('#tipoId').val('');
        $('#modalTipo').modal('show');
    });
    
    /**
     * Edita un tipo
     */
    $(document).on('click', '.btn-editar-tipo', function() {
        const tipoId = $(this).data('id');
        const url = NOTIFICACIONES_URLS.tipoDetail(tipoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const tipo = response.data;
                    $('#modalTipoLabel').text('Editar Tipo de Notificación');
                    $('#tipoId').val(tipo.id);
                    $('#tipoCodigo').val(tipo.codigo);
                    $('#tipoNombre').val(tipo.nombre);
                    $('#tipoDescripcion').val(tipo.descripcion || '');
                    $('#tipoPlantilla').val(tipo.plantilla || '');
                    $('#modalTipo').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina un tipo
     */
    $(document).on('click', '.btn-eliminar-tipo', function() {
        const tipoId = $(this).data('id');
        const nombre = $(this).data('nombre');
        const url = NOTIFICACIONES_URLS.tipoDelete(tipoId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el tipo "${nombre}"?`,
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
                                text: response.message || 'Tipo eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableTipos.ajax.reload(null, false);
                            // Limpiar cache de tipos
                            tiposCache = [];
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Maneja el envío del formulario de tipo
     */
    $(document).on('submit', '#formTipo', function(e) {
        e.preventDefault();
        
        const tipoId = $('#tipoId').val();
        const formData = {
            codigo: $('#tipoCodigo').val().trim(),
            nombre: $('#tipoNombre').val().trim(),
            descripcion: $('#tipoDescripcion').val().trim() || null,
            plantilla: $('#tipoPlantilla').val().trim() || null,
        };
        
        if (!formData.codigo) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El código es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (!formData.nombre) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El nombre es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (tipoId) {
            url = NOTIFICACIONES_URLS.tipoUpdate(tipoId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = NOTIFICACIONES_URLS.tipoCreate;
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
                    $('#modalTipo').modal('hide');
                    tableTipos.ajax.reload(null, false);
                    // Limpiar cache de tipos
                    tiposCache = [];
                }
            }
        );
    });
    
    // ========================================================================
    // EVENTOS PARA NOTIFICACIONES
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva notificación
     */
    $(document).on('click', '#btnCrearNotificacion', function() {
        $('#modalNotificacionLabel').text('Nueva Notificación');
        $('#formNotificacion')[0].reset();
        $('#notificacionId').val('');
        $('#notificacionEsLeida').prop('checked', false);
        
        loadUsuariosForSelect('#notificacionUsuario');
        loadTiposForSelect('#notificacionTipo');
        loadDocumentosForSelect('#notificacionDocumento', function() {
            $('#notificacionDocumento').prepend('<option value="">Ninguno</option>');
            $('#notificacionDocumento').val('');
        });
        
        $('#modalNotificacion').modal('show');
    });
    
    /**
     * Edita una notificación
     */
    $(document).on('click', '.btn-editar-notificacion', function() {
        const notificacionId = $(this).data('id');
        const url = NOTIFICACIONES_URLS.notificacionDetail(notificacionId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const notificacion = response.data;
                    $('#modalNotificacionLabel').text('Editar Notificación');
                    $('#notificacionId').val(notificacion.id);
                    $('#notificacionTitulo').val(notificacion.titulo);
                    $('#notificacionMensaje').val(notificacion.mensaje);
                    $('#notificacionURL').val(notificacion.url_relacionada || '');
                    $('#notificacionEsLeida').prop('checked', notificacion.es_leida);
                    
                    loadUsuariosForSelect('#notificacionUsuario', function() {
                        $('#notificacionUsuario').val(notificacion.usuario_id);
                    });
                    
                    loadTiposForSelect('#notificacionTipo', function() {
                        $('#notificacionTipo').val(notificacion.tipo_notificacion_id);
                    });
                    
                    loadDocumentosForSelect('#notificacionDocumento', function() {
                        $('#notificacionDocumento').prepend('<option value="">Ninguno</option>');
                        if (notificacion.documento_id) {
                            $('#notificacionDocumento').val(notificacion.documento_id);
                        } else {
                            $('#notificacionDocumento').val('');
                        }
                    });
                    
                    $('#modalNotificacion').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina una notificación
     */
    $(document).on('click', '.btn-eliminar-notificacion', function() {
        const notificacionId = $(this).data('id');
        const titulo = $(this).data('titulo');
        const url = NOTIFICACIONES_URLS.notificacionDelete(notificacionId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la notificación "${titulo}"?`,
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
                                text: response.message || 'Notificación eliminada correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableNotificaciones.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Marca una notificación como leída
     */
    $(document).on('click', '.btn-marcar-leida', function() {
        const notificacionId = $(this).data('id');
        const url = NOTIFICACIONES_URLS.notificacionMarcarLeida(notificacionId);
        
        ajaxRequest(
            url,
            'POST',
            null,
            function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Notificación marcada como leída',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    tableNotificaciones.ajax.reload(null, false);
                }
            }
        );
    });
    
    /**
     * Marca una notificación como no leída
     */
    $(document).on('click', '.btn-marcar-no-leida', function() {
        const notificacionId = $(this).data('id');
        const url = NOTIFICACIONES_URLS.notificacionMarcarNoLeida(notificacionId);
        
        ajaxRequest(
            url,
            'POST',
            null,
            function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Notificación marcada como no leída',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    tableNotificaciones.ajax.reload(null, false);
                }
            }
        );
    });
    
    /**
     * Maneja el envío del formulario de notificación
     */
    $(document).on('submit', '#formNotificacion', function(e) {
        e.preventDefault();
        
        const notificacionId = $('#notificacionId').val();
        const formData = {
            usuario_id: parseInt($('#notificacionUsuario').val()),
            tipo_notificacion_id: parseInt($('#notificacionTipo').val()),
            titulo: $('#notificacionTitulo').val().trim(),
            mensaje: $('#notificacionMensaje').val().trim(),
            url_relacionada: $('#notificacionURL').val().trim() || null,
            documento_id: $('#notificacionDocumento').val() ? parseInt($('#notificacionDocumento').val()) : null,
            es_leida: $('#notificacionEsLeida').is(':checked'),
        };
        
        if (!formData.usuario_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar un usuario',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (!formData.tipo_notificacion_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar un tipo de notificación',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (!formData.titulo) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El título es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (!formData.mensaje) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El mensaje es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (notificacionId) {
            url = NOTIFICACIONES_URLS.notificacionUpdate(notificacionId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = NOTIFICACIONES_URLS.notificacionCreate;
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
                    $('#modalNotificacion').modal('hide');
                    tableNotificaciones.ajax.reload(null, false);
                }
            }
        );
    });
    
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    // Inicializar tablas cuando se muestran los tabs
    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function(e) {
        const target = $(e.target).attr('href');
        
        if (target === '#tipos' && !$.fn.DataTable.isDataTable('#tableTipos')) {
            initTableTipos();
        } else if (target === '#notificaciones' && !$.fn.DataTable.isDataTable('#tableNotificaciones')) {
            initTableNotificaciones();
        }
    });
    
    // Inicializar la tabla del tab activo al cargar la página
    try {
        const $activeTab = $('.nav-tabs .nav-link.active');
        const activeTabHref = $activeTab.length > 0 ? $activeTab.attr('href') : null;
        
        if (activeTabHref === '#tipos') {
            initTableTipos();
        }
    } catch (error) {
        console.error('Error al inicializar tablas:', error);
    }
    
    // Cargar datos cuando se muestran los modales
    $(document).on('show.bs.modal', '#modalNotificacion', function() {
        loadUsuariosForSelect('#notificacionUsuario');
        loadTiposForSelect('#notificacionTipo');
        loadDocumentosForSelect('#notificacionDocumento', function() {
            $('#notificacionDocumento').prepend('<option value="">Ninguno</option>');
        });
    });
});



