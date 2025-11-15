// Mobile menu toggle
document.addEventListener("DOMContentLoaded", () => {
  // Theme switching functionality
  function initTheme() {
    const themeToggle = document.getElementById("themeToggle")
    const themeIcon = document.querySelector(".theme-icon")
    const savedTheme = localStorage.getItem("theme")

    // Apply saved theme or default to dark
    if (savedTheme === "light") {
      document.body.classList.add("theme-light")
      if (themeIcon) themeIcon.textContent = "🌙"
    }

    // Theme toggle handler
    if (themeToggle) {
      themeToggle.addEventListener("click", () => {
        document.body.classList.toggle("theme-light")
        const isLight = document.body.classList.contains("theme-light")

        // Update icon
        if (themeIcon) {
          themeIcon.textContent = isLight ? "🌙" : "☀️"
        }

        // Save preference
        localStorage.setItem("theme", isLight ? "light" : "dark")
      })
    }
  }

  // Initialize theme
  initTheme()

  const mobileMenuToggle = document.getElementById("mobileMenuToggle")
  const nav = document.querySelector(".nav")

  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener("click", () => {
      nav.classList.toggle("active")
    })
  }

  // Hero search functionality
  const heroSearchBtn = document.getElementById("heroSearchBtn")
  const heroSearch = document.getElementById("heroSearch")
  const heroSearchForm = document.querySelector(".search-box-hero")

  if (heroSearchForm) {
    heroSearchForm.addEventListener("submit", (e) => {
      e.preventDefault()
      const searchInput = heroSearchForm.querySelector('input[name="q"]') || heroSearch
      const searchTerm = searchInput ? searchInput.value.trim() : ""
      if (searchTerm) {
        // Redirigir a la página de búsqueda con el término
        const searchUrl = `/buscar/?q=${encodeURIComponent(searchTerm)}`
        window.location.href = searchUrl
      } else {
        // Si no hay término, ir a la página de búsqueda sin query
        window.location.href = "/buscar/"
      }
    })
  }

  if (heroSearchBtn) {
    heroSearchBtn.addEventListener("click", (e) => {
      e.preventDefault()
      const searchTerm = heroSearch ? heroSearch.value.trim() : ""
      if (searchTerm) {
        const searchUrl = `/buscar/?q=${encodeURIComponent(searchTerm)}`
        window.location.href = searchUrl
      } else {
        window.location.href = "/buscar/"
      }
    })
  }

  if (heroSearch) {
    heroSearch.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault()
        const searchTerm = heroSearch.value.trim()
        if (searchTerm) {
          const searchUrl = `/buscar/?q=${encodeURIComponent(searchTerm)}`
          window.location.href = searchUrl
        } else {
          window.location.href = "/buscar/"
        }
      }
    })
  }

  // Sidebar toggle for mobile (search page)
  const sidebarToggle = document.getElementById("sidebarToggle")
  const sidebar = document.getElementById("sidebar")
  const sidebarClose = document.getElementById("sidebarClose")

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.add("active")
    })
  }

  if (sidebarClose && sidebar) {
    sidebarClose.addEventListener("click", () => {
      sidebar.classList.remove("active")
    })
  }

  // Filter accordion functionality
  const filterHeaders = document.querySelectorAll(".filter-header")

  filterHeaders.forEach((header) => {
    header.addEventListener("click", function () {
      const filterId = this.getAttribute("data-filter")
      const filterContent = document.getElementById(`filter-${filterId}`)

      this.classList.toggle("active")
      filterContent.classList.toggle("active")
    })
  })

  // Initialize filters as open by default
  filterHeaders.forEach((header) => {
    const filterId = header.getAttribute("data-filter")
    const filterContent = document.getElementById(`filter-${filterId}`)
    header.classList.add("active")
    filterContent.classList.add("active")
  })

  // Comment form submission
  const commentForm = document.getElementById("commentForm")

  if (commentForm) {
    commentForm.addEventListener("submit", (e) => {
      e.preventDefault()

      const commentText = document.getElementById("commentText").value.trim()
      const commentAuthor = document.getElementById("commentAuthor").value.trim()

      if (commentText && commentAuthor) {
        console.log("[v0] New comment submitted:", { author: commentAuthor, text: commentText })

        // Create new comment element
        const commentsList = document.querySelector(".comments-list")
        const newComment = document.createElement("article")
        newComment.className = "comment"

        const today = new Date()
        const dateStr = today.toLocaleDateString("es-ES", {
          day: "numeric",
          month: "long",
          year: "numeric",
        })

        newComment.innerHTML = `
                    <div class="comment-header">
                        <span class="comment-author">${commentAuthor}</span>
                        <span class="comment-date">${dateStr}</span>
                    </div>
                    <p class="comment-text">${commentText}</p>
                `

        // Insert at the beginning of comments list
        commentsList.insertBefore(newComment, commentsList.firstChild)

        // Clear form
        document.getElementById("commentText").value = ""
        document.getElementById("commentAuthor").value = ""

        // Show success message (optional)
        alert("Comentario publicado exitosamente")
      } else {
        alert("Por favor complete todos los campos")
      }
    })
  }

  // Search functionality on search page
  const sidebarSearch = document.getElementById("sidebarSearch")
  const filtersForm = document.getElementById("filtersForm")

  if (sidebarSearch) {
    sidebarSearch.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault()
        if (filtersForm) {
          filtersForm.submit()
        }
      }
    })
  }

  // Filter change handlers - auto-submit on change (optional)
  const filterSelects = document.querySelectorAll(".form-control")
  let filterTimeout

  // Optional: Auto-submit after user stops changing filters (debounce)
  filterSelects.forEach((select) => {
    select.addEventListener("change", function () {
      // Clear previous timeout
      clearTimeout(filterTimeout)
      
      // Optional: Auto-submit after 500ms of no changes
      // Uncomment the following lines if you want auto-submit on filter change
      // filterTimeout = setTimeout(() => {
      //   if (filtersForm) {
      //     filtersForm.submit()
      //   }
      // }, 500)
    })
  })

  // Filter change handlers for checkboxes/radios
  const filterCheckboxes = document.querySelectorAll(".filter-option input")

  filterCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", function () {
      // Optional: Auto-submit on checkbox/radio change
      // Uncomment if you want auto-submit
      // if (filtersForm) {
      //   filtersForm.submit()
      // }
    })
  })

  // Highlight search matches on results page
  const resultsContainer = document.querySelector('.results-list')
  if (resultsContainer) {
    const params = new URLSearchParams(window.location.search)
    const queryValue = params.get('q')

    if (queryValue) {
      const tokens = queryValue
        .split(/\s+/)
        .map((token) => token.trim())
        .filter((token) => token.length > 0)

      if (tokens.length) {
        const escapedTokens = tokens.map((token) => token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
        const regex = new RegExp(`(${escapedTokens.join('|')})`, 'gi')
        const highlightTargets = resultsContainer.querySelectorAll(
          '.result-title a, .result-description, .meta-author, .meta-editor'
        )

        highlightTargets.forEach((element) => {
          if (!regex.source.trim()) return
          if (element.innerHTML.includes('search-highlight')) return
          element.innerHTML = element.innerHTML.replace(
            regex,
            '<mark class="search-highlight">$1</mark>'
          )
        })
      }
    }
  }

  // Note: heroSearchForm ya está manejado arriba en la sección "Hero search functionality"
})

