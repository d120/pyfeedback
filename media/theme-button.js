const btn = document.getElementById('theme-button');

btn.addEventListener('click', () => {
    const body = document.body;

    if (body.classList.contains('light')) {
        body.classList.replace('light', 'dark');
    } else {
        body.classList.replace('dark', 'light');
    }
});