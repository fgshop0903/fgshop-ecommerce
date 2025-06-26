document.addEventListener('DOMContentLoaded', () => {

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    function sendAjaxRequest(url, formData) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                // Si hay un error, intentamos leer el JSON del cuerpo para mostrar un mensaje más específico
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (data.summary_html) {
                    const summaryContainer = document.getElementById('order-summary-content');
                    if (summaryContainer) {
                        summaryContainer.innerHTML = data.summary_html;
                    }
                }
                const whatsappBtn = document.getElementById('whatsapp-confirm-btn');
                if (whatsappBtn) {
                    whatsappBtn.href = data.whatsapp_url || "";
                    if (data.has_selected_items === true) {
                        whatsappBtn.classList.remove('disabled');
                    } else {
                        whatsappBtn.classList.add('disabled');
                    }
                }
            }
            return data;
        })
        .catch(errorData => {
            console.error('Error AJAX:', errorData);
            if (errorData && errorData.error) {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: errorData.error,
                });
            } else {
                alert('Hubo un error de conexión. Inténtalo de nuevo.');
            }
            return Promise.reject(errorData);
        });
    }

    function updateMasterCheckboxState(cardBody) {
        if (!cardBody) return;
        const masterCheckbox = document.querySelector(`[data-card-body-id="${cardBody.id}"]`);
        if (!masterCheckbox) return;
        const allCheckboxes = cardBody.querySelectorAll('.item-checkbox');
        masterCheckbox.checked = Array.from(allCheckboxes).every(cb => cb.checked);
    }

    // --- LISTENERS DE EVENTOS ---

    // 1. Delegación de eventos para CLICKS
    document.body.addEventListener('click', e => {
        if (e.target.closest('.quantity-btn')) {
            e.preventDefault();
            const button = e.target.closest('.quantity-btn');
            const targetInput = document.querySelector(button.dataset.target);
            if (!targetInput) return;

            const change = parseInt(button.dataset.change, 10);
            let currentValue = parseInt(targetInput.value, 10);
            let newValue = currentValue + change;
            const maxValue = parseInt(targetInput.max, 10);

            if (newValue < 1) newValue = 1;
            if (!isNaN(maxValue) && newValue > maxValue) {
                // NUEVO CÓDIGO CON SWEETALERT2
                Swal.fire({
                    icon: 'warning', // Icono de advertencia
                    title: 'Stock no disponible',
                    text: `No puedes pedir más de ${maxValue} unidades.`,
                    toast: true, // Lo convierte en una notificación pequeña tipo "toast"
                    position: 'top-end', // Posición en la esquina superior derecha
                    showConfirmButton: false, // Oculta el botón de "OK"
                    timer: 3000, // Se cierra automáticamente después de 3 segundos
                    timerProgressBar: true, // Muestra una barra de progreso
                });
                newValue = maxValue;
            }

            if (newValue !== currentValue) {
                targetInput.value = newValue;
                const form = targetInput.closest('form');
                sendAjaxRequest(form.action, new FormData(form));
            }
        }
    });

    // 2. Delegación de eventos para CAMBIOS (inputs, checkboxes)
    document.body.addEventListener('change', e => {
        // Listener para checkboxes de items individuales
        if (e.target.matches('.item-checkbox')) {
            const checkbox = e.target;
            const variantId = checkbox.value;
            const isSelected = checkbox.checked;
            const formData = new FormData();
            formData.append('selected', isSelected);

            sendAjaxRequest(`/carrito/toggle-selection/${variantId}/`, formData)
                .then(() => {
                    const cardBody = checkbox.closest('.card-body');
                    updateMasterCheckboxState(cardBody);
                });
        }

        // Listener para checkboxes "Seleccionar todos"
        if (e.target.matches('.select-all-supplier')) {
            const masterCheckbox = e.target;
            const cardBody = document.getElementById(masterCheckbox.dataset.cardBodyId);
            if (!cardBody) return;

            const isSelected = masterCheckbox.checked;
            const variantIdsToToggle = [];

            cardBody.querySelectorAll('.item-checkbox').forEach(itemCheckbox => {
                itemCheckbox.checked = isSelected;
                variantIdsToToggle.push(itemCheckbox.value);
            });

            if (variantIdsToToggle.length > 0) {
                const formData = new FormData();
                formData.append('selected', isSelected);
                variantIdsToToggle.forEach(id => formData.append('variant_ids[]', id));
                sendAjaxRequest('/carrito/bulk-toggle-selection/', formData);
            }
        }

        if (e.target.matches('.quantity-input')) {
            const input = e.target;
            let currentValue = parseInt(input.value, 10);
            const maxValue = parseInt(input.max, 10);
            let valueToUpdate = currentValue;

            // Validar que no sea menor que 1
            if (isNaN(currentValue) || currentValue < 1) {
                valueToUpdate = 1;
            }
            
            // Validar contra el stock máximo
            if (!isNaN(maxValue) && currentValue > maxValue) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Stock no disponible',
                    text: `Solo quedan ${maxValue} unidades disponibles.`,
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3500,
                    timerProgressBar: true,
                });
                valueToUpdate = maxValue;
            }
            
            // Actualizar el valor del input si se corrigió
            input.value = valueToUpdate;

            // Enviar la petición AJAX
            const form = input.closest('form');
            if (form) {
                // Creamos un nuevo FormData para asegurarnos de que usa el valor corregido
                const formData = new FormData(form);
                formData.set('quantity', valueToUpdate);
                sendAjaxRequest(form.action, formData);
            }
        }
    });

    document.body.addEventListener('keydown', e => {
        // Verificamos si la tecla Enter se presionó en un input de cantidad
        if (e.target.matches('.quantity-input') && e.keyCode === 13) { // <-- CAMBIO AQUÍ
            // Prevenimos la acción por defecto (enviar el formulario)
            e.preventDefault();
            // Le quitamos el foco al input para que se dispare el evento 'change'
            e.target.blur();
        }
    });
    
    // Sincronizar todos los checkboxes maestros al cargar
    document.querySelectorAll('.select-all-supplier').forEach(masterCheckbox => {
        const cardBody = document.getElementById(masterCheckbox.dataset.cardBodyId);
        updateMasterCheckboxState(cardBody);
    });
});