window.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('theme-button');
    if (!btn) return;

    const root = document.documentElement;

    const applyTheme = (theme) => {
        root.classList.remove('light', 'dark');
        root.classList.add(theme);
    };

    btn.addEventListener('click', () => {
        const current = root.classList.contains('dark') ? 'dark' : 'light';
        const next = current === 'dark' ? 'light' : 'dark';

        applyTheme(next);
        localStorage.setItem('theme', next);
    });
});

document.querySelector('.dropdown-trigger').addEventListener('click', function(e) {
    e.preventDefault();
    this.parentElement.querySelector('.dropdown-content').classList.toggle('show');
});