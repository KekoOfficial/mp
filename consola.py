const express = require('express');
const path = require('path');
const app = express();
app.use(express.json());
app.use(express.static('static'));

// --- RUTAS DE NAVEGACIÓN ---

// Portal de Entrada
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'templates/login.html')));

// Acceso al Segundo Sistema (5.9K)
app.get('/login_global', (req, res) => res.sendFile(path.join(__dirname, 'templates/login2.html')));

// Dashboards
app.get('/panel_admin', (req, res) => res.sendFile(path.join(__dirname, 'templates/set.html')));
app.get('/chat_global', (req, res) => res.sendFile(path.join(__dirname, 'templates/global_chat.html')));

// --- COMUNICACIÓN ENTRE BOTS ---
app.post('/api/bridge', (req, res) => {
    const { from, message, target } = req.body;
    console.log(`[BRIDGE] Mensaje de ${from} hacia ${target}: ${message}`);
    // Aquí puedes guardar logs o reenviar a bases de datos
    res.json({ status: "Entregado al núcleo MP" });
});

app.listen(4000, () => console.log("🚀 IMPERIO MP: MULTI-CORE ONLINE (PORT 4000)"));
