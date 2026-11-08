// Login form: POST credentials; the server answers with an HttpOnly session cookie.
document.getElementById('loginForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const errorBox = document.getElementById('loginError');
    errorBox.textContent = '';
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                username: document.getElementById('username').value,
                password: document.getElementById('password').value,
            }),
        });
        if (response.ok) {
            window.location.href = '/';
        } else if (response.status === 429) {
            errorBox.textContent = 'Demasiados intentos. Espere un minuto.';
        } else {
            errorBox.textContent = 'Credenciales no válidas.';
        }
    } catch (err) {
        errorBox.textContent = 'No se pudo contactar con el servidor.';
    }
});
