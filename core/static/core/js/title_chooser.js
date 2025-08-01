// ARCHIVO: FGSHOP/core/static/core/js/title_chooser.js (VERSIÓN FINAL Y COMPLETA)

document.addEventListener('DOMContentLoaded', function() {

    // --- LÓGICA DE DECISIÓN PRINCIPAL ---
    
    // CASO 1: El usuario está logueado y tiene una preferencia en la base de datos.
    // En este caso, Django ya muestra el saludo correcto. El script solo debe ocultar el banner y terminar.
    if (window.FGSHOP_USER_DATA && window.FGSHOP_USER_DATA.isAuthenticated && window.FGSHOP_USER_DATA.titlePreference) {
        const banner = document.getElementById('choice-banner');
        if (banner) {
            banner.style.display = 'none';
        }
        return; // El script termina aquí. No hace nada más.
    }

    // --- El resto del código solo se ejecuta para INVITADOS o usuarios sin preferencia ---
    
    const banner = document.getElementById('choice-banner');
    if (!banner) {
        // Si por alguna razón el banner no existe en el HTML, no continuamos para evitar errores.
        return;
    }
    
    // Selectores de los elementos del DOM que vamos a manipular
    const selectPatronaBtn = document.getElementById('select-patrona');
    const selectKingBtn = document.getElementById('select-king');
    const closeBannerBtn = document.getElementById('close-banner');
    const titlePlaceholders = document.querySelectorAll('.user-title');
    const offcanvasLogoLink = document.getElementById('offcanvas-logo-link');
    const offcanvasGreeting = document.getElementById('offcanvas-greeting');
    const loginGreetingText = document.getElementById('login-greeting-text');
    const newsletterPitch = document.getElementById('newsletter-pitch');

    // Funciones para manejar Cookies
    function setCookie(name, value, days) {
        let expires = "";
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }
        document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    // Función que aplica los cambios visuales para invitados
    function applyGuestVisualChanges(choice) {
        if (!choice) return;

        // El valor de la cookie es 'Patrona' o 'king'
        let finalTitle = choice;
        if (choice === 'king') {
            finalTitle = Math.random() < 0.5 ? 'mi King' : 'mi Rey';
        }

        titlePlaceholders.forEach(placeholder => { placeholder.textContent = finalTitle; });

        if (offcanvasLogoLink && offcanvasGreeting) {
            offcanvasLogoLink.classList.add('d-none');
            offcanvasGreeting.classList.remove('d-none');
        }

        if (loginGreetingText) {
            loginGreetingText.textContent = `Hola ${finalTitle}, Inicia sesión`;
        }

        if (newsletterPitch) {
            if (choice === 'Patrona') {
                newsletterPitch.textContent = "Suscríbete a nuestro boletín y sé la primera en enterarte.";
            } else if (choice === 'king') {
                newsletterPitch.textContent = "Suscríbete a nuestro boletín y sé el primero en enterarte.";
            }
        }
    }

    // Función que se ejecuta cuando el invitado hace clic en una opción
    function handleChoice(choice) {
        setCookie('userTitlePreference', choice, 365); // Guarda 'Patrona' o 'king'
        applyGuestVisualChanges(choice);
        
        banner.style.opacity = '0';
        setTimeout(() => { banner.style.display = 'none'; }, 300);
    }

    // --- LÓGICA PRINCIPAL PARA INVITADOS ---
    const savedCookie = getCookie('userTitlePreference');
    const wasBannerClosed = sessionStorage.getItem('choiceBannerClosed');

    if (savedCookie === 'Patrona' || savedCookie === 'king') {
        // CASO 2: Es un invitado que ya eligió en una visita anterior.
        applyGuestVisualChanges(savedCookie);
        banner.style.display = 'none';
    } else {
        // CASO 3: Es un invitado nuevo o uno que nunca eligió.
        // Preparamos los botones para que pueda elegir.
        selectPatronaBtn.addEventListener('click', () => handleChoice('Patrona'));
        selectKingBtn.addEventListener('click', () => handleChoice('king'));
        closeBannerBtn.addEventListener('click', () => {
            banner.style.opacity = '0';
            setTimeout(() => { banner.style.display = 'none'; }, 300);
            sessionStorage.setItem('choiceBannerClosed', 'true');
        });

        // Si no ha cerrado el banner en esta sesión, lo mostramos.
        if (!wasBannerClosed) {
            setTimeout(() => {
                banner.style.display = 'block';
                void banner.offsetWidth; // truco para forzar la transición CSS
                banner.style.opacity = '1';
            }, 1500);
        }
    }
});