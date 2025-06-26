document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM Cargado - Menú Multinivel v7');

    const offcanvasNavbar = document.getElementById('offcanvasNavbar');
    if (!offcanvasNavbar) return;

    const menuContainerWrapper = offcanvasNavbar.querySelector('.main-menu-container-wrapper');
    const allMenuPanels = offcanvasNavbar.querySelectorAll('.menu-panel'); // Todos los paneles (L1, L2, L3)
    const panelLevel1 = offcanvasNavbar.querySelector('.menu-panel.level-1');

    if (!menuContainerWrapper || !panelLevel1 || allMenuPanels.length === 0) {
        console.error('Elementos base del menú multinivel no encontrados.');
        return;
    }

    // --- Lógica para Móvil (Clic) ---
    function setActivePanelMobile(targetPanelId) {
        console.log('Activando panel móvil:', targetPanelId);
        let panelFound = false;
        allMenuPanels.forEach(panel => {
            if (panel.id === targetPanelId.substring(1)) { // Quitar el '#' del selector
                panel.classList.add('active');
                panel.classList.remove('prev-active'); // Asegurar que no esté oculto a la izquierda
                panelFound = true;
            } else {
                // Si el panel actual es el que se va a mostrar, los otros no se mueven aún
                // Si un panel más profundo se va a mostrar, los anteriores se mueven a 'prev-active'
                if (panel.classList.contains('active')) { // Si este era el panel activo
                    panel.classList.remove('active');
                    panel.classList.add('prev-active'); // Moverlo a la izquierda
                } else {
                     panel.classList.remove('prev-active'); // Asegurar que los otros estén listos para entrar
                }
            }
        });
        if (!panelFound) console.warn("Panel target no encontrado:", targetPanelId);
    }

    // Event listeners para items que abren subpaneles
    menuContainerWrapper.querySelectorAll('[data-bs-toggle="offcanvas-panel"]').forEach(toggler => {
        toggler.addEventListener('click', function (event) {
            if (window.innerWidth < 992 && this.classList.contains('has-submenu')) {
                event.preventDefault();
                const targetPanelId = this.dataset.bsTarget;
                setActivePanelMobile(targetPanelId);

                // Resaltar padre (opcional)
                this.closest('ul').querySelectorAll('.nav-item-custom').forEach(li => li.classList.remove('active-parent'));
                this.classList.add('active-parent');
            }
            // En escritorio, el 'a' href navegará directamente
        });
    });

    // Event listeners para botones "Volver"
    menuContainerWrapper.querySelectorAll('.btn-back-offcanvas').forEach(backButton => {
        backButton.addEventListener('click', function () {
            if (window.innerWidth < 992) {
                const targetLevel = this.dataset.bsTargetLevel;
                const currentPanel = this.closest('.menu-panel');
                
                currentPanel.classList.remove('active'); // Oculta el panel actual (se va a la derecha)
                // No necesitamos añadir prev-active aquí, porque el que se muestra viene de la derecha.

                if (targetLevel === "1") {
                    panelLevel1.classList.add('active'); // Muestra Nivel 1
                    panelLevel1.classList.remove('prev-active'); // Asegura que esté en posición 0
                } else if (targetLevel === "2") {
                    const parentPanelTargetId = this.dataset.bsParentTarget; // ej: "#panel-category1-slug"
                    if (parentPanelTargetId) {
                        const parentPanel = menuContainerWrapper.querySelector(parentPanelTargetId);
                        if (parentPanel) {
                            parentPanel.classList.add('active');
                            parentPanel.classList.remove('prev-active');
                        }
                    }
                }
                // Quitar resaltado de padre (opcional)
                 const activeParent = currentPanel.closest('.main-menu-container-wrapper').querySelector('.active-parent');
                 if(activeParent) activeParent.classList.remove('active-parent');
            }
        });
    });

    let desktopHoverTimeout;
    const desktopMegamenuContainer = document.createElement('div'); // Crear un contenedor flotante
    desktopMegamenuContainer.className = 'megamenu-panel-desktop-version'; // Usar el CSS de escritorio
    offcanvasNavbar.querySelector('.offcanvas-body').appendChild(desktopMegamenuContainer);

    menuContainerWrapper.querySelectorAll('.nav-item-custom.has-submenu[data-bs-toggle="offcanvas-panel"]').forEach(itemLvl1 => {
        const targetPanelId = itemLvl1.dataset.bsTarget;
        const panelContentSource = menuContainerWrapper.querySelector(targetPanelId);

        itemLvl1.addEventListener('mouseenter', function() {
            if (window.innerWidth >= 992 && panelContentSource) {
                clearTimeout(desktopHoverTimeout);
                desktopMegamenuContainer.innerHTML = panelContentSource.innerHTML; // Copia el contenido
                desktopMegamenuContainer.classList.add('is-visible');
                // Posicionar desktopMegamenuContainer al lado de itemLvl1
                const mainCategoriesList = offcanvasNavbar.querySelector('.menu-panel.level-1');
                if (mainCategoriesList) {
                    desktopMegamenuContainer.style.left = mainCategoriesList.offsetWidth + 'px';
                }

            }
        });
        itemLvl1.addEventListener('mouseleave', function() {
            if (window.innerWidth >= 992) {
                desktopHoverTimeout = setTimeout(() => {
                    if (!desktopMegamenuContainer.matches(':hover')) {
                        desktopMegamenuContainer.classList.remove('is-visible');
                    }
                }, 150);
            }
        });
    });
    desktopMegamenuContainer.addEventListener('mouseenter', () => {
         if (window.innerWidth >= 992) clearTimeout(desktopHoverTimeout);
    });
    desktopMegamenuContainer.addEventListener('mouseleave', () => {
         if (window.innerWidth >= 992) {
            desktopHoverTimeout = setTimeout(() => {
                desktopMegamenuContainer.classList.remove('is-visible');
            }, 150);
         }
    });

});