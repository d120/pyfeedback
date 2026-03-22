window.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('theme-button');

    if (!btn) return;
    
    btn.addEventListener('click', () => {
        const html = document.documentElement;
        const isDark = html.classList.contains('dark');
        const newTheme = isDark ? 'light' : 'dark';

        html.classList.remove('light', 'dark');
        html.classList.add(newTheme);

        localStorage.setItem('theme', newTheme);
    });
});

document.querySelector('.dropdown-trigger').addEventListener('click', function(e) {
    e.preventDefault();
    this.parentElement.querySelector('.dropdown-content').classList.toggle('show');
});