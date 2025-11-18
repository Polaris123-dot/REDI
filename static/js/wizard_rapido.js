/**
 * Wizard Rápido - Crear Documento, Archivo, Proyecto y Publicación
 */

// Esperar a que jQuery esté disponible
(function() {
    'use strict';
    
    // Función para inicializar cuando jQuery esté disponible
    function initWizard() {
        if (typeof jQuery === 'undefined') {
            // Si jQuery no está disponible, intentar de nuevo en 100ms
            setTimeout(initWizard, 100);
            return;
        }
        
        // jQuery está disponible, usar $ localmente
        var $ = jQuery;
        
        let currentStep = 1;
        const totalSteps = 3;
        let wizardData = {
            documento: null,
            archivo: null,
            proyecto: null,
            publicacion: null
        };
        
        // Lista de autores agregados
        let autoresList = [];
        
        // Slug generado para la publicación
        let slugGenerado = null;

        // URLs de las APIs
        const WIZARD_URLS = {
            tiposRecurso: '/repositorio/tipos-recurso/para-select/',
            colecciones: '/repositorio/colecciones/para-select/',
            tiposProyecto: '/proyectos/tipos-proyecto/select/',
            usuarios: '/repositorio/usuarios/para-select/',
            categorias: '/publicaciones/categorias/para-select/',
            etiquetas: '/publicaciones/etiquetas/para-select/',
            generarSlugPreview: '/publicaciones/generar-slug-preview/',
            crearDocumento: '/repositorio/documentos/crear/',
            crearAutor: '/repositorio/autores/crear/',
            crearProyecto: '/proyectos/crear/',
            crearPublicacion: '/publicaciones/crear/'
        };

        // Función para obtener el token CSRF
        function getCSRFToken() {
            return $('[name=csrfmiddlewaretoken]').val() || $('input[name="csrfmiddlewaretoken"]').val();
        }

        // Función para escapar HTML
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text ? text.replace(/[&<>"']/g, m => map[m]) : '';
        }

        // Cargar datos iniciales
        function loadInitialData() {
            // Cargar tipos de recurso
            $.ajax({
                url: WIZARD_URLS.tiposRecurso,
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function(response) {
                    if (response.success) {
                        const select = $('#wizardTipoRecurso');
                        select.empty();
                        select.append('<option value="">Seleccione un tipo</option>');
                        response.data.forEach(function(tipo) {
                            select.append(`<option value="${tipo.id}">${escapeHtml(tipo.nombre)}</option>`);
                        });
                    }
                },
                error: function() {
                    console.error('Error al cargar tipos de recurso');
                }
            });

            // Cargar colecciones
            $.ajax({
                url: WIZARD_URLS.colecciones,
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function(response) {
                    if (response.success) {
                        const select = $('#wizardColeccion');
                        select.empty();
                        select.append('<option value="">Seleccione una colección</option>');
                        response.data.forEach(function(coleccion) {
                            select.append(`<option value="${coleccion.id}">${escapeHtml(coleccion.nombre)}</option>`);
                        });
                    }
                },
                error: function() {
                    console.error('Error al cargar colecciones');
                }
            });

            // Cargar tipos de proyecto
            $.ajax({
                url: WIZARD_URLS.tiposProyecto,
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function(response) {
                    if (response.success) {
                        const select = $('#wizardTipoProyecto');
                        select.empty();
                        select.append('<option value="">Seleccione un tipo de proyecto</option>');
                        response.data.forEach(function(tipo) {
                            select.append(`<option value="${tipo.id}">${escapeHtml(tipo.nombre)}</option>`);
                        });
                    }
                },
                error: function() {
                    console.error('Error al cargar tipos de proyecto');
                }
            });
            
            // Cargar usuarios para autores
            $.ajax({
                url: WIZARD_URLS.usuarios,
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function(response) {
                    if (response.success) {
                        const select = $('#autorUsuarioSelect');
                        select.empty();
                        select.append('<option value="">Seleccione un usuario</option>');
                        response.data.forEach(function(usuario) {
                            select.append(`<option value="${usuario.id}">${escapeHtml(usuario.nombre)}</option>`);
                        });
                    }
                },
                error: function() {
                    console.error('Error al cargar usuarios');
                }
            });
            
            // Cargar categorías
            $.ajax({
                url: WIZARD_URLS.categorias,
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function(response) {
                    if (response.success) {
                        const select = $('#wizardCategorias');
                        select.empty();
                        response.data.forEach(function(categoria) {
                            select.append(`<option value="${categoria.id}">${escapeHtml(categoria.ruta_completa || categoria.nombre)}</option>`);
                        });
                        // Inicializar Select2
                        if ($.fn.select2) {
                            select.select2({
                                theme: 'bootstrap4',
                                placeholder: 'Seleccione categorías',
                                allowClear: true
                            });
                        }
                    }
                },
                error: function() {
                    console.error('Error al cargar categorías');
                }
            });
            
            // Cargar etiquetas
            $.ajax({
                url: WIZARD_URLS.etiquetas,
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                success: function(response) {
                    if (response.success) {
                        const select = $('#wizardEtiquetas');
                        select.empty();
                        response.data.forEach(function(etiqueta) {
                            select.append(`<option value="${etiqueta.id}">${escapeHtml(etiqueta.nombre)}</option>`);
                        });
                        // Inicializar Select2
                        if ($.fn.select2) {
                            select.select2({
                                theme: 'bootstrap4',
                                placeholder: 'Seleccione etiquetas',
                                allowClear: true
                            });
                        }
                    }
                },
                error: function() {
                    console.error('Error al cargar etiquetas');
                }
            });
        }
        
        // Mostrar lista de autores
        function renderAutoresList() {
            const container = $('#wizardAutoresList');
            container.empty();
            
            if (autoresList.length === 0) {
                container.html('<p class="text-muted">No hay autores agregados</p>');
                return;
            }
            
            autoresList.forEach(function(autor, index) {
                const isUsuario = autor.usuario_id !== null && autor.usuario_id !== undefined;
                const nombreCompleto = isUsuario ? autor.usuario_nombre : `${autor.nombre} ${autor.apellidos}`;
                const badge = isUsuario ? '<span class="badge badge-info">Usuario</span>' : '<span class="badge badge-secondary">No Usuario</span>';
                
                container.append(`
                    <div class="card mb-2" data-index="${index}">
                        <div class="card-body p-2">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${escapeHtml(nombreCompleto)}</strong> ${badge}
                                    <small class="text-muted d-block">Orden: ${autor.orden_autor}</small>
                                </div>
                                <button type="button" class="btn btn-sm btn-danger btn-eliminar-autor" data-index="${index}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `);
            });
        }
        
        // Agregar autor a la lista
        function agregarAutor(autorData) {
            autoresList.push(autorData);
            renderAutoresList();
        }
        
        // Eliminar autor de la lista
        function eliminarAutor(index) {
            autoresList.splice(index, 1);
            renderAutoresList();
        }
        
        // Crear autores en el documento (secuencialmente para evitar bloqueos de BD)
        function crearAutoresEnDocumento(documentoId) {
            return new Promise((resolve, reject) => {
                if (autoresList.length === 0) {
                    resolve();
                    return;
                }
                
                // Crear autores uno por uno secuencialmente
                let index = 0;
                
                function crearSiguienteAutor() {
                    if (index >= autoresList.length) {
                        resolve();
                        return;
                    }
                    
                    const autor = autoresList[index];
                    const autorIndex = index;
                    index++;
                    
                    // Si es autor-usuario, obtener nombre y apellidos del usuario
                    let nombre = autor.nombre || '';
                    let apellidos = autor.apellidos || '';
                    
                    if (autor.usuario_id) {
                        // Para autores-usuarios, el nombre viene del usuario
                        // Dividir el nombre completo del usuario
                        const nombreCompleto = autor.usuario_nombre || '';
                        const partes = nombreCompleto.split(' ');
                        if (partes.length > 0) {
                            nombre = partes[0];
                            apellidos = partes.slice(1).join(' ') || nombreCompleto;
                        } else {
                            nombre = nombreCompleto;
                            apellidos = '';
                        }
                    }
                    
                    const data = {
                        documento_id: documentoId,
                        nombre: nombre,
                        apellidos: apellidos,
                        email: autor.email || null,
                        afiliacion: autor.afiliacion || null,
                        orcid_id: autor.orcid_id || null,
                        orden_autor: autor.orden_autor || (autorIndex + 1),
                        es_correspondiente: autor.es_correspondiente || false,
                        es_autor_principal: autor.es_autor_principal || false,
                        usuario_id: autor.usuario_id || null
                    };
                    
                    $.ajax({
                        url: WIZARD_URLS.crearAutor,
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        },
                        data: JSON.stringify(data),
                        success: function(response) {
                            if (response.success) {
                                // Crear siguiente autor
                                crearSiguienteAutor();
                            } else {
                                reject(response.error || 'Error al crear autor');
                            }
                        },
                        error: function(xhr) {
                            let error = 'Error al crear autor';
                            if (xhr.responseJSON && xhr.responseJSON.error) {
                                error = xhr.responseJSON.error;
                            }
                            reject(error);
                        }
                    });
                }
                
                // Iniciar creación secuencial
                crearSiguienteAutor();
            });
        }
        

        // Actualizar paso actual
        function updateStep() {
            // Ocultar todos los pasos
            $('.wizard-step').addClass('d-none');
            
            // Mostrar paso actual
            $(`#step${currentStep}`).removeClass('d-none');
            
            // Actualizar barra de progreso
            const progress = (currentStep / totalSteps) * 100;
            $('#wizardProgress').css('width', progress + '%').text(`Paso ${currentStep} de ${totalSteps}`);
            
            // Actualizar botones
            if (currentStep === 1) {
                $('#btnWizardAnterior').hide();
            } else {
                $('#btnWizardAnterior').show();
            }
            
            if (currentStep === totalSteps) {
                $('#btnWizardSiguiente').hide();
                $('#btnWizardFinalizar').show();
            } else {
                $('#btnWizardSiguiente').show();
                $('#btnWizardFinalizar').hide();
            }
            
            // Inicializar Select2 en el paso 3 si es necesario
            if (currentStep === 3 && $.fn.select2) {
                // Reinicializar Select2 para categorías y etiquetas si no están inicializados
                if (!$('#wizardCategorias').hasClass('select2-hidden-accessible')) {
                    $('#wizardCategorias').select2({
                        theme: 'bootstrap4',
                        placeholder: 'Seleccione categorías',
                        allowClear: true
                    });
                }
                if (!$('#wizardEtiquetas').hasClass('select2-hidden-accessible')) {
                    $('#wizardEtiquetas').select2({
                        theme: 'bootstrap4',
                        placeholder: 'Seleccione etiquetas',
                        allowClear: true
                    });
                }
            }
        }

        // Validar paso actual
        function validateStep(step) {
            if (step === 1) {
                const titulo = $('#wizardTitulo').val().trim();
                if (!titulo) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'El título del documento es obligatorio'
                    });
                    return false;
                }
                const archivo = $('#wizardArchivo')[0].files[0];
                if (!archivo) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Debe seleccionar un archivo PDF'
                    });
                    return false;
                }
                if (archivo.type !== 'application/pdf') {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'El archivo debe ser un PDF'
                    });
                    return false;
                }
                return true;
            } else if (step === 2) {
                const tipoProyecto = $('#wizardTipoProyecto').val();
                if (!tipoProyecto) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'El tipo de proyecto es obligatorio'
                    });
                    return false;
                }
                return true;
            }
            return true;
        }

        // Procesar paso actual
        function processStep(step) {
            return new Promise((resolve, reject) => {
                if (step === 1) {
                    // Crear documento con archivo PDF
                    const archivo = $('#wizardArchivo')[0].files[0];
                    const formData = new FormData();
                    formData.append('titulo', $('#wizardTitulo').val().trim());
                    formData.append('resumen', $('#wizardResumen').val().trim() || '');
                    formData.append('tipo_recurso_id', $('#wizardTipoRecurso').val() || '');
                    formData.append('coleccion_id', $('#wizardColeccion').val() || '');
                    formData.append('archivo', archivo); // Archivo PDF
                    formData.append('csrfmiddlewaretoken', getCSRFToken());
                    
                    $.ajax({
                        url: WIZARD_URLS.crearDocumento,
                        method: 'POST',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(response) {
                            if (response.success) {
                                wizardData.documento = response.data;
                                // El archivo se crea automáticamente con el documento
                                wizardData.archivo = response.data.archivo || null;
                                
                                // Crear autores en el documento
                                crearAutoresEnDocumento(wizardData.documento.id).then(() => {
                                    resolve();
                                }).catch(error => {
                                    reject('Error al crear autores: ' + error);
                                });
                            } else {
                                reject(response.error || 'Error al crear documento');
                            }
                        },
                        error: function(xhr) {
                            let error = 'Error al crear documento';
                            if (xhr.responseJSON && xhr.responseJSON.error) {
                                error = xhr.responseJSON.error;
                            }
                            reject(error);
                        }
                    });
                } else if (step === 2) {
                    // Crear proyecto
                    // Filtrar solo autores-usuarios para el proyecto
                    const autoresUsuarios = autoresList.filter(function(autor) {
                        return autor.usuario_id !== null && autor.usuario_id !== undefined;
                    });
                    
                    const formData = new FormData();
                    formData.append('documento_id', wizardData.documento.id);
                    formData.append('tipo_proyecto_id', $('#wizardTipoProyecto').val());
                    formData.append('descripcion', $('#wizardDescripcionProyecto').val().trim() || '');
                    formData.append('estado', $('#wizardEstadoProyecto').val());
                    formData.append('visibilidad', $('#wizardVisibilidadProyecto').val());
                    formData.append('autores', JSON.stringify(autoresUsuarios.map(function(autor) {
                        return {
                            usuario_id: autor.usuario_id,
                            afiliacion: autor.afiliacion || '',
                            orcid_id: autor.orcid_id || '',
                            orden_autor: autor.orden_autor,
                            es_correspondiente: autor.es_correspondiente || false,
                            es_autor_principal: autor.es_autor_principal || false
                        };
                    })));
                    formData.append('csrfmiddlewaretoken', getCSRFToken());
                    
                    $.ajax({
                        url: WIZARD_URLS.crearProyecto,
                        method: 'POST',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(response) {
                            if (response.success) {
                                wizardData.proyecto = response.data;
                                resolve();
                            } else {
                                reject(response.error || 'Error al crear proyecto');
                            }
                        },
                        error: function(xhr) {
                            let error = 'Error al crear proyecto';
                            if (xhr.responseJSON && xhr.responseJSON.error) {
                                error = xhr.responseJSON.error;
                            }
                            reject(error);
                        }
                    });
                } else if (step === 3) {
                    // Crear publicación
                    // Obtener categorías seleccionadas
                    const categoriasSeleccionadas = $('#wizardCategorias').val() || [];
                    const categorias = categoriasSeleccionadas.map(function(id) {
                        return { id: parseInt(id) };
                    });
                    
                    // Obtener etiquetas seleccionadas
                    const etiquetasSeleccionadas = $('#wizardEtiquetas').val() || [];
                    const etiquetas = etiquetasSeleccionadas.map(function(id) {
                        return { id: parseInt(id) };
                    });
                    
                    // Extraer slug de la URL si existe, o usar el slug generado
                    let slugParaEnviar = slugGenerado;
                    const urlExterna = $('#wizardUrlExterna').val().trim();
                    if (urlExterna && !slugParaEnviar) {
                        // Intentar extraer el slug de la URL externa
                        const match = urlExterna.match(/\/publicacion\/([^\/]+)\/?/);
                        if (match && match[1]) {
                            slugParaEnviar = match[1];
                            console.log('Slug extraído de URL:', slugParaEnviar);
                        }
                    }
                    
                    // Si aún no hay slug, extraerlo de la URL externa si está presente
                    if (!slugParaEnviar && urlExterna) {
                        const urlMatch = urlExterna.match(/\/publicacion\/([^\/]+)\/?/);
                        if (urlMatch && urlMatch[1]) {
                            slugParaEnviar = urlMatch[1];
                            console.log('Slug extraído de URL externa:', slugParaEnviar);
                        }
                    }
                    
                    console.log('Slug que se enviará al crear publicación:', slugParaEnviar);
                    
                    const data = {
                        proyectos: [{
                            id: wizardData.proyecto.id,
                            orden: 1,
                            rol_en_publicacion: 'artículo principal'
                        }],
                        tipo_publicacion: $('#wizardTipoPublicacion').val(),
                        estado: $('#wizardEstadoPublicacion').val(),
                        fecha_publicacion: $('#wizardFechaPublicacion').val() || null,
                        url_externa: urlExterna || null,
                        categorias: categorias,
                        etiquetas: etiquetas,
                        slug: slugParaEnviar || null  // Enviar el slug exacto que se generó
                    };
                    
                    $.ajax({
                        url: WIZARD_URLS.crearPublicacion,
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        },
                        data: JSON.stringify(data),
                        success: function(response) {
                            if (response.success) {
                                wizardData.publicacion = response.data;
                                resolve();
                            } else {
                                reject(response.error || 'Error al crear publicación');
                            }
                        },
                        error: function(xhr) {
                            let error = 'Error al crear publicación';
                            if (xhr.responseJSON && xhr.responseJSON.error) {
                                error = xhr.responseJSON.error;
                            }
                            reject(error);
                        }
                    });
                }
            });
        }

        // Inicializar wizard cuando se abre el modal
        $(document).on('shown.bs.modal', '#modalWizardRapido', function() {
            currentStep = 1;
            wizardData = {
                documento: null,
                archivo: null,
                proyecto: null,
                publicacion: null
            };
            autoresList = [];
            slugGenerado = null;  // Resetear el slug al abrir el modal
            updateStep();
            loadInitialData();
        });

        // Botón Siguiente
        $(document).on('click', '#btnWizardSiguiente', function() {
            if (validateStep(currentStep)) {
                const btn = $(this);
                btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Procesando...');
                
                processStep(currentStep).then(() => {
                    currentStep++;
                    updateStep();
                    btn.prop('disabled', false).html('Siguiente <i class="fas fa-arrow-right"></i>');
                }).catch(error => {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: error
                    });
                    btn.prop('disabled', false).html('Siguiente <i class="fas fa-arrow-right"></i>');
                });
            }
        });

        // Botón Anterior
        $(document).on('click', '#btnWizardAnterior', function() {
            currentStep--;
            updateStep();
        });

        // Botón Finalizar
        $(document).on('click', '#btnWizardFinalizar', function() {
            if (validateStep(currentStep)) {
                const btn = $(this);
                btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Finalizando...');
                
                processStep(currentStep).then(() => {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Éxito!',
                        html: `
                            <p>Se ha completado el proceso exitosamente:</p>
                            <ul class="text-left">
                                <li><strong>Documento:</strong> ${escapeHtml(wizardData.documento.titulo || 'N/A')}</li>
                                <li><strong>Proyecto:</strong> ${escapeHtml(wizardData.proyecto.titulo || 'N/A')}</li>
                                <li><strong>Publicación:</strong> Creada exitosamente</li>
                            </ul>
                        `,
                        confirmButtonText: 'Aceptar'
                    }).then(() => {
                        $('#modalWizardRapido').modal('hide');
                        // Recargar la página o redirigir
                        window.location.reload();
                    });
                }).catch(error => {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: error
                    });
                    btn.prop('disabled', false).html('<i class="fas fa-check"></i> Finalizar');
                });
            }
        });

        // Preview del archivo PDF
        $(document).on('change', '#wizardArchivo', function() {
            const file = this.files[0];
            const preview = $('#wizardArchivoPreview');
            
            if (file) {
                if (file.type === 'application/pdf') {
                    const fileSize = (file.size / 1024 / 1024).toFixed(2);
                    preview.html(`
                        <div class="alert alert-info">
                            <i class="fas fa-file-pdf"></i> 
                            <strong>Archivo seleccionado:</strong> ${escapeHtml(file.name)} 
                            (${fileSize} MB)
                        </div>
                    `);
                } else {
                    preview.html(`
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle"></i> 
                            El archivo debe ser un PDF
                        </div>
                    `);
                    $(this).val('');
                }
            } else {
                preview.empty();
            }
        });

        // Resetear wizard al cerrar modal
        $(document).on('hidden.bs.modal', '#modalWizardRapido', function() {
            currentStep = 1;
            wizardData = {
                documento: null,
                archivo: null,
                proyecto: null,
                publicacion: null
            };
            autoresList = [];
            renderAutoresList();
            $('#formWizardRapido')[0].reset();
            $('#wizardArchivoPreview').empty();
            updateStep();
        });
        
        // Inicializar lista de autores cuando se abre el wizard
        $(document).on('shown.bs.modal', '#modalWizardRapido', function() {
            renderAutoresList();
        });
        
        // Abrir modal de agregar autor
        $(document).on('click', '#btnAgregarAutor', function() {
            $('#modalAgregarAutor').modal('show');
        });
        
        // Cambiar entre autor-usuario y autor-no-usuario
        $(document).on('change', 'input[name="autorTipo"]', function() {
            const tipo = $(this).val();
            if (tipo === 'usuario') {
                $('#autorUsuarioFields').show();
                $('#autorNoUsuarioFields').hide();
                $('#autorUsuarioSelect').prop('required', true);
                $('#autorNombre').prop('required', false);
                $('#autorApellidos').prop('required', false);
            } else {
                $('#autorUsuarioFields').hide();
                $('#autorNoUsuarioFields').show();
                $('#autorUsuarioSelect').prop('required', false);
                $('#autorNombre').prop('required', true);
                $('#autorApellidos').prop('required', true);
            }
        });
        
        // Enviar formulario de agregar autor
        $(document).on('submit', '#formAgregarAutor', function(e) {
            e.preventDefault();
            
            const tipo = $('input[name="autorTipo"]:checked').val();
            let autorData = {
                orden_autor: parseInt($('#autorOrden').val()) || 1,
                es_correspondiente: $('#autorCorrespondiente').is(':checked'),
                es_autor_principal: $('#autorPrincipal').is(':checked')
            };
            
            if (tipo === 'usuario') {
                const usuarioId = $('#autorUsuarioSelect').val();
                if (!usuarioId) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Debe seleccionar un usuario'
                    });
                    return;
                }
                
                // Obtener nombre del usuario seleccionado
                const usuarioOption = $('#autorUsuarioSelect option:selected');
                autorData.usuario_id = parseInt(usuarioId);
                autorData.usuario_nombre = usuarioOption.text();
                autorData.afiliacion = $('#autorUsuarioAfiliacion').val() || null;
                autorData.orcid_id = $('#autorUsuarioOrcid').val() || null;
            } else {
                const nombre = $('#autorNombre').val().trim();
                const apellidos = $('#autorApellidos').val().trim();
                
                if (!nombre || !apellidos) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'El nombre y los apellidos son obligatorios'
                    });
                    return;
                }
                
                autorData.usuario_id = null;
                autorData.nombre = nombre;
                autorData.apellidos = apellidos;
                autorData.email = $('#autorEmail').val() || null;
                autorData.afiliacion = $('#autorAfiliacion').val() || null;
                autorData.orcid_id = $('#autorOrcid').val() || null;
            }
            
            agregarAutor(autorData);
            $('#modalAgregarAutor').modal('hide');
            $('#formAgregarAutor')[0].reset();
            $('#autorUsuarioFields').show();
            $('#autorNoUsuarioFields').hide();
            $('input[name="autorTipo"][value="usuario"]').prop('checked', true);
        });
        
        // Eliminar autor de la lista
        $(document).on('click', '.btn-eliminar-autor', function() {
            const index = $(this).data('index');
            eliminarAutor(index);
        });
        
        // Botón Generar URL
        $(document).on('click', '#btnWizardGenerarUrl', function(e) {
            e.preventDefault();
            
            if (!wizardData.proyecto || !wizardData.proyecto.id) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Debe completar el paso 2 (Crear Proyecto) antes de generar la URL.',
                    confirmButtonText: 'Aceptar'
                });
                return;
            }
            
            const proyectoId = wizardData.proyecto.id;
            
            // Hacer petición al backend para obtener un slug de previsualización
            $.ajax({
                url: `${WIZARD_URLS.generarSlugPreview}?proyecto_id=${proyectoId}`,
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                success: function(response) {
                    if (response.success && response.slug_preview) {
                        // Guardar el slug generado EXACTAMENTE como viene del servidor
                        slugGenerado = response.slug_preview;
                        
                        const fullUrl = `${window.location.origin}/publicacion/${response.slug_preview}/`;
                        $('#wizardUrlExterna').val(fullUrl);
                        
                        // Mostrar el slug en consola para debugging
                        console.log('Slug generado y guardado:', slugGenerado);
                        
                        Swal.fire({
                            icon: 'success',
                            title: 'URL Generada',
                            text: 'La URL ha sido generada y colocada en el campo "URL Externa".',
                            toast: true,
                            position: 'top-end',
                            showConfirmButton: false,
                            timer: 3000,
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
                    Swal.fire({
                        icon: 'error',
                        title: 'Error de Comunicación',
                        text: 'No se pudo comunicar con el servidor para generar la URL.'
                    });
                }
            });
        });
    }
    
    // Iniciar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWizard);
    } else {
        initWizard();
    }
})();
