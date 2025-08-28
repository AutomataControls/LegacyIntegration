/*
 * AutomataControls™ Remote Portal - Server
 * Copyright © 2024 AutomataNexus, LLC. All rights reserved.
 * 
 * PROPRIETARY AND CONFIDENTIAL
 * This software is proprietary to AutomataNexus and constitutes valuable 
 * trade secrets. This software may not be copied, distributed, modified, 
 * or disclosed to third parties without prior written authorization from 
 * AutomataNexus. Use of this software is governed by a commercial license
 * agreement. Unauthorized use is strictly prohibited.
 * 
 * AutomataNexusBms Controller Software
 */

require('dotenv').config();
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const fs = require('fs');
const app = express();
const server = require('http').createServer(app);
const io = require('socket.io')(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
    methods: ["GET", "POST"]
  }
});
const pty = require('node-pty');
const { Resend } = require('resend');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const winston = require('winston');

// Initialize Resend with API key
const resend = new Resend(process.env.RESEND_API);

// Logger configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

if (process.env.LOG_TO_FILE === 'true') {
  logger.add(new winston.transports.File({ 
    filename: path.join(process.env.LOG_PATH || '/var/log', 'automata-portal.log')
  }));
}

// Security middleware
app.use(helmet({
  contentSecurityPolicy: false // Disabled for iframe compatibility
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT || '100')
});
app.use('/api', limiter);

// JSON middleware
app.use(express.json());

// Authentication middleware
const authenticateRequest = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey || apiKey !== process.env.API_AUTH_KEY) {
    logger.warn(`Unauthorized access attempt from ${req.ip}`);
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  next();
};

// Apply authentication to API routes
app.use('/api', authenticateRequest);

// Store terminal sessions
const terminals = {};

// Serve static files
app.use('/static', express.static(path.join(__dirname, 'public')));
app.use('/assets', express.static(path.join(__dirname, 'public/assets')));

