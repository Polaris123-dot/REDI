/**
 * Script de gestión para Metadatos
 * Usa jQuery, DataTables, SweetAlert2, Select2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tableEsquemas, tableCampos, tableMetadatosDocumentos;
    let esquemasCache = [];
    let camposCache = [];
    let documentosCache = [];
    
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
     * Obtiene el badge para el tipo de dato
     */
    function getTipoDatoBadge(tipo) {
        const badges = {
            'texto': 'badge-info',
            'numero': 'badge-primary',
            'fecha': 'badge-success',
            'booleano': 'badge-warning',
            'lista': 'badge-secondary',
            'json': 'badge-dark'
        };
        return badges[tipo] || 'badge-secondary';
    }
    
    // ========================================================================
    // CARGAR DATOS PARA SELECTS
    // ========================================================================
    
    /**
     * Carga los esquemas para el select
     */
    function loadEsquemasForSelect(callback) {
        if (esquemasCache.length > 0) {
            if (callback) callback(esquemasCache);
            return;
        }
        ajaxRequest(
            METADATOS_URLS.esquemasForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    esquemasCache = response.data;
                    if (callback) callback(esquemasCache);
                }
            }
        );
    }
    
    /**
     * Carga los campos para el select, opcionalmente filtrados por esquema
     */
    function loadCamposForSelect(esquemaId, callback) {
        const url = esquemaId ? 
            `${METADATOS_URLS.camposForSelect}?esquema_id=${esquemaId}` : 
            METADATOS_URLS.camposForSelect;
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    camposCache = response.data;
                    if (callback) callback(camposCache);
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
            METADATOS_URLS.documentosForSelect,
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
    
    // ========================================================================
    // INICIALIZACIÓN DE TABLAS
    // ========================================================================
    
    /**
     * Inicializa la tabla de esquemas
     */
    function initTableEsquemas() {
        tableEsquemas = $('#tableEsquemas').DataTable({
            ajax: {
                url: METADATOS_URLS.esquemasList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { data: 'nombre' },
                { data: 'prefijo' },
                { 
                    data: 'namespace',
                    render: function(data) {
                        return escapeHtml(data).substring(0, 50) + (data.length > 50 ? '...' : '');
                    }
                },
                { data: 'version' },
                { 
                    data: 'campos_count',
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
                                <button type="button" class="btn btn-info btn-editar-esquema" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-esquema" data-id="${row.id}" title="Eliminar">
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
     * Inicializa la tabla de campos
     */
    function initTableCampos() {
        tableCampos = $('#tableCampos').DataTable({
            ajax: {
                url: METADATOS_URLS.camposList,
                type: 'GET',
                dataSrc: 'data'
            },
            columns: [
                { data: 'id' },
                { data: 'esquema_nombre' },
                { data: 'nombre' },
                { data: 'etiqueta' },
                { 
                    data: 'tipo_dato',
                    render: function(data) {
                        const badge = getTipoDatoBadge(data);
                        return `<span class="badge ${badge} badge-tipo-dato">${data}</span>`;
                    }
                },
                { 
                    data: 'es_obligatorio',
                    render: function(data) {
                        return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                { 
                    data: 'es_repetible',
                    render: function(data) {
                        return data ? '<span class="badge badge-info">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                { 
                    data: 'valores_count',
                    render: function(data) {
                        return `<span class="badge badge-primary">${data}</span>`;
                    }
                },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-campo" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-campo" data-id="${row.id}" title="Eliminar">
                                    <i class="fas fa-trash"></i><span> Eliminar</span>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            order: [[1, 'asc'], [2, 'asc']],
            language: {
                url: '/static/DataTables/es-ES.json'
            },
            responsive: true
        });
    }
    
    /**
     * Inicializa la tabla de metadatos de documentos
     */
    function initTableMetadatosDocumentos() {
        tableMetadatosDocumentos = $('#tableMetadatosDocumentos').DataTable({
            ajax: {
                url: METADATOS_URLS.metadatosDocumentosList,
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
                { data: 'campo_metadato_nombre' },
                { data: 'campo_metadato_esquema' },
                { 
                    data: 'tipo_dato',
                    render: function(data) {
                        const badge = getTipoDatoBadge(data);
                        return `<span class="badge ${badge} badge-tipo-dato">${data}</span>`;
                    }
                },
                { 
                    data: 'valor',
                    render: function(data) {
                        if (!data) return '<span class="text-muted">-</span>';
                        const valor = escapeHtml(data);
                        return valor.substring(0, 50) + (valor.length > 50 ? '...' : '');
                    }
                },
                { data: 'idioma' },
                { data: 'orden' },
                {
                    data: null,
                    orderable: false,
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-info btn-editar-metadato-documento" data-id="${row.id}" title="Editar">
                                    <i class="fas fa-edit"></i><span> Editar</span>
                                </button>
                                <button type="button" class="btn btn-danger btn-eliminar-metadato-documento" data-id="${row.id}" title="Eliminar">
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
    // MANEJO DE VALORES DE METADATOS POR TIPO DE DATO
    // ========================================================================
    
    /**
     * Actualiza el input del valor según el tipo de dato del campo seleccionado
     */
    function updateValorInput() {
        const campoId = $('#metadato_documento_campo_id').val();
        if (!campoId) {
            // Ocultar todos los inputs
            $('#metadato_documento_valor_texto, #metadato_documento_valor_numero, #metadato_documento_valor_fecha, #metadato_documento_valor_booleano, #metadato_documento_valor_json, #metadato_documento_valor_lista').hide();
            $('#metadato_documento_valor_required').text('');
            return;
        }
        
        // Buscar el campo en el cache
        const campo = camposCache.find(c => c.id == campoId);
        if (!campo) {
            // Recargar campos si no está en cache
            loadCamposForSelect(null, function() {
                updateValorInput();
            });
            return;
        }
        
        const tipoDato = campo.tipo_dato;
        const esObligatorio = campo.es_obligatorio || false;
        
        // Actualizar el indicador de obligatorio
        if (esObligatorio) {
            $('#metadato_documento_valor_required').text('*');
        } else {
            $('#metadato_documento_valor_required').text('');
        }
        
        // Ocultar todos los inputs
        $('#metadato_documento_valor_texto, #metadato_documento_valor_numero, #metadato_documento_valor_fecha, #metadato_documento_valor_booleano_container, #metadato_documento_valor_json, #metadato_documento_valor_lista').hide();
        
        // Mostrar el input correspondiente
        switch(tipoDato) {
            case 'texto':
                $('#metadato_documento_valor_texto').show().prop('required', esObligatorio);
                break;
            case 'numero':
                $('#metadato_documento_valor_numero').show().prop('required', esObligatorio);
                break;
            case 'fecha':
                $('#metadato_documento_valor_fecha').show().prop('required', esObligatorio);
                break;
            case 'booleano':
                $('#metadato_documento_valor_booleano_container').show();
                $('#metadato_documento_valor_booleano').prop('required', esObligatorio);
                break;
            case 'json':
                $('#metadato_documento_valor_json').show().prop('required', esObligatorio);
                break;
            case 'lista':
                $('#metadato_documento_valor_lista').show().prop('required', esObligatorio);
                // Cargar opciones del campo
                if (campo.valores_posibles && Array.isArray(campo.valores_posibles)) {
                    let options = '<option value="">Seleccionar valor...</option>';
                    campo.valores_posibles.forEach(function(opcion) {
                        options += `<option value="${escapeHtml(opcion)}">${escapeHtml(opcion)}</option>`;
                    });
                    $('#metadato_documento_valor_lista').html(options);
                }
                break;
        }
    }
    
    /**
     * Obtiene el valor del input según el tipo de dato
     */
    function getValorFromInput() {
        const campoId = $('#metadato_documento_campo_id').val();
        if (!campoId) return null;
        
        const campo = camposCache.find(c => c.id == campoId);
        if (!campo) return null;
        
        const tipoDato = campo.tipo_dato;
        let valor = null;
        
        switch(tipoDato) {
            case 'texto':
                valor = $('#metadato_documento_valor_texto').val();
                break;
            case 'numero':
                valor = $('#metadato_documento_valor_numero').val();
                break;
            case 'fecha':
                valor = $('#metadato_documento_valor_fecha').val();
                break;
            case 'booleano':
                valor = $('#metadato_documento_valor_booleano').is(':checked');
                break;
            case 'json':
                valor = $('#metadato_documento_valor_json').val();
                break;
            case 'lista':
                valor = $('#metadato_documento_valor_lista').val();
                break;
        }
        
        return valor;
    }
    
    /**
     * Establece el valor en el input según el tipo de dato
     */
    function setValorToInput(valor, tipoDato) {
        if (valor === null || valor === undefined || valor === '') {
            // Limpiar valores si no hay valor
            $('#metadato_documento_valor_texto').val('');
            $('#metadato_documento_valor_numero').val('');
            $('#metadato_documento_valor_fecha').val('');
            $('#metadato_documento_valor_booleano').prop('checked', false);
            $('#metadato_documento_valor_json').val('');
            $('#metadato_documento_valor_lista').val('');
            return;
        }
        
        switch(tipoDato) {
            case 'texto':
            case 'lista':
                $('#metadato_documento_valor_texto').val(valor);
                break;
            case 'numero':
                $('#metadato_documento_valor_numero').val(valor);
                break;
            case 'fecha':
                // Convertir fecha a formato YYYY-MM-DD
                if (valor instanceof Date) {
                    valor = valor.toISOString().split('T')[0];
                } else if (typeof valor === 'string' && valor.length > 10) {
                    valor = valor.substring(0, 10);
                }
                $('#metadato_documento_valor_fecha').val(valor);
                break;
            case 'booleano':
                $('#metadato_documento_valor_booleano').prop('checked', valor === true || valor === 'true' || valor === 1 || valor === '1' || valor === 'True');
                break;
            case 'json':
                if (typeof valor === 'object') {
                    valor = JSON.stringify(valor, null, 2);
                }
                $('#metadato_documento_valor_json').val(valor);
                break;
        }
    }
    
    // ========================================================================
    // MANEJO DE ESQUEMAS
    // ========================================================================
    
    /**
     * Limpia el formulario de esquema
     */
    function limpiarFormEsquema() {
        $('#formEsquema')[0].reset();
        $('#esquema_id').val('');
        $('#modalEsquemaLabel').text('Nuevo Esquema de Metadatos');
    }
    
    /**
     * Maneja la creación de un esquema
     */
    function crearEsquema() {
        limpiarFormEsquema();
        $('#modalEsquema').modal('show');
    }
    
    /**
     * Maneja la edición de un esquema
     */
    function editarEsquema(esquemaId) {
        ajaxRequest(
            METADATOS_URLS.esquemaDetail(esquemaId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const esquema = response.data;
                    $('#esquema_id').val(esquema.id);
                    $('#esquema_nombre').val(esquema.nombre);
                    $('#esquema_prefijo').val(esquema.prefijo);
                    $('#esquema_namespace').val(esquema.namespace);
                    $('#esquema_version').val(esquema.version || '');
                    $('#esquema_descripcion').val(esquema.descripcion || '');
                    $('#modalEsquemaLabel').text('Editar Esquema de Metadatos');
                    $('#modalEsquema').modal('show');
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de un esquema
     */
    function eliminarEsquema(esquemaId) {
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
                    METADATOS_URLS.esquemaDelete(esquemaId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Esquema eliminado exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableEsquemas.ajax.reload();
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE CAMPOS
    // ========================================================================
    
    /**
     * Limpia el formulario de campo
     */
    function limpiarFormCampo() {
        $('#formCampo')[0].reset();
        $('#campo_id').val('');
        $('#campo_esquema_id').val('').trigger('change');
        $('#campo_valores_posibles').val('');
        $('#modalCampoLabel').text('Nuevo Campo de Metadatos');
    }
    
    /**
     * Maneja la creación de un campo
     */
    function crearCampo() {
        limpiarFormCampo();
        loadEsquemasForSelect(function(esquemas) {
            $('#campo_esquema_id').empty().append('<option value="">Seleccionar esquema...</option>');
            esquemas.forEach(function(esquema) {
                $('#campo_esquema_id').append(`<option value="${esquema.id}">${escapeHtml(esquema.nombre)}</option>`);
            });
            $('#campo_esquema_id').trigger('change');
        });
        $('#modalCampo').modal('show');
    }
    
    /**
     * Maneja la edición de un campo
     */
    function editarCampo(campoId) {
        ajaxRequest(
            METADATOS_URLS.campoDetail(campoId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const campo = response.data;
                    loadEsquemasForSelect(function(esquemas) {
                        $('#campo_esquema_id').empty().append('<option value="">Seleccionar esquema...</option>');
                        esquemas.forEach(function(esquema) {
                            $('#campo_esquema_id').append(`<option value="${esquema.id}">${escapeHtml(esquema.nombre)}</option>`);
                        });
                        
                        $('#campo_id').val(campo.id);
                        $('#campo_esquema_id').val(campo.esquema_id).trigger('change');
                        $('#campo_nombre').val(campo.nombre);
                        $('#campo_etiqueta').val(campo.etiqueta);
                        $('#campo_tipo_dato').val(campo.tipo_dato);
                        $('#campo_es_obligatorio').prop('checked', campo.es_obligatorio);
                        $('#campo_es_repetible').prop('checked', campo.es_repetible);
                        
                        if (campo.valores_posibles) {
                            if (typeof campo.valores_posibles === 'object') {
                                $('#campo_valores_posibles').val(JSON.stringify(campo.valores_posibles, null, 2));
                            } else {
                                $('#campo_valores_posibles').val(campo.valores_posibles);
                            }
                        } else {
                            $('#campo_valores_posibles').val('');
                        }
                        
                        $('#campo_descripcion').val(campo.descripcion || '');
                        $('#modalCampoLabel').text('Editar Campo de Metadatos');
                        $('#modalCampo').modal('show');
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de un campo
     */
    function eliminarCampo(campoId) {
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
                    METADATOS_URLS.campoDelete(campoId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Campo eliminado exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableCampos.ajax.reload();
                        }
                    }
                );
            }
        });
    }
    
    // ========================================================================
    // MANEJO DE METADATOS DE DOCUMENTOS
    // ========================================================================
    
    /**
     * Limpia el formulario de metadato de documento
     */
    function limpiarFormMetadatoDocumento() {
        $('#formMetadatoDocumento')[0].reset();
        $('#metadato_documento_id').val('');
        $('#metadato_documento_documento_id').val('').trigger('change');
        $('#metadato_documento_campo_id').val('').trigger('change');
        $('#metadato_documento_orden').val('0');
        $('#metadato_documento_valor_texto, #metadato_documento_valor_numero, #metadato_documento_valor_fecha, #metadato_documento_valor_booleano_container, #metadato_documento_valor_json, #metadato_documento_valor_lista').hide();
        $('#metadato_documento_valor_texto, #metadato_documento_valor_numero, #metadato_documento_valor_fecha, #metadato_documento_valor_json, #metadato_documento_valor_lista').val('');
        $('#metadato_documento_valor_booleano').prop('checked', false);
        $('#modalMetadatoDocumentoLabel').text('Nuevo Metadato de Documento');
    }
    
    /**
     * Maneja la creación de un metadato de documento
     */
    function crearMetadatoDocumento() {
        limpiarFormMetadatoDocumento();
        loadDocumentosForSelect(function(documentos) {
            $('#metadato_documento_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
            documentos.forEach(function(documento) {
                $('#metadato_documento_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
            });
            $('#metadato_documento_documento_id').trigger('change');
        });
        loadCamposForSelect(null, function(campos) {
            $('#metadato_documento_campo_id').empty().append('<option value="">Seleccionar campo...</option>');
            campos.forEach(function(campo) {
                $('#metadato_documento_campo_id').append(`<option value="${campo.id}" data-tipo="${campo.tipo_dato}">${escapeHtml(campo.text)}</option>`);
            });
            $('#metadato_documento_campo_id').trigger('change');
        });
        $('#modalMetadatoDocumento').modal('show');
    }
    
    /**
     * Maneja la edición de un metadato de documento
     */
    function editarMetadatoDocumento(metadatoId) {
        ajaxRequest(
            METADATOS_URLS.metadatoDocumentoDetail(metadatoId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const metadato = response.data;
                    
                    loadDocumentosForSelect(function(documentos) {
                        $('#metadato_documento_documento_id').empty().append('<option value="">Seleccionar documento...</option>');
                        documentos.forEach(function(documento) {
                            $('#metadato_documento_documento_id').append(`<option value="${documento.id}">${escapeHtml(documento.text)}</option>`);
                        });
                        
                        loadCamposForSelect(null, function(campos) {
                            $('#metadato_documento_campo_id').empty().append('<option value="">Seleccionar campo...</option>');
                            campos.forEach(function(campo) {
                                $('#metadato_documento_campo_id').append(`<option value="${campo.id}" data-tipo="${campo.tipo_dato}">${escapeHtml(campo.text)}</option>`);
                            });
                            
                            $('#metadato_documento_id').val(metadato.id);
                            $('#metadato_documento_documento_id').val(metadato.documento_id).trigger('change');
                            $('#metadato_documento_campo_id').val(metadato.campo_metadato_id).trigger('change');
                            $('#metadato_documento_idioma').val(metadato.idioma || '');
                            $('#metadato_documento_orden').val(metadato.orden || 0);
                            
                            // Actualizar el input del valor según el tipo de dato del campo
                            updateValorInput();
                            
                            // Esperar un momento para que se actualice el input, luego establecer el valor
                            setTimeout(function() {
                                setValorToInput(metadato.valor, metadato.tipo_dato);
                            }, 100);
                            
                            $('#modalMetadatoDocumentoLabel').text('Editar Metadato de Documento');
                            $('#modalMetadatoDocumento').modal('show');
                        });
                    });
                }
            }
        );
    }
    
    /**
     * Maneja la eliminación de un metadato de documento
     */
    function eliminarMetadatoDocumento(metadatoId) {
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
                    METADATOS_URLS.metadatoDocumentoDelete(metadatoId),
                    'DELETE',
                    null,
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Metadato eliminado exitosamente',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            tableMetadatosDocumentos.ajax.reload();
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
        // Botones de esquemas
        $(document).on('click', '#btnCrearEsquema', crearEsquema);
        $(document).on('click', '.btn-editar-esquema', function() {
            editarEsquema($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-esquema', function() {
            eliminarEsquema($(this).data('id'));
        });
        
        // Botones de campos
        $(document).on('click', '#btnCrearCampo', crearCampo);
        $(document).on('click', '.btn-editar-campo', function() {
            editarCampo($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-campo', function() {
            eliminarCampo($(this).data('id'));
        });
        
        // Botones de metadatos de documentos
        $(document).on('click', '#btnCrearMetadatoDocumento', crearMetadatoDocumento);
        $(document).on('click', '.btn-editar-metadato-documento', function() {
            editarMetadatoDocumento($(this).data('id'));
        });
        $(document).on('click', '.btn-eliminar-metadato-documento', function() {
            eliminarMetadatoDocumento($(this).data('id'));
        });
        
        // Formulario de esquema
        $('#formEsquema').on('submit', function(e) {
            e.preventDefault();
            const esquemaId = $('#esquema_id').val();
            const formData = {
                nombre: $('#esquema_nombre').val(),
                prefijo: $('#esquema_prefijo').val(),
                namespace: $('#esquema_namespace').val(),
                version: $('#esquema_version').val() || null,
                descripcion: $('#esquema_descripcion').val() || null
            };
            
            const url = esquemaId ? 
                METADATOS_URLS.esquemaUpdate(esquemaId) : 
                METADATOS_URLS.esquemaCreate;
            const method = esquemaId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Esquema guardado exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalEsquema').modal('hide');
                    tableEsquemas.ajax.reload();
                    esquemasCache = []; // Limpiar cache
                }
            });
        });
        
        // Formulario de campo
        $('#formCampo').on('submit', function(e) {
            e.preventDefault();
            const campoId = $('#campo_id').val();
            const formData = {
                esquema_id: $('#campo_esquema_id').val(),
                nombre: $('#campo_nombre').val(),
                etiqueta: $('#campo_etiqueta').val(),
                tipo_dato: $('#campo_tipo_dato').val(),
                es_obligatorio: $('#campo_es_obligatorio').is(':checked'),
                es_repetible: $('#campo_es_repetible').is(':checked'),
                valores_posibles: $('#campo_valores_posibles').val() || null,
                descripcion: $('#campo_descripcion').val() || null
            };
            
            const url = campoId ? 
                METADATOS_URLS.campoUpdate(campoId) : 
                METADATOS_URLS.campoCreate;
            const method = campoId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Campo guardado exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalCampo').modal('hide');
                    tableCampos.ajax.reload();
                    camposCache = []; // Limpiar cache
                }
            });
        });
        
        // Formulario de metadato de documento
        $('#formMetadatoDocumento').on('submit', function(e) {
            e.preventDefault();
            const metadatoId = $('#metadato_documento_id').val();
            const formData = {
                documento_id: $('#metadato_documento_documento_id').val(),
                campo_metadato_id: $('#metadato_documento_campo_id').val(),
                valor: getValorFromInput(),
                idioma: $('#metadato_documento_idioma').val() || null,
                orden: parseInt($('#metadato_documento_orden').val()) || 0
            };
            
            const url = metadatoId ? 
                METADATOS_URLS.metadatoDocumentoUpdate(metadatoId) : 
                METADATOS_URLS.metadatoDocumentoCreate;
            const method = metadatoId ? 'PUT' : 'POST';
            
            ajaxRequest(url, method, formData, function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || 'Metadato guardado exitosamente',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    $('#modalMetadatoDocumento').modal('hide');
                    tableMetadatosDocumentos.ajax.reload();
                }
            });
        });
        
        // Cuando se cambia el campo de metadatos, actualizar el input del valor
        $('#metadato_documento_campo_id').on('change', function() {
            updateValorInput();
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
     * Inicializa todo el módulo de metadatos
     */
    function initMetadatos() {
        initTableEsquemas();
        initTableCampos();
        initTableMetadatosDocumentos();
        initEventListeners();
    }
    
    // Exportar función de inicialización
    window.initMetadatos = initMetadatos;
});

