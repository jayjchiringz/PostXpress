// Make sure this script is properly included and loads after the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarCollapse');
    const content = document.getElementById('content'); // Add content container

    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('active'); // Toggle sidebar width
        content.classList.toggle('active'); // Adjust content width
    });
});

