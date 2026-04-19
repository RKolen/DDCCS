import * as React from 'react';
import type { HeadFC, PageProps } from 'gatsby';

const IndexPage: React.FC<PageProps> = () => (
  <main>
    <h1>D&amp;D Character Consultant</h1>
    <p>Gatsby frontend — connected to Drupal CMS.</p>
  </main>
);

export const Head: HeadFC = () => <title>D&amp;D Character Consultant</title>;

export default IndexPage;
