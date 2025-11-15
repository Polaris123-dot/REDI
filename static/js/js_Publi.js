// Función para seleccionar y mover etiquetas de la izquierda a la derecha
function selectTag(tagElement) {
    // Crear una copia del elemento de etiqueta seleccionado
    const tagCopy = tagElement.cloneNode(true);
    
    // Asignar una función para que pueda ser removida al hacer clic
    tagCopy.onclick = function() {
        removeTag(tagCopy);
    };
    
    // Agregar la etiqueta seleccionada a la columna de etiquetas seleccionadas
    document.getElementById("selectedTags").appendChild(tagCopy);
    
    // Remover la etiqueta original de la lista de disponibles
    tagElement.remove();
}

// Función para devolver etiquetas seleccionadas a la columna de disponibles
function removeTag(tagElement) {
    // Crear una copia de la etiqueta seleccionada
    const tagCopy = tagElement.cloneNode(true);

    // Asignar la función para que vuelva a poder ser seleccionada
    tagCopy.onclick = function() {
        selectTag(tagCopy);
    };
    
    // Agregar la etiqueta de vuelta a la lista de disponibles
    document.getElementById("availableTags").appendChild(tagCopy);

    // Remover la etiqueta de la lista de seleccionadas
    tagElement.remove();
}




let currentPage = 1; // Página actual que se está mostrando
function searchAuthor() {
    const query = document.getElementById("searchInput").value;
    const buscarAutoresUrl = Urls.buscar_autores();

    fetch(`${buscarAutoresUrl}?query=${query}&page=${currentPage}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(responseData => {
        console.log(responseData);

        const authors = responseData.data;
        const authorsContainer = document.getElementById("authorsContainer");
        authorsContainer.innerHTML = ""; // Limpiar el contenedor

        if (authors && authors.length > 0) {
            authors.forEach(author => {
                const card = document.createElement("div");
                card.className = "col-md-6 mb-3"; // Cada tarjeta ocupa 6 columnas en pantallas medianas
                card.innerHTML = `
                    <div class="author-card" data-author-id="${author.id}">
                        <div class="card-body">
                            <h3 class="profile-name">${author.nombre} ${author.apellidos}</h3>
                            <p class="profile-job">${author.job_title || "Trabajo no disponible"}</p>
                            <button class="btn btn-outline-success btn-sm" onclick="addProfile('${author.id}', '${author.nombre}', '${author.apellidos}', '${author.profile_image || "../../dist/img/user4-128x128.jpg"}', '${author.job_title || "Trabajo no disponible"}')">Seleccionar</button>
                        </div>
                    </div>
                `;
                authorsContainer.appendChild(card);
            });

            updatePaginationControls(responseData.pagination);
        } else {
            authorsContainer.innerHTML = "<p>No se encontraron autores.</p>";
        }
    })
    .catch(error => console.error('Error al buscar autores:', error));
}



function updatePaginationControls(pagination) {
    const paginationContainer = document.getElementById("paginationContainer");
    paginationContainer.innerHTML = ""; // Limpiar el contenedor

    if (pagination.has_previous) {
        const prevButton = document.createElement("button");
        prevButton.textContent = "Anterior";
        prevButton.className = "btn btn-secondary";
        prevButton.onclick = () => {
            currentPage--;
            searchAuthor(); // Cargar la página anterior
        };
        paginationContainer.appendChild(prevButton);
    }

    const pageIndicator = document.createElement("span");
    pageIndicator.textContent = `Página ${pagination.current_page} de ${pagination.total_pages}`;
    paginationContainer.appendChild(pageIndicator);

    if (pagination.has_next) {
        const nextButton = document.createElement("button");
        nextButton.textContent = "Siguiente";
        nextButton.className = "btn btn-secondary";
        nextButton.onclick = () => {
            currentPage++;
            searchAuthor(); // Cargar la página siguiente
        };
        paginationContainer.appendChild(nextButton);
    }
}


let autoresSeleccionados = [];

function addProfile(authorId, nombre, apellidos, profileImage, jobTitle) {
    // Verificar si el autor ya está en la lista para evitar duplicados
    if (!autoresSeleccionados.includes(authorId)) {
        autoresSeleccionados.push(authorId); // Agregar el ID del autor al arreglo
    }

    // Verificar y agregar el perfil a la primera tarjeta disponible
    if (document.getElementById("targetCard1").classList.contains("d-none")) {
        document.getElementById("targetCard1").classList.remove("d-none");
        document.getElementById("targetName1").innerText = `${nombre} ${apellidos}`;
        document.getElementById("targetJob1").innerText = jobTitle;
        document.getElementById("targetImg1").src = profileImage;
    } else if (document.getElementById("targetCard2").classList.contains("d-none")) {
        document.getElementById("targetCard2").classList.remove("d-none");
        document.getElementById("targetName2").innerText = `${nombre} ${apellidos}`;
        document.getElementById("targetJob2").innerText = jobTitle;
        document.getElementById("targetImg2").src = profileImage;
    } else {
        alert("No hay cuadros disponibles para agregar el perfil.");
    }

    console.log("Autores seleccionados:", autoresSeleccionados); // Muestra los IDs en la consola
}

// Guardar los IDs de etiquetas y autores seleccionados al hacer clic en un solo botón
function guardarEtiquetasSeleccionadas() {
    // Capturar IDs de autores seleccionados
    console.log("Autores seleccionados:", autoresSeleccionados);

    // Capturar IDs de etiquetas seleccionadas
    const selectedTags = document.getElementById("selectedTags").children;
    const etiquetasSeleccionadas = Array.from(selectedTags).map(tag => tag.getAttribute("data-tag-id"));
    console.log("Etiquetas seleccionadas:", etiquetasSeleccionadas);

    // Llamar a la función para enviar los datos al servidor
    enviarAlServidor(autoresSeleccionados, etiquetasSeleccionadas);
}

function enviarAlServidor(autores, etiquetas) {
    // Define la URL del servidor donde se enviarán los datos
    
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        // Seleccionar el elemento por su ID
    const infoBox = document.getElementById("id_proyecto");
    const id_proyecto = infoBox.getAttribute("data-tag-id");
    
    // Estructura los datos en el formato adecuado
    const datos = {
        autoresSeleccionados: autores,
        etiquetasSeleccionadas: etiquetas,
        id_proyecto: id_proyecto
    };
    console.log(datos)

    // Realiza la solicitud al servidor
    const buscarPublicacionesUrl = '/Proyectos/api/publicaciones/';
 // Usando django_js_reverse

    console.log(buscarPublicacionesUrl)

    fetch(`${buscarPublicacionesUrl}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken 
        },
        body: JSON.stringify(datos) // Convierte los datos a JSON
    })
    .then(response => response.json())
    .then(data => {
        console.log("Datos guardados con éxito en el servidor:", data);
        // Ejemplo de uso:
        showAlert('success', 'Operación exitosa', 'La publicación se creó correctamente.', 'create_publicaction.html');

    })
    .catch(error => {
        console.error("Error al enviar datos al servidor:", error);
    });
}


