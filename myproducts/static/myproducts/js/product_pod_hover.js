// myproducts/static/myproducts/js/product_pod_hover.js

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.product-pod').forEach(pod => {
        // --- Elementos del DOM ---
        const mainImage = pod.querySelector('.card-img-top');
        const prevBtn = pod.querySelector('.pod-gallery-btn.prev');
        const nextBtn = pod.querySelector('.pod-gallery-btn.next');
        const colorSwatchesContainer = pod.querySelector('.color-swatches');
        const imageContainer = pod.querySelector('.product-image-container');

        // --- Variables de Estado ---
        if (!mainImage) return; // Si no hay imagen, no hacer nada
        
        const originalImageSrc = mainImage.src;
        let currentImageSet = [];
        let currentIndex = 0;
        let activeSwatch = null;

        // --- Función de ayuda ---
        const updateImage = (index) => {
            if (currentImageSet && currentImageSet[index]) {
                mainImage.src = currentImageSet[index];
                currentIndex = index;
            }
        };

        // --- Event Listeners ---

        if (prevBtn && nextBtn) {
            prevBtn.addEventListener('click', (e) => {
                e.preventDefault(); e.stopPropagation();
                const newIndex = (currentIndex - 1 + currentImageSet.length) % currentImageSet.length;
                updateImage(newIndex);
            });
            nextBtn.addEventListener('click', (e) => {
                e.preventDefault(); e.stopPropagation();
                const newIndex = (currentIndex + 1) % currentImageSet.length;
                updateImage(newIndex);
            });
        }
        
if (colorSwatchesContainer) {
            const swatches = colorSwatchesContainer.querySelectorAll('.swatch');

            // --- INICIO DE LA NUEVA LÓGICA DE INICIALIZACIÓN ---
            if (swatches.length > 0) {
                const firstSwatch = swatches[0];
                
                // 1. Lo seleccionamos visualmente
                activeSwatch = firstSwatch;
                activeSwatch.classList.add('selected');
                
                // 2. Cargamos su set de imágenes en el estado inicial
                const initialImagesAttr = firstSwatch.dataset.images;
                if (initialImagesAttr && initialImagesAttr.length > 0) {
                    currentImageSet = initialImagesAttr.split(',');
                }
            }
            // --- FIN DE LA NUEVA LÓGICA ---
            
            swatches.forEach(swatch => {
                swatch.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();

                    if (swatch === activeSwatch) return;
                    
                    if (activeSwatch) activeSwatch.classList.remove('selected');
                    swatch.classList.add('selected');
                    activeSwatch = swatch;

                    const imagesAttr = swatch.dataset.images;
                    if (imagesAttr && imagesAttr.length > 0) {
                        currentImageSet = imagesAttr.split(',');
                    } else {
                        currentImageSet = [originalImageSrc];
                    }
                    updateImage(0); // Mostramos la primera imagen del nuevo set
                });
            });
        }
    });
});