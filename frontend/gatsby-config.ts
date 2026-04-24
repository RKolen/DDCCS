import type { GatsbyConfig } from 'gatsby';
import dotenv from 'dotenv';

dotenv.config({ path: `.env.${process.env.NODE_ENV ?? 'development'}` });

const config: GatsbyConfig = {
  siteMetadata: {
    title: 'D&D Character Consultant',
    siteUrl: 'http://localhost:8000',
  },
  // Proxy /api/* to Drupal during development — avoids browser cert/CORS issues.
  plugins: [
    {
      resolve: 'gatsby-source-drupal',
      options: {
        baseUrl: process.env.DRUPAL_BASE_URL ?? 'https://drupal-cms.ddev.site',
        apiBase: 'jsonapi',
        basicAuth: {
          username: process.env.DRUPAL_USER,
          password: process.env.DRUPAL_PASSWORD,
        },
        fastBuilds: true,
        // Only pull published content.
        params: {
          'filter[status]': 1,
        },
      },
    },
    'gatsby-plugin-image',
    'gatsby-plugin-sharp',
    'gatsby-transformer-sharp',
  ],
};

export default config;
