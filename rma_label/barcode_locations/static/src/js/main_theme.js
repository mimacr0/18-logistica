document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');
    const htmlElement = document.documentElement;

    const updateIcons = (isLight) => {
        if (isLight) {
            darkIcon.classList.remove('theme-icon-active');
            darkIcon.classList.add('theme-icon-inactive');
            lightIcon.classList.remove('theme-icon-inactive');
            lightIcon.classList.add('theme-icon-active');
        } else {
            darkIcon.classList.remove('theme-icon-inactive');
            darkIcon.classList.add('theme-icon-active');
            lightIcon.classList.remove('theme-icon-active');
            lightIcon.classList.add('theme-icon-inactive');
        }
    };

    // Initialize theme
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
    const isLightInitial = savedTheme === 'light' || (!savedTheme && systemPrefersLight);

    if (isLightInitial) {
        htmlElement.classList.add('light');
    }
    updateIcons(isLightInitial);

    themeToggleBtn.addEventListener('click', () => {
        const isLight = htmlElement.classList.toggle('light');
        updateIcons(isLight);
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    });
});
