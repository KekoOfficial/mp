const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

// --- CONFIGURACIÓN DE SEGURIDAD MP ---
app.use(express.json());
app.use(cookieParser());
app.use(session({
    secret: 'CLAVE_SECRETA_IMPERIO_MP_2026',
    resave: false,
    saveUninitialized: true,
    cookie: { maxAge: 3600000 } // 1 hora de sesión
}));

// Servidor de archivos estáticos (CSS/JS)
app.use(express.static(path.join(__dirname, 'static')));

// --- MIDDLEWARE DE PROTECCIÓN ---
const authMiddleware = (req, res, next) => {
    if (req.session.isLogged) {
        next();
    } else {
        res.redirect('/');
    }
};

// --- RUTAS DE NAVEGACIÓN ---

// 1. Portal Principal
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'login.html'));
});

// 2. Login Global (Sistema 2)
app.get('/login_global', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'login2.html'));
});

// 3. Lógica de Autenticación (POST)
app.post('/auth/login', (req, res) => {
    const { u, p } = req.body;
    // Lógica para Martín Mp y sus 10 Admins
    if ((u === 'MartinMp' || u.startsWith('admin')) && p === '1234') {
        req.session.isLogged = true;
        req.session.user = u;
        res.json({ success: true, redirect: '/panel_admin' });
    } else {
        res.json({ success: false, msg: 'ACCESO DENEGADO' });
    }
});

// 4. Panel V10 (PROTEGIDO)
app.get('/panel_admin', authMiddleware, (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'set.html'));
});

// 5. Chat Global 5.9K (PROTEGIDO)
app.get('/chat_global', authMiddleware, (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'global_chat.html'));
});

// --- PUENTE DE DATOS ULTRA (API BRIDGE) ---
app.post('/api/bridge', (req, res) => {
    const data = req.body;
    
    // Inyectar datos en el flujo de Socket.io
    io.emit('server_event', {
        ...data,
        timestamp: new Date().toLocaleTimeString()
    });

    // Log en consola con formato de matriz
    console.log(`\n[📡 BRIDGE] ${data.sistema} | USUARIO: ${data.user} | MSG: ${data.msg}`);
    
    res.sendStatus(200);
});

// --- GESTIÓN DE TIEMPO REAL ---
let activeConnections = 0;
io.on('connection', (socket) => {
    activeConnections++;
    io.emit('stats_update', { online: activeConnections });
    console.log(`🔌 NODO CONECTADO. TOTAL: ${activeConnections}`);

    socket.on('disconnect', () => {
        activeConnections--;
        io.emit('stats_update', { online: activeConnections });
    });
});

// --- ARRANQUE DEL SISTEMA ---
const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
    console.clear();
    const banner = `
    ██╗███╗   ███╗██████╗ ███████╗██████╗ ██╗ ██████╗ 
    ██║████╗ ████║██╔══██╗██╔════╝██╔══██╗██║██╔═══██╗
    ██║██╔████╔██║██████╔╝█████╗  ██████╔╝██║██║   ██║
    ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  ██╔══██╗██║██║   ██║
    ██║██║ ╚═╝ ██║██║     ███████╗██║  ██║██║╚██████╔╝
    ╚═╝╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ 
    `;
    console.log("\x1b[32m%s\x1b[0m", banner);
    console.log(`🚩 STATUS:  SISTEMA MP V10 - ACTIVO`);
    console.log(`🌐 ACCESO:  http://localhost:${PORT}`);
    console.log(`🛡️  PROTECCIÓN: SESIONES Y COOKIES ACTIVADAS`);
    console.log(`👥 MIEMBROS: 5,975 CONFIGURADOS\n`);
});
