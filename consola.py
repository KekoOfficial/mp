const express = require('express');
const path = require('path');
const app = express();

// Importante: Para que lea el cuerpo de las peticiones de los bots
app.use(express.json());
app.use(express.static('static'));

// --- RUTA 1: PORTAL PRINCIPAL ---
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates/login.html'));
});

// --- RUTA 2: EL PUENTE HACIA EL CHAT GLOBAL (SOLUCIONA TU ERROR) ---
app.get('/login_global', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates/login2.html'));
});

// --- RUTA 3: DASHBOARD DE LOS 5,975 MIEMBROS ---
app.get('/chat_global', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates/global_chat.html'));
});

// --- RUTA 4: PANEL V10 (ADMINS) ---
app.get('/panel_admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates/set.html'));
});

// --- API BRIDGE (RECIBE DATOS DE BOT.PY Y BOT2.PY) ---
app.post('/api/bridge', (req, res) => {
    const data = req.body;
    console.log(`[MP-SYSTEM] Datos recibidos de: ${data.sistema || 'BOT'}`);
    res.sendStatus(200);
});

// Puerto de salida
const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
    console.log(`🚀 IMPERIO MP: NÚCLEOS SINCRONIZADOS EN PUERTO ${PORT}`);
});
