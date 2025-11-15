/**
 * Script de gestión para Búsqueda
 * Usa jQuery, DataTables, SweetAlert2, Select2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tableIndices, tableBusquedas;
    let documentosCache = [];
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
     * Formatea un objeto JSON para mostrar
     */
    function formatJSON(obj) {
        if (!obj) return '<span class="text-muted">-</span>';
        try {
            if (typeof obj === 'string') {
                obj = JSON.parse(obj);
            }
            return '<pre class="mb-0" style="font-size: 0.75rem; max-height: 100px; overflow-y: auto;">' + 
                   escapeHtml(JSON.stringify(obj, null, 2)) + 
                   '</pre>';
        } catch (e) {
            return escapeHtml(String(obj));
        }
    }
    
    // ========================================================================
    // CARGAR DATOS PARA SELECTS
    // ========================================================================
    
    /**
     * Carga los documentos para el select
     * @param {boolean} incluirConIndice - Si es true, incluye documentos que ya tienen índice
     * @param {number} indiceIdExcluir - ID del índice a excluir (para edición)
     * @param {function} callback - Función callback
     */
    function loadDocumentosForSelect(callback, incluirConIndice = false, indiceIdExcluir = null) {
        let url = BUSQUEDA_URLS.documentosForSelect;
        if (incluirConIndice || indiceIdExcluir) {
            const params = new URLSearchParams();
            if (incluirConIndice) params.append('incluir_con_indice', 'true');
            if (indiceIdExcluir) params.append('indice_id_excluir', indiceIdExcluir);
            url += '?' + params.toString();
        }
        
        // No cachear porque la lista puede cambiar cuando se crean índices
        ajaxRequest(
            url,
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
            BUSQUEDA_URLS.usuariosForSelect,
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
     * Inicializa la tabla de índices
     */
    function initTableIndices() {
        tableIndices = $('#tableIndices').DataTable({
            ajax: {
                url: BUSQUEDA_URLS.indicesList,
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
                    data: 'contenido_indexado_preview',
                    render: function(data, type, row) {
                        const preview = escapeHtml(data);
                        const length = row.contenido_indexado_length || 0;
                        return `<div class="contenido-preview" title="${length} caracteres">${preview}</div>`;
                    }
                },
                { 
                    data: 'palabras_clave_indexadas',
                    render: function(data) {
                        if (!data) return '<span class="text-muted">-</span>';
                        return escapeHtml(data).substring(0, 50) + (data.length > 50 ? '...' : '');
                    }
                },
                { 
                    data: 'fecha_indexacion',
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
                                <button type="button" class="btn btn-info btn-editar-indice" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-indice" data-id="${row.id}" title="Eliminar">
                                    <i class="fas fa-trash"></i><span> Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            order: [[4, 'desc']],
            language: {
                url: '/static/DataTables/es-ES.json'
            },
            responsive: true
        });
    }
    
    /**
     * Inicializa la tabla de búsquedas
     */
    function initTableBusquedas() {
        tableBusquedas = $('#tableBusquedas').DataTable({
            ajax: {
                url: BUSQUEDA_URLS.busquedasList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { 
                    data: 'termino_busqueda',
                    render: function(data) {
                        return `<strong>${escapeHtml(data)}</strong>`;
                    }
                },
                { 
                    data: 'usuario_nombre',
                    render: function(data) {
                        return data || '<span class="text-muted">Anónimo</span>';
                    }
                },
                { 
                    data: 'resultados_encontrados',
                    render: function(data) {
                        return `<span class="badge badge-info">${data}</span>`;
                    }
                },
                { 
                    data: 'filtros_aplicados',
                    render: function(data) {
                        return formatJSON(data);
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
                                <button type="button" class="btn btn-info btn-editar-busqueda" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-busqueda" data-id="${row.id}" title="Eliminar">
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
    
    // ========================================================================
    // MANEJO DE ÍNDICES
    // ========================================================================
    
    /**
     * Limpia el formulario de índice
     */
    function limpiarFormIndice() {
        $('#formIndice')[0].reset();
        $('#indice_id').val('');
        $('#indice_documento_id').val('').trigger('change');
        $('#modalIndiceLabel').text('Nuevo Índice de Búsqueda');
        // Recargar documentos porque la lista puede haber cambiado
        documentosCache = [];
    }
    
    /**
     * Maneja la creación de un índice
     */
    function crearIndice() {
        limpiarFormIndice();
        loadDocumentosForSelect(function(documentos) {
            $('#indice_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
            documentos.forEach(function(documento) {
                $('#indice_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
            });
            $('#indice_documento_id').trigger('change');
        });
        $('#modalIndice').modal('show');
    }
    
    /**
     * Maneja la edición de un índice
     */
    function editarIndice(indiceId) {
        ajaxRequest(
            BUSQUEDA_URLS.indiceDetail(indiceId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const indice = response.data;
                    
                    // Para editar, cargar todos los documentos incluyendo el actual
                    loadDocumentosForSelect(function(documentos) {
                        $('#indice_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
                        documentos.forEach(function(documento) {
                            const tieneIndice = documento.tiene_indice ? ' (tiene índice)' : '';
                            $('#indice_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}${tieneIndice}</option>`);
                        });
                        
                        $('#indice_id').val(indice.id);
                        $('#indice_documento_id').val(indice.documento_id).trigger('change');
                        $('#indice_contenido_indexado').val(indice.contenido_indexado);
                        $('#indice_palabras_clave_indexadas').val(indice.palabras_clave_indexadas || '');
                        $('#modalIndiceLabel').text('Editar Índice de Búsqueda');
                        $('#modalIndice').modal('show');
                    }, true, indice.id);
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de un índice
     */
    function eliminarIndice(indiceId) {
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
                    BUSQUEDA_URLS.indiceDelete(indiceId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Índice eliminado exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableIndices.ajax.reload();
                            // Limpiar cache de documentos para que se actualice la lista
                            documentosCache = [];
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE BÚSQUEDAS
    // ========================================================================
    
    /**
     * Limpia el formulario de búsqueda
     */
    function limpiarFormBusqueda() {
        $('#formBusqueda')[0].reset();
        $('#busqueda_id').val('');
        $('#busqueda_usuario_id').val('').trigger('change');
        $('#busqueda_resultados_encontrados').val('0');
        $('#busqueda_filtros_aplicados').val('');
        $('#modalBusquedaLabel').text('Nueva Búsqueda');
    }
    
    /**
     * Maneja la creación de una búsqueda
     */
    function crearBusqueda() {
        limpiarFormBusqueda();
        loadUsuariosForSelect(function(usuarios) {
            $('#busqueda_usuario_id').empty().append('<option value="">Seleccionar usuario...</option>');
            usuarios.forEach(function(usuario) {
                $('#busqueda_usuario_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
            });
            $('#busqueda_usuario_id').trigger('change');
        });
        $('#modalBusqueda').modal('show');
    }
    
    /**
     * Maneja la edición de una búsqueda
     */
    function editarBusqueda(busquedaId) {
        ajaxRequest(
            BUSQUEDA_URLS.busquedaDetail(busquedaId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const busqueda = response.data;
                    
                    loadUsuariosForSelect(function(usuarios) {
                        $('#busqueda_usuario_id').empty().append('<option value="">Seleccionar usuario...</option>');
                        usuarios.forEach(function(usuario) {
                            $('#busqueda_usuario_id').append(`<option value="${usuario.id}">${escapeHtml(usuario.text)}</option>`);
                        });
                        
                        $('#busqueda_id').val(busqueda.id);
                        $('#busqueda_termino_busqueda').val(busqueda.termino_busqueda);
                        $('#busqueda_usuario_id').val(busqueda.usuario_id || '').trigger('change');
                        $('#busqueda_resultados_encontrados').val(busqueda.resultados_encontrados || 0);
                        $('#busqueda_ip_address').val(busqueda.ip_address || '');
                        
                        if (busqueda.filtros_aplicados) {
                            if (typeof busqueda.filtros_aplicados === 'object') {
                                $('#busqueda_filtros_aplicados').val(JSON.stringify(busqueda.filtros_aplicados, null, 2));
                            } else {
                                $('#busqueda_filtros_aplicados').val(busqueda.filtros_aplicados);
                            }
                        } else {
                            $('#busqueda_filtros_aplicados').val('');
                        }
                        
                        $('#modalBusquedaLabel').text('Editar Búsqueda');
                        $('#modalBusqueda').modal('show');
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de una búsqueda
     */
    function eliminarBusqueda(busquedaId) {
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
                    BUSQUEDA_URLS.busquedaDelete(busquedaId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Búsqueda eliminada exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableBusquedas.ajax.reload();
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
        // Botones de índices
        $(document).on('click', '#btnCrearIndice', crearIndice);
        $(document).on('click', '.btn-editar-indice', function() {
            editarIndice($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-indice', function() {
            eliminarIndice($(this).data('id'));
        });
        
        // Botones de búsquedas
        $(document).on('click', '#btnCrearBusqueda', crearBusqueda);
        $(document).on('click', '.btn-editar-busqueda', function() {
            editarBusqueda($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-busqueda', function() {
            eliminarBusqueda($(this).data('id'));
        });
        
        // Formulario de índice
        $('#formIndice').on('submit', function(e) {
            e.preventDefault();
            const indiceId = $('#indice_id').val();
            const formData = {
                contenido_indexado: $('#indice_contenido_indexado').val(),
                palabras_clave_indexadas: $('#indice_palabras_clave_indexadas').val() || null
            };
            
            // Solo incluir documento_id si se está creando o si cambió
            const documentoId = $('#indice_documento_id').val();
            if (!indiceId || documentoId) {
                formData.documento_id = documentoId;
            }
            
            const url = indiceId ? 
                BUSQUEDA_URLS.indiceUpdate(indiceId) : 
                BUSQUEDA_URLS.indiceCreate;
            const method = indiceId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Índice guardado exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalIndice').modal('hide');
                    tableIndices.ajax.reload();
                    // Limpiar cache de documentos
                    documentosCache = [];
                }
            });
        });
        
        // Formulario de búsqueda
        $('#formBusqueda').on('submit', function(e) {
            e.preventDefault();
            const busquedaId = $('#busqueda_id').val();
            
            // Procesar filtros_aplicados
            let filtros_aplicados = $('#busqueda_filtros_aplicados').val().trim();
            if (filtros_aplicados) {
                try {
                    filtros_aplicados = JSON.parse(filtros_aplicados);
                } catch (e) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Los filtros aplicados deben ser un JSON válido',
                        confirmButtonText: 'Aceptar'
                    });
                    return;
                }
            } else {
                filtros_aplicados = null;
            }
            
            const formData = {
                termino_busqueda: $('#busqueda_termino_busqueda').val(),
                usuario_id: $('#busqueda_usuario_id').val() || null,
                resultados_encontrados: parseInt($('#busqueda_resultados_encontrados').val()) || 0,
                ip_address: $('#busqueda_ip_address').val() || null,
                filtros_aplicados: filtros_aplicados
            };
            
            const url = busquedaId ? 
                BUSQUEDA_URLS.busquedaUpdate(busquedaId) : 
                BUSQUEDA_URLS.busquedaCreate;
            const method = busquedaId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Búsqueda guardada exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalBusqueda').modal('hide');
                    tableBusquedas.ajax.reload();
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
     * Inicializa todo el módulo de búsqueda
     */
    function initBusqueda() {
        initTableIndices();
        initTableBusquedas();
        initEventListeners();
    }
    
    // Exportar función de inicialización
    window.initBusqueda = initBusqueda;
});

