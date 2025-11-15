/**
 * Script de gestión para Estadísticas
 * Usa jQuery, DataTables, SweetAlert2, Select2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tableVisitas, tableDescargas, tableEstadisticasAgregadas;
    let documentosCache = [];
    let archivosCache = [];
    let usuariosCache = [];
    
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
    
    /**
     * Obtiene el token CSRF
     */
    function getCSRFToken() {
        return $('[name=csrfmiddlewaretoken]').val() || $('input[name="csrfmiddlewaretoken"]').val() || '';
    }
    
    /**
     * Función genérica para hacer peticiones AJAX
     */
    function ajaxRequest(url, method, data, successCallback, errorCallback) {
        const options = {
            url: url,
            method: method,
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            success: function(response) {
                if (successCallback) successCallback(response);
            },
            error: function(xhr, status, error) {
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
     * Formatea una fecha
     */
    function formatDate(dateString) {
        if (!dateString) return '';
        try {
            const date = new Date(dateString);
            return date.toLocaleString('es-ES', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    }
    
    /**
     * Obtiene el badge para el tipo de acceso
     */
    function getTipoAccesoBadge(tipo) {
        const badges = {
            'vista': 'badge-info',
            'descarga': 'badge-primary',
            'preview': 'badge-secondary'
        };
        return badges[tipo] || 'badge-secondary';
    }
    
    /**
     * Obtiene el badge para el período
     */
    function getPeriodoBadge(periodo) {
        const badges = {
            'diario': 'badge-success',
            'semanal': 'badge-info',
            'mensual': 'badge-primary',
            'anual': 'badge-warning'
        };
        return badges[periodo] || 'badge-secondary';
    }
    
    // ========================================================================
    // CARGAR DATOS PARA SELECTS
    // ========================================================================
    
    /**
     * Carga los documentos para el select
     */
    function loadDocumentosForSelect(callback) {
        if (documentosCache.length > 0) {
            if (callback) callback(documentosCache);
            return;
        }
        ajaxRequest(
            ESTADISTICAS_URLS.documentosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    documentosCache = response.data;
                    if (callback) callback(documentosCache);
                }
            }
        );
    }
    
    /**
     * Carga los archivos para el select
     */
    function loadArchivosForSelect(callback) {
        if (archivosCache.length > 0) {
            if (callback) callback(archivosCache);
            return;
        }
        ajaxRequest(
            ESTADISTICAS_URLS.archivosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    archivosCache = response.data;
                    if (callback) callback(archivosCache);
                }
            }
        );
    }
    
    /**
     * Carga los usuarios para el select
     */
    function loadUsuariosForSelect(callback) {
        if (usuariosCache.length > 0) {
            if (callback) callback(usuariosCache);
            return;
        }
        ajaxRequest(
            ESTADISTICAS_URLS.usuariosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    usuariosCache = response.data;
                    if (callback) callback(usuariosCache);
                }
            }
        );
    }
    
    // ========================================================================
    // INICIALIZACIÓN DE TABLAS
    // ========================================================================
    
    /**
     * Inicializa la tabla de visitas
     */
    function initTableVisitas() {
        tableVisitas = $('#tableVisitas').DataTable({
            ajax: {
                url: ESTADISTICAS_URLS.visitasList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { 
                    data: 'documento_titulo',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 40) + (data.length > 40 ? '...' : '');
                    }
                },
                { 
                    data: 'usuario_nombre',
                    render: function(data) {
                        return data || '<span class="text-muted">Anónimo</span>';
                    }
                },
                { 
                    data: 'tipo_acceso',
                    render: function(data, type, row) {
                        const badge = getTipoAccesoBadge(data);
                        return `<span class="badge ${badge} badge-tipo-acceso">${row.tipo_acceso_display}</span>`;
                    }
                },
                { data: 'ip_address' },
                { data: 'pais' },
                { data: 'ciudad' },
                { 
                    data: 'fecha',
                    render: function(data) {
                        return formatDate(data);
                    }
                },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-visita" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-visita" data-id="${row.id}" title="Eliminar">
                                    <i class="fas fa-trash"></i><span> Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            order: [[7, 'desc']],
            language: {
                url: '/static/DataTables/es-ES.json'
            },
            responsive: true
        });
    }
    
    /**
     * Inicializa la tabla de descargas
     */
    function initTableDescargas() {
        tableDescargas = $('#tableDescargas').DataTable({
            ajax: {
                url: ESTADISTICAS_URLS.descargasList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { 
                    data: 'archivo_nombre',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 30) + (data.length > 30 ? '...' : '');
                    }
                },
                { 
                    data: 'documento_titulo',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 40) + (data.length > 40 ? '...' : '');
                    }
                },
                { 
                    data: 'usuario_nombre',
                    render: function(data) {
                        return data || '<span class="text-muted">Anónimo</span>';
                    }
                },
                { data: 'ip_address' },
                { 
                    data: 'fecha',
                    render: function(data) {
                        return formatDate(data);
                    }
                },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-descarga" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-descarga" data-id="${row.id}" title="Eliminar">
                                    <i class="fas fa-trash"></i><span> Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            order: [[5, 'desc']],
            language: {
                url: '/static/DataTables/es-ES.json'
            },
            responsive: true
        });
    }
    
    /**
     * Inicializa la tabla de estadísticas agregadas
     */
    function initTableEstadisticasAgregadas() {
        tableEstadisticasAgregadas = $('#tableEstadisticasAgregadas').DataTable({
            ajax: {
                url: ESTADISTICAS_URLS.estadisticasAgregadasList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { 
                    data: 'documento_titulo',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 40) + (data.length > 40 ? '...' : '');
                    }
                },
                { 
                    data: 'periodo',
                    render: function(data, type, row) {
                        const badge = getPeriodoBadge(data);
                        return `<span class="badge ${badge} badge-periodo">${row.periodo_display}</span>`;
                    }
                },
                { 
                    data: 'fecha_inicio',
                    render: function(data) {
                        if (!data) return '';
                        try {
                            const date = new Date(data);
                            return date.toLocaleDateString('es-ES');
                        } catch (e) {
                            return data;
                        }
                    }
                },
                { 
                    data: 'total_visitas',
                    render: function(data) {
                        return `<span class="badge badge-info">${data}</span>`;
                    }
                },
                { 
                    data: 'total_descargas',
                    render: function(data) {
                        return `<span class="badge badge-primary">${data}</span>`;
                    }
                },
                { 
                    data: 'visitas_unicas',
                    render: function(data) {
                        return `<span class="badge badge-success">${data}</span>`;
                    }
                },
                { 
                    data: 'descargas_unicas',
                    render: function(data) {
                        return `<span class="badge badge-warning">${data}</span>`;
                    }
                },
                { 
                    data: 'tiempo_promedio_lectura',
                    render: function(data) {
                        if (!data) return '<span class="text-muted">-</span>';
                        const minutos = Math.floor(data / 60);
                        const segundos = data % 60;
                        return `${minutos}m ${segundos}s`;
                    }
                },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-estadistica-agregada" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-estadistica-agregada" data-id="${row.id}" title="Eliminar">
                                    <i class="fas fa-trash"></i><span> Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            order: [[0, 'desc']],
            language: {
                url: '/static/DataTables/es-ES.json'
            },
            responsive: true
        });
    }
    
    // ========================================================================
    // MANEJO DE VISITAS
    // ========================================================================
    
    /**
     * Limpia el formulario de visita
     */
    function limpiarFormVisita() {
        $('#formVisita')[0].reset();
        $('#visita_id').val('');
        $('#visita_documento_id').val('').trigger('change');
        $('#visita_usuario_id').val('').trigger('change');
        $('#modalVisitaLabel').text('Nueva Visita de Documento');
    }
    
    /**
     * Maneja la creación de una visita
     */
    function crearVisita() {
        limpiarFormVisita();
        loadDocumentosForSelect(function(documentos) {
            $('#visita_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
            documentos.forEach(function(documento) {
                $('#visita_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
            });
            $('#visita_documento_id').trigger('change');
        });
        loadUsuariosForSelect(function(usuarios) {
            $('#visita_usuario_id').empty().append('<option value="">Seleccionar usuario...</option>');
            usuarios.forEach(function(usuario) {
                $('#visita_usuario_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
            });
            $('#visita_usuario_id').trigger('change');
        });
        $('#modalVisita').modal('show');
    }
    
    /**
     * Maneja la edición de una visita
     */
    function editarVisita(visitaId) {
        ajaxRequest(
            ESTADISTICAS_URLS.visitaDetail(visitaId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const visita = response.data;
                    
                    loadDocumentosForSelect(function(documentos) {
                        $('#visita_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
                        documentos.forEach(function(documento) {
                            $('#visita_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
                        });
                        
                        loadUsuariosForSelect(function(usuarios) {
                            $('#visita_usuario_id').empty().append('<option value="">Seleccionar usuario...</option>');
                            usuarios.forEach(function(usuario) {
                                $('#visita_usuario_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
                            });
                            
                            $('#visita_id').val(visita.id);
                            $('#visita_documento_id').val(visita.documento_id).trigger('change');
                            $('#visita_usuario_id').val(visita.usuario_id || '').trigger('change');
                            $('#visita_tipo_acceso').val(visita.tipo_acceso);
                            $('#visita_ip_address').val(visita.ip_address || '');
                            $('#visita_pais').val(visita.pais || '');
                            $('#visita_ciudad').val(visita.ciudad || '');
                            $('#visita_referer').val(visita.referer || '');
                            $('#visita_user_agent').val(visita.user_agent || '');
                            $('#modalVisitaLabel').text('Editar Visita de Documento');
                            $('#modalVisita').modal('show');
                        });
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de una visita
     */
    function eliminarVisita(visitaId) {
        Swal.fire({
            title: '¿Está seguro?',
            text: 'Esta acción no se puede deshacer',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    ESTADISTICAS_URLS.visitaDelete(visitaId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Visita eliminada exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableVisitas.ajax.reload();
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE DESCARGAS
    // ========================================================================
    
    /**
     * Limpia el formulario de descarga
     */
    function limpiarFormDescarga() {
        $('#formDescarga')[0].reset();
        $('#descarga_id').val('');
        $('#descarga_archivo_id').val('').trigger('change');
        $('#descarga_usuario_id').val('').trigger('change');
        $('#modalDescargaLabel').text('Nueva Descarga de Archivo');
    }
    
    /**
     * Maneja la creación de una descarga
     */
    function crearDescarga() {
        limpiarFormDescarga();
        loadArchivosForSelect(function(archivos) {
            $('#descarga_archivo_id').empty().append('<option value="">Seleccionar archivo...</option>');
            archivos.forEach(function(archivo) {
                $('#descarga_archivo_id').append(`<option value="${archivo.id}">${escapeHtml(archivo.text)}</option>`);
            });
            $('#descarga_archivo_id').trigger('change');
        });
        loadUsuariosForSelect(function(usuarios) {
            $('#descarga_usuario_id').empty().append('<option value="">Seleccionar usuario...</option>');
            usuarios.forEach(function(usuario) {
                $('#descarga_usuario_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
            });
            $('#descarga_usuario_id').trigger('change');
        });
        $('#modalDescarga').modal('show');
    }
    
    /**
     * Maneja la edición de una descarga
     */
    function editarDescarga(descargaId) {
        ajaxRequest(
            ESTADISTICAS_URLS.descargaDetail(descargaId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const descarga = response.data;
                    
                    loadArchivosForSelect(function(archivos) {
                        $('#descarga_archivo_id').empty().append('<option value="">Seleccionar archivo...</option>');
                        archivos.forEach(function(archivo) {
                            $('#descarga_archivo_id').append(`<option value="${archivo.id}">${escapeHtml(archivo.text)}</option>`);
                        });
                        
                        loadUsuariosForSelect(function(usuarios) {
                            $('#descarga_usuario_id').empty().append('<option value="">Seleccionar usuario...</option>');
                            usuarios.forEach(function(usuario) {
                                $('#descarga_usuario_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
                            });
                            
                            $('#descarga_id').val(descarga.id);
                            $('#descarga_archivo_id').val(descarga.archivo_id).trigger('change');
                            $('#descarga_usuario_id').val(descarga.usuario_id || '').trigger('change');
                            $('#descarga_ip_address').val(descarga.ip_address || '');
                            $('#modalDescargaLabel').text('Editar Descarga de Archivo');
                            $('#modalDescarga').modal('show');
                        });
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de una descarga
     */
    function eliminarDescarga(descargaId) {
        Swal.fire({
            title: '¿Está seguro?',
            text: 'Esta acción no se puede deshacer',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    ESTADISTICAS_URLS.descargaDelete(descargaId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Descarga eliminada exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableDescargas.ajax.reload();
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE ESTADÍSTICAS AGREGADAS
    // ========================================================================
    
    /**
     * Limpia el formulario de estadística agregada
     */
    function limpiarFormEstadisticaAgregada() {
        $('#formEstadisticaAgregada')[0].reset();
        $('#estadistica_agregada_id').val('');
        $('#estadistica_agregada_documento_id').val('').trigger('change');
        $('#estadistica_agregada_total_visitas').val('0');
        $('#estadistica_agregada_total_descargas').val('0');
        $('#estadistica_agregada_visitas_unicas').val('0');
        $('#estadistica_agregada_descargas_unicas').val('0');
        $('#modalEstadisticaAgregadaLabel').text('Nueva Estadística Agregada');
    }
    
    /**
     * Maneja la creación de una estadística agregada
     */
    function crearEstadisticaAgregada() {
        limpiarFormEstadisticaAgregada();
        loadDocumentosForSelect(function(documentos) {
            $('#estadistica_agregada_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
            documentos.forEach(function(documento) {
                $('#estadistica_agregada_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
            });
            $('#estadistica_agregada_documento_id').trigger('change');
        });
        $('#modalEstadisticaAgregada').modal('show');
    }
    
    /**
     * Maneja la edición de una estadística agregada
     */
    function editarEstadisticaAgregada(estadisticaId) {
        ajaxRequest(
            ESTADISTICAS_URLS.estadisticaAgregadaDetail(estadisticaId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const estadistica = response.data;
                    
                    loadDocumentosForSelect(function(documentos) {
                        $('#estadistica_agregada_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
                        documentos.forEach(function(documento) {
                            $('#estadistica_agregada_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
                        });
                        
                        $('#estadistica_agregada_id').val(estadistica.id);
                        $('#estadistica_agregada_documento_id').val(estadistica.documento_id).trigger('change');
                        $('#estadistica_agregada_periodo').val(estadistica.periodo);
                        
                        if (estadistica.fecha_inicio) {
                            const fecha = new Date(estadistica.fecha_inicio);
                            const fechaStr = fecha.toISOString().split('T')[0];
                            $('#estadistica_agregada_fecha_inicio').val(fechaStr);
                        }
                        
                        $('#estadistica_agregada_total_visitas').val(estadistica.total_visitas || 0);
                        $('#estadistica_agregada_total_descargas').val(estadistica.total_descargas || 0);
                        $('#estadistica_agregada_visitas_unicas').val(estadistica.visitas_unicas || 0);
                        $('#estadistica_agregada_descargas_unicas').val(estadistica.descargas_unicas || 0);
                        $('#estadistica_agregada_tiempo_promedio_lectura').val(estadistica.tiempo_promedio_lectura || '');
                        $('#modalEstadisticaAgregadaLabel').text('Editar Estadística Agregada');
                        $('#modalEstadisticaAgregada').modal('show');
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de una estadística agregada
     */
    function eliminarEstadisticaAgregada(estadisticaId) {
        Swal.fire({
            title: '¿Está seguro?',
            text: 'Esta acción no se puede deshacer',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    ESTADISTICAS_URLS.estadisticaAgregadaDelete(estadisticaId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Estadística eliminada exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableEstadisticasAgregadas.ajax.reload();
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================
    
    /**
     * Inicializa todos los event listeners
     */
    function initEventListeners() {
        // Botones de visitas
        $(document).on('click', '#btnCrearVisita', crearVisita);
        $(document).on('click', '.btn-editar-visita', function() {
            editarVisita($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-visita', function() {
            eliminarVisita($(this).data('id'));
        });
        
        // Botones de descargas
        $(document).on('click', '#btnCrearDescarga', crearDescarga);
        $(document).on('click', '.btn-editar-descarga', function() {
            editarDescarga($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-descarga', function() {
            eliminarDescarga($(this).data('id'));
        });
        
        // Botones de estadísticas agregadas
        $(document).on('click', '#btnCrearEstadisticaAgregada', crearEstadisticaAgregada);
        $(document).on('click', '.btn-editar-estadistica-agregada', function() {
            editarEstadisticaAgregada($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-estadistica-agregada', function() {
            eliminarEstadisticaAgregada($(this).data('id'));
        });
        
        // Formulario de visita
        $('#formVisita').on('submit', function(e) {
            e.preventDefault();
            const visitaId = $('#visita_id').val();
            const formData = {
                documento_id: $('#visita_documento_id').val(),
                usuario_id: $('#visita_usuario_id').val() || null,
                tipo_acceso: $('#visita_tipo_acceso').val(),
                ip_address: $('#visita_ip_address').val() || null,
                pais: $('#visita_pais').val() || null,
                ciudad: $('#visita_ciudad').val() || null,
                referer: $('#visita_referer').val() || null,
                user_agent: $('#visita_user_agent').val() || null
            };
            
            const url = visitaId ? 
                ESTADISTICAS_URLS.visitaUpdate(visitaId) : 
                ESTADISTICAS_URLS.visitaCreate;
            const method = visitaId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Visita guardada exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalVisita').modal('hide');
                    tableVisitas.ajax.reload();
                }
            });
        });
        
        // Formulario de descarga
        $('#formDescarga').on('submit', function(e) {
            e.preventDefault();
            const descargaId = $('#descarga_id').val();
            const formData = {
                archivo_id: $('#descarga_archivo_id').val(),
                usuario_id: $('#descarga_usuario_id').val() || null,
                ip_address: $('#descarga_ip_address').val() || null
            };
            
            const url = descargaId ? 
                ESTADISTICAS_URLS.descargaUpdate(descargaId) : 
                ESTADISTICAS_URLS.descargaCreate;
            const method = descargaId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Descarga guardada exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalDescarga').modal('hide');
                    tableDescargas.ajax.reload();
                }
            });
        });
        
        // Formulario de estadística agregada
        $('#formEstadisticaAgregada').on('submit', function(e) {
            e.preventDefault();
            const estadisticaId = $('#estadistica_agregada_id').val();
            const formData = {
                documento_id: $('#estadistica_agregada_documento_id').val(),
                periodo: $('#estadistica_agregada_periodo').val(),
                fecha_inicio: $('#estadistica_agregada_fecha_inicio').val(),
                total_visitas: parseInt($('#estadistica_agregada_total_visitas').val()) || 0,
                total_descargas: parseInt($('#estadistica_agregada_total_descargas').val()) || 0,
                visitas_unicas: parseInt($('#estadistica_agregada_visitas_unicas').val()) || 0,
                descargas_unicas: parseInt($('#estadistica_agregada_descargas_unicas').val()) || 0,
                tiempo_promedio_lectura: $('#estadistica_agregada_tiempo_promedio_lectura').val() ? parseInt($('#estadistica_agregada_tiempo_promedio_lectura').val()) : null
            };
            
            const url = estadisticaId ? 
                ESTADISTICAS_URLS.estadisticaAgregadaUpdate(estadisticaId) : 
                ESTADISTICAS_URLS.estadisticaAgregadaCreate;
            const method = estadisticaId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Estadística guardada exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalEstadisticaAgregada').modal('hide');
                    tableEstadisticasAgregadas.ajax.reload();
                }
            });
        });
        
        // Inicializar Select2
        $('.select2').select2({
            theme: 'bootstrap4',
            width: '100%'
        });
    }
    
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    /**
     * Inicializa todo el módulo de estadísticas
     */
    function initEstadisticas() {
        initTableVisitas();
        initTableDescargas();
        initTableEstadisticasAgregadas();
        initEventListeners();
    }
    
    // Exportar función de inicialización
    window.initEstadisticas = initEstadisticas;
});



