

document.addEventListener('DOMContentLoaded', function() {
    
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    
    const appointmentDateFields = document.querySelectorAll('.appointment-date');
    if (appointmentDateFields.length > 0) {
        appointmentDateFields.forEach(field => {
            field.addEventListener('change', function() {
                console.log('Appointment date selected:', this.value);
                
            });
        });
    }
    
    
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            setTimeout(() => {
                const closeButton = message.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.click();
                }
            }, 5000); 
        });
    }
    
    
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
   
    const dynamicContentContainers = document.querySelectorAll('[data-dynamic-content]');
    if (dynamicContentContainers.length > 0) {
        dynamicContentContainers.forEach(container => {
            const endpoint = container.getAttribute('data-endpoint');
            if (endpoint) {
                console.log('Would load content from:', endpoint);
                
            }
        });
    }
});