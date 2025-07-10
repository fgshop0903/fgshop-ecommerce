document.addEventListener('DOMContentLoaded', () => {
    const dataElement = document.getElementById('product-detail-variant-data');
    if (!dataElement) {
        // Si no hay datos de variantes, no se ejecuta el script.
        return;
    }

    const data = JSON.parse(dataElement.textContent);
    if (!data || !data.variants || data.variants.length === 0) {
        const container = document.getElementById('variant-selectors-container');
        if (container) container.innerHTML = '<p class="text-danger">Este producto no está disponible actualmente.</p>';
        const addToCartBtn = document.getElementById('add-to-cart-btn');
        if (addToCartBtn) {
            addToCartBtn.disabled = true;
            addToCartBtn.textContent = 'No Disponible';
        }
        return;
    }

    new VariantSelector(data);
});

class VariantSelector {
    constructor(data) {
        this.variants = data.variants;
        this.attributes = data.attributes_definition;
        this.basePrice = parseFloat(data.product_base_price);
        this.defaultVariantId = data.default_variant_id;

        // ==========================================================
        // 1. Identificamos al "Rey" (el atributo visual/primario)
        // ==========================================================
        this.primaryAttributeSlug = this.attributes.find(attr => attr.type === 'image_swatch')?.id_slug || this.attributes[0]?.id_slug;
        this.useVariantSpecificImages = data.use_variant_specific_images || false;
        this.selectedOptions = {};
        this.currentVariant = null;
        this.currentImageIndex = 0;
        this.images = [];

        this.cacheDOM();
        this.init();
    }

    cacheDOM() {
        this.dom = {
            selectorsContainer: document.getElementById('variant-selectors-container'),
            mainImage: document.getElementById('main-product-image'),
            thumbnails: document.getElementById('thumbnail-container'),
            prevBtn: document.getElementById('prev-image-btn'),
            nextBtn: document.getElementById('next-image-btn'),
            skuDesktop: document.getElementById('variant-sku-desktop'),
            skuMobile: document.getElementById('variant-sku-mobile'),
            price: document.getElementById('variant-price'),
            basePrice: document.getElementById('variant-base-price'),
            discountBadge: document.getElementById('variant-discount-badge'),
            stockInfo: document.getElementById('stock-info'),
            addToCartBtn: document.getElementById('add-to-cart-btn'),
            variantIdInput: document.getElementById('selected-variant-id'),
            quantityInput: document.getElementById('quantity-input'),
            formQuantityInput: document.getElementById('form-quantity-input'),
            qtyMinus: document.getElementById('quantity-minus'),
            qtyPlus: document.getElementById('quantity-plus'),
            installmentsInfo: document.getElementById('installments-info'),
        };
    }

    init() {
        this.buildSelectors();
        this.bindEvents();
        const urlParams = new URLSearchParams(window.location.search);
        const variantIdFromUrl = parseInt(urlParams.get('variant'), 10);
        let initialVariant = this.variants.find(v => v.id === variantIdFromUrl);
        if (!initialVariant) {
            initialVariant = this.variants.find(v => v.id === this.defaultVariantId) || 
                            this.variants.find(v => v.is_active && v.stock > 0) || 
                            this.variants.find(v => v.is_active) ||
                            this.variants[0];
        }
        if (initialVariant) {
            this.selectedOptions = { ...initialVariant.attribute_options };
        }
        this.updateState();
    }

