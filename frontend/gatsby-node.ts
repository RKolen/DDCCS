import * as https from 'https';
import type { GatsbyNode } from 'gatsby';
import { createProxyMiddleware } from 'http-proxy-middleware';

const DRUPAL_URL = 'https://drupal-cms.ddev.site';

// Accept DDEV's locally-signed certificate in the dev proxy.
// This agent is only used for the server-side proxy — never reaches the browser.
const devAgent = new https.Agent({ rejectUnauthorized: false });

export const onCreateDevServer: GatsbyNode['onCreateDevServer'] = ({ app }) => {
  app.use(
    createProxyMiddleware({
      target: DRUPAL_URL,
      changeOrigin: true,
      agent: devAgent,
      pathFilter: '/api',
      // Tell Drupal the connection is HTTPS so basic_auth doesn't redirect to
      // HTTPS when an Authorization header is present.
      headers: { 'X-Forwarded-Proto': 'https' },
    }),
  );
};
