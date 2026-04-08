/**
 * Proxy middleware for social media crawler detection.
 * Intercepts requests from Facebook, Twitter, LinkedIn etc. and serves
 * pre-rendered HTML with OG meta tags from the backend.
 */
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

module.exports = function(app) {
  app.use((req, res, next) => {
    const ua = req.headers['user-agent'] || '';
    const path = req.path;

    // Only intercept non-API, non-static paths from crawlers
    if (path.startsWith('/api') || path.startsWith('/static') || path.includes('.')) {
      return next();
    }

    if (!CRAWLER_REGEX.test(ua)) {
      return next();
    }

    // Check if the path matches a route with OG support
    const matchesOgRoute = OG_ROUTES.some(r => r.test(path));
    if (!matchesOgRoute) {
      return next();
    }

    // Fetch OG HTML from backend
    const backendUrl = `http://0.0.0.0:8001/api/og-preview?path=${encodeURIComponent(path)}`;
    const http = require('http');

    http.get(backendUrl, (backendRes) => {
      if (backendRes.statusCode === 200) {
        let body = '';
        backendRes.on('data', chunk => { body += chunk; });
        backendRes.on('end', () => {
          res.setHeader('Content-Type', 'text/html; charset=utf-8');
          res.status(200).send(body);
        });
      } else {
        // Fall through to React SPA
        next();
      }
    }).on('error', () => {
      next();
    });
  });
};
