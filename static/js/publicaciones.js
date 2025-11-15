/**
 * Script de gestión para Publicaciones
 * Usa jQuery, DataTables, SweetAlert2, Select2 y URL Reverse
 */

jQuery(document).ready(function($) {
    // Variables globales
    let tablePublicaciones;
    
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
    
    // ========================================================================
    // TABLA DATATABLES
    // ========================================================================
    
    /**
     * Inicializa la tabla de Publicaciones
     */
    function initTablePublicaciones() {
        const $table = $('#tablePublicaciones');
        if ($table.length === 0) {
            console.warn('La tabla #tablePublicaciones no existe en el DOM');
            return;
        }
        
        if ($table.find('thead tr').length === 0) {
            console.error('La tabla #tablePublicaciones no tiene la estructura correcta (falta thead)');
            return;
        }
        
        // Destruir la tabla si ya existe
        if ($.fn.DataTable.isDataTable('#tablePublicaciones')) {
            $('#tablePublicaciones').DataTable().destroy();
        }
        
        tablePublicaciones = $('#tablePublicaciones').DataTable({
            responsive: true,
            processing: true,
            serverSide: false,
            autoWidth: false,
            deferRender: true,
            ajax: {
                url: PUBLICACIONES_URLS.publicacionesList,
                type: 'GET',
                dataSrc: function(json) {
                    if (json && json.success && json.data) {
                        return json.data;
                    } else {
                        console.error('Respuesta inválida del servidor:', json);
                        return [];
                    }
                },
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar publicaciones:', error, thrown);
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'No se pudieron cargar las publicaciones',
                            confirmButtonText: 'Aceptar'
                        });
                    }
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'titulo' },
                { 
                    data: 'tipo_publicacion_display',
                    render: function(data) {
                        const badgeClass = {
                            'Revista': 'badge-primary',
                            'Libro': 'badge-info',
                            'Congreso': 'badge-success',
                            'Repositorio': 'badge-secondary',
                            'Otro': 'badge-warning'
                        };
                        const className = badgeClass[data] || 'badge-secondary';
                        return `<span class="badge ${className}">${escapeHtml(data)}</span>`;
                    }
                },
                { data: 'editor_nombre' },
                { 
                    data: 'estado_display',
                    render: function(data) {
                        const badgeClass = {
                            'Borrador': 'badge-secondary',
                            'En Proceso': 'badge-warning',
                            'Publicada': 'badge-success',
                            'Archivada': 'badge-dark'
                        };
                        const className = badgeClass[data] || 'badge-secondary';
                        return `<span class="badge ${className} badge-estado">${escapeHtml(data)}</span>`;
                    }
                },
                { 
                    data: 'proyectos_count',
                    render: function(data) {
                        return `<span class="badge badge-info">${data || 0}</span>`;
                    }
                },
                { 
                    data: 'fecha_creacion',
                    render: function(data) {
                        if (data) {
                            const date = new Date(data);
                            return date.toLocaleDateString('es-ES');
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
                        const tituloEscapado = escapeHtml(row.titulo || '');
                        // Construir la URL para la página de detalle pública
                        const publicDetailUrl = `${window.location.origin}/publicacion/${row.slug}/`;
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <a class="btn btn-outline-primary"
                                   href="${publicDetailUrl}"
                                   target="_blank"
                                   rel="noopener noreferrer"
                                   title="Ver en catálogo público">
                                    <i class="fas fa-globe"></i>
                                    <span class="d-none d-md-inline ml-1">Público</span>
                                </a>
                                <button class="btn btn-info btn-ver-publicacion" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
                                        title="Ver Detalles">
                                    <i class="fas fa-eye"></i>
                                    <span class="d-none d-md-inline ml-1">Ver</span>
                                </button>
                                <button class="btn btn-warning btn-editar-publicacion" 
                                        data-id="${row.id}" 
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-publicacion" 
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
            order: [[6, 'desc']], // Ordenar por fecha de creación descendente
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    // ========================================================================
    // FUNCIONES PARA CARGAR SELECTS
    // ========================================================================
    
    /**
     * Carga los usuarios para el select de editores
     */
    function loadUsuariosForSelect() {
        const $select = $('#publicacionEditor');
        if ($select.length === 0) return;
        
        ajaxRequest(
            PUBLICACIONES_URLS.usuariosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success && response.data) {
                    $select.empty().append('<option value="">Seleccione un editor</option>');
                    response.data.forEach(function(usuario) {
                        $select.append(`<option value="${usuario.id}">${escapeHtml(usuario.nombre)}</option>`);
                    });
                }
            }
        );
    }
    
    /**
     * Carga los proyectos para el select2
     */
    function loadProyectosForSelect() {
        const $select = $('#publicacionProyectos');
        if ($select.length === 0) return;
        
        ajaxRequest(
            PUBLICACIONES_URLS.proyectosForSelect,
            'GET',
            null,
            function(response) {
                if (response.success && response.data) {
                    $select.empty();
                    response.data.forEach(function(proyecto) {
                        const option = new Option(proyecto.titulo, proyecto.id, false, false);
                        $select.append(option);
                    });
                    
                    // Inicializar Select2 si no está inicializado
                    if ($select.hasClass('select2-hidden-accessible')) {
                        $select.select2('destroy');
                    }
                    $select.select2({
                        theme: 'bootstrap4',
                        placeholder: 'Seleccione uno o más proyectos',
                        allowClear: true
                    });
                }
            }
        );
    }
    
    /**
     * Carga las categorías para el select2
     */
    function loadCategoriasForSelect() {
        const $select = $('#publicacionCategorias');
        if ($select.length === 0) return;
        
        ajaxRequest(
            PUBLICACIONES_URLS.categoriasForSelect,
            'GET',
            null,
            function(response) {
                if (response.success && response.data) {
                    $select.empty();
                    response.data.forEach(function(categoria) {
                        const option = new Option(categoria.ruta_completa, categoria.id, false, false);
                        $select.append(option);
                    });
                    
                    // Inicializar Select2 si no está inicializado
                    if ($select.hasClass('select2-hidden-accessible')) {
                        $select.select2('destroy');
                    }
                    $select.select2({
                        theme: 'bootstrap4',
                        placeholder: 'Seleccione una o más categorías',
                        allowClear: true
                    });
                }
            }
        );
    }
    
    /**
     * Carga las etiquetas para el select2
     */
    function loadEtiquetasForSelect() {
        const $select = $('#publicacionEtiquetas');
        if ($select.length === 0) return;
        
        ajaxRequest(
            PUBLICACIONES_URLS.etiquetasForSelect,
            'GET',
            null,
            function(response) {
                if (response.success && response.data) {
                    $select.empty();
                    response.data.forEach(function(etiqueta) {
                        const option = new Option(etiqueta.nombre, etiqueta.id, false, false);
                        $select.append(option);
                    });
                    
                    // Inicializar Select2 si no está inicializado
                    if ($select.hasClass('select2-hidden-accessible')) {
                        $select.select2('destroy');
                    }
                    $select.select2({
                        theme: 'bootstrap4',
                        placeholder: 'Seleccione una o más etiquetas',
                        allowClear: true
                    });
                }
            }
        );
    }
    
    /**
     * Carga todos los selects necesarios para el modal
     */
    function loadPublicacionSelects() {
        loadUsuariosForSelect();
        loadProyectosForSelect();
        loadCategoriasForSelect();
        loadEtiquetasForSelect();
    }
    
    // ========================================================================
    // MANEJO DEL MODAL
    // ========================================================================
    
    /**
     * Abre el modal para crear una nueva publicación
     */
    function openCreateModal() {
        const $modal = $('#modalPublicacion');
        if ($modal.length === 0) return;
        
        // Resetear el formulario
        $('#formPublicacion')[0].reset();
        $('#publicacionId').val('');
        $('#modalPublicacionLabel').text('Nueva Publicación');
        
        // Cargar selects
        loadPublicacionSelects();
        
        // Resetear Select2
        $('#publicacionProyectos').val(null).trigger('change');
        $('#publicacionCategorias').val(null).trigger('change');
        $('#publicacionEtiquetas').val(null).trigger('change');
        
        // Establecer editor por defecto (usuario actual)
        // Esto se puede hacer desde el backend o aquí
        
        // Mostrar el modal
        $modal.modal('show');
    }
    
    /**
     * Abre el modal para editar una publicación
     */
    function openEditModal(publicacionId) {
        const $modal = $('#modalPublicacion');
        if ($modal.length === 0) return;
        
        ajaxRequest(
            PUBLICACIONES_URLS.publicacionDetail(publicacionId),
            'GET',
            null,
            function(response) {
                if (response.success && response.data) {
                    const pub = response.data;
                    
                    // Llenar campos básicos
                    $('#publicacionId').val(pub.id);
                    $('#publicacionTipo').val(pub.tipo_publicacion);
                    $('#publicacionEstado').val(pub.estado);
                    $('#publicacionISSN').val(pub.issn || '');
                    $('#publicacionISBN').val(pub.isbn || '');
                    $('#publicacionDOI').val(pub.doi || '');
                    $('#publicacionUrlExterna').val(pub.url_externa || '');
                    
                    // Fecha de publicación
                    if (pub.fecha_publicacion) {
                        const fecha = new Date(pub.fecha_publicacion);
                        const fechaLocal = fecha.toISOString().slice(0, 16);
                        $('#publicacionFechaPublicacion').val(fechaLocal);
                    }
                    
                    // Cargar selects y establecer valores
                    loadPublicacionSelects();
                    
                    // Esperar a que se carguen los selects antes de establecer valores
                    setTimeout(function() {
                        // Editor
                        $('#publicacionEditor').val(pub.editor_id);
                        
                        // Proyectos
                        const proyectosIds = pub.proyectos ? pub.proyectos.map(p => p.id) : [];
                        $('#publicacionProyectos').val(proyectosIds).trigger('change');
                        
                        // Categorías
                        const categoriasIds = pub.categorias ? pub.categorias.map(c => c.id) : [];
                        $('#publicacionCategorias').val(categoriasIds).trigger('change');
                        
                        // Etiquetas
                        const etiquetasIds = pub.etiquetas ? pub.etiquetas.map(e => e.id) : [];
                        $('#publicacionEtiquetas').val(etiquetasIds).trigger('change');
                    }, 500);
                    
                    $('#modalPublicacionLabel').text('Editar Publicación');
                    $modal.modal('show');
                }
            }
        );
    }
    
    // ========================================================================
    // MANEJO DEL FORMULARIO
    // ========================================================================
    
    /**
     * Maneja el envío del formulario
     */
    $(document).on('submit', '#formPublicacion', function(e) {
        e.preventDefault();
        
        const publicacionId = $('#publicacionId').val();
        const isEdit = publicacionId !== '';
        
        // Recopilar datos del formulario
        const formData = {
            tipo_publicacion: $('#publicacionTipo').val(),
            editor_id: parseInt($('#publicacionEditor').val()),
            estado: $('#publicacionEstado').val(),
            fecha_publicacion: $('#publicacionFechaPublicacion').val() || null,
            issn: $('#publicacionISSN').val().trim() || null,
            isbn: $('#publicacionISBN').val().trim() || null,
            doi: $('#publicacionDOI').val().trim() || null,
            url_externa: $('#publicacionUrlExterna').val().trim() || null,
            proyectos: $('#publicacionProyectos').val() ? $('#publicacionProyectos').val().map(id => ({ id: parseInt(id) })) : [],
            categorias: $('#publicacionCategorias').val() ? $('#publicacionCategorias').val().map(id => parseInt(id)) : [],
            etiquetas: $('#publicacionEtiquetas').val() ? $('#publicacionEtiquetas').val().map(id => parseInt(id)) : [],
        };
        
        // Validaciones básicas
        if (!formData.proyectos || formData.proyectos.length === 0) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Debe seleccionar al menos un proyecto.',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        if (!formData.editor_id) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Debe seleccionar un editor',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        // Determinar URL y método
        let url, method;
        if (isEdit) {
            url = PUBLICACIONES_URLS.publicacionUpdate(publicacionId);
            method = 'POST';
            formData._method = 'PUT';
        } else {
            url = PUBLICACIONES_URLS.publicacionCreate;
            method = 'POST';
        }
        
        // Enviar datos
        ajaxRequest(
            url,
            method,
            formData,
            function(response) {
                if (response.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Éxito',
                        text: response.message || (isEdit ? 'Publicación actualizada exitosamente' : 'Publicación creada exitosamente'),
                        confirmButtonText: 'Aceptar'
                    }).then(() => {
                        $('#modalPublicacion').modal('hide');
                        tablePublicaciones.ajax.reload();
                    });
                }
            }
        );
    });
    
    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================
    
    // Botón crear publicación
    $(document).on('click', '#btnCrearPublicacion', function(e) {
        e.preventDefault();
        openCreateModal();
    });
    
    // Botón editar publicación
    $(document).on('click', '.btn-editar-publicacion', function(e) {
        e.preventDefault();
        const publicacionId = $(this).data('id');
        openEditModal(publicacionId);
    });
    
    // Botón ver publicación
    $(document).on('click', '.btn-ver-publicacion', function(e) {
        e.preventDefault();
        const publicacionId = $(this).data('id');
        const titulo = $(this).data('titulo');
        
        ajaxRequest(
            PUBLICACIONES_URLS.publicacionDetail(publicacionId),
            'GET',
            null,
            function(response) {
                if (response.success && response.data) {
                    const pub = response.data;
                    
                    let proyectosHtml = '<ul>';
                    if (pub.proyectos && pub.proyectos.length > 0) {
                        pub.proyectos.forEach(function(proy) {
                            proyectosHtml += `<li>${escapeHtml(proy.titulo)}</li>`;
                        });
                    } else {
                        proyectosHtml += '<li>No hay proyectos asociados</li>';
                    }
                    proyectosHtml += '</ul>';
                    
                    let categoriasHtml = '';
                    if (pub.categorias && pub.categorias.length > 0) {
                        pub.categorias.forEach(function(cat) {
                            categoriasHtml += `<span class="badge badge-primary mr-1">${escapeHtml(cat.nombre)}</span>`;
                        });
                    } else {
                        categoriasHtml = '<span class="text-muted">No hay categorías</span>';
                    }
                    
                    let etiquetasHtml = '';
                    if (pub.etiquetas && pub.etiquetas.length > 0) {
                        pub.etiquetas.forEach(function(etq) {
                            etiquetasHtml += `<span class="badge badge-info mr-1">${escapeHtml(etq.nombre)}</span>`;
                        });
                    } else {
                        etiquetasHtml = '<span class="text-muted">No hay etiquetas</span>';
                    }
                    
                    Swal.fire({
                        icon: 'info',
                        title: escapeHtml(pub.titulo),
                        html: `
                            <div class="text-left">
                                <p><strong>Descripción:</strong> ${escapeHtml(pub.descripcion || 'Sin descripción')}</p>
                                <p><strong>Tipo:</strong> ${escapeHtml(pub.tipo_publicacion)}</p>
                                <p><strong>Estado:</strong> ${escapeHtml(pub.estado)}</p>
                                <p><strong>Editor:</strong> ${escapeHtml(pub.editor_nombre || '')}</p>
                                <p><strong>Proyectos:</strong> ${proyectosHtml}</p>
                                <p><strong>Categorías:</strong> ${categoriasHtml}</p>
                                <p><strong>Etiquetas:</strong> ${etiquetasHtml}</p>
                                ${pub.issn ? `<p><strong>ISSN:</strong> ${escapeHtml(pub.issn)}</p>` : ''}
                                ${pub.isbn ? `<p><strong>ISBN:</strong> ${escapeHtml(pub.isbn)}</p>` : ''}
                                ${pub.doi ? `<p><strong>DOI:</strong> ${escapeHtml(pub.doi)}</p>` : ''}
                                ${pub.url_externa ? `<p><strong>URL Externa:</strong> <a href="${escapeHtml(pub.url_externa)}" target="_blank">${escapeHtml(pub.url_externa)}</a></p>` : ''}
                            </div>
                        `,
                        width: '600px',
                        confirmButtonText: 'Cerrar'
                    });
                }
            }
        );
    });
    
    // Botón eliminar publicación
    $(document).on('click', '.btn-eliminar-publicacion', function(e) {
        e.preventDefault();
        const publicacionId = $(this).data('id');
        const titulo = $(this).data('titulo');
        
        Swal.fire({
            icon: 'warning',
            title: '¿Eliminar publicación?',
            text: `¿Está seguro de eliminar la publicación "${escapeHtml(titulo)}"?`,
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                ajaxRequest(
                    PUBLICACIONES_URLS.publicacionDelete(publicacionId),
                    'POST',
                    { _method: 'DELETE' },
                    function(response) {
                        if (response.success) {
                            Swal.fire({
                                icon: 'success',
                                title: 'Eliminado',
                                text: response.message || 'Publicación eliminada exitosamente',
                                confirmButtonText: 'Aceptar'
                            }).then(() => {
                                tablePublicaciones.ajax.reload();
                            });
                        }
                    }
                );
            }
        });
    });
    
    // Cargar selects cuando se abre el modal
    $(document).on('show.bs.modal', '#modalPublicacion', function() {
        loadPublicacionSelects();
    });

    // Botón para generar URL externa
    $(document).on('click', '#btnGenerarUrlExterna', function(e) {
        e.preventDefault();
        
        const proyectosSeleccionados = $('#publicacionProyectos').val();
        if (!proyectosSeleccionados || proyectosSeleccionados.length === 0) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Debe seleccionar al menos un proyecto en la pestaña "Proyectos" para generar la URL.',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        const primerProyectoId = proyectosSeleccionados[0];
        
        // Hacer petición al backend para obtener un slug de previsualización
        $.ajax({
            url: `${PUBLICACIONES_URLS.generarSlugPreview}?proyecto_id=${primerProyectoId}`,
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            beforeSend: showLoading,
            success: function(response) {
                hideLoading();
                if (response.success && response.slug_preview) {
                    const fullUrl = `${window.location.origin}/publicacion/${response.slug_preview}/`;
                    $('#publicacionUrlExterna').val(fullUrl);
                    Swal.fire({
                        icon: 'success',
                        title: 'URL de Previsualización Generada',
                        text: `La URL ha sido generada y colocada en el campo "URL Externa". La URL final puede variar si el identificador ya existe.`,
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 4000,
                        timerProgressBar: true
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: response.error || 'No se pudo generar la URL de previsualización.'
                    });
                }
            },
            error: function() {
                hideLoading();
                Swal.fire({
                    icon: 'error',
                    title: 'Error de Comunicación',
                    text: 'No se pudo comunicar con el servidor para generar la URL.'
                });
            }
        });
    });
    
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    // Inicializar tabla
    if ($('#tablePublicaciones').length > 0) {
        initTablePublicaciones();
    }
    
    console.log('✅ Script de publicaciones inicializado correctamente');
});



