/**
 * Script de gestión para Repositorio (Tipos de Recurso, Estados de Documento, etc.)
 * Usa jQuery, DataTables, SweetAlert2 y URL Reverse
 */

$(document).ready(function() {
    // Variables globales - Declarar todas las tablas al inicio
    let tableTiposRecurso, tableEstadosDocumento, tableComunidades, 
        tableColecciones, tableLicencias, tableDocumentos, 
        tableAutores, tableColaboradores;
    
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
    
    // Hacer disponible escapeHtml globalmente para uso en DataTables render
    window.escapeHtml = escapeHtml;
    
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
    
    // ========================================================================
    // TABLAS DATATABLES
    // ========================================================================
    
    /**
     * Inicializa la tabla de Tipos de Recurso
     */
    function initTableTiposRecurso() {
        tableTiposRecurso = $('#tableTiposRecurso').DataTable({
            responsive: {
                details: {
                    type: 'column',
                    target: 'tr'
                }
            },
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.tiposRecursoList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar tipos de recurso:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los tipos de recurso',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'nombre' },
                { 
                    data: 'descripcion',
                    render: function(data) {
                        return data ? (data.length > 50 ? data.substring(0, 50) + '...' : data) : '-';
                    }
                },
                { 
                    data: 'icono',
                    render: function(data) {
                        if (data) {
                            return `<i class="${escapeHtml(data)}"></i> ${escapeHtml(data)}`;
                        }
                        return '-';
                    }
                },
                { 
                    data: 'categoria',
                    render: function(data) {
                        return data ? `<span class="badge badge-info">${escapeHtml(data)}</span>` : '-';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const escapeHtmlFn = window.escapeHtml || escapeHtml;
                        const nombreEscapado = escapeHtmlFn(row.nombre || '');
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-warning btn-editar-tipo-recurso" 
                                        data-id="${row.id}" 
                                        data-nombre="${nombreEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-tipo-recurso" 
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
     * Inicializa la tabla de Estados de Documento
     */
    function initTableEstadosDocumento() {
        tableEstadosDocumento = $('#tableEstadosDocumento').DataTable({
            responsive: {
                details: {
                    type: 'column',
                    target: 'tr'
                }
            },
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.estadosDocumentoList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar estados de documento:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los estados de documento',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'orden', width: '10%' },
                { data: 'nombre' },
                { 
                    data: 'descripcion',
                    render: function(data) {
                        return data ? (data.length > 50 ? data.substring(0, 50) + '...' : data) : '-';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const escapeHtmlFn = window.escapeHtml || escapeHtml;
                        const nombreEscapado = escapeHtmlFn(row.nombre || '');
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-warning btn-editar-estado-documento" 
                                        data-id="${row.id}" 
                                        data-nombre="${nombreEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-estado-documento" 
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
    
    // ========================================================================
    // GESTIÓN DE TIPOS DE RECURSO
    // ========================================================================
    
    /**
     * Abre el modal para crear un nuevo tipo de recurso
     */
    $('#btnCrearTipoRecurso').on('click', function() {
        $('#modalTipoRecursoLabel').text('Nuevo Tipo de Recurso');
        $('#formTipoRecurso')[0].reset();
        $('#tipoRecursoId').val('');
        $('#modalTipoRecurso').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de tipo de recurso
     */
    $('#formTipoRecurso').on('submit', function(e) {
        e.preventDefault();
        
        const tipoRecursoId = $('#tipoRecursoId').val();
        const formData = {
            nombre: $('#tipoRecursoNombre').val().trim(),
            descripcion: $('#tipoRecursoDescripcion').val().trim(),
            icono: $('#tipoRecursoIcono').val().trim(),
            categoria: $('#tipoRecursoCategoria').val().trim(),
        };
        
        // Validar nombre
        if (!formData.nombre) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El nombre es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        // Enviar datos
        let url, method, sendData;
        if (tipoRecursoId) {
            url = REPOSITORIO_URLS.tipoRecursoUpdate(tipoRecursoId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.tipoRecursoCreate;
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
                    $('#modalTipoRecurso').modal('hide');
                    tableTiposRecurso.ajax.reload(null, false);
                }
            }
        );
    });
    
    /**
     * Abre el modal para editar un tipo de recurso
     */
    $(document).on('click', '.btn-editar-tipo-recurso', function() {
        const tipoRecursoId = $(this).data('id');
        const url = REPOSITORIO_URLS.tipoRecursoDetail(tipoRecursoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const tipo = response.data;
                    $('#modalTipoRecursoLabel').text('Editar Tipo de Recurso');
                    $('#tipoRecursoId').val(tipo.id);
                    $('#tipoRecursoNombre').val(tipo.nombre);
                    $('#tipoRecursoDescripcion').val(tipo.descripcion || '');
                    $('#tipoRecursoIcono').val(tipo.icono || '');
                    $('#tipoRecursoCategoria').val(tipo.categoria || '');
                    $('#modalTipoRecurso').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina un tipo de recurso
     */
    $(document).on('click', '.btn-eliminar-tipo-recurso', function() {
        const tipoRecursoId = $(this).data('id');
        const tipoRecursoNombre = $(this).data('nombre');
        const url = REPOSITORIO_URLS.tipoRecursoDelete(tipoRecursoId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el tipo de recurso "${tipoRecursoNombre}"?`,
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
                                text: response.message || 'Tipo de recurso eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableTiposRecurso.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    // ========================================================================
    // GESTIÓN DE ESTADOS DE DOCUMENTO
    // ========================================================================
    
    /**
     * Abre el modal para crear un nuevo estado de documento
     */
    $('#btnCrearEstadoDocumento').on('click', function() {
        $('#modalEstadoDocumentoLabel').text('Nuevo Estado de Documento');
        $('#formEstadoDocumento')[0].reset();
        $('#estadoDocumentoId').val('');
        $('#estadoDocumentoOrden').val(0);
        $('#modalEstadoDocumento').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de estado de documento
     */
    $('#formEstadoDocumento').on('submit', function(e) {
        e.preventDefault();
        
        const estadoDocumentoId = $('#estadoDocumentoId').val();
        const formData = {
            nombre: $('#estadoDocumentoNombre').val().trim(),
            descripcion: $('#estadoDocumentoDescripcion').val().trim(),
            orden: parseInt($('#estadoDocumentoOrden').val()) || 0,
        };
        
        // Validar nombre
        if (!formData.nombre) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El nombre es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        // Enviar datos
        let url, method, sendData;
        if (estadoDocumentoId) {
            url = REPOSITORIO_URLS.estadoDocumentoUpdate(estadoDocumentoId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.estadoDocumentoCreate;
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
                    $('#modalEstadoDocumento').modal('hide');
                    tableEstadosDocumento.ajax.reload(null, false);
                }
            }
        );
    });
    
    /**
     * Abre el modal para editar un estado de documento
     */
    $(document).on('click', '.btn-editar-estado-documento', function() {
        const estadoDocumentoId = $(this).data('id');
        const url = REPOSITORIO_URLS.estadoDocumentoDetail(estadoDocumentoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const estado = response.data;
                    $('#modalEstadoDocumentoLabel').text('Editar Estado de Documento');
                    $('#estadoDocumentoId').val(estado.id);
                    $('#estadoDocumentoNombre').val(estado.nombre);
                    $('#estadoDocumentoDescripcion').val(estado.descripcion || '');
                    $('#estadoDocumentoOrden').val(estado.orden || 0);
                    $('#modalEstadoDocumento').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina un estado de documento
     */
    $(document).on('click', '.btn-eliminar-estado-documento', function() {
        const estadoDocumentoId = $(this).data('id');
        const estadoDocumentoNombre = $(this).data('nombre');
        const url = REPOSITORIO_URLS.estadoDocumentoDelete(estadoDocumentoId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el estado de documento "${estadoDocumentoNombre}"?`,
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
                                text: response.message || 'Estado de documento eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableEstadosDocumento.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    // ========================================================================
    // COMUNIDADES
    // ========================================================================
    
    let comunidadesData = [];
    let usuariosData = [];
    
    /**
     * Carga las comunidades para usar en selects
     */
    function loadComunidadesForSelect(excludeId = null, targetSelect = null) {
        ajaxRequest(
            REPOSITORIO_URLS.comunidadesForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    comunidadesData = response.data;
                    
                    // Cargar en comunidadPadre si existe
                    const selectPadre = $('#comunidadPadre');
                    if (selectPadre.length > 0) {
                        selectPadre.empty();
                        selectPadre.append('<option value="">Ninguna (Comunidad raíz)</option>');
                        comunidadesData.forEach(function(comunidad) {
                            if (excludeId && comunidad.id === excludeId) return;
                            selectPadre.append(
                                `<option value="${comunidad.id}">${escapeHtml(comunidad.nombre)}</option>`
                            );
                        });
                    }
                    
                    // Cargar en coleccionComunidad si existe
                    const selectComunidad = $('#coleccionComunidad');
                    if (selectComunidad.length > 0) {
                        selectComunidad.empty();
                        selectComunidad.append('<option value="">Seleccione una comunidad</option>');
                        comunidadesData.forEach(function(comunidad) {
                            selectComunidad.append(
                                `<option value="${comunidad.id}">${escapeHtml(comunidad.nombre)}</option>`
                            );
                        });
                    }
                }
            }
        );
    }
    
    /**
     * Carga los usuarios para usar en selects
     */
    function loadUsuariosForSelect() {
        ajaxRequest(
            REPOSITORIO_URLS.usuariosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    usuariosData = response.data;
                    const selects = $('#comunidadAdministrador, #coleccionAdministrador');
                    selects.empty();
                    selects.append('<option value="">Seleccione un usuario</option>');
                    
                    usuariosData.forEach(function(usuario) {
                        selects.append(
                            `<option value="${usuario.id}">${escapeHtml(usuario.nombre)} (${escapeHtml(usuario.username)})</option>`
                        );
                    });
                }
            }
        );
    }
    
    /**
     * Carga las colecciones de una comunidad para usar en selects
     */
    function loadColeccionesForSelect(comunidadId, excludeId = null) {
        if (!comunidadId) {
            $('#coleccionPadre').empty().append('<option value="">Ninguna (Colección raíz)</option>');
            return;
        }
        
        ajaxRequest(
            REPOSITORIO_URLS.coleccionesPorComunidad(comunidadId),
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const select = $('#coleccionPadre');
                    select.empty();
                    select.append('<option value="">Ninguna (Colección raíz)</option>');
                    
                    response.data.forEach(function(coleccion) {
                        if (excludeId && coleccion.id === excludeId) return;
                        select.append(
                            `<option value="${coleccion.id}">${escapeHtml(coleccion.nombre)}</option>`
                        );
                    });
                }
            }
        );
    }
    
    /**
     * Inicializa la tabla de Comunidades
     */
    function initTableComunidades() {
        tableComunidades = $('#tableComunidades').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.comunidadesList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar comunidades:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las comunidades',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'nombre' },
                { 
                    data: 'comunidad_padre_nombre',
                    render: function(data) {
                        return data ? escapeHtml(data) : '-';
                    }
                },
                { data: 'administrador_nombre' },
                { 
                    data: 'estado',
                    render: function(data) {
                        const badges = {
                            'activa': 'success',
                            'inactiva': 'warning',
                            'archivada': 'secondary'
                        };
                        const badge = badges[data] || 'secondary';
                        return `<span class="badge badge-${badge}">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'es_publica',
                    render: function(data) {
                        return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-danger">No</span>';
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
                                <button class="btn btn-warning btn-editar-comunidad" 
                                        data-id="${row.id}" 
                                        data-nombre="${escapeHtml(row.nombre || '')}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-comunidad" 
                                        data-id="${row.id}" 
                                        data-nombre="${escapeHtml(row.nombre || '')}"
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
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Abre el modal para crear una nueva comunidad
     */
    $(document).on('click', '#btnCrearComunidad', function() {
        if ($('#modalComunidad').length === 0) return;
        $('#modalComunidadLabel').text('Nueva Comunidad');
        $('#formComunidad')[0].reset();
        $('#comunidadId').val('');
        $('#comunidadEsPublica').prop('checked', true);
        $('#comunidadEstado').val('activa');
        loadComunidadesForSelect();
        loadUsuariosForSelect();
        $('#modalComunidad').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de comunidad
     */
    $('#formComunidad').on('submit', function(e) {
        e.preventDefault();
        
        const comunidadId = $('#comunidadId').val();
        const formData = {
            nombre: $('#comunidadNombre').val().trim(),
            descripcion: $('#comunidadDescripcion').val().trim(),
            comunidad_padre_id: $('#comunidadPadre').val() || null,
            administrador_id: $('#comunidadAdministrador').val(),
            logo: $('#comunidadLogo').val().trim() || null,
            banner: $('#comunidadBanner').val().trim() || null,
            estado: $('#comunidadEstado').val(),
            es_publica: $('#comunidadEsPublica').is(':checked'),
        };
        
        if (!formData.nombre || !formData.administrador_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El nombre y el administrador son obligatorios',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (comunidadId) {
            url = REPOSITORIO_URLS.comunidadUpdate(comunidadId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.comunidadCreate;
            method = 'POST';
            sendData = formData;
        }
        
        ajaxRequest(url, method, sendData, function(response) {
            if (response.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: response.message || 'Operación realizada correctamente',
                    timer: 2000,
                    showConfirmButton: false
                });
                $('#modalComunidad').modal('hide');
                tableComunidades.ajax.reload(null, false);
            }
        });
    });
    
    /**
     * Abre el modal para editar una comunidad
     */
    $(document).on('click', '.btn-editar-comunidad', function() {
        const comunidadId = $(this).data('id');
        const url = REPOSITORIO_URLS.comunidadDetail(comunidadId);
        
        ajaxRequest(url, 'GET', null, function(response) {
            if (response.success) {
                const comunidad = response.data;
                $('#modalComunidadLabel').text('Editar Comunidad');
                $('#comunidadId').val(comunidad.id);
                $('#comunidadNombre').val(comunidad.nombre);
                $('#comunidadDescripcion').val(comunidad.descripcion || '');
                $('#comunidadLogo').val(comunidad.logo || '');
                $('#comunidadBanner').val(comunidad.banner || '');
                $('#comunidadEstado').val(comunidad.estado);
                $('#comunidadEsPublica').prop('checked', comunidad.es_publica);
                
                loadComunidadesForSelect(comunidad.id);
                loadUsuariosForSelect();
                
                setTimeout(() => {
                    $('#comunidadPadre').val(comunidad.comunidad_padre_id || '');
                    $('#comunidadAdministrador').val(comunidad.administrador_id);
                }, 500);
                
                $('#modalComunidad').modal('show');
            }
        });
    });
    
    /**
     * Elimina una comunidad
     */
    $(document).on('click', '.btn-eliminar-comunidad', function() {
        const comunidadId = $(this).data('id');
        const comunidadNombre = $(this).data('nombre');
        const url = REPOSITORIO_URLS.comunidadDelete(comunidadId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la comunidad "${comunidadNombre}"?`,
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(url, 'POST', { _method: 'DELETE' }, function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Comunidad eliminada correctamente',
                            timer: 2000,
                            showConfirmButton: false
                        });
                        tableComunidades.ajax.reload(null, false);
                    }
                });
            }
        });
    });
    
    // ========================================================================
    // COLECCIONES
    // ========================================================================
    
    
    /**
     * Inicializa la tabla de Colecciones
     */
    function initTableColecciones() {
        tableColecciones = $('#tableColecciones').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.coleccionesList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar colecciones:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las colecciones',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'nombre' },
                { data: 'comunidad_nombre' },
                { 
                    data: 'coleccion_padre_nombre',
                    render: function(data) {
                        return data ? escapeHtml(data) : '-';
                    }
                },
                { data: 'administrador_nombre' },
                { 
                    data: 'politica_ingreso',
                    render: function(data) {
                        const badges = {
                            'abierto': 'success',
                            'cerrado': 'danger',
                            'revision': 'warning'
                        };
                        const badge = badges[data] || 'secondary';
                        return `<span class="badge badge-${badge}">${escapeHtml(data)}</span>`;
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
                                <button class="btn btn-warning btn-editar-coleccion" 
                                        data-id="${row.id}" 
                                        data-nombre="${escapeHtml(row.nombre || '')}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-coleccion" 
                                        data-id="${row.id}" 
                                        data-nombre="${escapeHtml(row.nombre || '')}"
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
            order: [[2, 'asc'], [1, 'asc']],
            dom: 'lBfrtip',
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Abre el modal para crear una nueva colección
     */
    $('#btnCrearColeccion').on('click', function() {
        $('#modalColeccionLabel').text('Nueva Colección');
        $('#formColeccion')[0].reset();
        $('#coleccionId').val('');
        $('#coleccionEsPublica').prop('checked', true);
        $('#coleccionPoliticaIngreso').val('abierto');
        loadComunidadesForSelect();
        loadUsuariosForSelect();
        $('#coleccionPadre').empty().append('<option value="">Ninguna (Colección raíz)</option>');
        $('#modalColeccion').modal('show');
    });
    
    /**
     * Cuando se cambia la comunidad, actualizar las colecciones padre disponibles
     */
    $('#coleccionComunidad').on('change', function() {
        const comunidadId = $(this).val();
        loadColeccionesForSelect(comunidadId);
    });
    
    /**
     * Maneja el envío del formulario de colección
     */
    $('#formColeccion').on('submit', function(e) {
        e.preventDefault();
        
        const coleccionId = $('#coleccionId').val();
        const formData = {
            nombre: $('#coleccionNombre').val().trim(),
            descripcion: $('#coleccionDescripcion').val().trim(),
            comunidad_id: $('#coleccionComunidad').val(),
            coleccion_padre_id: $('#coleccionPadre').val() || null,
            administrador_id: $('#coleccionAdministrador').val(),
            politica_ingreso: $('#coleccionPoliticaIngreso').val(),
            es_publica: $('#coleccionEsPublica').is(':checked'),
        };
        
        if (!formData.nombre || !formData.comunidad_id || !formData.administrador_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El nombre, la comunidad y el administrador son obligatorios',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (coleccionId) {
            url = REPOSITORIO_URLS.coleccionUpdate(coleccionId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.coleccionCreate;
            method = 'POST';
            sendData = formData;
        }
        
        ajaxRequest(url, method, sendData, function(response) {
            if (response.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: response.message || 'Operación realizada correctamente',
                    timer: 2000,
                    showConfirmButton: false
                });
                $('#modalColeccion').modal('hide');
                tableColecciones.ajax.reload(null, false);
            }
        });
    });
    
    /**
     * Abre el modal para editar una colección
     */
    $(document).on('click', '.btn-editar-coleccion', function() {
        const coleccionId = $(this).data('id');
        const url = REPOSITORIO_URLS.coleccionDetail(coleccionId);
        
        ajaxRequest(url, 'GET', null, function(response) {
            if (response.success) {
                const coleccion = response.data;
                $('#modalColeccionLabel').text('Editar Colección');
                $('#coleccionId').val(coleccion.id);
                $('#coleccionNombre').val(coleccion.nombre);
                $('#coleccionDescripcion').val(coleccion.descripcion || '');
                $('#coleccionPoliticaIngreso').val(coleccion.politica_ingreso);
                $('#coleccionEsPublica').prop('checked', coleccion.es_publica);
                
                loadComunidadesForSelect();
                loadUsuariosForSelect();
                
                setTimeout(() => {
                    $('#coleccionComunidad').val(coleccion.comunidad_id);
                    loadColeccionesForSelect(coleccion.comunidad_id, coleccion.id);
                    setTimeout(() => {
                        $('#coleccionPadre').val(coleccion.coleccion_padre_id || '');
                    }, 300);
                    $('#coleccionAdministrador').val(coleccion.administrador_id);
                }, 500);
                
                $('#modalColeccion').modal('show');
            }
        });
    });
    
    /**
     * Elimina una colección
     */
    $(document).on('click', '.btn-eliminar-coleccion', function() {
        const coleccionId = $(this).data('id');
        const coleccionNombre = $(this).data('nombre');
        const url = REPOSITORIO_URLS.coleccionDelete(coleccionId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la colección "${coleccionNombre}"?`,
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(url, 'POST', { _method: 'DELETE' }, function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Colección eliminada correctamente',
                            timer: 2000,
                            showConfirmButton: false
                        });
                        tableColecciones.ajax.reload(null, false);
                    }
                });
            }
        });
    });
    
    // ========================================================================
    // LICENCIAS
    // ========================================================================
    
    
    /**
     * Inicializa la tabla de Licencias
     */
    function initTableLicencias() {
        tableLicencias = $('#tableLicencias').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.licenciasList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar licencias:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las licencias',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'nombre' },
                { data: 'codigo' },
                { 
                    data: 'version',
                    render: function(data) {
                        return data ? escapeHtml(data) : '-';
                    }
                },
                { 
                    data: 'permite_comercial',
                    render: function(data) {
                        return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-danger">No</span>';
                    }
                },
                { 
                    data: 'permite_modificacion',
                    render: function(data) {
                        return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-danger">No</span>';
                    }
                },
                { 
                    data: 'requiere_attribucion',
                    render: function(data) {
                        return data ? '<span class="badge badge-warning">Sí</span>' : '<span class="badge badge-secondary">No</span>';
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
                                <button class="btn btn-warning btn-editar-licencia" 
                                        data-id="${row.id}" 
                                        data-nombre="${escapeHtml(row.nombre || '')}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-licencia" 
                                        data-id="${row.id}" 
                                        data-nombre="${escapeHtml(row.nombre || '')}"
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
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Abre el modal para crear una nueva licencia
     */
    $('#btnCrearLicencia').on('click', function() {
        $('#modalLicenciaLabel').text('Nueva Licencia');
        $('#formLicencia')[0].reset();
        $('#licenciaId').val('');
        $('#licenciaRequiereAttribucion').prop('checked', true);
        $('#modalLicencia').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de licencia
     */
    $('#formLicencia').on('submit', function(e) {
        e.preventDefault();
        
        const licenciaId = $('#licenciaId').val();
        const formData = {
            nombre: $('#licenciaNombre').val().trim(),
            codigo: $('#licenciaCodigo').val().trim(),
            version: $('#licenciaVersion').val().trim() || null,
            url: $('#licenciaUrl').val().trim() || null,
            descripcion: $('#licenciaDescripcion').val().trim() || null,
            permite_comercial: $('#licenciaPermiteComercial').is(':checked'),
            permite_modificacion: $('#licenciaPermiteModificacion').is(':checked'),
            requiere_attribucion: $('#licenciaRequiereAttribucion').is(':checked'),
            texto_completo: $('#licenciaTextoCompleto').val().trim() || null,
        };
        
        if (!formData.nombre || !formData.codigo) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El nombre y el código son obligatorios',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (licenciaId) {
            url = REPOSITORIO_URLS.licenciaUpdate(licenciaId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.licenciaCreate;
            method = 'POST';
            sendData = formData;
        }
        
        ajaxRequest(url, method, sendData, function(response) {
            if (response.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: response.message || 'Operación realizada correctamente',
                    timer: 2000,
                    showConfirmButton: false
                });
                $('#modalLicencia').modal('hide');
                tableLicencias.ajax.reload(null, false);
            }
        });
    });
    
    /**
     * Abre el modal para editar una licencia
     */
    $(document).on('click', '.btn-editar-licencia', function() {
        const licenciaId = $(this).data('id');
        const url = REPOSITORIO_URLS.licenciaDetail(licenciaId);
        
        ajaxRequest(url, 'GET', null, function(response) {
            if (response.success) {
                const licencia = response.data;
                $('#modalLicenciaLabel').text('Editar Licencia');
                $('#licenciaId').val(licencia.id);
                $('#licenciaNombre').val(licencia.nombre);
                $('#licenciaCodigo').val(licencia.codigo);
                $('#licenciaVersion').val(licencia.version || '');
                $('#licenciaUrl').val(licencia.url || '');
                $('#licenciaDescripcion').val(licencia.descripcion || '');
                $('#licenciaPermiteComercial').prop('checked', licencia.permite_comercial);
                $('#licenciaPermiteModificacion').prop('checked', licencia.permite_modificacion);
                $('#licenciaRequiereAttribucion').prop('checked', licencia.requiere_attribucion);
                $('#licenciaTextoCompleto').val(licencia.texto_completo || '');
                $('#modalLicencia').modal('show');
            }
        });
    });
    
    /**
     * Elimina una licencia
     */
    $(document).on('click', '.btn-eliminar-licencia', function() {
        const licenciaId = $(this).data('id');
        const licenciaNombre = $(this).data('nombre');
        const url = REPOSITORIO_URLS.licenciaDelete(licenciaId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la licencia "${licenciaNombre}"?`,
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(url, 'POST', { _method: 'DELETE' }, function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Licencia eliminada correctamente',
                            timer: 2000,
                            showConfirmButton: false
                        });
                        tableLicencias.ajax.reload(null, false);
                    }
                });
            }
        });
    });
    
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    // Inicializar solo las tablas que existen en la página actual
    // Esto permite que el mismo JS funcione en diferentes páginas HTML
    
    if ($('#tableTiposRecurso').length > 0) {
        initTableTiposRecurso();
    }
    if ($('#tableEstadosDocumento').length > 0) {
        initTableEstadosDocumento();
    }
    if ($('#tableComunidades').length > 0) {
        initTableComunidades();
    }
    if ($('#tableColecciones').length > 0) {
        initTableColecciones();
    }
    if ($('#tableLicencias').length > 0) {
        initTableLicencias();
    }
    if ($('#tableDocumentos').length > 0) {
        initTableDocumentos();
    }
    if ($('#tableAutores').length > 0) {
        initTableAutores();
    }
    if ($('#tableColaboradores').length > 0) {
        initTableColaboradores();
    }
    
    // Botones de acceso rápido
    $('#btnAccesoRapidoEstados').on('click', function() {
        $('#estados-documento-tab').tab('show');
    });
    
    // Recargar tablas cuando se cambia de tab (solo si la tabla existe)
    $('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
        const target = $(e.target).attr('href');
        if (target === '#tipos-recurso' && typeof tableTiposRecurso !== 'undefined' && tableTiposRecurso) {
            tableTiposRecurso.columns.adjust().responsive.recalc();
        } else if (target === '#estados-documento' && typeof tableEstadosDocumento !== 'undefined' && tableEstadosDocumento) {
            tableEstadosDocumento.columns.adjust().responsive.recalc();
        } else if (target === '#comunidades' && typeof tableComunidades !== 'undefined' && tableComunidades) {
            tableComunidades.columns.adjust().responsive.recalc();
        } else if (target === '#colecciones' && typeof tableColecciones !== 'undefined' && tableColecciones) {
            tableColecciones.columns.adjust().responsive.recalc();
        } else if (target === '#licencias' && typeof tableLicencias !== 'undefined' && tableLicencias) {
            tableLicencias.columns.adjust().responsive.recalc();
        } else if (target === '#documentos' && typeof tableDocumentos !== 'undefined' && tableDocumentos) {
            tableDocumentos.columns.adjust().responsive.recalc();
        } else if (target === '#autores' && typeof tableAutores !== 'undefined' && tableAutores) {
            tableAutores.columns.adjust().responsive.recalc();
        } else if (target === '#colaboradores' && typeof tableColaboradores !== 'undefined' && tableColaboradores) {
            tableColaboradores.columns.adjust().responsive.recalc();
        }
    });
    
    // ========================================================================
    // DOCUMENTOS
    // ========================================================================
    
    let categoriasData = [];
    let etiquetasData = [];
    let tiposRecursoData = [];
    let estadosDocumentoData = [];
    let licenciasData = [];
    let coleccionesData = [];
    
    /**
     * Carga los datos para los selects del formulario de documentos
     */
    function loadDocumentoSelects() {
        // Verificar si el modal de documento existe
        if ($('#modalDocumento').length === 0) return;
        
        // Cargar tipos de recurso
        if ($('#documentoTipoRecurso').length > 0) {
            ajaxRequest(
                REPOSITORIO_URLS.tiposRecursoForSelect,
                'GET',
                null,
                function(response) {
                    if (response.success) {
                        tiposRecursoData = response.data;
                        const select = $('#documentoTipoRecurso');
                        if (select.length > 0) {
                            select.empty();
                            select.append('<option value="">Seleccione un tipo</option>');
                            tiposRecursoData.forEach(function(tipo) {
                                select.append(`<option value="${tipo.id}">${escapeHtml(tipo.nombre)}</option>`);
                            });
                        }
                    }
                }
            );
        }
        
        // Cargar colecciones
        if ($('#documentoColeccion').length > 0) {
            ajaxRequest(
                REPOSITORIO_URLS.coleccionesList,
                'GET',
                null,
                function(response) {
                    if (response.success) {
                        coleccionesData = response.data;
                        const select = $('#documentoColeccion');
                        if (select.length > 0) {
                            select.empty();
                            select.append('<option value="">Seleccione una colección</option>');
                            coleccionesData.forEach(function(coleccion) {
                                select.append(`<option value="${coleccion.id}">${escapeHtml(coleccion.comunidad_nombre)} - ${escapeHtml(coleccion.nombre)}</option>`);
                            });
                        }
                    }
                }
            );
        }
        
        // Cargar estados de documento
        if ($('#documentoEstado').length > 0) {
            ajaxRequest(
                REPOSITORIO_URLS.estadosDocumentoForSelect,
                'GET',
                null,
                function(response) {
                    if (response.success) {
                        estadosDocumentoData = response.data;
                        const select = $('#documentoEstado');
                        if (select.length > 0) {
                            select.empty();
                            select.append('<option value="">Seleccione un estado</option>');
                            estadosDocumentoData.forEach(function(estado) {
                                select.append(`<option value="${estado.id}">${escapeHtml(estado.nombre)}</option>`);
                            });
                        }
                    }
                }
            );
        }
        
        // Cargar licencias
        if ($('#documentoLicencia').length > 0) {
            ajaxRequest(
                REPOSITORIO_URLS.licenciasForSelect,
                'GET',
                null,
                function(response) {
                    if (response.success) {
                        licenciasData = response.data;
                        const select = $('#documentoLicencia');
                        if (select.length > 0) {
                            select.empty();
                            select.append('<option value="">Ninguna</option>');
                            licenciasData.forEach(function(licencia) {
                                select.append(`<option value="${licencia.id}">${escapeHtml(licencia.nombre)} (${escapeHtml(licencia.codigo)})</option>`);
                            });
                        }
                    }
                }
            );
        }
        
        // Cargar categorías para Select2
        if ($('#documentoCategorias').length > 0) {
            ajaxRequest(
                REPOSITORIO_URLS.categoriasForSelect,
                'GET',
                null,
                function(response) {
                    if (response.success) {
                        categoriasData = response.data;
                        const select = $('#documentoCategorias');
                        if (select.length > 0) {
                            select.empty();
                            categoriasData.forEach(function(categoria) {
                                select.append(`<option value="${categoria.id}">${escapeHtml(categoria.ruta_completa)}</option>`);
                            });
                            if (typeof select.select2 === 'function') {
                                select.select2({
                                    theme: 'bootstrap4',
                                    placeholder: 'Seleccione categorías',
                                    allowClear: true
                                });
                            }
                        }
                    }
                }
            );
        }
        
        // Cargar etiquetas para Select2
        if ($('#documentoEtiquetas').length > 0) {
            ajaxRequest(
                REPOSITORIO_URLS.etiquetasForSelect,
                'GET',
                null,
                function(response) {
                    if (response.success) {
                        etiquetasData = response.data;
                        const select = $('#documentoEtiquetas');
                        if (select.length > 0) {
                            select.empty();
                            etiquetasData.forEach(function(etiqueta) {
                                select.append(`<option value="${etiqueta.id}">${escapeHtml(etiqueta.nombre)}</option>`);
                            });
                            if (typeof select.select2 === 'function') {
                                select.select2({
                                    theme: 'bootstrap4',
                                    placeholder: 'Seleccione etiquetas',
                                    allowClear: true
                                });
                            }
                        }
                    }
                }
            );
        }
    }
    
    /**
     * Inicializa la tabla de Documentos
     */
    function initTableDocumentos() {
        tableDocumentos = $('#tableDocumentos').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.documentosList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar documentos:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los documentos',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { 
                    data: 'titulo',
                    render: function(data, type, row) {
                        const tituloEscapado = escapeHtml(data || '');
                        return tituloEscapado.length > 50 ? tituloEscapado.substring(0, 50) + '...' : tituloEscapado;
                    }
                },
                { data: 'tipo_recurso_nombre' },
                { 
                    data: 'coleccion_nombre',
                    render: function(data, type, row) {
                        return `${escapeHtml(row.comunidad_nombre || '')} - ${escapeHtml(data || '')}`;
                    }
                },
                { data: 'creador_nombre' },
                { 
                    data: 'estado_nombre',
                    render: function(data) {
                        return `<span class="badge badge-info">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'visibilidad',
                    render: function(data) {
                        const badges = {
                            'publico': 'success',
                            'privado': 'danger',
                            'restringido': 'warning'
                        };
                        const badge = badges[data] || 'secondary';
                        return `<span class="badge badge-${badge}">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'fecha_creacion',
                    render: function(data) {
                        if (!data) return '-';
                        return escapeHtml(data);
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const escapeHtmlFn = window.escapeHtml || escapeHtml;
                        const tituloEscapado = escapeHtmlFn(row.titulo || '');
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-ver-documento" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
                                        title="Ver detalles">
                                    <i class="fas fa-eye"></i>
                                    <span class="d-none d-md-inline ml-1">Ver</span>
                                </button>
                                <button class="btn btn-warning btn-editar-documento" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-documento" 
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
            order: [[7, 'desc']], // Ordenar por fecha de creación descendente
            dom: 'lBfrtip',
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Abre el modal para crear un nuevo documento
     */
    $(document).on('click', '#btnCrearDocumento', function(e) {
        e.preventDefault();
        $('#modalDocumentoLabel').text('Nuevo Documento');
        $('#formDocumento')[0].reset();
        $('#documentoId').val('');
        $('#documentoVisibilidad').val('publico');
        $('#documentoIdioma').val('es');
        $('#documentoVersionActual').val(1);
        
        // Cargar todos los selects
        loadDocumentoSelects();
        
        // Reiniciar Select2
        $('#documentoCategorias').val(null).trigger('change');
        $('#documentoEtiquetas').val(null).trigger('change');
        
        // Resetear pestañas del modal
        $('#info-basica-tab').tab('show');
        
        $('#modalDocumento').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de documento
     */
    $('#formDocumento').on('submit', function(e) {
        e.preventDefault();
        
        const documentoId = $('#documentoId').val();
        
        // Obtener valores de Select2
        const categoriasIds = $('#documentoCategorias').val() || [];
        const etiquetasIds = $('#documentoEtiquetas').val() || [];
        
        const formData = {
            titulo: $('#documentoTitulo').val().trim(),
            resumen: $('#documentoResumen').val().trim() || null,
            tipo_recurso_id: $('#documentoTipoRecurso').val(),
            coleccion_id: $('#documentoColeccion').val(),
            estado_id: $('#documentoEstado').val(),
            idioma: $('#documentoIdioma').val().trim() || 'es',
            fecha_publicacion: $('#documentoFechaPublicacion').val() || null,
            fecha_aceptacion: $('#documentoFechaAceptacion').val() || null,
            fecha_publicacion_disponible: $('#documentoFechaPublicacionDisponible').val() || null,
            visibilidad: $('#documentoVisibilidad').val(),
            version_actual: parseInt($('#documentoVersionActual').val()) || 1,
            handle: $('#documentoHandle').val().trim() || null,
            numero_acceso: $('#documentoNumeroAcceso').val().trim() || null,
            doi: $('#documentoDOI').val().trim() || null,
            isbn: $('#documentoISBN').val().trim() || null,
            issn: $('#documentoISSN').val().trim() || null,
            licencia_id: $('#documentoLicencia').val() || null,
            palabras_clave: $('#documentoPalabrasClave').val().trim() || null,
            temas: $('#documentoTemas').val().trim() || null,
            campos_personalizados: $('#documentoCamposPersonalizados').val().trim() || null,
            metadata_completa: $('#documentoMetadataCompleta').val().trim() || null,
            categorias_ids: categoriasIds,
            etiquetas_ids: etiquetasIds,
        };
        
        // Validaciones básicas
        if (!formData.titulo || !formData.tipo_recurso_id || !formData.coleccion_id || !formData.estado_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Por favor complete todos los campos obligatorios',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (documentoId) {
            url = REPOSITORIO_URLS.documentoUpdate(documentoId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.documentoCreate;
            method = 'POST';
            sendData = formData;
        }
        
        ajaxRequest(url, method, sendData, function(response) {
            if (response.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: response.message || 'Operación realizada correctamente',
                    timer: 2000,
                    showConfirmButton: false
                });
                $('#modalDocumento').modal('hide');
                tableDocumentos.ajax.reload(null, false);
            }
        });
    });
    
    /**
     * Abre el modal para editar un documento
     */
    $(document).on('click', '.btn-editar-documento', function() {
        const documentoId = $(this).data('id');
        const url = REPOSITORIO_URLS.documentoDetail(documentoId);
        
        ajaxRequest(url, 'GET', null, function(response) {
            if (response.success) {
                const documento = response.data;
                $('#modalDocumentoLabel').text('Editar Documento');
                $('#documentoId').val(documento.id);
                $('#documentoTitulo').val(documento.titulo);
                $('#documentoResumen').val(documento.resumen || '');
                $('#documentoHandle').val(documento.handle || '');
                $('#documentoDOI').val(documento.doi || '');
                $('#documentoISBN').val(documento.isbn || '');
                $('#documentoISSN').val(documento.issn || '');
                $('#documentoNumeroAcceso').val(documento.numero_acceso || '');
                $('#documentoIdioma').val(documento.idioma || 'es');
                $('#documentoVisibilidad').val(documento.visibilidad || 'publico');
                $('#documentoVersionActual').val(documento.version_actual || 1);
                $('#documentoPalabrasClave').val(documento.palabras_clave || '');
                
                // Fechas
                if (documento.fecha_publicacion) {
                    $('#documentoFechaPublicacion').val(documento.fecha_publicacion);
                }
                if (documento.fecha_aceptacion) {
                    $('#documentoFechaAceptacion').val(documento.fecha_aceptacion);
                }
                if (documento.fecha_publicacion_disponible) {
                    // Convertir formato de fecha para datetime-local
                    const fecha = documento.fecha_publicacion_disponible.replace(' ', 'T');
                    $('#documentoFechaPublicacionDisponible').val(fecha.substring(0, 16));
                }
                
                // JSON fields
                if (documento.temas) {
                    $('#documentoTemas').val(JSON.stringify(documento.temas, null, 2));
                }
                if (documento.campos_personalizados) {
                    $('#documentoCamposPersonalizados').val(JSON.stringify(documento.campos_personalizados, null, 2));
                }
                if (documento.metadata_completa) {
                    $('#documentoMetadataCompleta').val(JSON.stringify(documento.metadata_completa, null, 2));
                }
                
                // Cargar selects
                loadDocumentoSelects();
                
                // Establecer valores después de cargar los selects
                setTimeout(() => {
                    $('#documentoTipoRecurso').val(documento.tipo_recurso_id);
                    $('#documentoColeccion').val(documento.coleccion_id);
                    $('#documentoEstado').val(documento.estado_id);
                    $('#documentoLicencia').val(documento.licencia_id || '');
                    
                    // Establecer categorías y etiquetas en Select2
                    if (documento.categorias && documento.categorias.length > 0) {
                        const categoriasIds = documento.categorias.map(c => c.id);
                        $('#documentoCategorias').val(categoriasIds).trigger('change');
                    }
                    
                    if (documento.etiquetas && documento.etiquetas.length > 0) {
                        const etiquetasIds = documento.etiquetas.map(e => e.id);
                        $('#documentoEtiquetas').val(etiquetasIds).trigger('change');
                    }
                }, 800);
                
                // Resetear pestañas del modal
                $('#info-basica-tab').tab('show');
                
                $('#modalDocumento').modal('show');
            }
        });
    });
    
    /**
     * Muestra los detalles de un documento
     */
    $(document).on('click', '.btn-ver-documento', function() {
        const documentoId = $(this).data('id');
        const documentoNombre = $(this).data('titulo');
        const url = REPOSITORIO_URLS.documentoDetail(documentoId);
        
        ajaxRequest(url, 'GET', null, function(response) {
            if (response.success) {
                const doc = response.data;
                
                // Formatear categorías y etiquetas
                let categoriasHtml = doc.categorias && doc.categorias.length > 0 
                    ? doc.categorias.map(c => `<span class="badge badge-primary">${escapeHtml(c.nombre)}</span>`).join(' ')
                    : '<span class="text-muted">Ninguna</span>';
                
                let etiquetasHtml = doc.etiquetas && doc.etiquetas.length > 0 
                    ? doc.etiquetas.map(e => `<span class="badge badge-info">${escapeHtml(e.nombre)}</span>`).join(' ')
                    : '<span class="text-muted">Ninguna</span>';
                
                // Formatear fechas
                const fechaPub = doc.fecha_publicacion || 'No especificada';
                const fechaAcep = doc.fecha_aceptacion || 'No especificada';
                const fechaCreacion = doc.fecha_creacion || 'No disponible';
                
                // Formatear visibilidad
                const visibilidadBadges = {
                    'publico': '<span class="badge badge-success">Público</span>',
                    'privado': '<span class="badge badge-danger">Privado</span>',
                    'restringido': '<span class="badge badge-warning">Restringido</span>'
                };
                const visibilidadHtml = visibilidadBadges[doc.visibilidad] || doc.visibilidad;
                
                Swal.fire({
                    title: escapeHtml(doc.titulo),
                    html: `
                        <div class="text-left">
                            <p><strong>Handle:</strong> ${escapeHtml(doc.handle || 'N/A')}</p>
                            <p><strong>Tipo de Recurso:</strong> ${escapeHtml(doc.tipo_recurso_nombre)}</p>
                            <p><strong>Colección:</strong> ${escapeHtml(doc.comunidad_nombre)} - ${escapeHtml(doc.coleccion_nombre)}</p>
                            <p><strong>Creador:</strong> ${escapeHtml(doc.creador_nombre)}</p>
                            <p><strong>Estado:</strong> <span class="badge badge-info">${escapeHtml(doc.estado_nombre)}</span></p>
                            <p><strong>Visibilidad:</strong> ${visibilidadHtml}</p>
                            <p><strong>Idioma:</strong> ${escapeHtml(doc.idioma || 'es')}</p>
                            <p><strong>Versión Actual:</strong> ${doc.version_actual || 1}</p>
                            <p><strong>Fecha de Publicación:</strong> ${escapeHtml(fechaPub)}</p>
                            <p><strong>Fecha de Aceptación:</strong> ${escapeHtml(fechaAcep)}</p>
                            <p><strong>Fecha de Creación:</strong> ${escapeHtml(fechaCreacion)}</p>
                            ${doc.doi ? `<p><strong>DOI:</strong> ${escapeHtml(doc.doi)}</p>` : ''}
                            ${doc.isbn ? `<p><strong>ISBN:</strong> ${escapeHtml(doc.isbn)}</p>` : ''}
                            ${doc.issn ? `<p><strong>ISSN:</strong> ${escapeHtml(doc.issn)}</p>` : ''}
                            ${doc.licencia_nombre ? `<p><strong>Licencia:</strong> ${escapeHtml(doc.licencia_nombre)}</p>` : ''}
                            ${doc.palabras_clave ? `<p><strong>Palabras Clave:</strong> ${escapeHtml(doc.palabras_clave)}</p>` : ''}
                            <p><strong>Resumen:</strong> ${escapeHtml(doc.resumen || 'No especificado')}</p>
                            <p><strong>Categorías:</strong><br>${categoriasHtml}</p>
                            <p><strong>Etiquetas:</strong><br>${etiquetasHtml}</p>
                        </div>
                    `,
                    width: '700px',
                    confirmButtonText: 'Cerrar',
                    customClass: {
                        htmlContainer: 'text-left'
                    }
                });
            }
        });
    });
    
    /**
     * Elimina un documento
     */
    $(document).on('click', '.btn-eliminar-documento', function() {
        const documentoId = $(this).data('id');
        const documentoNombre = $(this).data('titulo');
        const url = REPOSITORIO_URLS.documentoDelete(documentoId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el documento "${documentoNombre}"?`,
            html: `<p>Esta acción eliminará también todas las versiones y archivos asociados.</p>`,
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(url, 'POST', { _method: 'DELETE' }, function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Documento eliminado correctamente',
                            timer: 2000,
                            showConfirmButton: false
                        });
                        tableDocumentos.ajax.reload(null, false);
                    }
                });
            }
        });
    });
    
    // ========================================================================
    // AUTORES
    // ========================================================================
    
    let documentosData = [];
    
    /**
     * Carga los documentos para usar en selects
     */
    function loadDocumentosForSelect() {
        ajaxRequest(
            REPOSITORIO_URLS.documentosList,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    documentosData = response.data;
                    const selects = $('#autorDocumento, #colaboradorDocumento');
                    selects.empty();
                    selects.append('<option value="">Seleccione un documento</option>');
                    documentosData.forEach(function(documento) {
                        selects.append(
                            `<option value="${documento.id}">${escapeHtml(documento.titulo)}</option>`
                        );
                    });
                }
            }
        );
    }
    
    /**
     * Inicializa la tabla de Autores
     */
    function initTableAutores() {
        tableAutores = $('#tableAutores').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.autoresList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar autores:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los autores',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { 
                    data: null,
                    render: function(data, type, row) {
                        return `${escapeHtml(row.nombre)} ${escapeHtml(row.apellidos)}`;
                    }
                },
                { 
                    data: 'documento_titulo',
                    render: function(data) {
                        const tituloEscapado = escapeHtml(data || '');
                        return tituloEscapado.length > 40 ? tituloEscapado.substring(0, 40) + '...' : tituloEscapado;
                    }
                },
                { 
                    data: 'usuario_nombre',
                    render: function(data) {
                        return data ? escapeHtml(data) : '<span class="text-muted">-</span>';
                    }
                },
                { 
                    data: 'email',
                    render: function(data) {
                        return data ? escapeHtml(data) : '<span class="text-muted">-</span>';
                    }
                },
                { data: 'orden_autor' },
                { 
                    data: 'es_autor_principal',
                    render: function(data) {
                        return data ? '<span class="badge badge-success">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                { 
                    data: 'es_correspondiente',
                    render: function(data) {
                        return data ? '<span class="badge badge-info">Sí</span>' : '<span class="badge badge-secondary">No</span>';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const escapeHtmlFn = window.escapeHtml || escapeHtml;
                        const nombreCompleto = escapeHtmlFn(`${row.nombre} ${row.apellidos}`);
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-warning btn-editar-autor" 
                                        data-id="${row.id}" 
                                        data-nombre="${nombreCompleto}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-autor" 
                                        data-id="${row.id}" 
                                        data-nombre="${nombreCompleto}"
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
            order: [[5, 'asc'], [1, 'asc']], // Ordenar por orden_autor y nombre
            dom: 'lBfrtip',
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Abre el modal para crear un nuevo autor
     */
    $(document).on('click', '#btnCrearAutor', function(e) {
        e.preventDefault();
        $('#modalAutorLabel').text('Nuevo Autor');
        $('#formAutor')[0].reset();
        $('#autorId').val('');
        $('#autorOrden').val(1);
        loadDocumentosForSelect();
        loadUsuariosForSelect();
        $('#modalAutor').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de autor
     */
    $('#formAutor').on('submit', function(e) {
        e.preventDefault();
        
        const autorId = $('#autorId').val();
        const formData = {
            documento_id: $('#autorDocumento').val(),
            usuario_id: $('#autorUsuario').val() || null,
            nombre: $('#autorNombre').val().trim(),
            apellidos: $('#autorApellidos').val().trim(),
            email: $('#autorEmail').val().trim() || null,
            afiliacion: $('#autorAfiliacion').val().trim() || null,
            orcid_id: $('#autorORCID').val().trim() || null,
            orden_autor: parseInt($('#autorOrden').val()) || 1,
            es_autor_principal: $('#autorPrincipal').is(':checked'),
            es_correspondiente: $('#autorCorrespondiente').is(':checked'),
        };
        
        // Validaciones básicas
        if (!formData.documento_id || !formData.nombre || !formData.apellidos) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Por favor complete todos los campos obligatorios',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (autorId) {
            url = REPOSITORIO_URLS.autorUpdate(autorId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.autorCreate;
            method = 'POST';
            sendData = formData;
        }
        
        ajaxRequest(url, method, sendData, function(response) {
            if (response.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: response.message || 'Operación realizada correctamente',
                    timer: 2000,
                    showConfirmButton: false
                });
                $('#modalAutor').modal('hide');
                tableAutores.ajax.reload(null, false);
            }
        });
    });
    
    /**
     * Abre el modal para editar un autor
     */
    $(document).on('click', '.btn-editar-autor', function() {
        const autorId = $(this).data('id');
        const url = REPOSITORIO_URLS.autorDetail(autorId);
        
        ajaxRequest(url, 'GET', null, function(response) {
            if (response.success) {
                const autor = response.data;
                $('#modalAutorLabel').text('Editar Autor');
                $('#autorId').val(autor.id);
                $('#autorNombre').val(autor.nombre);
                $('#autorApellidos').val(autor.apellidos);
                $('#autorEmail').val(autor.email || '');
                $('#autorAfiliacion').val(autor.afiliacion || '');
                $('#autorORCID').val(autor.orcid_id || '');
                $('#autorOrden').val(autor.orden_autor || 1);
                $('#autorPrincipal').prop('checked', autor.es_autor_principal);
                $('#autorCorrespondiente').prop('checked', autor.es_correspondiente);
                
                loadDocumentosForSelect();
                loadUsuariosForSelect();
                
                setTimeout(() => {
                    $('#autorDocumento').val(autor.documento_id);
                    $('#autorUsuario').val(autor.usuario_id || '');
                }, 500);
                
                $('#modalAutor').modal('show');
            }
        });
    });
    
    /**
     * Elimina un autor
     */
    $(document).on('click', '.btn-eliminar-autor', function() {
        const autorId = $(this).data('id');
        const autorNombre = $(this).data('nombre');
        const url = REPOSITORIO_URLS.autorDelete(autorId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el autor "${autorNombre}"?`,
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(url, 'POST', { _method: 'DELETE' }, function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Autor eliminado correctamente',
                            timer: 2000,
                            showConfirmButton: false
                        });
                        tableAutores.ajax.reload(null, false);
                    }
                });
            }
        });
    });
    
    // ========================================================================
    // COLABORADORES
    // ========================================================================
    
    
    /**
     * Inicializa la tabla de Colaboradores
     */
    function initTableColaboradores() {
        tableColaboradores = $('#tableColaboradores').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            ajax: {
                url: REPOSITORIO_URLS.colaboradoresList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar colaboradores:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los colaboradores',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'usuario_nombre' },
                { 
                    data: 'documento_titulo',
                    render: function(data) {
                        const tituloEscapado = escapeHtml(data || '');
                        return tituloEscapado.length > 40 ? tituloEscapado.substring(0, 40) + '...' : tituloEscapado;
                    }
                },
                { 
                    data: 'rol',
                    render: function(data) {
                        const badges = {
                            'editor': 'primary',
                            'revisor': 'info',
                            'colaborador': 'secondary',
                            'supervisor': 'warning',
                            'patrocinador': 'success'
                        };
                        const badge = badges[data] || 'secondary';
                        const labels = {
                            'editor': 'Editor',
                            'revisor': 'Revisor',
                            'colaborador': 'Colaborador',
                            'supervisor': 'Supervisor',
                            'patrocinador': 'Patrocinador'
                        };
                        return `<span class="badge badge-${badge}">${escapeHtml(labels[data] || data)}</span>`;
                    }
                },
                { 
                    data: 'fecha_asignacion',
                    render: function(data) {
                        return data ? escapeHtml(data) : '-';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    width: '18%',
                    render: function(data, type, row) {
                        const escapeHtmlFn = window.escapeHtml || escapeHtml;
                        const usuarioNombre = escapeHtmlFn(row.usuario_nombre || '');
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-warning btn-editar-colaborador" 
                                        data-id="${row.id}" 
                                        data-nombre="${usuarioNombre}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-colaborador" 
                                        data-id="${row.id}" 
                                        data-nombre="${usuarioNombre}"
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
            order: [[2, 'asc'], [1, 'asc']], // Ordenar por documento y usuario
            dom: 'lBfrtip',
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Abre el modal para crear un nuevo colaborador
     */
    $(document).on('click', '#btnCrearColaborador', function(e) {
        e.preventDefault();
        $('#modalColaboradorLabel').text('Nuevo Colaborador');
        $('#formColaborador')[0].reset();
        $('#colaboradorId').val('');
        loadDocumentosForSelect();
        loadUsuariosForSelect();
        $('#modalColaborador').modal('show');
    });
    
    /**
     * Maneja el envío del formulario de colaborador
     */
    $('#formColaborador').on('submit', function(e) {
        e.preventDefault();
        
        const colaboradorId = $('#colaboradorId').val();
        
        const formData = {
            documento_id: $('#colaboradorDocumento').val(),
            usuario_id: $('#colaboradorUsuario').val(),
            rol: $('#colaboradorRol').val(),
            permisos: $('#colaboradorPermisos').val().trim() || null,
        };
        
        // Validaciones básicas
        if (!formData.documento_id || !formData.usuario_id || !formData.rol) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Por favor complete todos los campos obligatorios',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (colaboradorId) {
            url = REPOSITORIO_URLS.colaboradorUpdate(colaboradorId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = REPOSITORIO_URLS.colaboradorCreate;
            method = 'POST';
            sendData = formData;
        }
        
        ajaxRequest(url, method, sendData, function(response) {
            if (response.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Éxito',
                    text: response.message || 'Operación realizada correctamente',
                    timer: 2000,
                    showConfirmButton: false
                });
                $('#modalColaborador').modal('hide');
                tableColaboradores.ajax.reload(null, false);
            }
        });
    });
    
    /**
     * Abre el modal para editar un colaborador
     */
    $(document).on('click', '.btn-editar-colaborador', function() {
        const colaboradorId = $(this).data('id');
        const url = REPOSITORIO_URLS.colaboradorDetail(colaboradorId);
        
        ajaxRequest(url, 'GET', null, function(response) {
            if (response.success) {
                const colaborador = response.data;
                $('#modalColaboradorLabel').text('Editar Colaborador');
                $('#colaboradorId').val(colaborador.id);
                $('#colaboradorRol').val(colaborador.rol);
                
                if (colaborador.permisos) {
                    $('#colaboradorPermisos').val(JSON.stringify(colaborador.permisos, null, 2));
                } else {
                    $('#colaboradorPermisos').val('');
                }
                
                loadDocumentosForSelect();
                loadUsuariosForSelect();
                
                setTimeout(() => {
                    $('#colaboradorDocumento').val(colaborador.documento_id);
                    $('#colaboradorUsuario').val(colaborador.usuario_id);
                }, 500);
                
                $('#modalColaborador').modal('show');
            }
        });
    });
    
    /**
     * Elimina un colaborador
     */
    $(document).on('click', '.btn-eliminar-colaborador', function() {
        const colaboradorId = $(this).data('id');
        const colaboradorNombre = $(this).data('nombre');
        const url = REPOSITORIO_URLS.colaboradorDelete(colaboradorId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el colaborador "${colaboradorNombre}"?`,
            showCancelButton: true,
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(url, 'POST', { _method: 'DELETE' }, function(response) {
                    if (response.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Éxito',
                            text: response.message || 'Colaborador eliminado correctamente',
                            timer: 2000,
                            showConfirmButton: false
                        });
                        tableColaboradores.ajax.reload(null, false);
                    }
                });
            }
        });
    });
    
    // ========================================================================
    // FIN DE INICIALIZACIÓN
    // ========================================================================
}); // Fin de $(document).ready
