/**
 * Script de gestión para Interacción
 * Usa jQuery, DataTables, SweetAlert2, Select2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tableComentarios, tableValoraciones, tableCitas, tableReferencias;
    let documentosCache = [];
    let usuariosCache = [];
    let comentariosCache = [];
    
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
     * Carga los documentos para los selects
     */
    function loadDocumentosForSelect(selectId, callback) {
        if (documentosCache.length > 0) {
            populateSelect(selectId, documentosCache, 'id', 'text');
            if (callback) callback();
            return;
        }
        
        ajaxRequest(
            INTERACCION_URLS.documentosForSelect,
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
     * Carga los usuarios para los selects
     */
    function loadUsuariosForSelect(selectId, callback) {
        if (usuariosCache.length > 0) {
            populateSelect(selectId, usuariosCache, 'id', 'text');
            if (callback) callback();
            return;
        }
        
        ajaxRequest(
            INTERACCION_URLS.usuariosForSelect,
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
     * Carga los comentarios para el select de comentario padre
     */
    function loadComentariosForSelect(selectId, documentoId, excludeId = null) {
        ajaxRequest(
            INTERACCION_URLS.comentariosList,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const comentarios = response.data.filter(c => 
                        c.documento_id == documentoId && c.id != excludeId
                    );
                    populateSelect(selectId, comentarios, 'id', 'contenido', true);
                }
            }
        );
    }
    
    /**
     * Pobla un select con datos
     */
    function populateSelect(selectId, data, valueKey, textKey, truncate = false) {
        const $select = $(selectId);
        const currentValue = $select.val();
        $select.empty();
        
        if (selectId.includes('Padre') || selectId.includes('padre')) {
            $select.append('<option value="">Ninguno (comentario principal)</option>');
        } else {
            $select.append('<option value="">Seleccione...</option>');
        }
        
        data.forEach(function(item) {
            let text = item[textKey] || '';
            if (truncate && text.length > 50) {
                text = text.substring(0, 50) + '...';
            }
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
     * Inicializa la tabla de Comentarios
     */
    function initTableComentarios() {
        const $table = $('#tableComentarios');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableComentarios')) {
            $('#tableComentarios').DataTable().destroy();
        }
        
        tableComentarios = $('#tableComentarios').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: INTERACCION_URLS.comentariosList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar comentarios:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los comentarios',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'documento_titulo' },
                { data: 'usuario_nombre' },
                { 
                    data: 'contenido',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'es_publico',
                    render: function(data) {
                        return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                { 
                    data: 'es_moderado',
                    render: function(data) {
                        return data ? '<span class="badge badge-warning">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                { 
                    data: 'respuestas_count',
                    render: function(data) {
                        return `<span class="badge badge-info">${data || 0}</span>`;
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
                    width: '18%',
                    render: function(data, type, row) {
                        const contenidoEscapado = escapeHtml((row.contenido || '').substring(0, 50));
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-comentario" 
                                        data-id="${row.id}" 
                                        data-contenido="${contenidoEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-comentario" 
                                        data-id="${row.id}" 
                                        data-contenido="${contenidoEscapado}"
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
    
    /**
     * Inicializa la tabla de Valoraciones
     */
    function initTableValoraciones() {
        const $table = $('#tableValoraciones');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableValoraciones')) {
            $('#tableValoraciones').DataTable().destroy();
        }
        
        tableValoraciones = $('#tableValoraciones').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: INTERACCION_URLS.valoracionesList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar valoraciones:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las valoraciones',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'documento_titulo' },
                { data: 'usuario_nombre' },
                { 
                    data: 'calificacion',
                    render: function(data) {
                        let stars = '';
                        for (let i = 1; i <= 5; i++) {
                            if (i <= data) {
                                stars += '<i class="fas fa-star rating-stars"></i>';
                            } else {
                                stars += '<i class="far fa-star rating-stars"></i>';
                            }
                        }
                        return `<span>${stars} (${data}/5)</span>`;
                    }
                },
                { 
                    data: 'comentario',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'fecha',
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
                    width: '18%',
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-valoracion" 
                                        data-id="${row.id}" 
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-valoracion" 
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
            order: [[5, 'desc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Inicializa la tabla de Citas
     */
    function initTableCitas() {
        const $table = $('#tableCitas');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableCitas')) {
            $('#tableCitas').DataTable().destroy();
        }
        
        tableCitas = $('#tableCitas').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: INTERACCION_URLS.citasList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar citas:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las citas',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'documento_citado_titulo' },
                { data: 'documento_que_cita_titulo' },
                { 
                    data: 'contexto',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'fecha_citacion',
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
                    width: '18%',
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-cita" 
                                        data-id="${row.id}" 
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-cita" 
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
            order: [[4, 'desc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Inicializa la tabla de Referencias Bibliográficas
     */
    function initTableReferencias() {
        const $table = $('#tableReferencias');
        if ($table.length === 0 || $table.find('thead tr').length === 0) {
            return;
        }
        
        if ($.fn.DataTable.isDataTable('#tableReferencias')) {
            $('#tableReferencias').DataTable().destroy();
        }
        
        tableReferencias = $('#tableReferencias').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: INTERACCION_URLS.referenciasList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar referencias:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las referencias bibliográficas',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'documento_titulo' },
                { 
                    data: 'tipo_display',
                    render: function(data) {
                        const badgeClass = {
                            'Artículo': 'badge-primary',
                            'Libro': 'badge-info',
                            'Capítulo': 'badge-success',
                            'Tesis': 'badge-warning',
                            'Congreso': 'badge-danger',
                            'Patente': 'badge-dark',
                            'Web': 'badge-secondary',
                            'Otros': 'badge-secondary'
                        };
                        const className = badgeClass[data] || 'badge-secondary';
                        return `<span class="badge ${className}">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'titulo',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 100 ? data.substring(0, 100) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { 
                    data: 'autores',
                    render: function(data) {
                        if (!data) return '-';
                        const truncated = data.length > 50 ? data.substring(0, 50) + '...' : data;
                        return escapeHtml(truncated);
                    }
                },
                { data: 'año' },
                { 
                    data: 'doi',
                    render: function(data) {
                        if (!data) return '-';
                        return `<a href="https://doi.org/${escapeHtml(data)}" target="_blank">${escapeHtml(data)}</a>`;
                    }
                },
                { data: 'orden' },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const tituloEscapado = escapeHtml((row.titulo || '').substring(0, 50));
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-referencia" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-referencia" 
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
            order: [[7, 'asc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    // ========================================================================
    // EVENTOS PARA COMENTARIOS
    // ========================================================================
    
    /**
     * Abre el modal para crear un nuevo comentario
     */
    $(document).on('click', '#btnCrearComentario', function() {
        $('#modalComentarioLabel').text('Nuevo Comentario');
        $('#formComentario')[0].reset();
        $('#comentarioId').val('');
        $('#comentarioEsPublico').prop('checked', true);
        $('#comentarioEsModerado').prop('checked', false);
        
        loadDocumentosForSelect('#comentarioDocumento');
        loadUsuariosForSelect('#comentarioUsuario', function() {
            // Por defecto, seleccionar el usuario actual
            // Esto se puede hacer si tienes el ID del usuario actual
        });
        $('#comentarioPadre').empty().append('<option value="">Ninguno (comentario principal)</option>');
        
        $('#modalComentario').modal('show');
    });
    
    /**
     * Carga comentarios cuando se selecciona un documento
     */
    $(document).on('change', '#comentarioDocumento', function() {
        const documentoId = $(this).val();
        if (documentoId) {
            loadComentariosForSelect('#comentarioPadre', documentoId, $('#comentarioId').val());
        } else {
            $('#comentarioPadre').empty().append('<option value="">Ninguno (comentario principal)</option>');
        }
    });
    
    /**
     * Edita un comentario
     */
    $(document).on('click', '.btn-editar-comentario', function() {
        const comentarioId = $(this).data('id');
        const url = INTERACCION_URLS.comentarioDetail(comentarioId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const comentario = response.data;
                    $('#modalComentarioLabel').text('Editar Comentario');
                    $('#comentarioId').val(comentario.id);
                    $('#comentarioContenido').val(comentario.contenido);
                    $('#comentarioEsPublico').prop('checked', comentario.es_publico);
                    $('#comentarioEsModerado').prop('checked', comentario.es_moderado);
                    
                    loadDocumentosForSelect('#comentarioDocumento', function() {
                        $('#comentarioDocumento').val(comentario.documento_id);
                        loadComentariosForSelect('#comentarioPadre', comentario.documento_id, comentario.id);
                        if (comentario.comentario_padre_id) {
                            setTimeout(() => {
                                $('#comentarioPadre').val(comentario.comentario_padre_id);
                            }, 500);
                        }
                    });
                    
                    loadUsuariosForSelect('#comentarioUsuario', function() {
                        $('#comentarioUsuario').val(comentario.usuario_id);
                    });
                    
                    $('#modalComentario').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina un comentario
     */
    $(document).on('click', '.btn-eliminar-comentario', function() {
        const comentarioId = $(this).data('id');
        const contenido = $(this).data('contenido');
        const url = INTERACCION_URLS.comentarioDelete(comentarioId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar este comentario?`,
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
                                text: response.message || 'Comentario eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableComentarios.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Maneja el envío del formulario de comentario
     */
    $(document).on('submit', '#formComentario', function(e) {
        e.preventDefault();
        
        const comentarioId = $('#comentarioId').val();
        const formData = {
            documento_id: parseInt($('#comentarioDocumento').val()),
            usuario_id: parseInt($('#comentarioUsuario').val()) || null,
            comentario_padre_id: $('#comentarioPadre').val() ? parseInt($('#comentarioPadre').val()) : null,
            contenido: $('#comentarioContenido').val().trim(),
            es_moderado: $('#comentarioEsModerado').is(':checked'),
            es_publico: $('#comentarioEsPublico').is(':checked'),
        };
        
        if (!formData.documento_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar un documento',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (!formData.contenido) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El contenido es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (comentarioId) {
            url = INTERACCION_URLS.comentarioUpdate(comentarioId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = INTERACCION_URLS.comentarioCreate;
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
                    $('#modalComentario').modal('hide');
                    tableComentarios.ajax.reload(null, false);
                }
            }
        );
    });
    
    // ========================================================================
    // EVENTOS PARA VALORACIONES
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva valoración
     */
    $(document).on('click', '#btnCrearValoracion', function() {
        $('#modalValoracionLabel').text('Nueva Valoración');
        $('#formValoracion')[0].reset();
        $('#valoracionId').val('');
        
        loadDocumentosForSelect('#valoracionDocumento');
        loadUsuariosForSelect('#valoracionUsuario');
        
        $('#modalValoracion').modal('show');
    });
    
    /**
     * Edita una valoración
     */
    $(document).on('click', '.btn-editar-valoracion', function() {
        const valoracionId = $(this).data('id');
        const url = INTERACCION_URLS.valoracionDetail(valoracionId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const valoracion = response.data;
                    $('#modalValoracionLabel').text('Editar Valoración');
                    $('#valoracionId').val(valoracion.id);
                    $('#valoracionCalificacion').val(valoracion.calificacion);
                    $('#valoracionComentario').val(valoracion.comentario || '');
                    
                    loadDocumentosForSelect('#valoracionDocumento', function() {
                        $('#valoracionDocumento').val(valoracion.documento_id);
                    });
                    
                    loadUsuariosForSelect('#valoracionUsuario', function() {
                        $('#valoracionUsuario').val(valoracion.usuario_id);
                    });
                    
                    $('#modalValoracion').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina una valoración
     */
    $(document).on('click', '.btn-eliminar-valoracion', function() {
        const valoracionId = $(this).data('id');
        const url = INTERACCION_URLS.valoracionDelete(valoracionId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar esta valoración?`,
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
                                text: response.message || 'Valoración eliminada correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableValoraciones.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Maneja el envío del formulario de valoración
     */
    $(document).on('submit', '#formValoracion', function(e) {
        e.preventDefault();
        
        const valoracionId = $('#valoracionId').val();
        const formData = {
            documento_id: parseInt($('#valoracionDocumento').val()),
            usuario_id: parseInt($('#valoracionUsuario').val()) || null,
            calificacion: parseInt($('#valoracionCalificacion').val()),
            comentario: $('#valoracionComentario').val().trim() || null,
        };
        
        if (!formData.documento_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar un documento',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (!formData.calificacion || formData.calificacion < 1 || formData.calificacion > 5) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar una calificación entre 1 y 5',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (valoracionId) {
            url = INTERACCION_URLS.valoracionUpdate(valoracionId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = INTERACCION_URLS.valoracionCreate;
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
                    $('#modalValoracion').modal('hide');
                    tableValoraciones.ajax.reload(null, false);
                }
            }
        );
    });
    
    // ========================================================================
    // EVENTOS PARA CITAS
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva cita
     */
    $(document).on('click', '#btnCrearCita', function() {
        $('#modalCitaLabel').text('Nueva Cita');
        $('#formCita')[0].reset();
        $('#citaId').val('');
        
        loadDocumentosForSelect('#citaDocumentoCitado');
        loadDocumentosForSelect('#citaDocumentoQueCita');
        
        $('#modalCita').modal('show');
    });
    
    /**
     * Edita una cita
     */
    $(document).on('click', '.btn-editar-cita', function() {
        const citaId = $(this).data('id');
        const url = INTERACCION_URLS.citaDetail(citaId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const cita = response.data;
                    $('#modalCitaLabel').text('Editar Cita');
                    $('#citaId').val(cita.id);
                    $('#citaContexto').val(cita.contexto || '');
                    
                    loadDocumentosForSelect('#citaDocumentoCitado', function() {
                        $('#citaDocumentoCitado').val(cita.documento_citado_id);
                    });
                    
                    loadDocumentosForSelect('#citaDocumentoQueCita', function() {
                        $('#citaDocumentoQueCita').val(cita.documento_que_cita_id);
                    });
                    
                    $('#modalCita').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina una cita
     */
    $(document).on('click', '.btn-eliminar-cita', function() {
        const citaId = $(this).data('id');
        const url = INTERACCION_URLS.citaDelete(citaId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar esta cita?`,
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
                                text: response.message || 'Cita eliminada correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableCitas.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Maneja el envío del formulario de cita
     */
    $(document).on('submit', '#formCita', function(e) {
        e.preventDefault();
        
        const citaId = $('#citaId').val();
        const formData = {
            documento_citado_id: parseInt($('#citaDocumentoCitado').val()),
            documento_que_cita_id: parseInt($('#citaDocumentoQueCita').val()),
            contexto: $('#citaContexto').val().trim() || null,
        };
        
        if (!formData.documento_citado_id || !formData.documento_que_cita_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar ambos documentos',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (formData.documento_citado_id === formData.documento_que_cita_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Un documento no puede citarse a sí mismo',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (citaId) {
            url = INTERACCION_URLS.citaUpdate(citaId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = INTERACCION_URLS.citaCreate;
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
                    $('#modalCita').modal('hide');
                    tableCitas.ajax.reload(null, false);
                }
            }
        );
    });
    
    // ========================================================================
    // EVENTOS PARA REFERENCIAS BIBLIOGRÁFICAS
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva referencia
     */
    $(document).on('click', '#btnCrearReferencia', function() {
        $('#modalReferenciaLabel').text('Nueva Referencia Bibliográfica');
        $('#formReferencia')[0].reset();
        $('#referenciaId').val('');
        $('#referenciaTipo').val('otros');
        $('#referenciaOrden').val(0);
        
        loadDocumentosForSelect('#referenciaDocumento');
        
        $('#modalReferencia').modal('show');
    });
    
    /**
     * Edita una referencia
     */
    $(document).on('click', '.btn-editar-referencia', function() {
        const referenciaId = $(this).data('id');
        const url = INTERACCION_URLS.referenciaDetail(referenciaId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const referencia = response.data;
                    $('#modalReferenciaLabel').text('Editar Referencia Bibliográfica');
                    $('#referenciaId').val(referencia.id);
                    $('#referenciaTipo').val(referencia.tipo);
                    $('#referenciaTitulo').val(referencia.titulo);
                    $('#referenciaAutores').val(referencia.autores || '');
                    $('#referenciaAno').val(referencia.año || '');
                    $('#referenciaDOI').val(referencia.doi || '');
                    $('#referenciaURL').val(referencia.url || '');
                    $('#referenciaCitaCompleta').val(referencia.cita_completa || '');
                    $('#referenciaOrden').val(referencia.orden || 0);
                    
                    loadDocumentosForSelect('#referenciaDocumento', function() {
                        $('#referenciaDocumento').val(referencia.documento_id);
                    });
                    
                    $('#modalReferencia').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina una referencia
     */
    $(document).on('click', '.btn-eliminar-referencia', function() {
        const referenciaId = $(this).data('id');
        const titulo = $(this).data('titulo');
        const url = INTERACCION_URLS.referenciaDelete(referenciaId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la referencia "${titulo}"?`,
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
                                text: response.message || 'Referencia eliminada correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableReferencias.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Maneja el envío del formulario de referencia
     */
    $(document).on('submit', '#formReferencia', function(e) {
        e.preventDefault();
        
        const referenciaId = $('#referenciaId').val();
        const formData = {
            documento_id: parseInt($('#referenciaDocumento').val()),
            tipo: $('#referenciaTipo').val(),
            titulo: $('#referenciaTitulo').val().trim(),
            autores: $('#referenciaAutores').val().trim() || null,
            año: $('#referenciaAno').val() ? parseInt($('#referenciaAno').val()) : null,
            doi: $('#referenciaDOI').val().trim() || null,
            url: $('#referenciaURL').val().trim() || null,
            cita_completa: $('#referenciaCitaCompleta').val().trim() || null,
            orden: parseInt($('#referenciaOrden').val()) || 0,
        };
        
        if (!formData.documento_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar un documento',
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
        
        let url, method, sendData;
        if (referenciaId) {
            url = INTERACCION_URLS.referenciaUpdate(referenciaId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = INTERACCION_URLS.referenciaCreate;
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
                    $('#modalReferencia').modal('hide');
                    tableReferencias.ajax.reload(null, false);
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
        
        if (target === '#comentarios' && !$.fn.DataTable.isDataTable('#tableComentarios')) {
            initTableComentarios();
        } else if (target === '#valoraciones' && !$.fn.DataTable.isDataTable('#tableValoraciones')) {
            initTableValoraciones();
        } else if (target === '#citas' && !$.fn.DataTable.isDataTable('#tableCitas')) {
            initTableCitas();
        } else if (target === '#referencias' && !$.fn.DataTable.isDataTable('#tableReferencias')) {
            initTableReferencias();
        }
    });
    
    // Inicializar la tabla del tab activo al cargar la página
    try {
        const $activeTab = $('.nav-tabs .nav-link.active');
        const activeTabHref = $activeTab.length > 0 ? $activeTab.attr('href') : null;
        
        if (activeTabHref === '#comentarios') {
            initTableComentarios();
        }
    } catch (error) {
        console.error('Error al inicializar tablas:', error);
    }
    
    // Cargar documentos y usuarios cuando se muestran los modales
    $(document).on('show.bs.modal', '#modalComentario, #modalValoracion, #modalCita, #modalReferencia', function() {
        const modalId = $(this).attr('id');
        if (modalId === 'modalComentario') {
            loadDocumentosForSelect('#comentarioDocumento');
            loadUsuariosForSelect('#comentarioUsuario');
        } else if (modalId === 'modalValoracion') {
            loadDocumentosForSelect('#valoracionDocumento');
            loadUsuariosForSelect('#valoracionUsuario');
        } else if (modalId === 'modalCita') {
            loadDocumentosForSelect('#citaDocumentoCitado');
            loadDocumentosForSelect('#citaDocumentoQueCita');
        } else if (modalId === 'modalReferencia') {
            loadDocumentosForSelect('#referenciaDocumento');
        }
    });
});



