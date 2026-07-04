// Interacciones Dinámicas del Panel Administrativo de Salvador
document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Confirmación de seguridad antes de eliminar un platillo del menú
    const deleteButtons = document.querySelectorAll(".btn-danger");
    
    if (deleteButtons.length > 0) {
        deleteButtons.forEach(button => {
            button.addEventListener("click", (e) => {
                const confirmar = confirm("¿Estás seguro de que deseas eliminar este platillo del menú activo?");
                if (!confirmar) {
                    e.preventDefault(); // Cancela la acción (el redireccionamiento) si el admin dice que no
                }
            });
        });
    }

    // 2. Alerta visual rápida y envío automático al cambiar el estado de una habitación
    const statusSelectors = document.querySelectorAll(".room-status-select");
    
    if (statusSelectors.length > 0) {
        statusSelectors.forEach(select => {
            select.addEventListener("change", (e) => {
                const nuevoEstado = e.target.value;
                if (nuevoEstado) {
                    console.log(`Enviando actualización de estatus: ${nuevoEstado}`);
                    // Opcional: puedes añadir un mensaje temporal en consola o pantalla antes de recargar
                }
            });
        });
    }
});