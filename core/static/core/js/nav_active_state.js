// ARCHIVO: nav_active_state.js
// Este script se encarga de resaltar el botón activo en la barra de navegación inferior móvil.

document.addEventListener('DOMContentLoaded', () => {
    const bottomNav = document.querySelector('.mobile-bottom-nav');
    // Si no existe la barra de navegación en la página, no hacemos nada.
    if (!bottomNav) {
        return;
    }

    const navItems = bottomNav.querySelectorAll('a.nav-item-mobile');
    const currentPath = window.location.pathname;

    let bestMatch = null;
    let longestMatchLength = 0;

    navItems.forEach(item => {
        // Obtenemos la URL del botón
        const itemPath = item.getAttribute('href');

        // Comprobamos si la URL actual EMPIEZA con la URL del botón.
        // Esto es clave para que /ofertas/zapatillas/ siga resaltando el botón de /ofertas/
        if (currentPath.startsWith(itemPath)) {
            // Si encontramos una coincidencia, comprobamos si es más específica (más larga)
            // que la que ya teníamos.
            if (itemPath.length > longestMatchLength) {
                longestMatchLength = itemPath.length;
                bestMatch = item;
            }
        }
    });

    // Caso especial para la página de inicio.
    // Si estamos exactamente en '/', el mejor match debe ser el botón de inicio.
    if (currentPath === '/') {
        const homeButton = bottomNav.querySelector('a[href="/"]');
        if (homeButton) {
            bestMatch = homeButton;
        }
    }
    
    // Si encontramos un "mejor match", le añadimos la clase para resaltarlo.
    if (bestMatch) {
        bestMatch.classList.add('highlight');
    }
});