import './src/styles/reset.css';
import './src/styles/tokens.css';
import './src/styles/global.css';
import './src/styles/layout.css';
import './src/styles/console.css';
import './src/styles/screens.css';
import './src/styles/screens-series.css';
import './src/styles/arcs.css';

import * as React from 'react';
import { GlobalLayout } from './src/components/layout/GlobalLayout';
import type { GatsbyBrowser } from 'gatsby';

export const wrapPageElement: GatsbyBrowser['wrapPageElement'] = ({ element, props }) =>
  React.createElement(GlobalLayout, { location: props.location }, element);
