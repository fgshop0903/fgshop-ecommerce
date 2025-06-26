document.addEventListener('DOMContentLoaded', () => {

    const variantsDataElement = document.getElementById('variants-data');
    if (!variantsDataElement) {
        console.error('Elemento #variants-data no encontrado. Asegúrate de que el json_script se renderiza correctamente.');
        return;
    }
    
    const variantsData = JSON.parse(variantsDataElement.textContent);
    console.log("Datos de variantes cargados:", variantsData);
    
    const dataElement = document.getElementById('product-detail-variant-data');
    if (!dataElement) {
        console.error("Elemento 'product-detail-variant-data' no encontrado.");
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

        // --- ¡AQUÍ ESTÁ EL CAMBIO! ---
        // 1. Leer el parámetro de la URL
        const urlParams = new URLSearchParams(window.location.search);
        const variantIdFromUrl = parseInt(urlParams.get('variant'), 10);
        
        let initialVariant = null;

        // 2. Si hay un ID de variante en la URL, esa es nuestra prioridad
        if (variantIdFromUrl) {
            initialVariant = this.variants.find(v => v.id === variantIdFromUrl);
        }

        // 3. Si no, usamos la lógica de fallback que ya tenías
        if (!initialVariant) {
            initialVariant = this.variants.find(v => v.id === this.defaultVariantId) || 
                            this.variants.find(v => v.is_active && v.stock > 0) || 
                            this.variants.find(v => v.is_active) ||
                            this.variants[0];
        }
        
        // El resto del código se mantiene igual
        if (initialVariant) {
            this.selectedOptions = { ...initialVariant.attribute_options };
        }
        
        this.updateState();
    }

    buildSelectors() {
        this.attributes.forEach(attr => {
            const container = document.createElement('div');
            container.className = 'mb-3';
            container.innerHTML = `<label class="form-label fw-bold">${attr.name}: <span id="selected-${attr.id_slug}"></span></label>`;
            
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

            // 1. Asegúrate de que se hizo clic en un botón válido y no deshabilitado
            if (!btn || btn.disabled) {
                return;
            }

            const attribute = btn.parentElement.dataset.attribute;
            const value = btn.dataset.value;

            // --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
            // 2. Si la opción clickeada ya es la seleccionada, no hagas nada.
            if (this.selectedOptions[attribute] === value) {
                console.log(`Opción '${value}' ya seleccionada. Ignorando clic.`);
                return; // Salimos de la función sin hacer cambios.
            }

            // 3. Si es una nueva opción, actualiza la selección y el estado
            this.selectedOptions[attribute] = value;
            this.updateState();
        });

        this.dom.thumbnails.addEventListener('click', e => {
            const thumb = e.target.closest('img');
            if (thumb) this.displayImage(parseInt(thumb.dataset.index));
        });

        this.dom.nextBtn.addEventListener('click', () => this.displayImage((this.currentImageIndex + 1) % this.images.length));
        this.dom.prevBtn.addEventListener('click', () => this.displayImage((this.currentImageIndex - 1 + this.images.length) % this.images.length));
        
        this.dom.qtyMinus.addEventListener('click', () => this.updateQuantity(-1));
        this.dom.qtyPlus.addEventListener('click', () => this.updateQuantity(1));
        this.dom.quantityInput.addEventListener('change', () => this.updateQuantity(0));
    }
    
    updateState() {
        this.updateAvailableSwatches();
        this.currentVariant = this.variants.find(v => this.attributes.every(attr => v.attribute_options[attr.id_slug] === this.selectedOptions[attr.id_slug])) || null;
        this.updateSelectedNames();
        this.updateDetails();
        this.updateGallery();
    }
    
    updateAvailableSwatches() {
        const primaryAttribute = this.attributes[0].id_slug;
        const primarySelectedValue = this.selectedOptions[primaryAttribute];
        this.dom.selectorsContainer.querySelectorAll('.variant-swatch').forEach(btn => {
            const attributeOfThisButton = btn.parentElement.dataset.attribute;
            const valueOfThisButton = btn.dataset.value;            
            let isPossible = false;
            if (attributeOfThisButton === primaryAttribute) {
                isPossible = this.variants.some(
                    variant => variant.attribute_options[primaryAttribute] === valueOfThisButton
                );
            } 
            else {
                isPossible = this.variants.some(variant => 
                    variant.attribute_options[primaryAttribute] === primarySelectedValue &&
                    variant.attribute_options[attributeOfThisButton] === valueOfThisButton
                );
            }
            btn.disabled = !isPossible;
            btn.classList.toggle('selected', this.selectedOptions[attributeOfThisButton] === valueOfThisButton);
        });
    }

    updateSelectedNames() {
        this.attributes.forEach(attr => {
            const span = document.getElementById(`selected-${attr.id_slug}`);
            if(span) span.textContent = this.selectedOptions[attr.id_slug] || '';
        });
    }

    updateDetails() {
    const discountBadge = this.dom.basePrice.nextElementSibling;
    this.dom.basePrice.style.display = 'none';
    if (discountBadge) discountBadge.style.display = 'none';
    this.dom.installmentsInfo.style.display = 'none';
    this.dom.installmentsInfo.innerHTML = '';

    if (this.currentVariant) {
        const nuevoSku = this.currentVariant.sku;
        if (this.dom.skuDesktop) this.dom.skuDesktop.textContent = nuevoSku;
        if (this.dom.skuMobile) this.dom.skuMobile.textContent = nuevoSku;
        this.dom.price.textContent = `S/ ${parseFloat(this.currentVariant.price).toFixed(2)}`;
        this.dom.variantIdInput.value = this.currentVariant.id;
        
        const variantPrice = parseFloat(this.currentVariant.price);
        if (this.basePrice && this.basePrice > variantPrice) {
            this.dom.basePrice.textContent = `S/ ${this.basePrice.toFixed(2)}`;
            this.dom.basePrice.style.display = 'inline';
            const discount = Math.round(((this.basePrice - variantPrice) / this.basePrice) * 100);
            if (discountBadge) {
                discountBadge.textContent = `-${discount}%`;
                discountBadge.style.display = 'inline-block';
            }
        }
        if (this.currentVariant.cuotas) {
            const cuotasData = this.currentVariant.cuotas;
            this.dom.installmentsInfo.innerHTML = `<p class="mb-0">O págalo hasta en <strong>${cuotasData.numero} cuotas</strong> de <strong>S/ ${cuotasData.monto_mensual}</strong></p>`;
            this.dom.installmentsInfo.style.display = 'block';
        }

        // --- LÓGICA ORIGINAL RESTAURADA ---
        const inStock = this.currentVariant.is_active && this.currentVariant.stock > 0;
        this.dom.stockInfo.textContent = inStock ? `${this.currentVariant.stock} disponibles` : 'Agotado';
        this.dom.stockInfo.className = inStock ? 'form-text text-success' : 'form-text text-danger';
        this.dom.addToCartBtn.disabled = !inStock;
        this.dom.addToCartBtn.textContent = inStock ? 'Agregar al Carro' : 'Sin Stock';
        
        this.dom.quantityInput.max = this.currentVariant.stock;
        this.updateQuantity(0);

    } else {
        this.dom.addToCartBtn.textContent = 'Elige tus opciones';
        this.dom.addToCartBtn.disabled = true;
        if (this.dom.skuDesktop) this.dom.skuDesktop.textContent = 'N/A';
        if (this.dom.skuMobile) this.dom.skuMobile.textContent = 'N/A';
        this.dom.price.textContent = '';
        this.dom.stockInfo.textContent = 'Selecciona una combinación válida';
    }
}

    updateGallery() {
        this.images = [];
        if (this.currentVariant && this.currentVariant.images.length > 0) {
            this.images = this.currentVariant.images;
        } else {
            const color = this.selectedOptions.color;
            if (color) {
                const variantForImages = this.variants.find(v => v.attribute_options.color === color && v.images.length > 0);
                if (variantForImages) this.images = variantForImages.images;
            }
        }
        
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
            this.dom.thumbnails.innerHTML = '';
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
    
    updateQuantity(change) {
        let qty = (parseInt(this.dom.quantityInput.value) || 0) + change;
        const max = this.currentVariant ? this.currentVariant.stock : 1;
        if (qty < 1) qty = 1;
        if (qty > max) qty = max;
        this.dom.quantityInput.value = qty;
        this.dom.formQuantityInput.value = qty;
    }
}