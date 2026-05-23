import type { GatsbyConfig } from 'gatsby';
import dotenv from 'dotenv';
import path from 'node:path';

// Load shared service credentials from the project root first, then let
// frontend-specific env files fill in browser/site settings.
// dotenv does not override variables already in process.env.
dotenv.config({ path: path.resolve(__dirname, '..', '.env') });
dotenv.config({ path: `.env.${process.env.NODE_ENV ?? 'development'}` });
dotenv.config({ path: '.env.development' });

// Prefer GATSBY_DRUPAL_BASE_URL (set in .env.development as HTTP to avoid
// Node.js rejecting DDEV's self-signed cert) over the shared DRUPAL_BASE_URL.
const DRUPAL_URL  = process.env.GATSBY_DRUPAL_BASE_URL ?? process.env.DRUPAL_BASE_URL;
const DRUPAL_TOKEN = process.env.DRUPAL_GRAPHQL_TOKEN;
const SITE_URL    = process.env.SITE_URL;
const SITE_TITLE  = process.env.SITE_TITLE;

if (!DRUPAL_URL) {
  throw new Error('DRUPAL_BASE_URL is required but not set in the environment.');
}
if (!SITE_URL) {
  throw new Error('SITE_URL is required but not set in the environment.');
}

const authHeader = DRUPAL_TOKEN
  ? `Bearer ${DRUPAL_TOKEN}`
  : undefined;

const config: GatsbyConfig = {
  siteMetadata: {
    title: SITE_TITLE ?? 'D&D Campaign Console',
    siteUrl: SITE_URL,
  },
  plugins: [
    {
      resolve: 'gatsby-source-graphql',
      options: {
        typeName: 'Drupal',
        fieldName: 'drupal',
        url: `${DRUPAL_URL}/graphql`,
        headers: authHeader ? { Authorization: authHeader } : {},
        // Poll Drupal every 30 s in dev so content changes propagate
        // without needing a manual restart. /__refresh provides the
        // immediate push; refetchInterval is the fallback safety net.
        refetchInterval: 30,
      },
    },
    'gatsby-plugin-image',
    'gatsby-plugin-sharp',
    'gatsby-transformer-sharp',
  ],
};

export default config;
