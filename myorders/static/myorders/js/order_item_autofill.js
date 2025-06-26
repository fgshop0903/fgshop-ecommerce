        // Si se ha seleccionado una variante (el campo no está vacío)
        if (variantId) {
            // Construimos la URL de nuestra API
            const url = `/myorders/api/variant-details/${variantId}/`;
            
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error(data.error);
                        return;
                    }

                    // Obtenemos el prefijo del ID de la fila actual (ej. "items-0")
                    const idPrefix = variantInput.name.replace('-variant', '');
                    
                    // Buscamos los campos de la misma fila y los rellenamos
                    const nombreProductoInput = document.getElementById(`id_${idPrefix}-nombre_producto`);
                    const precioUnitarioInput = document.getElementById(`id_${idPrefix}-precio_unitario`);
                    const origenProductoInput = document.getElementById(`id_${idPrefix}-origen_producto_item`);

                    if (nombreProductoInput) nombreProductoInput.value = data.nombre_producto;
                    if (precioUnitarioInput) precioUnitarioInput.value = data.precio_unitario;
                    if (origenProductoInput) origenProductoInput.value = data.origen_producto_item;
                })
                .catch(error => console.error('Error al obtener detalles de la variante:', error));
        }