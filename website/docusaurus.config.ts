import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Statehouse',
  tagline: 'Strongly consistent state for agents and workflows',
  favicon: 'img/favicon.ico',

  // GitHub Pages configuration
  url: 'https://statehouse-dev.github.io',
  baseUrl: '/statehouse/',
  organizationName: 'statehouse-dev',
  projectName: 'statehouse',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: 'https://github.com/statehouse-dev/statehouse/tree/main/website/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    navbar: {
      title: 'Statehouse',
      logo: {
        alt: 'Statehouse Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/statehouse-dev/statehouse',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Introduction',
              to: '/introduction/what-is-statehouse',
            },
            {
              label: 'Getting Started',
              to: '/getting-started/installation',
            },
            {
              label: 'Python SDK',
              to: '/python-sdk/overview',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/statehouse-dev/statehouse',
            },
          ],
        },
        {
          title: 'Legal',
          items: [
            {
              label: 'License',
              to: '/license',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Statehouse. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['rust', 'python', 'bash'],
    },
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
