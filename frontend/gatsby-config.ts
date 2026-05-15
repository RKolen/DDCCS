import type { GatsbyConfig } from 'gatsby';
import dotenv from 'dotenv';

// Load env-specific file first, then fall back to .env.development for any
// unset values. dotenv does not override variables already in process.env.
dotenv.config({ path: `.env.${process.env.NODE_ENV ?? 'development'}` });
dotenv.config({ path: '.env.development' });

const DRUPAL_URL  = process.env.DRUPAL_BASE_URL;
const DRUPAL_USER = process.env.DRUPAL_USER;
const DRUPAL_PASS = process.env.DRUPAL_PASSWORD;
const SITE_URL    = process.env.SITE_URL;
const SITE_TITLE  = process.env.SITE_TITLE;

if (!DRUPAL_URL) {
  throw new Error('DRUPAL_BASE_URL is required but not set in the environment.');
}
if (!SITE_URL) {
  throw new Error('SITE_URL is required but not set in the environment.');
}

const authHeader = DRUPAL_USER && DRUPAL_PASS
  ? `Basic ${Buffer.from(`${DRUPAL_USER}:${DRUPAL_PASS}`).toString('base64')}`
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
      },
    },
    'gatsby-plugin-image',
    'gatsby-plugin-sharp',
    'gatsby-transformer-sharp',
  ],
};

export default config;
