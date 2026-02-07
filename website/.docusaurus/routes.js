import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/statehouse/docs',
    component: ComponentCreator('/statehouse/docs', 'ef6'),
    routes: [
      {
        path: '/statehouse/docs',
        component: ComponentCreator('/statehouse/docs', 'b93'),
        routes: [
          {
            path: '/statehouse/docs',
            component: ComponentCreator('/statehouse/docs', '646'),
            routes: [
              {
                path: '/statehouse/docs/',
                component: ComponentCreator('/statehouse/docs/', '365'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/concepts/determinism',
                component: ComponentCreator('/statehouse/docs/concepts/determinism', '534'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/concepts/replay',
                component: ComponentCreator('/statehouse/docs/concepts/replay', '84e'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/concepts/state-and-events',
                component: ComponentCreator('/statehouse/docs/concepts/state-and-events', '8ac'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/concepts/transactions',
                component: ComponentCreator('/statehouse/docs/concepts/transactions', '58b'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/concepts/versions',
                component: ComponentCreator('/statehouse/docs/concepts/versions', 'e63'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/examples/audit-and-replay',
                component: ComponentCreator('/statehouse/docs/examples/audit-and-replay', '109'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/examples/reference-agent',
                component: ComponentCreator('/statehouse/docs/examples/reference-agent', 'ccd'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/examples/resume-after-crash',
                component: ComponentCreator('/statehouse/docs/examples/resume-after-crash', '3b4'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/failure-modes/disk-full',
                component: ComponentCreator('/statehouse/docs/failure-modes/disk-full', '906'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/failure-modes/long-running-transactions',
                component: ComponentCreator('/statehouse/docs/failure-modes/long-running-transactions', 'fe2'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/failure-modes/partial-writes',
                component: ComponentCreator('/statehouse/docs/failure-modes/partial-writes', 'a74'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/failure-modes/process-crash',
                component: ComponentCreator('/statehouse/docs/failure-modes/process-crash', '62d'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/faq',
                component: ComponentCreator('/statehouse/docs/faq', '77b'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/getting-started/first-replay',
                component: ComponentCreator('/statehouse/docs/getting-started/first-replay', 'f79'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/getting-started/first-transaction',
                component: ComponentCreator('/statehouse/docs/getting-started/first-transaction', '1c2'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/getting-started/installation',
                component: ComponentCreator('/statehouse/docs/getting-started/installation', '56c'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/getting-started/running-statehoused',
                component: ComponentCreator('/statehouse/docs/getting-started/running-statehoused', '20e'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/grpc-internals/api-versioning',
                component: ComponentCreator('/statehouse/docs/grpc-internals/api-versioning', '5ec'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/grpc-internals/streaming-replay',
                component: ComponentCreator('/statehouse/docs/grpc-internals/streaming-replay', '463'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/grpc-internals/why-grpc',
                component: ComponentCreator('/statehouse/docs/grpc-internals/why-grpc', '935'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/introduction/design-philosophy',
                component: ComponentCreator('/statehouse/docs/introduction/design-philosophy', '0cb'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/introduction/what-is-statehouse',
                component: ComponentCreator('/statehouse/docs/introduction/what-is-statehouse', 'b23'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/introduction/when-not-to-use',
                component: ComponentCreator('/statehouse/docs/introduction/when-not-to-use', '193'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/introduction/when-to-use',
                component: ComponentCreator('/statehouse/docs/introduction/when-to-use', 'e94'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/license',
                component: ComponentCreator('/statehouse/docs/license', '8c5'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/operations/configuration',
                component: ComponentCreator('/statehouse/docs/operations/configuration', '0cb'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/operations/data-directories',
                component: ComponentCreator('/statehouse/docs/operations/data-directories', '948'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/operations/logging-and-metrics',
                component: ComponentCreator('/statehouse/docs/operations/logging-and-metrics', '9a9'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/operations/recovery',
                component: ComponentCreator('/statehouse/docs/operations/recovery', 'fcd'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/operations/snapshots',
                component: ComponentCreator('/statehouse/docs/operations/snapshots', '11d'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/python-sdk/client',
                component: ComponentCreator('/statehouse/docs/python-sdk/client', '66f'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/python-sdk/errors',
                component: ComponentCreator('/statehouse/docs/python-sdk/errors', 'a04'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/python-sdk/overview',
                component: ComponentCreator('/statehouse/docs/python-sdk/overview', 'a2f'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/python-sdk/reads',
                component: ComponentCreator('/statehouse/docs/python-sdk/reads', 'fb0'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/python-sdk/replay',
                component: ComponentCreator('/statehouse/docs/python-sdk/replay', '3fb'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/statehouse/docs/python-sdk/transactions',
                component: ComponentCreator('/statehouse/docs/python-sdk/transactions', '7ac'),
                exact: true,
                sidebar: "docs"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '/statehouse/',
    component: ComponentCreator('/statehouse/', 'd6f'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