    buildSelectors() {
        this.attributes.forEach(attr => {
            const container = document.createElement('div');
            container.className = 'mb-3';
            container.innerHTML = `<label class="form-label fw-bold">${attr.name}: <span id="selected-${attr.id_slug}" class="text-muted fw-normal"></span></label>`;
            const optionsWrapper = document.createElement('div');
            optionsWrapper.className = 'd-flex flex-wrap gap-2';
            optionsWrapper.dataset.attribute = attr.id_slug;
            attr.options_display_order.forEach(optionValue => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.dataset.value = optionValue;
                if (attr.type === 'image_swatch') {
                    const variantForImage = this.variants.find(v => v.attribute_options[attr.id_slug] === optionValue && v.images.length > 0);
                    const imgSrc = variantForImage ? variantForImage.images[0] : 'https://via.placeholder.com/40x40.png?text=?';
                    btn.className = 'variant-swatch color';
                    btn.innerHTML = `<img src="${imgSrc}" alt="${optionValue}">`;
                } else {
                    btn.className = 'variant-swatch size';
                    btn.textContent = optionValue;
                }
                optionsWrapper.appendChild(btn);
            });
            container.appendChild(optionsWrapper);
            this.dom.selectorsContainer.appendChild(container);
        });
    }

    bindEvents() {
        this.dom.selectorsContainer.addEventListener('click', e => {
            const btn = e.target.closest('.variant-swatch');
            if (!btn || btn.disabled) return;
            const attribute = btn.parentElement.dataset.attribute;
            const value = btn.dataset.value;
            if (this.selectedOptions[attribute] === value) return;
            this.selectedOptions[attribute] = value;
            this.updateState(attribute); // Le pasamos el atributo que cambió
        });

        // ... (resto de listeners sin cambios)
        this.dom.thumbnails.addEventListener('click', e => {const thumb = e.target.closest('img'); if (thumb) this.displayImage(parseInt(thumb.dataset.index));});
        this.dom.nextBtn.addEventListener('click', () => this.navigateGallery(1));
        this.dom.prevBtn.addEventListener('click', () => this.navigateGallery(-1));
        this.dom.qtyMinus.addEventListener('click', () => this.updateQuantity(-1));
        this.dom.qtyPlus.addEventListener('click', () => this.updateQuantity(1));
        this.dom.quantityInput.addEventListener('change', () => this.updateQuantity(0));
    }
    
    // ==========================================================
    // INICIO DE LAS FUNCIONES CORREGIDAS
    // ==========================================================

    updateState(changedAttributeSlug = null) {
        // Buscamos la variante que coincide exactamente con la selección actual del usuario
        let variantExists = this.variants.find(v => 
            this.attributes.every(attr => v.attribute_options[attr.id_slug] === this.selectedOptions[attr.id_slug])
        );

        // Si la combinación directa NO existe (ej. Marrón/S no existiera)
        if (!variantExists) {
            // Y si el atributo que cambió fue el primario (Color/Sabor)...
            if (changedAttributeSlug && changedAttributeSlug === this.primaryAttributeSlug) {
                // ...entonces SÍ hacemos el auto-ajuste a la primera talla disponible.
                const firstMatch = this.variants.find(v => v.attribute_options[this.primaryAttributeSlug] === this.selectedOptions[this.primaryAttributeSlug]);
                if (firstMatch) {
                    this.selectedOptions = { ...firstMatch.attribute_options };
                }
            }
        }
        
        // Ahora, con las opciones (potencialmente corregidas), encontramos la variante final
        this.currentVariant = this.variants.find(v => 
            this.attributes.every(attr => v.attribute_options[attr.id_slug] === this.selectedOptions[attr.id_slug])
        ) || null;

        // El resto del flujo actualiza la UI con lo que haya encontrado
        this.updateAvailableSwatches();
        this.updateSelectedNames();
        this.updateDetails();
        this.updateGallery();
    }
    
    updateAvailableSwatches() {
        // La selección del atributo "Rey" (Color/Sabor)
        const primarySelectionValue = this.selectedOptions[this.primaryAttributeSlug];

        this.dom.selectorsContainer.querySelectorAll('.variant-swatch').forEach(btn => {
            const attributeOfThisButton = btn.parentElement.dataset.attribute;
            const valueOfThisButton = btn.dataset.value;

            let isPossible = false;
            if (attributeOfThisButton === this.primaryAttributeSlug) {
                // El Rey (Color/Sabor) siempre es seleccionable
                isPossible = true; 
            } else {
                // Para el Súbdito (Talla), vemos si existe con el Rey actual
                isPossible = this.variants.some(variant => 
                    variant.attribute_options[this.primaryAttributeSlug] === primarySelectionValue &&
                    variant.attribute_options[attributeOfThisButton] === valueOfThisButton
                );
            }

            btn.disabled = !isPossible;
            btn.classList.toggle('selected', this.selectedOptions[attributeOfThisButton] === valueOfThisButton);
        });
    }

    // ==========================================================
    // FIN DE LAS FUNCIONES CORREGIDAS
    // ==========================================================

    updateSelectedNames() {
        this.attributes.forEach(attr => {
            const span = document.getElementById(`selected-${attr.id_slug}`);
            if(span) span.textContent = this.selectedOptions[attr.id_slug] || '';
        });
    }

    updateDetails() {
        const { price, basePrice, discountBadge, installmentsInfo, skuDesktop, skuMobile, stockInfo, addToCartBtn, variantIdInput } = this.dom;
        basePrice.style.display = 'none';
        if (discountBadge) discountBadge.style.display = 'none';
        installmentsInfo.style.display = 'none';
        if (this.currentVariant) {
            if (skuDesktop) skuDesktop.textContent = this.currentVariant.sku;
            if (skuMobile) skuMobile.textContent = this.currentVariant.sku;
            price.textContent = `S/ ${parseFloat(this.currentVariant.price).toFixed(2)}`;
            variantIdInput.value = this.currentVariant.id;
            const variantPrice = parseFloat(this.currentVariant.price);
            if (this.basePrice && this.basePrice > variantPrice) {
                basePrice.textContent = `S/ ${this.basePrice.toFixed(2)}`;
                basePrice.style.display = 'inline';
                if(discountBadge) {
                    const discount = Math.round(((this.basePrice - variantPrice) / this.basePrice) * 100);
                    discountBadge.textContent = `-${discount}%`;
                    discountBadge.style.display = 'inline-block';
                }
            }
            if (this.currentVariant.cuotas) {
                installmentsInfo.innerHTML = `<p class="mb-0">O págalo hasta en <strong>${this.currentVariant.cuotas.numero} cuotas</strong> de <strong>S/ ${this.currentVariant.cuotas.monto_mensual}</strong></p>`;
                installmentsInfo.style.display = 'block';
            }
            const inStock = this.currentVariant.is_active && this.currentVariant.stock > 0;
            stockInfo.textContent = inStock ? (this.currentVariant.stock < 10 ? `¡Últimas ${this.currentVariant.stock} unidades!` : 'En Stock') : 'Agotado';
            stockInfo.className = inStock ? 'form-text text-success' : 'form-text text-danger';
            addToCartBtn.disabled = !inStock;
            addToCartBtn.textContent = inStock ? 'Agregar al Carro' : 'Sin Stock';
            this.dom.quantityInput.max = this.currentVariant.stock;
            this.updateQuantity(0);
        } else {
            addToCartBtn.textContent = 'Combinación No Disponible';
            addToCartBtn.disabled = true;
            if (skuDesktop) skuDesktop.textContent = 'N/A';
            if (skuMobile) skuMobile.textContent = 'N/A';
            price.textContent = '';
            stockInfo.textContent = 'Selecciona una combinación válida';
        }
    }

    updateGallery() {
        this.images = []; // Limpiamos la galería

        // --- MODO 1: Imágenes por Variante Específica (Suplementos) ---
        if (this.useVariantSpecificImages) {
            if (this.currentVariant && this.currentVariant.images.length > 0) {
                this.images = this.currentVariant.images;
            }
        } 
        // --- MODO 2: Imágenes por Atributo Visual (Ropa) ---
        else {
            if (this.currentVariant && this.currentVariant.images.length > 0) {
                 this.images = this.currentVariant.images;
            } else {
                 // Fallback por si la variante no tiene imagen, pero su color sí.
                 const visualAttrSlug = this.primaryAttributeSlug;
                 const selectedVisualOption = this.selectedOptions[visualAttrSlug];
                 if (visualAttrSlug && selectedVisualOption) {
                    const variantForImages = this.variants.find(v => v.attribute_options[visualAttrSlug] === selectedVisualOption && v.images.length > 0);
                    if (variantForImages) this.images = variantForImages.images;
                 }
            }
        }
        
        // El resto de la función para renderizar la galería no cambia
        this.dom.thumbnails.innerHTML = '';
        if (this.images.length > 0) {
            this.images.forEach((src, index) => {
                const thumb = document.createElement('img');
                thumb.src = src;
                thumb.dataset.index = index;
                this.dom.thumbnails.appendChild(thumb);
            });
            this.displayImage(0);
        } else {
            this.dom.mainImage.src = 'https://via.placeholder.com/800x800.png?text=No+disponible';
        }
        const showNav = this.images.length > 1;
        this.dom.nextBtn.style.display = showNav ? 'block' : 'none';
        this.dom.prevBtn.style.display = showNav ? 'block' : 'none';
    }

    displayImage(index) {
        if (!this.images[index]) return;
        this.currentImageIndex = index;
        this.dom.mainImage.src = this.images[index];
        this.dom.thumbnails.querySelectorAll('img').forEach((img, i) => img.classList.toggle('active', i === index));
    }
    
    navigateGallery(direction) {
        if (this.images.length <= 1) return;
        const newIndex = (this.currentImageIndex + direction + this.images.length) % this.images.length;
        this.displayImage(newIndex);
    }
    
    updateQuantity(change) {
        let qty = parseInt(this.dom.quantityInput.value, 10) || 1;
        qty += change;
        const max = this.currentVariant ? this.currentVariant.stock : 1;
        if (qty < 1) qty = 1;
        if (qty > max) qty = max;
        this.dom.quantityInput.value = qty;
        this.dom.formQuantityInput.value = qty;
    }
}