// Agrega un botón único para manejar el guardado de ambas selecciones
// <button onclick="guardarSeleccion()">Guardar Selección</button>

function clearProfile(cardNumber) {
    // Identificar el ID del contenedor de la tarjeta y los elementos de la tarjeta
    const targetCard = document.getElementById(`targetCard${cardNumber}`);
    const targetName = document.getElementById(`targetName${cardNumber}`);
    const targetJob = document.getElementById(`targetJob${cardNumber}`);
    const targetImg = document.getElementById(`targetImg${cardNumber}`);

    // Ocultar la tarjeta
    targetCard.classList.add("d-none");

    // Limpiar contenido de la tarjeta
    targetName.innerText = "";
    targetJob.innerText = "";
    targetImg.src = "";

    // Quitar el ID del autor seleccionado de la lista (si existe)
    if (autoresSeleccionados[cardNumber - 1]) {
        autoresSeleccionados.splice(cardNumber - 1, 1);
    }

    console.log("Autores seleccionados después de remover:", autoresSeleccionados);
}


function showAlert(tipo, titulo, mensaje, url = null) {
    // Determina el ícono de la alerta en función del tipo
    let icono;
    switch (tipo) {
        case 'success':
            icono = 'success';
            break;
        case 'error':
            icono = 'error';
            break;
        case 'warning':
            icono = 'warning';
            break;
        case 'info':
            icono = 'info';
            break;
        default:
            icono = 'info';
    }

    // Configura la alerta de SweetAlert con los parámetros dados
    Swal.fire({
        title: titulo,
        text: mensaje,
        icon: icono,
        showCancelButton: url !== null,  // Solo muestra el botón si hay una URL
        confirmButtonText: 'Aceptar',
        cancelButtonText: 'Ir a la página',
    }).then((result) => {
        // Si se hace clic en "cancelar", redirige a la URL
        if (result.dismiss === Swal.DismissReason.cancel && url) {
            window.location.href = url;
        }
    });
}
