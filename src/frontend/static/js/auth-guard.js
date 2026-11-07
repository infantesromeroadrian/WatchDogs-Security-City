// Sends the user to the login page whenever the API answers 401 (expired or missing session).
(function () {
    const originalFetch = window.fetch.bind(window);
    window.fetch = async function (...args) {
        const response = await originalFetch(...args);
        const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
        if (response.status === 401 && url.includes('/api/') && !url.includes('/api/auth/login')) {
            window.location.href = '/login';
        }
        return response;
    };
})();
