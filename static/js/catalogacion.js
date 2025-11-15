/**
 * Script de gestión para Catalogación (Categorías y Etiquetas)
 * Usa jQuery, DataTables, SweetAlert2 y URL Reverse
 */

$(document).ready(function() {
    // Variables globales
    let tableCategorias, tableEtiquetas;
    let categoriasData = [];
    
    // ========================================================================
    // FUNCIONES AUXILIARES
    // ========================================================================
    
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
     * Carga las categorías y las actualiza en el select
     */
    function loadCategoriasForSelect() {
        ajaxRequest(
            CATALOGACION_URLS.categoriasList,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    categoriasData = response.data;
                    const select = $('#categoriaPadre');
                    select.empty();
                    select.append('<option value="">Ninguna (Categoría raíz)</option>');
                    
                    categoriasData.forEach(function(categoria) {
                        const indent = '&nbsp;'.repeat(categoria.nivel * 4);
                        select.append(
                            `<option value="${categoria.id}">${indent}${categoria.nombre}</option>`
                        );
                    });
                }
            }
        );
    }
    
    // ========================================================================
    // INICIALIZACIÓN DE DATATABLES
    // ========================================================================
    
    /**
     * Inicializa la tabla de Categorías
     */
    function initTableCategorias() {
        tableCategorias = $('#tableCategorias').DataTable({
            responsive: {
                details: {
                    type: 'column',
                    target: 'tr'
                }
            },
            processing: true,
            serverSide: false,
            ajax: {
                url: CATALOGACION_URLS.categoriasList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar categorías:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las categorías',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { 
                    data: 'nombre',
                    render: function(data, type, row) {
                        const indent = '&nbsp;'.repeat(row.nivel * 4);
                        return `${indent}${data}`;
                    }
                },
                { 
                    data: 'descripcion',
                    render: function(data) {
                        return data || '-';
                    }
                },
                { 
                    data: 'categoria_padre_nombre',
                    render: function(data) {
                        return data || '-';
                    }
                },
                { 
                    data: 'nivel',
                    render: function(data) {
                        return `<span class="badge badge-info badge-nivel">Nivel ${data}</span>`;
                    }
                },
                { 
                    data: 'subcategorias_count',
                    render: function(data) {
                        return `<span class="badge badge-secondary">${data}</span>`;
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-categoria" 
                                        data-id="${row.id}" 
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-categoria" 
                                        data-id="${row.id}" 
                                        data-nombre="${row.nombre}"
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
            order: [[4, 'asc'], [1, 'asc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Inicializa la tabla de Etiquetas
     */
    function initTableEtiquetas() {
        tableEtiquetas = $('#tableEtiquetas').DataTable({
            responsive: {
                details: {
                    type: 'column',
                    target: 'tr'
                }
            },
            processing: true,
            serverSide: false,
            ajax: {
                url: CATALOGACION_URLS.etiquetasList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar etiquetas:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar las etiquetas',
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
                        return data || '-';
                    }
                },
                { 
                    data: 'color',
                    render: function(data) {
                        if (data) {
                            return `<span class="color-preview" style="background-color: ${data};"></span> ${data}`;
                        }
                        return '-';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-etiqueta" 
                                        data-id="${row.id}" 
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-etiqueta" 
                                        data-id="${row.id}" 
                                        data-nombre="${row.nombre}"
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
    // GESTIÓN DE CATEGORÍAS
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva categoría
     */
    $('#btnCrearCategoria').on('click', function() {
        $('#modalCategoriaLabel').text('Nueva Categoría');
        $('#formCategoria')[0].reset();
        $('#categoriaId').val('');
        loadCategoriasForSelect();
        $('#modalCategoria').modal('show');
    });
    
    /**
     * Abre el modal para editar una categoría
     */
    $(document).on('click', '.btn-editar-categoria', function() {
        const categoriaId = $(this).data('id');
        const url = CATALOGACION_URLS.categoriaDetail(categoriaId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const categoria = response.data;
                    $('#modalCategoriaLabel').text('Editar Categoría');
                    $('#categoriaId').val(categoria.id);
                    $('#categoriaNombre').val(categoria.nombre);
                    $('#categoriaDescripcion').val(categoria.descripcion || '');
                    
                    // Cargar categorías y seleccionar la padre
                    loadCategoriasForSelect();
                    setTimeout(function() {
                        $('#categoriaPadre').val(categoria.categoria_padre_id || '');
                    }, 500);
                    
                    $('#modalCategoria').modal('show');
                }
            }
        );
    });
    
    /**
     * Maneja el envío del formulario de categoría
     */
    $('#formCategoria').on('submit', function(e) {
        e.preventDefault();
        
        const categoriaId = $('#categoriaId').val();
        const formData = {
            nombre: $('#categoriaNombre').val().trim(),
            descripcion: $('#categoriaDescripcion').val().trim(),
            categoria_padre_id: $('#categoriaPadre').val() || null
        };
        
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
        if (categoriaId) {
            url = CATALOGACION_URLS.categoriaUpdate(categoriaId);
            method = 'POST';  // Usar POST con _method para compatibilidad
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = CATALOGACION_URLS.categoriaCreate;
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
                    $('#modalCategoria').modal('hide');
                    tableCategorias.ajax.reload(null, false);
                }
            }
        );
    });
    
    /**
     * Maneja la eliminación de una categoría
     */
    $(document).on('click', '.btn-eliminar-categoria', function() {
        const categoriaId = $(this).data('id');
        const categoriaNombre = $(this).data('nombre');
        const url = CATALOGACION_URLS.categoriaDelete(categoriaId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la categoría "${categoriaNombre}"?`,
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
                                text: response.message || 'Categoría eliminada correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableCategorias.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    // ========================================================================
    // GESTIÓN DE ETIQUETAS
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva etiqueta
     */
    $('#btnCrearEtiqueta').on('click', function() {
        $('#modalEtiquetaLabel').text('Nueva Etiqueta');
        $('#formEtiqueta')[0].reset();
        $('#etiquetaId').val('');
        $('#colorPreview').css('background-color', '#FF5733');
        $('#modalEtiqueta').modal('show');
    });
    
    /**
     * Abre el modal para editar una etiqueta
     */
    $(document).on('click', '.btn-editar-etiqueta', function() {
        const etiquetaId = $(this).data('id');
        const url = CATALOGACION_URLS.etiquetaDetail(etiquetaId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const etiqueta = response.data;
                    $('#modalEtiquetaLabel').text('Editar Etiqueta');
                    $('#etiquetaId').val(etiqueta.id);
                    $('#etiquetaNombre').val(etiqueta.nombre);
                    $('#etiquetaDescripcion').val(etiqueta.descripcion || '');
                    $('#etiquetaColor').val(etiqueta.color || '');
                    $('#colorPreview').css('background-color', etiqueta.color || '#FF5733');
                    $('#modalEtiqueta').modal('show');
                }
            }
        );
    });
    
    /**
     * Actualiza el preview del color en tiempo real
     */
    $('#etiquetaColor').on('input', function() {
        let color = $(this).val().trim();
        if (color && !color.startsWith('#')) {
            color = '#' + color;
        }
        $('#colorPreview').css('background-color', color || '#FF5733');
    });
    
    /**
     * Maneja el envío del formulario de etiqueta
     */
    $('#formEtiqueta').on('submit', function(e) {
        e.preventDefault();
        
        const etiquetaId = $('#etiquetaId').val();
        const formData = {
            nombre: $('#etiquetaNombre').val().trim(),
            descripcion: $('#etiquetaDescripcion').val().trim(),
            color: $('#etiquetaColor').val().trim()
        };
        
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
        if (etiquetaId) {
            url = CATALOGACION_URLS.etiquetaUpdate(etiquetaId);
            method = 'POST';  // Usar POST con _method para compatibilidad
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = CATALOGACION_URLS.etiquetaCreate;
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
                    $('#modalEtiqueta').modal('hide');
                    tableEtiquetas.ajax.reload(null, false);
                }
            }
        );
    });
    
    /**
     * Maneja la eliminación de una etiqueta
     */
    $(document).on('click', '.btn-eliminar-etiqueta', function() {
        const etiquetaId = $(this).data('id');
        const etiquetaNombre = $(this).data('nombre');
        const url = CATALOGACION_URLS.etiquetaDelete(etiquetaId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar la etiqueta "${etiquetaNombre}"?`,
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
                                text: response.message || 'Etiqueta eliminada correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableEtiquetas.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    // Inicializar tablas cuando se carga la página
    initTableCategorias();
    initTableEtiquetas();
    
    // Cargar categorías para el select cuando se muestra el modal
    $('#modalCategoria').on('show.bs.modal', function() {
        loadCategoriasForSelect();
    });
    
    // Recargar tablas cuando se cambia de tab
    $('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
        const target = $(e.target).attr('href');
        if (target === '#categorias') {
            tableCategorias.columns.adjust().responsive.recalc();
        } else if (target === '#etiquetas') {
            tableEtiquetas.columns.adjust().responsive.recalc();
        }
    });
});
