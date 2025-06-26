// myproducts/static/myproducts/js/admin_spec_loader.js

window.addEventListener('load', function() {
    // Esperamos a que Django cargue sus scripts (si usa jQuery)
    if (typeof django !== 'undefined' && django.jQuery) {
        (function($) {
            $(document).ready(function() {
                setupSpecLoader();
            });
        })(django.jQuery);
    } else {
        // Fallback si no hay jQuery
        setupSpecLoader();
    }
});

function setupSpecLoader() {
    const specTextarea = document.getElementById('id_especificaciones');
    if (!specTextarea) return;

    // Obtener los datos de las plantillas que pasamos desde la vista de admin
    const templatesDataElement = document.getElementById('spec-templates-json-data');
    if (!templatesDataElement) return;

    const specTemplates = JSON.parse(templatesDataElement.textContent);
    
    // Crear el contenedor para nuestros botones
    const container = document.createElement('div');
    container.style.marginTop = '10px';
    container.innerHTML = '<label>Cargar plantilla:</label> ';

    // Crear el select (menú desplegable)
    const select = document.createElement('select');
    select.id = 'spec-template-selector';
    select.innerHTML = '<option value="">-- Seleccionar una plantilla --</option>';
    
    // Obtener los nombres de las plantillas que también pasamos
    const templateOptionsElement = document.getElementById('spec-templates-list');
    if (templateOptionsElement) {
        const templatesList = JSON.parse(templateOptionsElement.textContent);
        templatesList.forEach(tpl => {
            const option = document.createElement('option');
            option.value = tpl.id;
            option.textContent = tpl.name;
            select.appendChild(option);
        });
    }

    // Crear el botón de cargar
    const loadButton = document.createElement('button');
    loadButton.type = 'button';
    loadButton.textContent = 'Cargar';
    loadButton.className = 'button'; // Clase de botón del admin de Django
    loadButton.style.marginLeft = '10px';

    loadButton.addEventListener('click', function() {
        const templateId = select.value;
        if (templateId && specTemplates[templateId]) {
            // Rellenar el textarea con el JSON de la plantilla, bien formateado
            const jsonString = JSON.stringify(specTemplates[templateId], null, 4);
            specTextarea.value = jsonString;
        }
    });
    
    container.appendChild(select);
    container.appendChild(loadButton);

    // Insertar nuestro contenedor justo después del campo de especificaciones
    specTextarea.parentNode.insertBefore(container, specTextarea.nextSibling);
}