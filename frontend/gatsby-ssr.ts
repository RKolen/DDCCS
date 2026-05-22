import * as React from 'react';
import { GlobalLayout } from './src/components/layout/GlobalLayout';
import type { GatsbySSR } from 'gatsby';

export const wrapPageElement: GatsbySSR['wrapPageElement'] = ({ element, props }) =>
  React.createElement(GlobalLayout, { location: props.location }, element);
