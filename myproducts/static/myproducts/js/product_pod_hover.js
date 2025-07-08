document.addEventListener('DOMContentLoaded', () => {
    // Itera sobre cada tarjeta de producto en la página
    document.querySelectorAll('.product-pod').forEach(pod => {
        
        // --- 1. Selección de Elementos del DOM dentro de cada tarjeta ---
        const mainImage = pod.querySelector('.card-img-top');
        // ¡CORRECCIÓN CLAVE! Buscamos por la nueva clase genérica '.visual-swatches'
        const swatchesContainer = pod.querySelector('.visual-swatches'); 
        const prevBtn = pod.querySelector('.pod-gallery-btn.prev');
        const nextBtn = pod.querySelector('.pod-gallery-btn.next');

        // Si la tarjeta no tiene imagen principal o no tiene swatches, no hacemos nada.
        if (!mainImage || !swatchesContainer) {
            // Oculta los botones de galería si no hay swatches con qué interactuar
            if(prevBtn) prevBtn.style.display = 'none';
            if(nextBtn) nextBtn.style.display = 'none';
            return;
        }

        // --- 2. Variables de Estado para cada tarjeta ---
        let currentImageSet = [];
        let currentIndex = 0;
        let activeSwatch = null;

        // --- 3. Función para actualizar la imagen principal ---
        const updateImage = (index) => {
            if (currentImageSet && currentImageSet[index]) {
                mainImage.src = currentImageSet[index];
                currentIndex = index;
            }
        };

        // --- 4. Inicialización y Eventos ---
        const swatches = swatchesContainer.querySelectorAll('.swatch');

        // Al cargar la página, la vista de Django ya puso la imagen correcta.
        // Solo necesitamos activar visualmente el primer swatch y preparar su galería.
        if (swatches.length > 0) {
            const firstSwatch = swatches[0];
            activeSwatch = firstSwatch;
            activeSwatch.classList.add('selected'); // Marcar el primer swatch como activo

            // Cargar la galería de imágenes del primer swatch
            const initialImagesAttr = firstSwatch.dataset.images;
            if (initialImagesAttr) {
                currentImageSet = initialImagesAttr.split(',').filter(Boolean); // filter(Boolean) elimina strings vacíos
            }
            
            // Mostrar u ocultar los botones de galería según corresponda
            const showNav = currentImageSet.length > 1;
            if(prevBtn) prevBtn.style.display = showNav ? 'block' : 'none';
            if(nextBtn) nextBtn.style.display = showNav ? 'block' : 'none';
        } else {
            // Si no hay swatches, ocultar botones de galería
            if(prevBtn) prevBtn.style.display = 'none';
            if(nextBtn) nextBtn.style.display = 'none';
        }

        // Asignar el evento de clic a CADA swatch
        swatches.forEach(swatch => {
            swatch.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                if (swatch === activeSwatch) return; // No hacer nada si se hace clic en el swatch ya activo

                // Actualizar la selección visual
                if (activeSwatch) activeSwatch.classList.remove('selected');
                swatch.classList.add('selected');
                activeSwatch = swatch;

                // Cargar el nuevo set de imágenes desde el atributo data-images del swatch clickeado
                const imagesAttr = swatch.dataset.images;
                currentImageSet = imagesAttr ? imagesAttr.split(',').filter(Boolean) : [];
                
                // Mostrar la primera imagen del nuevo set
                updateImage(0);

                // Actualizar la visibilidad de los botones de galería
                const showNav = currentImageSet.length > 1;
                if(prevBtn) prevBtn.style.display = showNav ? 'block' : 'none';
                if(nextBtn) nextBtn.style.display = showNav ? 'block' : 'none';
            });
        });

        // Asignar eventos a los botones de la galería si existen
        if (prevBtn && nextBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault(); 
                e.stopPropagation();
                if (currentImageSet.length > 1) {
                    const newIndex = (currentIndex - 1 + currentImageSet.length) % currentImageSet.length;
                    updateImage(newIndex);
                }
            });

            nextBtn.addEventListener('click', (e) => {
                e.preventDefault(); 
                e.stopPropagation();
                if (currentImageSet.length > 1) {
                    const newIndex = (currentIndex + 1) % currentImageSet.length;
                    updateImage(newIndex);
                }
            });
        }
    });
});