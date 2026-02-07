import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'index',
    {
      type: 'category',
      label: 'Introduction',
      items: [
        'introduction/what-is-statehouse',
        'introduction/when-to-use',
        'introduction/when-not-to-use',
        'introduction/design-philosophy',
      ],
    },
    {
      type: 'category',
      label: 'Concepts',
      items: [
        'concepts/state-and-events',
        'concepts/transactions',
        'concepts/versions',
        'concepts/replay',
        'concepts/determinism',
      ],
    },
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/running-statehoused',
        'getting-started/first-transaction',
        'getting-started/first-replay',
      ],
    },
    {
      type: 'category',
      label: 'Tutorials',
      items: [
        'tutorials/overview',
        'tutorials/resumable-research-agent',
      ],
    },
    {
      type: 'category',
      label: 'Python SDK',
      items: [
        'python-sdk/overview',
        'python-sdk/client',
        'python-sdk/transactions',
        'python-sdk/reads',
        'python-sdk/replay',
        'python-sdk/errors',
      ],
    },
    {
      type: 'category',
      label: 'gRPC Internals',
      items: [
        'grpc-internals/why-grpc',
        'grpc-internals/api-versioning',
        'grpc-internals/streaming-replay',
      ],
    },
    {
      type: 'category',
      label: 'Operations',
      items: [
        'operations/configuration',
        'operations/data-directories',
        'operations/snapshots',
        'operations/recovery',
        'operations/logging-and-metrics',
        'operations/cli',
      ],
    },
    {
      type: 'category',
      label: 'Failure Modes',
      items: [
        'failure-modes/process-crash',
        'failure-modes/disk-full',
        'failure-modes/partial-writes',
        'failure-modes/long-running-transactions',
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/reference-agent',
        'examples/resume-after-crash',
        'examples/audit-and-replay',
      ],
    },
    'faq',
    'license',
  ],
};

export default sidebars;
