/**
 * Production-ready Express server for NoFeesApts.com
 * 
 * Handles:
 * 1. Social media crawler detection → serves pre-rendered OG HTML from backend
 * 2. Static file serving from the CRA build directory
 * 3. SPA fallback (index.html) for all client-side routes
 */
const express = require('express');
const path = require('path');
const http = require('http');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const HOST = process.env.HOST || '0.0.0.0';
const BACKEND_URL = 'http://0.0.0.0:8001';

const CRAWLER_REGEX = /facebookexternalhit|Facebot|Twitterbot|LinkedInBot|Slackbot|WhatsApp|TelegramBot|Discordbot|Pinterest|vkShare|Viber|Googlebot|bingbot|Applebot|iMessage|SkypeUriPreview|Embedly|Quora Link Preview|redditbot|Rogerbot|SummalyBot|Slurp/i;

const OG_ROUTES = [
  /^\/unit\/.+$/,
  /^\/apartments\/.+$/,
  /^\/(brooklyn|manhattan|queens|new-jersey|bronx|hoboken|jersey-city)$/,
  /^\/$/,
  /^\/neighborhoods$/,
  /^\/blog$/,
  /^\/fee-free-finds$/,
];

const buildDir = path.join(__dirname, 'build');

// Crawler detection middleware
app.use((req, res, next) => {
  const ua = req.headers['user-agent'] || '';
  const reqPath = req.path;

  // Skip API, static assets, and file requests
  if (reqPath.startsWith('/api') || reqPath.startsWith('/static') || reqPath.includes('.')) {
    return next();
  }

  if (!CRAWLER_REGEX.test(ua)) {
    return next();
  }

  const matchesOgRoute = OG_ROUTES.some(r => r.test(reqPath));
  if (!matchesOgRoute) {
    return next();
  }

  // Fetch OG HTML from backend
  const ogUrl = `${BACKEND_URL}/api/og-preview?path=${encodeURIComponent(reqPath)}`;
  
  http.get(ogUrl, (backendRes) => {
    if (backendRes.statusCode === 200) {
      let body = '';
      backendRes.on('data', chunk => { body += chunk; });
      backendRes.on('end', () => {
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.status(200).send(body);
      });
    } else {
      next();
    }
  }).on('error', () => {
    next();
  });
});

// Serve static files from build directory
app.use(express.static(buildDir));

// SPA fallback - serve index.html for all unmatched routes
app.get('*', (req, res) => {
  const indexPath = path.join(buildDir, 'index.html');
  if (fs.existsSync(indexPath)) {
    res.sendFile(indexPath);
  } else {
    res.status(404).send('Build not found. Run "yarn build" first.');
  }
});

app.listen(PORT, HOST, () => {
  console.log(`NoFeesApts frontend server running on ${HOST}:${PORT}`);
  console.log(`OG crawler detection: active`);
  console.log(`Serving static build from: ${buildDir}`);
});
