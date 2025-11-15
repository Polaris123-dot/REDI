/**
 * Script de gestión para Revisiones
 * Usa jQuery, DataTables, SweetAlert2, Select2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tableCriterios, tableProcesos, tableRevisiones, tableEvaluaciones;
    let criteriosCache = [];
    let documentosCache = [];
    let usuariosCache = [];
    let procesosCache = [];
    let revisionesCache = [];
    
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
     * Obtiene el badge para el estado
     */
    function getEstadoBadge(estado) {
        const badges = {
            'pendiente': 'badge-secondary',
            'en_revision': 'badge-info',
            'aprobado': 'badge-success',
            'rechazado': 'badge-danger',
            'requiere_cambios': 'badge-warning',
            'asignado': 'badge-secondary',
            'en_progreso': 'badge-info',
            'completado': 'badge-success'
        };
        return badges[estado] || 'badge-secondary';
    }
    
    // ========================================================================
    // CARGAR DATOS PARA SELECTS
    // ========================================================================
    
    /**
     * Carga los criterios para el select
     */
    function loadCriteriosForSelect(callback) {
        if (criteriosCache.length > 0) {
            if (callback) callback(criteriosCache);
            return;
        }
        ajaxRequest(
            REVISIONES_URLS.criteriosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    criteriosCache = response.data;
                    if (callback) callback(criteriosCache);
                }
            }
        );
    }
    
    /**
     * Carga los documentos para el select
     */
    function loadDocumentosForSelect(callback) {
        if (documentosCache.length > 0) {
            if (callback) callback(documentosCache);
            return;
        }
        ajaxRequest(
            REVISIONES_URLS.documentosForSelect,
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
     * Carga los usuarios para el select
     */
    function loadUsuariosForSelect(callback) {
        if (usuariosCache.length > 0) {
            if (callback) callback(usuariosCache);
            return;
        }
        ajaxRequest(
            REVISIONES_URLS.usuariosForSelect,
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
    
    /**
     * Carga los procesos para el select
     */
    function loadProcesosForSelect(callback) {
        ajaxRequest(
            REVISIONES_URLS.procesosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    procesosCache = response.data;
                    if (callback) callback(procesosCache);
                }
            }
        );
    }
    
    /**
     * Carga las revisiones para el select, opcionalmente filtradas por proceso
     */
    function loadRevisionesForSelect(procesoId, callback) {
        const url = procesoId ? 
            `${REVISIONES_URLS.revisionesForSelect}?proceso_id=${procesoId}` : 
            REVISIONES_URLS.revisionesForSelect;
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    revisionesCache = response.data;
                    if (callback) callback(revisionesCache);
                }
            }
        );
    }
    
    // ========================================================================
    // MANEJO DE TIPOS DE CRITERIOS
    // ========================================================================
    
    /**
     * Actualiza los campos del formulario de criterio según el tipo seleccionado
     */
    function updateCriterioTipoFields() {
        const tipo = $('#criterio_tipo').val();
        
        // Ocultar todos los campos primero
        $('#criterio_escala_container').hide();
        $('#criterio_escala_maxima_container').hide();
        $('#criterio_opciones_container').hide();
        
        // Mostrar campos según el tipo
        if (tipo === 'numerico') {
            $('#criterio_escala_container').show();
            $('#criterio_escala_maxima_container').show();
            $('#criterio_escala_minima').prop('required', true);
            $('#criterio_escala_maxima').prop('required', true);
            $('#criterio_opciones').prop('required', false);
        } else if (tipo === 'opcion') {
            $('#criterio_opciones_container').show();
            $('#criterio_opciones').prop('required', true);
            $('#criterio_escala_minima').prop('required', false);
            $('#criterio_escala_maxima').prop('required', false);
        } else {
            $('#criterio_escala_minima').prop('required', false);
            $('#criterio_escala_maxima').prop('required', false);
            $('#criterio_opciones').prop('required', false);
        }
    }
    
    /**
     * Actualiza los campos del formulario de evaluación según el tipo de criterio seleccionado
     */
    function updateEvaluacionValorFields(criterioId) {
        // Ocultar todos los campos de valor primero
        $('.valor-field').hide().removeClass('show');
        $('.valor-field input, .valor-field textarea, .valor-field select').prop('required', false);
        
        if (!criterioId) {
            return;
        }
        
        // Buscar el criterio en el cache
        const criterio = criteriosCache.find(c => c.id == criterioId);
        if (!criterio) {
            // Si no está en el cache, cargar criterios
            loadCriteriosForSelect(function() {
                updateEvaluacionValorFields(criterioId);
            });
            return;
        }
        
        // Mostrar el campo correspondiente según el tipo
        if (criterio.tipo === 'numerico') {
            $('#evaluacion_valor_numerico_container').show().addClass('show');
            $('#evaluacion_valor_numerico').prop('required', criterio.es_obligatorio);
            if (criterio.escala_minima !== null) {
                $('#evaluacion_valor_numerico').attr('min', criterio.escala_minima);
            }
            if (criterio.escala_maxima !== null) {
                $('#evaluacion_valor_numerico').attr('max', criterio.escala_maxima);
            }
            // Mostrar información de escala
            if (criterio.escala_minima !== null && criterio.escala_maxima !== null) {
                $('#evaluacion_escala_info').text(`Rango: ${criterio.escala_minima} - ${criterio.escala_maxima}`);
            } else {
                $('#evaluacion_escala_info').text('');
            }
        } else if (criterio.tipo === 'texto') {
            $('#evaluacion_valor_texto_container').show().addClass('show');
            $('#evaluacion_valor_texto').prop('required', criterio.es_obligatorio);
        } else if (criterio.tipo === 'booleano') {
            $('#evaluacion_valor_booleano_container').show().addClass('show');
            $('#evaluacion_valor_booleano').prop('required', criterio.es_obligatorio);
        } else if (criterio.tipo === 'opcion') {
            $('#evaluacion_valor_opcion_container').show().addClass('show');
            $('#evaluacion_valor_opcion').prop('required', criterio.es_obligatorio);
            
            // Cargar opciones
            const select = $('#evaluacion_valor_opcion');
            select.empty().append('<option value="">Seleccionar...</option>');
            if (criterio.opciones && criterio.opciones.length > 0) {
                criterio.opciones.forEach(function(opcion) {
                    select.append(`<option value="${escapeHtml(opcion)}">${escapeHtml(opcion)}</option>`);
                });
            }
        }
    }
    
    // ========================================================================
    // INICIALIZACIÓN DE TABLAS
    // ========================================================================
    
    /**
     * Inicializa la tabla de criterios
     */
    function initTableCriterios() {
        tableCriterios = $('#tableCriterios').DataTable({
            ajax: {
                url: REVISIONES_URLS.criteriosList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { data: 'nombre' },
                { 
                    data: 'tipo_display',
                    render: function(data, type, row) {
                        return `<span class="badge badge-info">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: null,
                    render: function(data, type, row) {
                        if (row.tipo === 'numerico' && row.escala_minima !== null && row.escala_maxima !== null) {
                            return `${row.escala_minima} - ${row.escala_maxima}`;
                        }
                        return '<span class="text-muted">-</span>';
                    }
                },
                { 
                    data: 'opciones',
                    render: function(data) {
                        if (data && data.length > 0) {
                            return escapeHtml(data.join(', ')).substring(0, 50) + (data.join(', ').length > 50 ? '...' : '');
                        }
                        return '<span class="text-muted">-</span>';
                    }
                },
                { 
                    data: 'es_obligatorio',
                    render: function(data) {
                        return data ? '<span class="badge badge-warning">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-criterio" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-criterio" data-id="${row.id}" title="Eliminar">
                                    <i class="fas fa-trash"></i><span> Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            order: [[0, 'asc']],
            language: {
                url: '/static/DataTables/es-ES.json'
            },
            responsive: true
        });
    }
    
    /**
     * Inicializa la tabla de procesos
     */
    function initTableProcesos() {
        tableProcesos = $('#tableProcesos').DataTable({
            ajax: {
                url: REVISIONES_URLS.procesosList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { 
                    data: 'documento_titulo',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 50) + (data.length > 50 ? '...' : '');
                    }
                },
                { 
                    data: 'tipo_revision_display',
                    render: function(data) {
                        return `<span class="badge badge-info">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'estado_display',
                    render: function(data, type, row) {
                        return `<span class="badge ${getEstadoBadge(row.estado)}">${escapeHtml(data)}</span>`;
                    }
                },
                { data: 'iniciado_por_nombre' },
                { 
                    data: 'fecha_inicio',
                    render: function(data) {
                        return formatDate(data);
                    }
                },
                { 
                    data: 'revisiones_count',
                    render: function(data) {
                        return `<span class="badge badge-info">${data}</span>`;
                    }
                },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-proceso" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-proceso" data-id="${row.id}" title="Eliminar">
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
     * Inicializa la tabla de revisiones
     */
    function initTableRevisiones() {
        tableRevisiones = $('#tableRevisiones').DataTable({
            ajax: {
                url: REVISIONES_URLS.revisionesList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { 
                    data: 'proceso_revision_texto',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 50) + (data.length > 50 ? '...' : '');
                    }
                },
                { data: 'revisor_nombre' },
                { 
                    data: 'estado_display',
                    render: function(data, type, row) {
                        return `<span class="badge ${getEstadoBadge(row.estado)}">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'calificacion_general',
                    render: function(data) {
                        if (data) {
                            return `<span class="badge badge-success">${data}/5</span>`;
                        }
                        return '<span class="text-muted">-</span>';
                    }
                },
                { 
                    data: 'recomendacion_display',
                    render: function(data) {
                        if (data) {
                            return `<span class="badge badge-info">${escapeHtml(data)}</span>`;
                        }
                        return '<span class="text-muted">-</span>';
                    }
                },
                { 
                    data: 'fecha_asignacion',
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
                                <button type="button" class="btn btn-info btn-editar-revision" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-revision" data-id="${row.id}" title="Eliminar">
                                    <i class="fas fa-trash"></i><span> Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            order: [[6, 'desc']],
            language: {
                url: '/static/DataTables/es-ES.json'
            },
            responsive: true
        });
    }
    
    /**
     * Inicializa la tabla de evaluaciones
     */
    function initTableEvaluaciones() {
        tableEvaluaciones = $('#tableEvaluaciones').DataTable({
            ajax: {
                url: REVISIONES_URLS.evaluacionesList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { 
                    data: 'revision_texto',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 50) + (data.length > 50 ? '...' : '');
                    }
                },
                { data: 'criterio_nombre' },
                { 
                    data: 'valor',
                    render: function(data, type, row) {
                        if (data === null || data === undefined) {
                            return '<span class="text-muted">-</span>';
                        }
                        if (row.criterio_tipo === 'booleano') {
                            return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-danger">No</span>';
                        }
                        return escapeHtml(String(data));
                    }
                },
                { 
                    data: 'comentarios',
                    render: function(data) {
                        if (!data) return '<span class="text-muted">-</span>';
                        return escapeHtml(data).substring(0, 50) + (data.length > 50 ? '...' : '');
                    }
                },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-evaluacion" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-evaluacion" data-id="${row.id}" title="Eliminar">
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
    // MANEJO DE CRITERIOS
    // ========================================================================
    
    /**
     * Limpia el formulario de criterio
     */
    function limpiarFormCriterio() {
        $('#formCriterio')[0].reset();
        $('#criterio_id').val('');
        $('#modalCriterioLabel').text('Nuevo Criterio de Revisión');
        updateCriterioTipoFields();
    }
    
    /**
     * Maneja la creación de un criterio
     */
    function crearCriterio() {
        limpiarFormCriterio();
        $('#modalCriterio').modal('show');
    }
    
    /**
     * Maneja la edición de un criterio
     */
    function editarCriterio(criterioId) {
        ajaxRequest(
            REVISIONES_URLS.criterioDetail(criterioId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const criterio = response.data;
                    
                    $('#criterio_id').val(criterio.id);
                    $('#criterio_nombre').val(criterio.nombre);
                    $('#criterio_descripcion').val(criterio.descripcion || '');
                    $('#criterio_tipo').val(criterio.tipo);
                    $('#criterio_escala_minima').val(criterio.escala_minima || '');
                    $('#criterio_escala_maxima').val(criterio.escala_maxima || '');
                    $('#criterio_es_obligatorio').prop('checked', criterio.es_obligatorio);
                    
                    if (criterio.opciones && criterio.opciones.length > 0) {
                        $('#criterio_opciones').val(JSON.stringify(criterio.opciones));
                    } else {
                        $('#criterio_opciones').val('');
                    }
                    
                    updateCriterioTipoFields();
                    $('#modalCriterioLabel').text('Editar Criterio de Revisión');
                    $('#modalCriterio').modal('show');
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de un criterio
     */
    function eliminarCriterio(criterioId) {
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
                    REVISIONES_URLS.criterioDelete(criterioId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Criterio eliminado exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableCriterios.ajax.reload();
                            criteriosCache = []; // Limpiar cache
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE PROCESOS
    // ========================================================================
    
    /**
     * Limpia el formulario de proceso
     */
    function limpiarFormProceso() {
        $('#formProceso')[0].reset();
        $('#proceso_id').val('');
        $('#proceso_documento_id').val('').trigger('change');
        $('#modalProcesoLabel').text('Nuevo Proceso de Revisión');
        documentosCache = []; // Limpiar cache para recargar
    }
    
    /**
     * Maneja la creación de un proceso
     */
    function crearProceso() {
        limpiarFormProceso();
        loadDocumentosForSelect(function(documentos) {
            $('#proceso_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
            documentos.forEach(function(documento) {
                $('#proceso_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
            });
            $('#proceso_documento_id').trigger('change');
        });
        $('#modalProceso').modal('show');
    }
    
    /**
     * Maneja la edición de un proceso
     */
    function editarProceso(procesoId) {
        ajaxRequest(
            REVISIONES_URLS.procesoDetail(procesoId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const proceso = response.data;
                    
                    loadDocumentosForSelect(function(documentos) {
                        $('#proceso_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
                        documentos.forEach(function(documento) {
                            $('#proceso_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
                        });
                        
                        $('#proceso_id').val(proceso.id);
                        $('#proceso_documento_id').val(proceso.documento_id).trigger('change');
                        $('#proceso_tipo_revision').val(proceso.tipo_revision);
                        $('#proceso_estado').val(proceso.estado);
                        $('#proceso_notas_generales').val(proceso.notas_generales || '');
                        $('#modalProcesoLabel').text('Editar Proceso de Revisión');
                        $('#modalProceso').modal('show');
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de un proceso
     */
    function eliminarProceso(procesoId) {
        Swal.fire({
            title: '¿Está seguro?',
            text: 'Esta acción eliminará también todas las revisiones y evaluaciones asociadas',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    REVISIONES_URLS.procesoDelete(procesoId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Proceso eliminado exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableProcesos.ajax.reload();
                            tableRevisiones.ajax.reload();
                            tableEvaluaciones.ajax.reload();
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE REVISIONES
    // ========================================================================
    
    /**
     * Limpia el formulario de revisión
     */
    function limpiarFormRevision() {
        $('#formRevision')[0].reset();
        $('#revision_id').val('');
        $('#revision_proceso_revision_id').val('').trigger('change');
        $('#revision_revisor_id').val('').trigger('change');
        $('#modalRevisionLabel').text('Nueva Revisión');
        procesosCache = []; // Limpiar cache
        usuariosCache = []; // Limpiar cache
    }
    
    /**
     * Maneja la creación de una revisión
     */
    function crearRevision() {
        limpiarFormRevision();
        loadProcesosForSelect(function(procesos) {
            $('#revision_proceso_revision_id').empty().append('<option value="">Seleccionar proceso...</option>');
            procesos.forEach(function(proceso) {
                $('#revision_proceso_revision_id').append(`<option value="${proceso.id}">${escapeHtml(proceso.text)}</option>`);
            });
            $('#revision_proceso_revision_id').trigger('change');
        });
        loadUsuariosForSelect(function(usuarios) {
            $('#revision_revisor_id').empty().append('<option value="">Seleccionar revisor...</option>');
            usuarios.forEach(function(usuario) {
                $('#revision_revisor_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
            });
            $('#revision_revisor_id').trigger('change');
        });
        $('#modalRevision').modal('show');
    }
    
    /**
     * Maneja la edición de una revisión
     */
    function editarRevision(revisionId) {
        ajaxRequest(
            REVISIONES_URLS.revisionDetail(revisionId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const revision = response.data;
                    
                    loadProcesosForSelect(function(procesos) {
                        $('#revision_proceso_revision_id').empty().append('<option value="">Seleccionar proceso...</option>');
                        procesos.forEach(function(proceso) {
                            $('#revision_proceso_revision_id').append(`<option value="${proceso.id}">${escapeHtml(proceso.text)}</option>`);
                        });
                        
                        loadUsuariosForSelect(function(usuarios) {
                            $('#revision_revisor_id').empty().append('<option value="">Seleccionar revisor...</option>');
                            usuarios.forEach(function(usuario) {
                                $('#revision_revisor_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
                            });
                            
                            $('#revision_id').val(revision.id);
                            $('#revision_proceso_revision_id').val(revision.proceso_revision_id).trigger('change');
                            $('#revision_revisor_id').val(revision.revisor_id).trigger('change');
                            $('#revision_estado').val(revision.estado);
                            $('#revision_calificacion_general').val(revision.calificacion_general || '');
                            $('#revision_comentarios_publicos').val(revision.comentarios_publicos || '');
                            $('#revision_comentarios_privados').val(revision.comentarios_privados || '');
                            $('#revision_recomendacion').val(revision.recomendacion || '');
                            $('#modalRevisionLabel').text('Editar Revisión');
                            $('#modalRevision').modal('show');
                        });
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de una revisión
     */
    function eliminarRevision(revisionId) {
        Swal.fire({
            title: '¿Está seguro?',
            text: 'Esta acción eliminará también todas las evaluaciones asociadas',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    REVISIONES_URLS.revisionDelete(revisionId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Revisión eliminada exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableRevisiones.ajax.reload();
                            tableEvaluaciones.ajax.reload();
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE EVALUACIONES
    // ========================================================================
    
    /**
     * Limpia el formulario de evaluación
     */
    function limpiarFormEvaluacion() {
        $('#formEvaluacion')[0].reset();
        $('#evaluacion_id').val('');
        $('#evaluacion_revision_id').val('').trigger('change');
        $('#evaluacion_criterio_id').val('').trigger('change');
        $('.valor-field').hide().removeClass('show');
        $('#modalEvaluacionLabel').text('Nueva Evaluación de Criterio');
        revisionesCache = []; // Limpiar cache
        criteriosCache = []; // Limpiar cache
    }
    
    /**
     * Maneja la creación de una evaluación
     */
    function crearEvaluacion() {
        limpiarFormEvaluacion();
        loadRevisionesForSelect(null, function(revisiones) {
            $('#evaluacion_revision_id').empty().append('<option value="">Seleccionar revisión...</option>');
            revisiones.forEach(function(revision) {
                $('#evaluacion_revision_id').append(`<option value="${revision.id}">${escapeHtml(revision.text)}</option>`);
            });
            $('#evaluacion_revision_id').trigger('change');
        });
        loadCriteriosForSelect(function(criterios) {
            $('#evaluacion_criterio_id').empty().append('<option value="">Seleccionar criterio...</option>');
            criterios.forEach(function(criterio) {
                $('#evaluacion_criterio_id').append(`<option value="${criterio.id}">${escapeHtml(criterio.text)}</option>`);
            });
            $('#evaluacion_criterio_id').trigger('change');
        });
        $('#modalEvaluacion').modal('show');
    }
    
    /**
     * Maneja la edición de una evaluación
     */
    function editarEvaluacion(evaluacionId) {
        ajaxRequest(
            REVISIONES_URLS.evaluacionDetail(evaluacionId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const evaluacion = response.data;
                    
                    loadRevisionesForSelect(null, function(revisiones) {
                        $('#evaluacion_revision_id').empty().append('<option value="">Seleccionar revisión...</option>');
                        revisiones.forEach(function(revision) {
                            $('#evaluacion_revision_id').append(`<option value="${revision.id}">${escapeHtml(revision.text)}</option>`);
                        });
                        
                        loadCriteriosForSelect(function(criterios) {
                            $('#evaluacion_criterio_id').empty().append('<option value="">Seleccionar criterio...</option>');
                            criterios.forEach(function(criterio) {
                                $('#evaluacion_criterio_id').append(`<option value="${criterio.id}">${escapeHtml(criterio.text)}</option>`);
                            });
                            
                            $('#evaluacion_id').val(evaluacion.id);
                            $('#evaluacion_revision_id').val(evaluacion.revision_id).trigger('change');
                            $('#evaluacion_criterio_id').val(evaluacion.criterio_id).trigger('change');
                            
                            // Establecer el valor según el tipo
                            setTimeout(function() {
                                updateEvaluacionValorFields(evaluacion.criterio_id);
                                
                                if (evaluacion.criterio_tipo === 'numerico') {
                                    $('#evaluacion_valor_numerico').val(evaluacion.valor_numerico || '');
                                } else if (evaluacion.criterio_tipo === 'texto') {
                                    $('#evaluacion_valor_texto').val(evaluacion.valor_texto || '');
                                } else if (evaluacion.criterio_tipo === 'booleano') {
                                    $('#evaluacion_valor_booleano').val(evaluacion.valor_booleano ? 'true' : 'false');
                                } else if (evaluacion.criterio_tipo === 'opcion') {
                                    $('#evaluacion_valor_opcion').val(evaluacion.valor_opcion || '');
                                }
                                
                                $('#evaluacion_comentarios').val(evaluacion.comentarios || '');
                            }, 100);
                            
                            $('#modalEvaluacionLabel').text('Editar Evaluación de Criterio');
                            $('#modalEvaluacion').modal('show');
                        });
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de una evaluación
     */
    function eliminarEvaluacion(evaluacionId) {
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
                    REVISIONES_URLS.evaluacionDelete(evaluacionId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Evaluación eliminada exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableEvaluaciones.ajax.reload();
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
        // Botones de criterios
        $(document).on('click', '#btnCrearCriterio', crearCriterio);
        $(document).on('click', '.btn-editar-criterio', function() {
            editarCriterio($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-criterio', function() {
            eliminarCriterio($(this).data('id'));
        });
        
        // Botones de procesos
        $(document).on('click', '#btnCrearProceso', crearProceso);
        $(document).on('click', '.btn-editar-proceso', function() {
            editarProceso($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-proceso', function() {
            eliminarProceso($(this).data('id'));
        });
        
        // Botones de revisiones
        $(document).on('click', '#btnCrearRevision', crearRevision);
        $(document).on('click', '.btn-editar-revision', function() {
            editarRevision($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-revision', function() {
            eliminarRevision($(this).data('id'));
        });
        
        // Botones de evaluaciones
        $(document).on('click', '#btnCrearEvaluacion', crearEvaluacion);
        $(document).on('click', '.btn-editar-evaluacion', function() {
            editarEvaluacion($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-evaluacion', function() {
            eliminarEvaluacion($(this).data('id'));
        });
        
        // Formulario de criterio
        $('#formCriterio').on('submit', function(e) {
            e.preventDefault();
            
            const criterioId = $('#criterio_id').val();
            const data = {
                nombre: $('#criterio_nombre').val().trim(),
                descripcion: $('#criterio_descripcion').val().trim(),
                tipo: $('#criterio_tipo').val(),
                es_obligatorio: $('#criterio_es_obligatorio').is(':checked'),
            };
            
            // Agregar campos según el tipo
            if (data.tipo === 'numerico') {
                data.escala_minima = parseInt($('#criterio_escala_minima').val()) || null;
                data.escala_maxima = parseInt($('#criterio_escala_maxima').val()) || null;
            } else if (data.tipo === 'opcion') {
                try {
                    const opcionesText = $('#criterio_opciones').val().trim();
                    if (opcionesText) {
                        data.opciones = JSON.parse(opcionesText);
                    }
                } catch (e) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Las opciones deben ser un array JSON válido'
                    });
                    return;
                }
            }
            
            const url = criterioId ? REVISIONES_URLS.criterioUpdate(criterioId) : REVISIONES_URLS.criterioCreate;
            const method = criterioId ? 'PUT' : 'POST';
            
            ajaxRequest(
                url,
                method,
                data,
                function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Criterio guardado exitosamente',
                            timer: 1500,
                            showConfirmButton: false
                        });
                        $('#modalCriterio').modal('hide');
                        tableCriterios.ajax.reload();
                        criteriosCache = []; // Limpiar cache
                    }
                }
            );
        });
        
        // Formulario de proceso
        $('#formProceso').on('submit', function(e) {
            e.preventDefault();
            
            const procesoId = $('#proceso_id').val();
            const data = {
                documento_id: $('#proceso_documento_id').val(),
                tipo_revision: $('#proceso_tipo_revision').val(),
                estado: $('#proceso_estado').val(),
                notas_generales: $('#proceso_notas_generales').val().trim(),
            };
            
            const url = procesoId ? REVISIONES_URLS.procesoUpdate(procesoId) : REVISIONES_URLS.procesoCreate;
            const method = procesoId ? 'PUT' : 'POST';
            
            ajaxRequest(
                url,
                method,
                data,
                function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Proceso guardado exitosamente',
                            timer: 1500,
                            showConfirmButton: false
                        });
                        $('#modalProceso').modal('hide');
                        tableProcesos.ajax.reload();
                    }
                }
            );
        });
        
        // Formulario de revisión
        $('#formRevision').on('submit', function(e) {
            e.preventDefault();
            
            const revisionId = $('#revision_id').val();
            const data = {
                proceso_revision_id: $('#revision_proceso_revision_id').val(),
                revisor_id: $('#revision_revisor_id').val(),
                estado: $('#revision_estado').val(),
                calificacion_general: $('#revision_calificacion_general').val() ? parseInt($('#revision_calificacion_general').val()) : null,
                comentarios_publicos: $('#revision_comentarios_publicos').val().trim(),
                comentarios_privados: $('#revision_comentarios_privados').val().trim(),
                recomendacion: $('#revision_recomendacion').val() || null,
            };
            
            const url = revisionId ? REVISIONES_URLS.revisionUpdate(revisionId) : REVISIONES_URLS.revisionCreate;
            const method = revisionId ? 'PUT' : 'POST';
            
            ajaxRequest(
                url,
                method,
                data,
                function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Revisión guardada exitosamente',
                            timer: 1500,
                            showConfirmButton: false
                        });
                        $('#modalRevision').modal('hide');
                        tableRevisiones.ajax.reload();
                    }
                }
            );
        });
        
        // Formulario de evaluación
        $('#formEvaluacion').on('submit', function(e) {
            e.preventDefault();
            
            const evaluacionId = $('#evaluacion_id').val();
            const criterioId = $('#evaluacion_criterio_id').val();
            
            if (!criterioId) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Debe seleccionar un criterio'
                });
                return;
            }
            
            // Buscar el criterio en el cache
            const criterio = criteriosCache.find(c => c.id == criterioId);
            if (!criterio) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudo obtener la información del criterio'
                });
                return;
            }
            
            const data = {
                revision_id: $('#evaluacion_revision_id').val(),
                criterio_id: criterioId,
                comentarios: $('#evaluacion_comentarios').val().trim(),
            };
            
            // Agregar el valor según el tipo
            if (criterio.tipo === 'numerico') {
                data.valor_numerico = $('#evaluacion_valor_numerico').val() ? parseInt($('#evaluacion_valor_numerico').val()) : null;
            } else if (criterio.tipo === 'texto') {
                data.valor_texto = $('#evaluacion_valor_texto').val().trim();
            } else if (criterio.tipo === 'booleano') {
                const valor = $('#evaluacion_valor_booleano').val();
                data.valor_booleano = valor === '' ? null : (valor === 'true');
            } else if (criterio.tipo === 'opcion') {
                data.valor_opcion = $('#evaluacion_valor_opcion').val().trim();
            }
            
            const url = evaluacionId ? REVISIONES_URLS.evaluacionUpdate(evaluacionId) : REVISIONES_URLS.evaluacionCreate;
            const method = evaluacionId ? 'PUT' : 'POST';
            
            ajaxRequest(
                url,
                method,
                data,
                function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Evaluación guardada exitosamente',
                            timer: 1500,
                            showConfirmButton: false
                        });
                        $('#modalEvaluacion').modal('hide');
                        tableEvaluaciones.ajax.reload();
                    }
                }
            );
        });
        
        // Cambio de tipo de criterio
        $('#criterio_tipo').on('change', updateCriterioTipoFields);
        
        // Cambio de criterio en evaluación
        $('#evaluacion_criterio_id').on('change', function() {
            const criterioId = $(this).val();
            updateEvaluacionValorFields(criterioId);
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
     * Inicializa todo el módulo
     */
    function initRevisiones() {
        initTableCriterios();
        initTableProcesos();
        initTableRevisiones();
        initTableEvaluaciones();
        initEventListeners();
        updateCriterioTipoFields(); // Inicializar campos de criterio
    }
    
    // Inicializar cuando el DOM esté listo
    initRevisiones();
});


