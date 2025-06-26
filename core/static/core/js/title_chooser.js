// ARCHIVO: FGSHOP/core/static/core/js/title_chooser.js (VERSIÓN FINAL Y VERIFICADA)
// Este código maneja todos los saludos personalizados para usuarios anónimos.

document.addEventListener('DOMContentLoaded', function() {

    // --- 1. Definimos todos los elementos del DOM que vamos a manipular ---
    const banner = document.getElementById('choice-banner');

    // Si el usuario está logueado, el banner no existe en el HTML. El script no debe hacer nada.
    // Si el banner no se encuentra por cualquier otra razón, también salimos para evitar errores.
    if (!banner) {
        return;
    }
    
    // Botones y placeholders del banner y la página
    const selectPatronaBtn = document.getElementById('select-patrona');
    const selectKingBtn = document.getElementById('select-king');
    const closeBannerBtn = document.getElementById('close-banner');
    const titlePlaceholders = document.querySelectorAll('.user-title');
    
    // Elementos de la UI que se personalizan
    const offcanvasLogoLink = document.getElementById('offcanvas-logo-link');
    const offcanvasGreeting = document.getElementById('offcanvas-greeting');
    const loginGreetingText = document.getElementById('login-greeting-text');
    const newsletterPitch = document.getElementById('newsletter-pitch');

    // --- 2. Funciones para manejar Cookies (verificadas) ---
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

    // --- 3. La función central que hace toda la magia visual ---
    function applyAllVisualChanges(choice) {
        if (!choice) return;

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

    // --- 4. Función que se activa al hacer clic en un botón del banner ---
    function handleChoice(choice) {
        setCookie('userTitlePreference', choice, 365);
        applyAllVisualChanges(choice);
        
        banner.style.opacity = '0';
        setTimeout(() => { banner.style.display = 'none'; }, 300);
    }

    // --- 5. Lógica principal que se ejecuta al cargar la página ---
    const savedChoice = getCookie('userTitlePreference');
    const wasBannerClosed = sessionStorage.getItem('choiceBannerClosed');

    if (savedChoice) {
        // Si la cookie EXISTE, aplicamos los cambios y nos aseguramos de que el banner esté oculto.
        applyAllVisualChanges(savedChoice);
        banner.style.display = 'none';
    } else {
        // Si la cookie NO EXISTE, añadimos los listeners y decidimos si mostrar el banner.
        selectPatronaBtn.addEventListener('click', () => handleChoice('Patrona'));
        selectKingBtn.addEventListener('click', () => handleChoice('king'));
        closeBannerBtn.addEventListener('click', () => {
            banner.style.opacity = '0';
            setTimeout(() => { banner.style.display = 'none'; }, 300);
            sessionStorage.setItem('choiceBannerClosed', 'true');
        });

        if (!wasBannerClosed) {
            // Y si no se ha cerrado en esta sesión, lo mostramos.
            setTimeout(() => {
                banner.style.display = 'block';
                void banner.offsetWidth;
                banner.style.opacity = '1';
            }, 1500);
        }
    }
});