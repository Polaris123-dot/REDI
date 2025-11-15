     
     console.log('Archivo paginate.js cargado correctamente');
     // Ejecutar la búsqueda cuando se escribe en el campo de búsqueda
        $('#search').on('keydown', function(event) {
            if (event.key === 'Enter') { // Verifica si la tecla presionada es "Enter"
                event.preventDefault(); // Evita el comportamiento predeterminado (como enviar un formulario)
                realizarBusqueda(); // Llama a la función de búsqueda
            }
        });

        // Ejecutar la búsqueda cuando se cambien los filtros
        $('#fecha-inicio, #fecha-fin, #autor-select, #asesor-select, #tema-select, #sede-select').on('change', function() {
            realizarBusqueda(); // Llamar a la función de búsqueda
        });

        function updatePagination(totalPages, currentPage) {
            const paginationControls = document.getElementById('pagination-controls');
            paginationControls.innerHTML = ''; // Limpiar controles anteriores

            // Función auxiliar para crear un elemento de página
            function createPageItem(page, isActive = false, isDisabled = false, label = null) {
                const li = document.createElement('li');
                li.classList.add('page-item');
                if (isActive) li.classList.add('active');
                if (isDisabled) li.classList.add('disabled');

                const a = document.createElement(isDisabled ? 'span' : 'a');
                a.classList.add('page-link');
                a.href = '#';
                a.dataset.page = page;
                a.innerHTML = label || page;

                li.appendChild(a);
                return li;
            }

            // Enlace a la página anterior
            paginationControls.appendChild(
                createPageItem(currentPage - 1, false, currentPage === 1, '&laquo;')
            );

            // Mostrar las páginas alrededor de la actual
            const range = 4;
            const startPage = Math.max(1, currentPage - range);
            const endPage = Math.min(totalPages, currentPage + range);

            // Enlace a la primera página con "..."
            if (startPage > 1) {
                paginationControls.appendChild(createPageItem(1));
                if (startPage > 2) {
                    paginationControls.appendChild(createPageItem(null, false, true, '...'));
                }
            }

            // Enlaces a las páginas del rango calculado
            for (let i = startPage; i <= endPage; i++) {
                paginationControls.appendChild(createPageItem(i, i === currentPage));
            }

            // Enlace a la última página con "..."
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    paginationControls.appendChild(createPageItem(null, false, true, '...'));
                }
                paginationControls.appendChild(createPageItem(totalPages));
            }

            // Enlace a la página siguiente
            paginationControls.appendChild(
                createPageItem(currentPage + 1, false, currentPage === totalPages, '&raquo;')
            );
        }

        // Manejar clic en los enlaces de paginación
        $(document).on('click', '.page-link', function(e) {
            e.preventDefault(); // Evitar la acción por defecto del enlace
            currentPage = $(this).data('page'); // Obtener el número de página
            realizarBusqueda(); // Volver a realizar la búsqueda
        });