// System info endpoint
app.get('/api/system-info', async (req, res) => {
  const { exec } = require('child_process');
  const util = require('util');
  const execPromise = util.promisify(exec);
  
  try {
    const hostname = require('os').hostname();
    const uptime = require('os').uptime();
    
    // Get CPU temp (Raspberry Pi specific)
    const cpuTemp = await execPromise('vcgencmd measure_temp')
      .then(r => r.stdout.trim().split('=')[1])
      .catch(() => 'N/A');
    
    // Get memory info
    const memInfo = await execPromise('free -m').then(r => {
      const lines = r.stdout.split('\n');
      const mem = lines[1].split(/\s+/);
      return {
        total: parseInt(mem[1]),
        used: parseInt(mem[2]),
        free: parseInt(mem[3]),
        percent: Math.round((parseInt(mem[2]) / parseInt(mem[1])) * 100)
      };
    });
    
    // Get disk usage
    const diskInfo = await execPromise('df -h /').then(r => {
      const lines = r.stdout.split('\n');
      const disk = lines[1].split(/\s+/);
      return {
        total: disk[1],
        used: disk[2],
        available: disk[3],
        percent: parseInt(disk[4])
      };
    });
    
    // Get CPU usage
    const cpuUsage = await execPromise("top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'")
      .then(r => parseFloat(r.stdout.trim()))
      .catch(() => 0);
    
    res.json({
      hostname,
      serial: process.env.CONTROLLER_SERIAL || 'AutomataNexusBms-XXXXXX',
      location: process.env.LOCATION || 'Unknown',
      uptime: Math.floor(uptime),
      cpu_temp: cpuTemp,
      cpu_usage: cpuUsage.toFixed(1),
      mem_total: memInfo.total,
      mem_used: memInfo.used,
      mem_free: memInfo.free,
      mem_percent: memInfo.percent,
      disk_total: diskInfo.total,
      disk_used: diskInfo.used,
      disk_available: diskInfo.available,
      disk_percent: diskInfo.percent,
      timestamp: new Date().toISOString()
    });
    
    logger.info('System info requested');
  } catch (error) {
    logger.error('System info error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Weather API endpoint
app.get('/api/weather', async (req, res) => {
  if (process.env.WEATHER_ENABLED !== 'true') {
    return res.json({
      temperature: 72,
      condition: 'Weather Disabled',
      humidity: 0,
      location: process.env.LOCATION || 'Local',
      icon: '01d'
    });
  }
  
  try {
    const axios = require('axios');
    const location = process.env.WEATHER_LOCATION || 'New York,US';
    const units = process.env.WEATHER_UNITS || 'imperial';
    const apiKey = process.env.OPENWEATHER_API;
    
    const response = await axios.get(
      `https://api.openweathermap.org/data/2.5/weather?q=${location}&units=${units}&appid=${apiKey}`
    );
    
    const data = response.data;
    res.json({
      temperature: Math.round(data.main.temp),
      condition: data.weather[0].main,
      humidity: data.main.humidity,
      location: data.name,
      icon: data.weather[0].icon,
      windSpeed: Math.round(data.wind.speed),
      windDirection: data.wind.deg,
      pressure: data.main.pressure,
      feelsLike: Math.round(data.main.feels_like)
    });
  } catch (error) {
    logger.error('Weather API error:', error);
    res.json({
      temperature: 72,
      condition: 'API Error',
      humidity: 65,
      location: 'Local',
      icon: '01d'
    });
  }
});

// Email notification endpoint
app.post('/api/notifications', async (req, res) => {
  const { subject, message, type } = req.body;
  
  try {
    const emailHtml = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #0f1823 0%, #1a2332 100%); padding: 20px; border-radius: 8px 8px 0 0;">
          <h1 style="color: #06b6d4; margin: 0;">AutomataNexusBms Controller Alert</h1>
        </div>
        <div style="background: #f5f5f5; padding: 20px;">
          <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid ${
            type === 'error' ? '#ef4444' : 
            type === 'warning' ? '#f59e0b' : 
            type === 'info' ? '#3b82f6' : '#10b981'
          };">
            <h2 style="color: #1e293b; margin-top: 0;">${subject}</h2>
            <p style="color: #475569; line-height: 1.6;">${message}</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            <p style="color: #94a3b8; font-size: 12px;">
              Controller: ${process.env.CONTROLLER_SERIAL || 'Unknown'}<br>
              Location: ${process.env.LOCATION || 'Unknown'}<br>
              Timestamp: ${new Date().toISOString()}
            </p>
          </div>
        </div>
        <div style="background: #1a2332; color: #64748b; padding: 15px; text-align: center; font-size: 12px;">
          © 2024 AutomataNexus, LLC. All rights reserved.
        </div>
      </div>
    `;
    
    const { data, error } = await resend.emails.send({
      from: process.env.EMAIL_FROM || 'noreply@automatacontrols.com',
      to: process.env.EMAIL_ADMIN || 'admin@automatacontrols.com',
      subject: `[${type.toUpperCase()}] ${subject}`,
      html: emailHtml
    });
    
    if (error) {
      throw error;
    }
    
    logger.info(`Email notification sent: ${subject}`);
    res.json({ success: true, messageId: data.id });
  } catch (error) {
    logger.error('Email notification error:', error);
    res.status(500).json({ error: 'Failed to send notification' });
  }
});

// Proxy Node-RED with authentication bypass for local access
app.use('/node-red', createProxyMiddleware({
  target: 'http://localhost:1880',
  changeOrigin: true,
  ws: true,
  pathRewrite: {
    '^/node-red': ''
  },
  onProxyReq: (proxyReq, req, res) => {
    proxyReq.setHeader('X-Forwarded-Host', req.headers.host);
    proxyReq.setHeader('X-Forwarded-Proto', req.protocol);
  }
}));

// Socket.IO terminal handling
io.on('connection', (socket) => {
  logger.info(`Terminal connection established: ${socket.id}`);
  
  socket.on('terminal-init', (data) => {
    const term = pty.spawn('bash', [], {
      name: 'xterm-256color',
      cols: data.cols || 80,
      rows: data.rows || 24,
      cwd: process.env.HOME,
      env: process.env
    });
    
    terminals[socket.id] = term;
    
    term.onData((data) => {
      socket.emit('terminal-output', data);
    });
    
    // Send welcome message with branding
    const serial = process.env.CONTROLLER_SERIAL || 'AutomataNexusBms-XXXXXX';
    socket.emit('terminal-output', '\x1b[1;36m╔═══════════════════════════════════════════════════════╗\r\n');
    socket.emit('terminal-output', '\x1b[1;36m║     AutomataControls™ Neural Terminal v2.0           ║\r\n');
    socket.emit('terminal-output', `\x1b[1;36m║     Controller: ${serial.padEnd(38)}║\r\n`);
    socket.emit('terminal-output', '\x1b[1;36m║     © 2024 AutomataNexus, LLC. All Rights Reserved   ║\r\n');
    socket.emit('terminal-output', '\x1b[1;36m╚═══════════════════════════════════════════════════════╝\x1b[0m\r\n\r\n');
  });
  
  socket.on('terminal-input', (data) => {
    if (terminals[socket.id]) {
      terminals[socket.id].write(data);
    }
  });
  
  socket.on('terminal-resize', (data) => {
    if (terminals[socket.id]) {
      terminals[socket.id].resize(data.cols, data.rows);
    }
  });
  
  socket.on('disconnect', () => {
    logger.info(`Terminal disconnected: ${socket.id}`);
    if (terminals[socket.id]) {
      terminals[socket.id].kill();
      delete terminals[socket.id];
    }
  });
});

// Serve the React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
const PORT = process.env.PORT || 8000;
const HOST = process.env.HOST || '0.0.0.0';

server.listen(PORT, HOST, () => {
  logger.info(`
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     AutomataControls™ Remote Portal v2.0                     ║
║     AutomataNexusBms Controller Software                     ║
║                                                               ║
║     Server running on: http://${HOST}:${PORT}                    ║
║     Node-RED proxy: http://localhost:${PORT}/node-red            ║
║                                                               ║
║     © 2024 AutomataNexus, LLC. All Rights Reserved           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
  `);
});