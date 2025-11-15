/**
 * Script de gestión para Proyectos (Tipos de Proyecto y Campos de Tipo de Proyecto)
 * Usa jQuery, DataTables, SweetAlert2 y URL Reverse
 */

// Esperar a que el DOM esté listo y que PROYECTOS_URLS esté definido
jQuery(document).ready(function($) {
    // Verificar que jQuery esté disponible
    if (typeof $ === 'undefined' || typeof jQuery === 'undefined') {
        console.error('jQuery no está disponible. El script de proyectos requiere jQuery.');
        return;
    }
    
    // Verificar que PROYECTOS_URLS esté disponible
    if (typeof PROYECTOS_URLS === 'undefined') {
        console.error('PROYECTOS_URLS no está definido. Asegúrate de que el script se cargue después del bloque de definición de URLs.');
        return;
    }
    
    console.log('Script de proyectos cargado correctamente');
    console.log('PROYECTOS_URLS disponible:', typeof PROYECTOS_URLS !== 'undefined');
    
    // Variables globales
    let tableTiposProyecto, tableCamposTipoProyecto, tableProyectos;
    let tiposProyectoData = [];
    
    // ========================================================================
    // FUNCIONES AUXILIARES
    // ========================================================================
    
    /**
     * Función auxiliar para escapar HTML (disponible globalmente)
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
     * Función para obtener CSRF token
     */
    function getCSRFToken() {
        // Intentar obtener del contexto global primero
        if (typeof window.getCSRFToken === 'function') {
            return window.getCSRFToken();
        }
        // Si no, buscar en el DOM
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    /**
     * Función genérica para hacer peticiones AJAX
     */
    function ajaxRequest(url, method, data, successCallback, errorCallback) {
        showLoading();
        
        const csrfToken = getCSRFToken();
        
        const options = {
            url: url,
            method: method,
            headers: {
                'X-CSRFToken': csrfToken,
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
     * Carga los tipos de proyecto y los actualiza en el select
     * @param {string} selectId - ID del select a poblar (opcional, por defecto '#campoTipoProyectoTipoProyecto')
     */
    function loadTiposProyectoForSelect(selectId) {
        if (!selectId) {
            selectId = '#campoTipoProyectoTipoProyecto';
        }
        
        ajaxRequest(
            PROYECTOS_URLS.tiposProyectoForSelect,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    tiposProyectoData = response.data;
                    const select = $(selectId);
                    if (select.length === 0) {
                        console.error('Select no encontrado:', selectId);
                        return;
                    }
                    select.empty();
                    select.append('<option value="">Seleccione un tipo de proyecto</option>');
                    
                    tiposProyectoData.forEach(function(tipo) {
                        select.append(
                            `<option value="${tipo.id}">${escapeHtml(tipo.nombre)}</option>`
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
     * Inicializa la tabla de Tipos de Proyecto
     */
    function initTableTiposProyecto() {
        // Verificar si la tabla existe antes de inicializar
        const $table = $('#tableTiposProyecto');
        if ($table.length === 0) {
            console.warn('La tabla #tableTiposProyecto no existe en el DOM');
            return;
        }
        // Verificar que el elemento de la tabla tenga la estructura correcta
        if ($table.find('thead tr').length === 0) {
            console.error('La tabla #tableTiposProyecto no tiene la estructura correcta (falta thead)');
            return;
        }
        
        // Verificar que el tab esté visible antes de inicializar
        const $tabPane = $('#tipos-proyecto');
        if ($tabPane.length > 0 && !$tabPane.hasClass('active') && !$tabPane.hasClass('show')) {
            // Si el tab no está visible, no inicializar ahora (se inicializará cuando se muestre)
            console.log('Tab tipos-proyecto no está visible, esperando a que se muestre...');
            return;
        }
        
        // Destruir la tabla si ya existe
        if ($.fn.DataTable.isDataTable('#tableTiposProyecto')) {
            $('#tableTiposProyecto').DataTable().destroy();
        }
        
        tableTiposProyecto = $('#tableTiposProyecto').DataTable({
            responsive: {
                details: {
                    type: 'column',
                    target: 'tr'
                }
            },
            processing: true,
            serverSide: false,
            autoWidth: false,
            deferRender: true,
            ajax: {
                url: PROYECTOS_URLS.tiposProyectoList,
                type: 'GET',
                dataSrc: function(json) {
                    // Validar que la respuesta tenga la estructura esperada
                    if (json && json.success && json.data) {
                        return json.data;
                    } else {
                        console.error('Respuesta inválida del servidor:', json);
                        return [];
                    }
                },
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar tipos de proyecto:', error, thrown);
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'No se pudieron cargar los tipos de proyecto',
                            confirmButtonText: 'Aceptar'
                        });
                    }
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'nombre' },
                { 
                    data: 'icono',
                    render: function(data, type, row) {
                        if (data) {
                            return `<i class="${data} icono-preview"></i> ${data}`;
                        }
                        return '-';
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
                { data: 'orden' },
                { 
                    data: 'es_activo',
                    render: function(data) {
                        if (data) {
                            return '<span class="badge badge-success badge-estado">Activo</span>';
                        }
                        return '<span class="badge badge-secondary badge-estado">Inactivo</span>';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-success btn-ver-proyectos-tipo" 
                                        data-id="${row.id}" 
                                        data-nombre="${row.nombre}"
                                        title="Ver Proyectos">
                                    <i class="fas fa-folder-open"></i>
                                    <span class="d-none d-md-inline ml-1">Proyectos (${row.proyectos_count})</span>
                                </button>
                                <button class="btn btn-info btn-editar-tipo-proyecto" 
                                        data-id="${row.id}" 
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-tipo-proyecto" 
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
            order: [[4, 'asc']], // Ordenar por orden ascendente (columna índice 4)
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Inicializa la tabla de Proyectos
     */
    function initTableProyectos() {
        // Verificar si la tabla existe antes de inicializar
        const $table = $('#tableProyectos');
        if ($table.length === 0) {
            console.warn('La tabla #tableProyectos no existe en el DOM');
            return;
        }
        // Verificar que el elemento de la tabla tenga la estructura correcta
        if ($table.find('thead tr').length === 0) {
            console.error('La tabla #tableProyectos no tiene la estructura correcta (falta thead)');
            return;
        }
        // Verificar que el tab esté visible antes de inicializar
        const $tabPane = $('#proyectos');
        if ($tabPane.length > 0 && !$tabPane.hasClass('active') && !$tabPane.hasClass('show')) {
            console.log('Tab proyectos no está visible, esperando a que se muestre...');
            return;
        }
        // Destruir la tabla si ya existe
        if ($.fn.DataTable.isDataTable('#tableProyectos')) {
            $('#tableProyectos').DataTable().destroy();
        }
        
        tableProyectos = $('#tableProyectos').DataTable({
            responsive: {
                details: {
                    type: 'column',
                    target: 'tr'
                }
            },
            processing: true,
            serverSide: false,
            ajax: {
                url: PROYECTOS_URLS.proyectosList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar proyectos:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los proyectos',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'titulo' },
                { data: 'tipo_proyecto_nombre' },
                { 
                    data: 'autores',
                    render: function(data, type, row) {
                        if (!data || data.length === 0) {
                            return '<span class="badge badge-secondary">Sin autores</span>';
                        }
                        // Mostrar los primeros 2 autores, y el resto con "+N"
                        const autoresMostrar = data.slice(0, 2);
                        const autoresRestantes = data.length - 2;
                        let html = autoresMostrar.map(autor => {
                            const nombreCompleto = escapeHtml(autor.nombre_completo || `${autor.nombre} ${autor.apellidos}`);
                            return `<span class="badge badge-primary" title="${nombreCompleto}">${nombreCompleto}</span>`;
                        }).join(' ');
                        if (autoresRestantes > 0) {
                            html += ` <span class="badge badge-info">+${autoresRestantes}</span>`;
                        }
                        return html;
                    }
                },
                { 
                    data: 'estado_display',
                    render: function(data, type, row) {
                        const badgeClass = {
                            'Borrador': 'badge-secondary',
                            'En Revisión': 'badge-warning',
                            'Aprobado': 'badge-success',
                            'Publicado': 'badge-info',
                            'Archivado': 'badge-dark',
                            'Rechazado': 'badge-danger'
                        };
                        const className = badgeClass[data] || 'badge-secondary';
                        return `<span class="badge ${className}">${data}</span>`;
                    }
                },
                { 
                    data: 'visibilidad_display',
                    render: function(data) {
                        return `<span class="badge badge-info">${data}</span>`;
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
                        // Usar la función escapeHtml global o una función local si no está disponible
                        const escapeHtmlFn = window.escapeHtml || function(text) {
                            if (!text) return '';
                            const map = {
                                '&': '&amp;',
                                '<': '&lt;',
                                '>': '&gt;',
                                '"': '&quot;',
                                "'": '&#039;'
                            };
                            return String(text).replace(/[&<>"']/g, m => map[m]);
                        };
                        
                        const tituloEscapado = escapeHtmlFn(row.titulo || '');
                        // Intentar usar el slug de la publicación relacionada, si no existe, usar búsqueda
                        let publicUrl = null;
                        if (row.publicacion_slug && PROYECTOS_URLS.proyectoPublicDetail) {
                            publicUrl = PROYECTOS_URLS.proyectoPublicDetail(row.publicacion_slug);
                        } else if (row.titulo && PROYECTOS_URLS.proyectoPublicSearch) {
                            // Si no hay publicación relacionada, redirigir a la búsqueda
                            publicUrl = PROYECTOS_URLS.proyectoPublicSearch(row.titulo);
                        }
                        
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                ${publicUrl ? `
                                <a class="btn btn-outline-primary"
                                   href="${publicUrl}"
                                   target="_blank"
                                   rel="noopener noreferrer"
                                   title="Ver en catálogo público">
                                    <i class="fas fa-globe"></i>
                                    <span class="d-none d-md-inline ml-1">Público</span>
                                </a>
                                ` : ''}
                                <button class="btn btn-info btn-ver-proyecto" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
                                        title="Ver detalles">
                                    <i class="fas fa-eye"></i>
                                    <span class="d-none d-md-inline ml-1">Ver</span>
                                </button>
                                <button class="btn btn-warning btn-editar-proyecto" 
                                        data-id="${row.id}" 
                                        data-titulo="${tituloEscapado}"
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-proyecto" 
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
            order: [[7, 'desc']], // Cambiado a columna 7 (Fecha Creación)
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    /**
     * Inicializa la tabla de Campos de Tipo de Proyecto
     */
    function initTableCamposTipoProyecto() {
        // Verificar si la tabla existe antes de inicializar
        const $table = $('#tableCamposTipoProyecto');
        if ($table.length === 0) {
            console.warn('La tabla #tableCamposTipoProyecto no existe en el DOM');
            return;
        }
        // Verificar que el elemento de la tabla tenga la estructura correcta
        if ($table.find('thead tr').length === 0) {
            console.error('La tabla #tableCamposTipoProyecto no tiene la estructura correcta (falta thead)');
            return;
        }
        // Verificar que el tab esté visible antes de inicializar
        const $tabPane = $('#campos-tipo-proyecto');
        if ($tabPane.length > 0 && !$tabPane.hasClass('active') && !$tabPane.hasClass('show')) {
            console.log('Tab campos-tipo-proyecto no está visible, esperando a que se muestre...');
            return;
        }
        // Destruir la tabla si ya existe
        if ($.fn.DataTable.isDataTable('#tableCamposTipoProyecto')) {
            $('#tableCamposTipoProyecto').DataTable().destroy();
        }
        
        tableCamposTipoProyecto = $('#tableCamposTipoProyecto').DataTable({
            responsive: {
                details: {
                    type: 'column',
                    target: 'tr'
                }
            },
            processing: true,
            serverSide: false,
            ajax: {
                url: PROYECTOS_URLS.camposTipoProyectoList,
                type: 'GET',
                dataSrc: 'data',
                error: function(xhr, error, thrown) {
                    console.error('Error al cargar campos de tipo de proyecto:', error);
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'No se pudieron cargar los campos de tipo de proyecto',
                        confirmButtonText: 'Aceptar'
                    });
                }
            },
            columns: [
                { data: 'id', width: '5%' },
                { data: 'tipo_proyecto_nombre' },
                { data: 'etiqueta' },
                { 
                    data: 'tipo_dato_display',
                    render: function(data, type, row) {
                        const badgeClass = {
                            'Texto': 'badge-primary',
                            'Área de Texto': 'badge-secondary',
                            'Número': 'badge-info',
                            'Fecha': 'badge-warning',
                            'Booleano': 'badge-success',
                            'Selección Única': 'badge-danger',
                            'Selección Múltiple': 'badge-dark',
                            'Archivo': 'badge-primary',
                            'URL': 'badge-info',
                            'Email': 'badge-secondary',
                            'JSON': 'badge-dark'
                        };
                        const className = badgeClass[data] || 'badge-secondary';
                        return `<span class="badge ${className}">${data}</span>`;
                    }
                },
                { 
                    data: 'categoria',
                    render: function(data) {
                        return data || '-';
                    }
                },
                { 
                    data: 'es_obligatorio',
                    render: function(data) {
                        if (data) {
                            return '<span class="badge badge-danger">Sí</span>';
                        }
                        return '<span class="badge badge-secondary">No</span>';
                    }
                },
                { data: 'orden' },
                {
                    data: null,
                    orderable: false,
                    className: 'text-center',
                    render: function(data, type, row) {
                        return `
                            <div class="btn-group btn-group-sm" role="group">
                                <button class="btn btn-info btn-editar-campo-tipo-proyecto" 
                                        data-id="${row.id}" 
                                        title="Editar">
                                    <i class="fas fa-edit"></i>
                                    <span class="d-none d-md-inline ml-1">Editar</span>
                                </button>
                                <button class="btn btn-danger btn-eliminar-campo-tipo-proyecto" 
                                        data-id="${row.id}" 
                                        data-etiqueta="${row.etiqueta}"
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
            order: [[1, 'asc'], [6, 'asc']],
            dom: 'lBfrtip',
            buttons: [],
            pageLength: 10,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
        });
    }
    
    // ========================================================================
    // GESTIÓN DE TIPOS DE PROYECTO
    // ========================================================================
    
    /**
     * Abre el modal para crear un nuevo tipo de proyecto
     */
    $(document).on('click', '#btnCrearTipoProyecto', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('Botón crear tipo proyecto clickeado');
        
        if ($('#modalTipoProyecto').length === 0) {
            console.error('Modal #modalTipoProyecto no encontrado');
            return false;
        }
        
        $('#modalTipoProyectoLabel').text('Nuevo Tipo de Proyecto');
        $('#formTipoProyecto')[0].reset();
        $('#tipoProyectoId').val('');
        $('#tipoProyectoActivo').prop('checked', true);
        $('#tipoProyectoOrden').val(0);
        if ($('#tipoProyectoColorPreview').length) {
            $('#tipoProyectoColorPreview').css('background-color', '#007bff');
        }
        $('#modalTipoProyecto').modal('show');
        
        return false;
    });
    
    /**
     * Abre el modal para editar un tipo de proyecto
     */
    $(document).on('click', '.btn-editar-tipo-proyecto', function() {
        const tipoProyectoId = $(this).data('id');
        const url = PROYECTOS_URLS.tipoProyectoDetail(tipoProyectoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const tipo = response.data;
                    $('#modalTipoProyectoLabel').text('Editar Tipo de Proyecto');
                    $('#tipoProyectoId').val(tipo.id);
                    $('#tipoProyectoNombre').val(tipo.nombre);
                    $('#tipoProyectoDescripcion').val(tipo.descripcion || '');
                    $('#tipoProyectoIcono').val(tipo.icono || '');
                    $('#tipoProyectoColor').val(tipo.color || '');
                    $('#tipoProyectoColorPreview').css('background-color', tipo.color || '#007bff');
                    $('#tipoProyectoPlantillaVista').val(tipo.plantilla_vista || '');
                    $('#tipoProyectoActivo').prop('checked', tipo.es_activo);
                    $('#tipoProyectoOrden').val(tipo.orden);
                    $('#modalTipoProyecto').modal('show');
                }
            }
        );
    });
    
    /**
     * Actualiza el preview del color en tiempo real
     */
    $(document).on('input', '#tipoProyectoColor', function() {
        let color = $(this).val().trim();
        if (color && !color.startsWith('#')) {
            color = '#' + color;
        }
        if ($('#tipoProyectoColorPreview').length) {
            $('#tipoProyectoColorPreview').css('background-color', color || '#007bff');
        }
    });
    
    /**
     * Maneja el envío del formulario de tipo de proyecto
     */
    $(document).on('submit', '#formTipoProyecto', function(e) {
        e.preventDefault();
        
        const tipoProyectoId = $('#tipoProyectoId').val();
        const formData = {
            nombre: $('#tipoProyectoNombre').val().trim(),
            descripcion: $('#tipoProyectoDescripcion').val().trim(),
            icono: $('#tipoProyectoIcono').val().trim(),
            color: $('#tipoProyectoColor').val().trim(),
            plantilla_vista: $('#tipoProyectoPlantillaVista').val().trim(),
            es_activo: $('#tipoProyectoActivo').is(':checked'),
            orden: parseInt($('#tipoProyectoOrden').val()) || 0
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
        if (tipoProyectoId) {
            url = PROYECTOS_URLS.tipoProyectoUpdate(tipoProyectoId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = PROYECTOS_URLS.tipoProyectoCreate;
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
                    $('#modalTipoProyecto').modal('hide');
                    tableTiposProyecto.ajax.reload(null, false);
                    // Recargar también los tipos para el select de campos
                    loadTiposProyectoForSelect();
                }
            }
        );
    });
    
    /**
     * Maneja la eliminación de un tipo de proyecto
     */
    $(document).on('click', '.btn-eliminar-tipo-proyecto', function() {
        const tipoProyectoId = $(this).data('id');
        const tipoProyectoNombre = $(this).data('nombre');
        const url = PROYECTOS_URLS.tipoProyectoDelete(tipoProyectoId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el tipo de proyecto "${tipoProyectoNombre}"?`,
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
                                text: response.message || 'Tipo de proyecto eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableTiposProyecto.ajax.reload(null, false);
                            tableCamposTipoProyecto.ajax.reload(null, false);
                            loadTiposProyectoForSelect();
                        }
                    }
                );
            }
        });
    });
    
    // ========================================================================
    // GESTIÓN DE CAMPOS DE TIPO DE PROYECTO
    // ========================================================================
    
    /**
     * Abre el modal para crear un nuevo campo de tipo de proyecto
     */
    $(document).on('click', '#btnCrearCampoTipoProyecto', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('Botón crear campo tipo proyecto clickeado');
        
        if ($('#modalCampoTipoProyecto').length === 0) {
            console.error('Modal #modalCampoTipoProyecto no encontrado');
            return false;
        }
        
        $('#modalCampoTipoProyectoLabel').text('Nuevo Campo de Tipo de Proyecto');
        $('#formCampoTipoProyecto')[0].reset();
        $('#campoTipoProyectoId').val('');
        $('#campoTipoProyectoOrden').val(0);
        $('#campoTipoProyectoBuscable').prop('checked', true);
        $('#campoTipoProyectoObligatorio').prop('checked', false);
        $('#campoTipoProyectoRepetible').prop('checked', false);
        $('#valoresPosiblesGroup').hide();
        loadTiposProyectoForSelect('#campoTipoProyectoTipoProyecto');
        $('#modalCampoTipoProyecto').modal('show');
        
        return false;
    });
    
    /**
     * Abre el modal para editar un campo de tipo de proyecto
     */
    $(document).on('click', '.btn-editar-campo-tipo-proyecto', function() {
        const campoId = $(this).data('id');
        const url = PROYECTOS_URLS.campoTipoProyectoDetail(campoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const campo = response.data;
                    $('#modalCampoTipoProyectoLabel').text('Editar Campo de Tipo de Proyecto');
                    $('#campoTipoProyectoId').val(campo.id);
                    $('#campoTipoProyectoTipoProyecto').val(campo.tipo_proyecto_id);
                    $('#campoTipoProyectoNombre').val(campo.nombre);
                    $('#campoTipoProyectoEtiqueta').val(campo.etiqueta);
                    $('#campoTipoProyectoDescripcion').val(campo.descripcion || '');
                    $('#campoTipoProyectoTipoDato').val(campo.tipo_dato);
                    $('#campoTipoProyectoCategoria').val(campo.categoria || '');
                    $('#campoTipoProyectoOrden').val(campo.orden);
                    $('#campoTipoProyectoValorPorDefecto').val(campo.valor_por_defecto || '');
                    $('#campoTipoProyectoValidador').val(campo.validador || '');
                    $('#campoTipoProyectoAyuda').val(campo.ayuda || '');
                    $('#campoTipoProyectoObligatorio').prop('checked', campo.es_obligatorio);
                    $('#campoTipoProyectoRepetible').prop('checked', campo.es_repetible);
                    $('#campoTipoProyectoBuscable').prop('checked', campo.es_buscable);
                    
                    // Manejar valores_posibles
                    if (campo.valores_posibles) {
                        if (Array.isArray(campo.valores_posibles)) {
                            $('#campoTipoProyectoValoresPosibles').val(JSON.stringify(campo.valores_posibles, null, 2));
                        } else {
                            $('#campoTipoProyectoValoresPosibles').val(JSON.stringify(campo.valores_posibles));
                        }
                    } else {
                        $('#campoTipoProyectoValoresPosibles').val('');
                    }
                    
                    // Mostrar/ocultar grupo de valores posibles según tipo de dato
                    if (campo.tipo_dato === 'select' || campo.tipo_dato === 'multiselect') {
                        $('#valoresPosiblesGroup').show();
                    } else {
                        $('#valoresPosiblesGroup').hide();
                    }
                    
                    loadTiposProyectoForSelect();
                    setTimeout(function() {
                        $('#campoTipoProyectoTipoProyecto').val(campo.tipo_proyecto_id);
                    }, 500);
                    
                    $('#modalCampoTipoProyecto').modal('show');
                }
            }
        );
    });
    
    /**
     * Muestra/oculta el grupo de valores posibles según el tipo de dato
     */
    $(document).on('change', '#campoTipoProyectoTipoDato', function() {
        const tipoDato = $(this).val();
        if (tipoDato === 'select' || tipoDato === 'multiselect') {
            $('#valoresPosiblesGroup').show();
        } else {
            $('#valoresPosiblesGroup').hide();
        }
    });
    
    /**
     * Maneja el envío del formulario de campo de tipo de proyecto
     */
    $(document).on('submit', '#formCampoTipoProyecto', function(e) {
        e.preventDefault();
        
        const campoId = $('#campoTipoProyectoId').val();
        const tipoDato = $('#campoTipoProyectoTipoDato').val();
        
        // Procesar valores_posibles
        let valoresPosibles = null;
        const valoresPosiblesText = $('#campoTipoProyectoValoresPosibles').val().trim();
        if (valoresPosiblesText && (tipoDato === 'select' || tipoDato === 'multiselect')) {
            try {
                valoresPosibles = JSON.parse(valoresPosiblesText);
                if (!Array.isArray(valoresPosibles)) {
                    throw new Error('Debe ser un array');
                }
            } catch (e) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Validación',
                    text: 'Los valores posibles deben ser un array JSON válido (ej: ["Opción 1", "Opción 2"])',
                    confirmButtonText: 'Aceptar'
                });
                return;
            }
        }
        
        const formData = {
            tipo_proyecto_id: $('#campoTipoProyectoTipoProyecto').val(),
            nombre: $('#campoTipoProyectoNombre').val().trim(),
            etiqueta: $('#campoTipoProyectoEtiqueta').val().trim(),
            descripcion: $('#campoTipoProyectoDescripcion').val().trim(),
            tipo_dato: tipoDato,
            categoria: $('#campoTipoProyectoCategoria').val().trim(),
            orden: parseInt($('#campoTipoProyectoOrden').val()) || 0,
            valor_por_defecto: $('#campoTipoProyectoValorPorDefecto').val().trim(),
            validador: $('#campoTipoProyectoValidador').val().trim(),
            ayuda: $('#campoTipoProyectoAyuda').val().trim(),
            es_obligatorio: $('#campoTipoProyectoObligatorio').is(':checked'),
            es_repetible: $('#campoTipoProyectoRepetible').is(':checked'),
            es_buscable: $('#campoTipoProyectoBuscable').is(':checked'),
            es_indexable: true, // Siempre indexable por defecto
            valores_posibles: valoresPosibles
        };
        
        if (!formData.tipo_proyecto_id) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El tipo de proyecto es obligatorio',
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
        
        if (!formData.etiqueta) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'La etiqueta es obligatoria',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        let url, method, sendData;
        if (campoId) {
            url = PROYECTOS_URLS.campoTipoProyectoUpdate(campoId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = PROYECTOS_URLS.campoTipoProyectoCreate;
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
                    $('#modalCampoTipoProyecto').modal('hide');
                    tableCamposTipoProyecto.ajax.reload(null, false);
                }
            }
        );
    });
    
    /**
     * Maneja la eliminación de un campo de tipo de proyecto
     */
    $(document).on('click', '.btn-eliminar-campo-tipo-proyecto', function() {
        const campoId = $(this).data('id');
        const campoEtiqueta = $(this).data('etiqueta');
        const url = PROYECTOS_URLS.campoTipoProyectoDelete(campoId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el campo "${campoEtiqueta}"?`,
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
                                text: response.message || 'Campo eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableCamposTipoProyecto.ajax.reload(null, false);
                            tableTiposProyecto.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    // ========================================================================
    // GESTIÓN DE PROYECTOS
    // ========================================================================
    
    /**
     * Abre el modal o vista para ver detalles de un proyecto
     */
    $(document).on('click', '.btn-ver-proyecto', function() {
        const proyectoId = $(this).data('id');
        const url = PROYECTOS_URLS.proyectoDetail(proyectoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const proyecto = response.data;
                    // Construir HTML con campos dinámicos
                    let camposHtml = '';
                    if (proyecto.valores_campos && Object.keys(proyecto.valores_campos).length > 0) {
                        camposHtml = '<hr><h6 class="mb-3"><i class="fas fa-list-ul"></i> Campos Dinámicos:</h6><div class="table-responsive"><table class="table table-sm table-bordered">';
                        camposHtml += '<thead><tr><th>Campo</th><th>Valor</th></tr></thead><tbody>';
                        Object.keys(proyecto.valores_campos).forEach(function(campoSlug) {
                            const valores = proyecto.valores_campos[campoSlug];
                            valores.forEach(function(valorObj, index) {
                                const valor = valorObj.valor !== null && valorObj.valor !== undefined ? String(valorObj.valor) : '(vacío)';
                                const campoNombre = index === 0 ? escapeHtml(campoSlug) : '';
                                camposHtml += `<tr><td><strong>${campoNombre}</strong></td><td>${escapeHtml(valor)}</td></tr>`;
                            });
                        });
                        camposHtml += '</tbody></table></div>';
                    }
                    
                    // Formatear fecha
                    let fechaCreacion = '-';
                    if (proyecto.fecha_creacion) {
                        const fecha = new Date(proyecto.fecha_creacion);
                        fechaCreacion = fecha.toLocaleDateString('es-ES', { 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    }
                    
                    // Mostrar información del proyecto en un modal
                    Swal.fire({
                        icon: 'info',
                        title: escapeHtml(proyecto.titulo),
                        html: `
                            <div class="text-left">
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-project-diagram"></i> Tipo de Proyecto:</strong><br>
                                        <span class="badge badge-primary">${escapeHtml(proyecto.tipo_proyecto_nombre)}</span></p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-user"></i> Creador:</strong><br>${escapeHtml(proyecto.creador_nombre)}</p>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-info-circle"></i> Estado:</strong><br>
                                        <span class="badge badge-info">${escapeHtml(proyecto.estado_display)}</span></p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-eye"></i> Visibilidad:</strong><br>
                                        <span class="badge badge-secondary">${escapeHtml(proyecto.visibilidad_display)}</span></p>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <p><strong><i class="fas fa-calendar"></i> Fecha de Creación:</strong><br>${fechaCreacion}</p>
                                    </div>
                                    <div class="col-md-6">
                                        ${proyecto.categorias_count > 0 ? `<p><strong><i class="fas fa-tags"></i> Categorías:</strong><br><span class="badge badge-info">${proyecto.categorias_count}</span></p>` : ''}
                                        ${proyecto.etiquetas_count > 0 ? `<p><strong><i class="fas fa-tag"></i> Etiquetas:</strong><br><span class="badge badge-secondary">${proyecto.etiquetas_count}</span></p>` : ''}
                                    </div>
                                </div>
                                ${proyecto.resumen ? `<hr><p><strong><i class="fas fa-file-alt"></i> Resumen:</strong><br>${escapeHtml(proyecto.resumen)}</p>` : ''}
                                ${proyecto.descripcion ? `<hr><p><strong><i class="fas fa-align-left"></i> Descripción:</strong><br>${escapeHtml(proyecto.descripcion)}</p>` : ''}
                                ${camposHtml}
                            </div>
                        `,
                        confirmButtonText: 'Cerrar',
                        width: '800px',
                        customClass: {
                            popup: 'text-left'
                        }
                    });
                }
            }
        );
    });
    
    /**
     * Abre el modal para editar un proyecto
     */
    $(document).on('click', '.btn-editar-proyecto', function() {
        const proyectoId = $(this).data('id');
        const url = PROYECTOS_URLS.proyectoDetail(proyectoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const proyecto = response.data;
                    $('#modalProyectoLabel').text('Editar Proyecto');
                    $('#proyectoId').val(proyecto.id);
                    $('#proyectoTitulo').val(proyecto.titulo);
                    $('#proyectoResumen').val(proyecto.resumen || '');
                    $('#proyectoDescripcion').val(proyecto.descripcion || '');
                    $('#proyectoEstado').val(proyecto.estado);
                    $('#proyectoVisibilidad').val(proyecto.visibilidad);
                    
                    // Cargar autores
                    $('#autoresContainer').empty();
                    autorCounter = 0; // Resetear contador
                    if (proyecto.autores && proyecto.autores.length > 0) {
                        // Esperar a que se carguen los usuarios antes de renderizar
                        loadUsuariosForSelect(function() {
                            proyecto.autores.forEach(function(autor) {
                                renderAutorInput(autor);
                            });
                        });
                    }
                    
                    // Cargar tipos de proyecto y seleccionar el actual
                    loadTiposProyectoForSelect('#proyectoTipoProyecto');
                    
                    // Cargar campos dinámicos y sus valores
                    setTimeout(function() {
                        $('#proyectoTipoProyecto').val(proyecto.tipo_proyecto_id);
                        loadCamposDinamicos(proyecto.tipo_proyecto_id);
                        
                        // Después de cargar los campos, poblar los valores
                        setTimeout(function() {
                            if (proyecto.valores_campos) {
                                Object.keys(proyecto.valores_campos).forEach(function(campoSlug) {
                                    const valores = proyecto.valores_campos[campoSlug];
                                    const campoItem = $(`.campo-dinamico-item[data-campo-slug="${campoSlug}"]`);
                                    
                                    if (campoItem.length > 0) {
                                        const repetible = campoItem.data('repetible');
                                        
                                        if (repetible && valores.length > 1) {
                                            // Campo repetible con múltiples valores
                                            valores.forEach(function(valorObj, index) {
                                                if (index === 0) {
                                                    // Primer valor ya existe
                                                    campoItem.find('.campo-repetible-item:first input, .campo-repetible-item:first textarea, .campo-repetible-item:first select').first().val(valorObj.valor);
                                                } else {
                                                    // Agregar valores adicionales
                                                    const btnAgregar = campoItem.find('.btn-agregar-valor');
                                                    btnAgregar.click();
                                                    setTimeout(function() {
                                                        const nuevoItem = campoItem.find('.campo-repetible-item').last();
                                                        nuevoItem.find('input, textarea, select').first().val(valorObj.valor);
                                                    }, 100);
                                                }
                                            });
                                        } else {
                                            // Campo no repetible o primer valor
                                            const valor = valores[0].valor;
                                            const input = campoItem.find('input, textarea, select').first();
                                            
                                            if (input.is('input[type="checkbox"]')) {
                                                input.prop('checked', valor === true || valor === '1' || valor === 1);
                                            } else if (input.is('select[multiple]')) {
                                                input.val(valor);
                                            } else {
                                                input.val(valor);
                                            }
                                        }
                                    }
                                });
                            }
                        }, 500);
                    }, 300);
                    
                    $('#modalProyecto').modal('show');
                }
            }
        );
    });
    
    /**
     * Elimina un proyecto
     */
    $(document).on('click', '.btn-eliminar-proyecto', function() {
        const proyectoId = $(this).data('id');
        const proyectoTitulo = $(this).data('titulo');
        const url = PROYECTOS_URLS.proyectoDelete(proyectoId);
        
        Swal.fire({
            icon: 'warning',
            title: '¿Está seguro?',
            text: `¿Desea eliminar el proyecto "${proyectoTitulo}"?`,
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
                                text: response.message || 'Proyecto eliminado correctamente',
                                timer: 2000,
                                showConfirmButton: false
                            });
                            tableProyectos.ajax.reload(null, false);
                        }
                    }
                );
            }
        });
    });
    
    /**
     * Ver proyectos de un tipo específico
     */
    $(document).on('click', '.btn-ver-proyectos-tipo', function() {
        const tipoId = $(this).data('id');
        const tipoNombre = $(this).data('nombre');
        const url = PROYECTOS_URLS.proyectosPorTipo(tipoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    const proyectos = response.data;
                    let proyectosHtml = '<div class="text-left"><p><strong>Proyectos de tipo:</strong> ' + tipoNombre + '</p>';
                    proyectosHtml += '<ul class="list-group">';
                    
                    if (proyectos.length === 0) {
                        proyectosHtml += '<li class="list-group-item">No hay proyectos de este tipo</li>';
                    } else {
                        proyectos.forEach(function(proyecto) {
                            proyectosHtml += `
                                <li class="list-group-item">
                                    <strong>${proyecto.titulo}</strong> - 
                                    <span class="badge badge-info">${proyecto.estado_display}</span>
                                    <br>
                                    <small>Creado por: ${proyecto.creador_nombre} | Fecha: ${new Date(proyecto.fecha_creacion).toLocaleDateString('es-ES')}</small>
                                </li>
                            `;
                        });
                    }
                    proyectosHtml += '</ul></div>';
                    
                    Swal.fire({
                        icon: 'info',
                        title: `Proyectos: ${tipoNombre}`,
                        html: proyectosHtml,
                        confirmButtonText: 'Cerrar',
                        width: '700px'
                    });
                }
            }
        );
    });
    
    /**
     * Abre el modal para crear un nuevo proyecto
     */
    $(document).on('click', '#btnCrearProyecto', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('Botón crear proyecto clickeado');
        
        if ($('#modalProyecto').length === 0) {
            console.error('Modal #modalProyecto no encontrado');
            return false;
        }
        
        $('#modalProyectoLabel').text('Nuevo Proyecto');
        $('#formProyecto')[0].reset();
        $('#proyectoId').val('');
        $('#proyectoEstado').val('borrador');
        $('#autoresContainer').empty(); // Limpiar autores
        autorCounter = 0; // Resetear contador de autores
        $('#proyectoVisibilidad').val('publico');
        $('#camposDinamicosContainer').empty();
        $('#camposDinamicosContainer').html('<p class="text-muted">Seleccione un tipo de proyecto para cargar los campos dinámicos</p>');
        camposDinamicosCache = [];
        loadTiposProyectoForSelect('#proyectoTipoProyecto');
        $('#modalProyecto').modal('show');
        
        return false;
    });
    
    /**
     * Carga los campos dinámicos cuando se selecciona un tipo de proyecto
     */
    $('#proyectoTipoProyecto').on('change', function() {
        const tipoProyectoId = $(this).val();
        if (tipoProyectoId) {
            loadCamposDinamicos(tipoProyectoId);
        } else {
            $('#camposDinamicosContainer').html('<p class="text-muted">Seleccione un tipo de proyecto para cargar los campos dinámicos</p>');
        }
    });
    
    /**
     * Carga los campos dinámicos de un tipo de proyecto
     */
    function loadCamposDinamicos(tipoProyectoId) {
        const url = PROYECTOS_URLS.camposPorTipoProyecto(tipoProyectoId);
        
        ajaxRequest(
            url,
            'GET',
            null,
            function(response) {
                if (response.success) {
                    renderCamposDinamicos(response.data);
                }
            }
        );
    }
    
    /**
     * Renderiza los campos dinámicos en el formulario
     */
    function renderCamposDinamicos(campos) {
        const container = $('#camposDinamicosContainer');
        container.empty();
        
        // Guardar en cache
        camposDinamicosCache = campos;
        
        if (campos.length === 0) {
            container.html('<p class="text-muted">Este tipo de proyecto no tiene campos dinámicos configurados</p>');
            return;
        }
        
        // Agrupar campos por categoría
        const camposPorCategoria = {};
        campos.forEach(function(campo) {
            const categoria = campo.categoria || 'General';
            if (!camposPorCategoria[categoria]) {
                camposPorCategoria[categoria] = [];
            }
            camposPorCategoria[categoria].push(campo);
        });
        
        // Renderizar campos por categoría
        Object.keys(camposPorCategoria).sort().forEach(function(categoria) {
            const camposCategoria = camposPorCategoria[categoria];
            
            // Card para la categoría
            let categoriaHtml = '<div class="campo-dinamico-group">';
            if (categoria !== 'General') {
                categoriaHtml += `<div class="campo-dinamico-categoria">${escapeHtml(categoria)}</div>`;
            }
            
            camposCategoria.forEach(function(campo) {
                categoriaHtml += renderCampoDinamico(campo);
            });
            
            categoriaHtml += '</div>';
            container.append(categoriaHtml);
        });
        
        // Aplicar estilos según el tema después de renderizar
        applyThemeToDynamicFields();
    }
    
    /**
     * Aplica estilos según el tema a los campos dinámicos
     */
    function applyThemeToDynamicFields() {
        const isDark = isDarkMode();
        
        // Aplicar estilos a todos los inputs, textareas y selects
        $('.campo-dinamico-item input[type="text"], .campo-dinamico-item input[type="number"], .campo-dinamico-item input[type="date"], .campo-dinamico-item input[type="url"], .campo-dinamico-item input[type="email"], .campo-dinamico-item textarea, .campo-dinamico-item select').each(function() {
            if (isDark) {
                $(this).css({
                    'background-color': '#495057',
                    'color': '#e9ecef',
                    'border-color': '#6c757d'
                });
            } else {
                $(this).css({
                    'background-color': '#ffffff',
                    'color': '#495057',
                    'border-color': '#ced4da'
                });
            }
        });
    }
    
    /**
     * Renderiza un campo dinámico individual
     */
    function renderCampoDinamico(campo) {
        const campoId = `campo_dinamico_${campo.slug}`;
        const campoName = `campos_dinamicos[${campo.slug}]`;
        const required = campo.es_obligatorio ? 'required' : '';
        const ayudaHtml = campo.ayuda ? `<small class="form-text text-muted">${escapeHtml(campo.ayuda)}</small>` : '';
        
        let campoHtml = `<div class="form-group campo-dinamico-item" data-campo-slug="${campo.slug}" data-tipo-dato="${campo.tipo_dato}" data-repetible="${campo.es_repetible}">`;
        campoHtml += `<label for="${campoId}" style="color: #495057; font-weight: 500;">${escapeHtml(campo.etiqueta)} ${campo.es_obligatorio ? '<span class="text-danger">*</span>' : ''}</label>`;
        
        // Renderizar según el tipo de dato
        if (campo.es_repetible) {
            // Campo repetible
            campoHtml += `<div class="campo-repetible-container" id="repetible_${campo.slug}">`;
            campoHtml += `<div class="campo-repetible-item">`;
            campoHtml += renderInputCampo(campo, campoId, campoName, required, 0);
            campoHtml += `</div>`;
            campoHtml += '</div>';
            campoHtml += `<button type="button" class="btn btn-sm btn-success btn-agregar-valor" data-campo-slug="${campo.slug}">`;
            campoHtml += '<i class="fas fa-plus"></i> Agregar otro valor</button>';
        } else {
            // Campo no repetible
            campoHtml += renderInputCampo(campo, campoId, campoName, required, 0);
        }
        
        campoHtml += ayudaHtml;
        campoHtml += '</div>';
        
        return campoHtml;
    }
    
    /**
     * Detecta si el tema oscuro está activo
     */
    function isDarkMode() {
        return document.body.classList.contains('dark-mode');
    }
    
    /**
     * Obtiene los estilos para inputs según el tema
     */
    function getInputStyles() {
        if (isDarkMode()) {
            return 'background-color: #495057 !important; color: #e9ecef !important; border-color: #6c757d !important;';
        } else {
            return 'background-color: #ffffff; color: #495057; border-color: #ced4da;';
        }
    }
    
    /**
     * Obtiene el color del texto según el tema
     */
    function getTextColor() {
        return isDarkMode() ? '#e9ecef' : '#495057';
    }
    
    /**
     * Renderiza el input según el tipo de dato
     */
    function renderInputCampo(campo, campoId, campoName, required, indice) {
        const valorDefecto = campo.valor_por_defecto || '';
        const campoIdFull = campo.es_repetible ? `${campoId}_${indice}` : campoId;
        const campoNameFull = campo.es_repetible ? `${campoName}[]` : campoName;
        const inputStyles = getInputStyles();
        const textColor = getTextColor();
        let inputHtml = '';
        
        switch(campo.tipo_dato) {
            case 'texto':
                inputHtml = `<input type="text" class="form-control" id="${campoIdFull}" name="${campoNameFull}" value="${escapeHtml(valorDefecto)}" ${required} />`;
                break;
            case 'textarea':
                inputHtml = `<textarea class="form-control" id="${campoIdFull}" name="${campoNameFull}" rows="3" ${required}>${escapeHtml(valorDefecto)}</textarea>`;
                break;
            case 'numero':
                inputHtml = `<input type="number" class="form-control" id="${campoIdFull}" name="${campoNameFull}" value="${escapeHtml(valorDefecto)}" step="any" ${required} />`;
                break;
            case 'fecha':
                inputHtml = `<input type="date" class="form-control" id="${campoIdFull}" name="${campoNameFull}" value="${escapeHtml(valorDefecto)}" ${required} />`;
                break;
            case 'booleano':
                const checked = valorDefecto === 'true' || valorDefecto === '1' ? 'checked' : '';
                inputHtml = `<div class="form-check">`;
                inputHtml += `<input type="checkbox" class="form-check-input" id="${campoIdFull}" name="${campoNameFull}" value="1" ${checked} />`;
                inputHtml += `<label class="form-check-label" for="${campoIdFull}">Sí</label>`;
                inputHtml += `</div>`;
                break;
            case 'select':
                inputHtml = `<select class="form-control" id="${campoIdFull}" name="${campoNameFull}" ${required}>`;
                inputHtml += '<option value="">Seleccione...</option>';
                if (campo.valores_posibles && Array.isArray(campo.valores_posibles)) {
                    campo.valores_posibles.forEach(function(opcion) {
                        const selected = opcion === valorDefecto ? 'selected' : '';
                        inputHtml += `<option value="${escapeHtml(opcion)}" ${selected}>${escapeHtml(opcion)}</option>`;
                    });
                }
                inputHtml += '</select>';
                break;
            case 'multiselect':
                inputHtml = `<select class="form-control" id="${campoIdFull}" name="${campoNameFull}" multiple ${required}>`;
                if (campo.valores_posibles && Array.isArray(campo.valores_posibles)) {
                    campo.valores_posibles.forEach(function(opcion) {
                        const selected = campo.valor_por_defecto && campo.valor_por_defecto.includes(opcion) ? 'selected' : '';
                        inputHtml += `<option value="${escapeHtml(opcion)}" ${selected}>${escapeHtml(opcion)}</option>`;
                    });
                }
                inputHtml += '</select>';
                break;
            case 'url':
                inputHtml = `<input type="url" class="form-control" id="${campoIdFull}" name="${campoNameFull}" value="${escapeHtml(valorDefecto)}" ${required} />`;
                break;
            case 'email':
                inputHtml = `<input type="email" class="form-control" id="${campoIdFull}" name="${campoNameFull}" value="${escapeHtml(valorDefecto)}" ${required} />`;
                break;
            case 'json':
                inputHtml = `<textarea class="form-control json-input" id="${campoIdFull}" name="${campoNameFull}" rows="3" ${required}>${escapeHtml(valorDefecto)}</textarea>`;
                break;
            default:
                inputHtml = `<input type="text" class="form-control" id="${campoIdFull}" name="${campoNameFull}" value="${escapeHtml(valorDefecto)}" ${required} />`;
        }
        
        // Si es repetible y no es el primer item, agregar botón de eliminar
        if (campo.es_repetible && indice > 0) {
            inputHtml = `<div class="input-group">${inputHtml}`;
            inputHtml += `<div class="input-group-append">`;
            inputHtml += `<button type="button" class="btn btn-danger btn-sm btn-eliminar-valor" data-campo-slug="${campo.slug}" data-indice="${indice}" title="Eliminar">`;
            inputHtml += '<i class="fas fa-times"></i></button>';
            inputHtml += `</div></div>`;
        }
        
        return inputHtml;
    }
    
    /**
     * Agrega un valor adicional a un campo repetible
     */
    $(document).on('click', '.btn-agregar-valor', function() {
        const campoSlug = $(this).data('campo-slug');
        const container = $(this).siblings('.campo-repetible-container');
        const campoItem = $(this).closest('.campo-dinamico-item');
        const tipoDato = campoItem.data('tipo-dato');
        const repetible = campoItem.data('repetible');
        
        // Obtener información del campo
        const campo = camposDinamicosCache.find(c => c.slug === campoSlug);
        if (!campo) return;
        
        // Contar cuántos valores hay
        const indice = container.children('.campo-repetible-item').length;
        
        // Crear nuevo item
        const campoId = `campo_dinamico_${campoSlug}_${indice}`;
        const campoName = `campos_dinamicos[${campoSlug}][]`;
        const required = campo.es_obligatorio ? 'required' : '';
        
        // Crear nuevo item con estilos inline para asegurar tema claro
        const nuevoItem = $('<div class="campo-repetible-item" style="margin-bottom: 0.5rem; padding: 0.75rem; background-color: #ffffff; border: 1px solid #ced4da; border-radius: 0.25rem;"></div>');
        const campoHtml = renderInputCampo(campo, `campo_dinamico_${campoSlug}`, `campos_dinamicos[${campoSlug}]`, required, indice);
        nuevoItem.html(campoHtml);
        container.append(nuevoItem);
        
        // Asegurar que los inputs dentro tengan estilos claros aplicados
        nuevoItem.find('input, textarea, select').each(function() {
            $(this).attr('style', $(this).attr('style') + '; background-color: #ffffff !important; color: #495057 !important;');
        });
    });
    
    /**
     * Elimina un valor de un campo repetible
     */
    $(document).on('click', '.btn-eliminar-valor', function() {
        $(this).closest('.campo-repetible-item').remove();
    });
    
    /**
     * Cache de campos dinámicos
     */
    let camposDinamicosCache = [];
    
    /**
     * Contador de autores para IDs únicos
     */
    let autorCounter = 0;
    
    /**
     * Cache de usuarios para select
     */
    let usuariosCache = [];
    
    /**
     * Carga los usuarios para el select
     */
    function loadUsuariosForSelect(callback) {
        if (usuariosCache.length > 0) {
            if (callback) callback(usuariosCache);
            return;
        }
        
        ajaxRequest(
            PROYECTOS_URLS.usuariosForSelect,
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
     * Renderiza un autor en el contenedor
     */
    function renderAutorInput(autor = null) {
        const autorId = autor ? autor.id : `new_${autorCounter++}`;
        const usuarioId = autor ? autor.usuario_id : '';
        const usuarioNombre = autor ? escapeHtml(autor.usuario_nombre || autor.nombre_completo) : '';
        const afiliacion = autor ? escapeHtml(autor.afiliacion || '') : '';
        const orcidId = autor ? escapeHtml(autor.orcid_id || '') : '';
        const ordenAutor = autor ? autor.orden_autor : 1;
        const esCorrespondiente = autor ? autor.es_correspondiente : false;
        const esAutorPrincipal = autor ? autor.es_autor_principal : false;
        
        // Cargar usuarios y crear el select
        loadUsuariosForSelect(function(usuarios) {
            let selectHtml = '<option value="">Seleccione un usuario...</option>';
            usuarios.forEach(function(usuario) {
                const selected = usuario.id == usuarioId ? 'selected' : '';
                selectHtml += `<option value="${usuario.id}" ${selected} data-email="${escapeHtml(usuario.email)}" data-first-name="${escapeHtml(usuario.first_name)}" data-last-name="${escapeHtml(usuario.last_name)}">${escapeHtml(usuario.text)}</option>`;
            });
            
            const html = `
                <div class="autor-item border p-3 mb-2 rounded" data-autor-id="${autorId}">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Usuario <span class="text-danger">*</span></label>
                                <select class="form-control autor-usuario" required>
                                    ${selectHtml}
                                </select>
                                <small class="form-text text-muted">Seleccione un usuario del sistema</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Orden</label>
                                <input type="number" class="form-control autor-orden" value="${ordenAutor}" min="1">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>&nbsp;</label>
                                <button type="button" class="btn btn-sm btn-danger btn-block btn-eliminar-autor">
                                    <i class="fas fa-trash"></i> Eliminar
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Afiliación (opcional)</label>
                                <input type="text" class="form-control autor-afiliacion" value="${afiliacion}" placeholder="Se usará la del usuario si no se especifica">
                                <small class="form-text text-muted">Sobrescribe la afiliación del usuario</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>ORCID ID (opcional)</label>
                                <input type="text" class="form-control autor-orcid" value="${orcidId}" placeholder="Se usará el del usuario si no se especifica">
                                <small class="form-text text-muted">Sobrescribe el ORCID del usuario</small>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input autor-correspondiente" ${esCorrespondiente ? 'checked' : ''}>
                                <label class="form-check-label">Autor de correspondencia</label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input autor-principal" ${esAutorPrincipal ? 'checked' : ''}>
                                <label class="form-check-label">Autor principal</label>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            $('#autoresContainer').append(html);
        });
    }
    
    /**
     * Agregar autor
     */
    $(document).on('click', '#btnAgregarAutor', function() {
        renderAutorInput();
    });
    
    /**
     * Eliminar autor
     */
    $(document).on('click', '.btn-eliminar-autor', function() {
        $(this).closest('.autor-item').remove();
    });
    
    /**
     * Obtener datos de autores del formulario
     */
    function getAutoresData() {
        const autores = [];
        $('#autoresContainer .autor-item').each(function(index) {
            const $item = $(this);
            const autorId = $item.data('autor-id');
            const usuarioId = $item.find('.autor-usuario').val();
            
            if (usuarioId) {
                autores.push({
                    id: autorId && autorId.toString().startsWith('new_') ? null : autorId,
                    usuario_id: parseInt(usuarioId),
                    afiliacion: $item.find('.autor-afiliacion').val().trim() || null,
                    orcid_id: $item.find('.autor-orcid').val().trim() || null,
                    orden_autor: parseInt($item.find('.autor-orden').val()) || (index + 1),
                    es_correspondiente: $item.find('.autor-correspondiente').is(':checked'),
                    es_autor_principal: $item.find('.autor-principal').is(':checked'),
                });
            }
        });
        return autores;
    }
    
    /**
     * Maneja el envío del formulario de proyecto
     */
    $(document).on('submit', '#formProyecto', function(e) {
        e.preventDefault();
        
        const proyectoId = $('#proyectoId').val();
        const tipoProyectoId = $('#proyectoTipoProyecto').val();
        
        // Validar que se haya seleccionado un tipo de proyecto
        if (!tipoProyectoId) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'Debe seleccionar un tipo de proyecto',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        // Recolectar datos del formulario
        const formData = {
            titulo: $('#proyectoTitulo').val().trim(),
            tipo_proyecto_id: tipoProyectoId,
            resumen: $('#proyectoResumen').val().trim(),
            descripcion: $('#proyectoDescripcion').val().trim(),
            estado: $('#proyectoEstado').val(),
            visibilidad: $('#proyectoVisibilidad').val(),
            documento_id: $('#proyectoDocumento').val() || null,  // Documento existente (opcional)
            autores: getAutoresData(),
            campos_dinamicos: {}
        };
        
        // Validar título
        if (!formData.titulo) {
            Swal.fire({
                icon: 'warning',
                title: 'Validación',
                text: 'El título es obligatorio',
                confirmButtonText: 'Aceptar'
            });
            return;
        }
        
        // Recolectar valores de campos dinámicos
        $('.campo-dinamico-item').each(function() {
            const campoSlug = $(this).data('campo-slug');
            const tipoDato = $(this).data('tipo-dato');
            const repetible = $(this).data('repetible');
            
            if (repetible) {
                // Campo repetible: recolectar todos los valores
                const valores = [];
                $(this).find('.campo-repetible-item input, .campo-repetible-item textarea, .campo-repetible-item select').each(function() {
                    let valor = $(this).val();
                    if ($(this).is('input[type="checkbox"]')) {
                        valor = $(this).is(':checked') ? '1' : '0';
                    } else if ($(this).is('select[multiple]')) {
                        valor = $(this).val(); // Array de valores seleccionados
                    }
                    if (valor !== '' && valor !== null && valor !== undefined) {
                        valores.push(valor);
                    }
                });
                if (valores.length > 0) {
                    formData.campos_dinamicos[campoSlug] = valores;
                }
            } else {
                // Campo no repetible: un solo valor
                const input = $(this).find('input, textarea, select').first();
                let valor = input.val();
                
                if (input.is('input[type="checkbox"]')) {
                    valor = input.is(':checked') ? '1' : '0';
                } else if (input.is('select[multiple]')) {
                    valor = input.val(); // Array
                }
                
                if (valor !== '' && valor !== null && valor !== undefined) {
                    formData.campos_dinamicos[campoSlug] = valor;
                }
            }
        });
        
        // Enviar datos
        let url, method, sendData;
        if (proyectoId) {
            url = PROYECTOS_URLS.proyectoUpdate(proyectoId);
            method = 'POST';
            sendData = $.extend({}, formData, { _method: 'PUT' });
        } else {
            url = PROYECTOS_URLS.proyectoCreate;
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
                    $('#modalProyecto').modal('hide');
                    tableProyectos.ajax.reload(null, false);
                }
            }
        );
    });
    
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================
    
    // Cargar tipos de proyecto y documentos disponibles cuando se muestra el modal de proyecto
    $(document).on('show.bs.modal', '#modalProyecto', function() {
        loadTiposProyectoForSelect('#proyectoTipoProyecto');
        loadDocumentosDisponibles();
    });
    
    /**
     * Carga los documentos disponibles (sin proyecto) para el select
     */
    function loadDocumentosDisponibles() {
        $.ajax({
            url: '/repositorio/documentos/disponibles/',
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            success: function(response) {
                if (response.success) {
                    const select = $('#proyectoDocumento');
                    select.empty();
                    select.append('<option value="">Seleccione un documento existente (opcional)</option>');
                    
                    response.data.forEach(function(doc) {
                        const tieneArchivo = doc.tiene_archivo ? ' (con PDF)' : ' (sin PDF)';
                        select.append(
                            `<option value="${doc.id}">${escapeHtml(doc.titulo)}${tieneArchivo}</option>`
                        );
                    });
                }
            },
            error: function() {
                console.error('Error al cargar documentos disponibles');
            }
        });
    }
    
    // Cargar tipos de proyecto cuando se muestra el modal de campo (usar delegación)
    $(document).on('show.bs.modal', '#modalCampoTipoProyecto', function() {
        loadTiposProyectoForSelect('#campoTipoProyectoTipoProyecto');
    });
    
    // Función para inicializar una tabla solo si está visible
    function initializeTableIfVisible(tableId, initFunction, tableVar) {
        const $tabPane = $(tableId.replace('table', '#').toLowerCase().replace('tableproyectos', '#proyectos').replace('tabletiposproyecto', '#tipos-proyecto').replace('tablecampostipoproyecto', '#campos-tipo-proyecto'));
        const $table = $(tableId);
        
        if ($table.length === 0) {
            return false;
        }
        
        // Si el tab pane está activo y visible, inicializar
        if ($tabPane.length > 0 && ($tabPane.hasClass('active') || $tabPane.hasClass('show'))) {
            if (typeof initFunction === 'function') {
                try {
                    initFunction();
                    return true;
                } catch (error) {
                    console.error('Error al inicializar tabla ' + tableId + ':', error);
                    return false;
                }
            }
        }
        return false;
    }
    
    // Inicializar solo la tabla del tab activo al cargar la página
    try {
        // Detectar qué tab está activo
        const $activeTab = $('.nav-tabs .nav-link.active');
        const activeTabHref = $activeTab.length > 0 ? $activeTab.attr('href') : null;
        
        // Si no hay tab activo, activar el primero (proyectos)
        if (!activeTabHref) {
            const $firstTab = $('.nav-tabs .nav-link').first();
            if ($firstTab.length > 0) {
                $firstTab.tab('show');
            }
        }
        
        // Inicializar solo la tabla del tab activo
        if (activeTabHref === '#proyectos' || !activeTabHref) {
            if ($('#tableProyectos').length > 0 && typeof initTableProyectos === 'function') {
                // Pequeño delay para asegurar que el DOM esté listo
                setTimeout(function() {
                    try {
                        initTableProyectos();
                    } catch (error) {
                        console.error('Error al inicializar tabla proyectos:', error);
                    }
                }, 200);
            }
        } else if (activeTabHref === '#tipos-proyecto') {
            if ($('#tableTiposProyecto').length > 0 && typeof initTableTiposProyecto === 'function') {
                setTimeout(function() {
                    try {
                        initTableTiposProyecto();
                    } catch (error) {
                        console.error('Error al inicializar tabla tipos proyecto:', error);
                    }
                }, 200);
            }
        } else if (activeTabHref === '#campos-tipo-proyecto') {
            if ($('#tableCamposTipoProyecto').length > 0 && typeof initTableCamposTipoProyecto === 'function') {
                setTimeout(function() {
                    try {
                        initTableCamposTipoProyecto();
                    } catch (error) {
                        console.error('Error al inicializar tabla campos tipo proyecto:', error);
                    }
                }, 200);
            }
        }
    } catch (error) {
        console.error('Error al inicializar tablas:', error);
    }
    
    // Inicializar tablas cuando se cambia de tab (solo si no están inicializadas)
    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function(e) {
        const target = $(e.target).attr('href');
        // Esperar a que el tab esté completamente visible
        setTimeout(function() {
            try {
                if (target === '#proyectos') {
                    if ($('#tableProyectos').length > 0) {
                        if (typeof tableProyectos === 'undefined' || !tableProyectos) {
                            if (typeof initTableProyectos === 'function') {
                                initTableProyectos();
                            }
                        } else {
                            // Solo recalcular si la tabla ya está inicializada y el elemento existe
                            try {
                                if (tableProyectos && $('#tableProyectos').is(':visible') && tableProyectos.columns) {
                                    tableProyectos.columns.adjust().responsive.recalc();
                                }
                            } catch (err) {
                                console.warn('No se pudo recalcular tabla proyectos:', err);
                            }
                        }
                    }
                } else if (target === '#tipos-proyecto') {
                    if ($('#tableTiposProyecto').length > 0) {
                        if (typeof tableTiposProyecto === 'undefined' || !tableTiposProyecto) {
                            if (typeof initTableTiposProyecto === 'function') {
                                initTableTiposProyecto();
                            }
                        } else {
                            try {
                                if (tableTiposProyecto && $('#tableTiposProyecto').is(':visible') && tableTiposProyecto.columns) {
                                    tableTiposProyecto.columns.adjust().responsive.recalc();
                                }
                            } catch (err) {
                                console.warn('No se pudo recalcular tabla tipos proyecto:', err);
                            }
                        }
                    }
                } else if (target === '#campos-tipo-proyecto') {
                    if ($('#tableCamposTipoProyecto').length > 0) {
                        if (typeof tableCamposTipoProyecto === 'undefined' || !tableCamposTipoProyecto) {
                            if (typeof initTableCamposTipoProyecto === 'function') {
                                initTableCamposTipoProyecto();
                            }
                        } else {
                            try {
                                if (tableCamposTipoProyecto && $('#tableCamposTipoProyecto').is(':visible') && tableCamposTipoProyecto.columns) {
                                    tableCamposTipoProyecto.columns.adjust().responsive.recalc();
                                }
                            } catch (err) {
                                console.warn('No se pudo recalcular tabla campos tipo proyecto:', err);
                            }
                        }
                    }
                }
            } catch (error) {
                console.warn('Error al manejar cambio de tab (no crítico):', error);
            }
        }, 250); // Aumentar el delay para asegurar que el tab esté completamente visible
    });
    
    // Observar cambios en el tema (cuando se agrega/remueve la clase dark-mode)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                // Aplicar estilos cuando cambie el tema
                applyThemeToDynamicFields();
            }
        });
    });
    
    // Observar cambios en el body para detectar cambios de tema
    if (document.body) {
        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
    
    // Log para confirmar que el script se ejecutó
    console.log('✅ Script de proyectos inicializado correctamente');
    console.log('📋 Event listeners registrados para:', {
        btnCrearProyecto: $('#btnCrearProyecto').length > 0 ? '✓' : '✗',
        btnCrearTipoProyecto: $('#btnCrearTipoProyecto').length > 0 ? '✓' : '✗',
        btnCrearCampoTipoProyecto: $('#btnCrearCampoTipoProyecto').length > 0 ? '✓' : '✗',
        modalProyecto: $('#modalProyecto').length > 0 ? '✓' : '✗',
        modalTipoProyecto: $('#modalTipoProyecto').length > 0 ? '✓' : '✗',
        modalCampoTipoProyecto: $('#modalCampoTipoProyecto').length > 0 ? '✓' : '✗'
    });
}); // Fin de jQuery(document).ready
