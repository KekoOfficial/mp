const express = require('express');
const app = express();
const path = require('path');

app.use(express.static('static'));
app.use(express.json());

// 1. LA ENTRADA (LOGIN AVANZADO)
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates/login.html'));
});

// 2. SISTEMA ALFA (Admin V10 - 10 Usuarios)
app.get('/panel_admin', (req, res) => {
    // Aquí puedes añadir validación de contraseña después
    res.sendFile(path.join(__dirname, 'templates/set.html'));
});

// 3. SISTEMA BETA (Chat Global - 5975 Miembros)
app.get('/chat_global', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates/global_chat.html'));
});

app.listen(process.env.PORT || 4000, () => {
    console.log("🚀 MULTI-SISTEMA MP ONLINE");
});
