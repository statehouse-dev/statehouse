import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import CodeBlock from '@theme/CodeBlock';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary')}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={clsx('margin-top--lg')}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/introduction/what-is-statehouse"
          >
            Read the Docs
          </Link>
          <Link
            className="button button--outline button--secondary button--lg margin-left--md"
            href="https://github.com/statehouse-dev/statehouse"
          >
            View on GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title}`}
      description="Strongly consistent state and memory engine for AI agents and workflows"
    >
      <HomepageHeader />
      <main>
        <div className="container margin-top--xl margin-bottom--xl">
          <div className="row">
            <div className="col col--10 col--offset-1">
              <h2 className="text--center margin-bottom--lg">
                Run Statehouse in 3 steps
              </h2>

              {/* Step 1: Docker */}
              <div className="margin-bottom--xl">
                <h3>1. Start the daemon (Docker)</h3>
                <p className="margin-bottom--sm">
                  No Rust needed. One command to run the Statehouse daemon on{' '}
                  <code>localhost:50051</code>:
                </p>
                <CodeBlock language="bash">
                  {`docker run -d -p 50051:50051 --name statehouse rtacconi/statehouse:latest`}
                </CodeBlock>
              </div>

              {/* Step 2: Pip */}
              <div className="margin-bottom--xl">
                <h3>2. Install the Python SDK</h3>
                <CodeBlock language="bash">{`pip install statehouse`}</CodeBlock>
                <p className="margin-top--sm text--secondary">
                  To install from source: clone the repo, then run{' '}
                  <code>pip install -e .</code> from the <code>python/</code>{' '}
                  directory.
                </p>
              </div>

              {/* Step 3: Example */}
              <div className="margin-bottom--xl">
                <h3>3. Use it: versioned state + replay</h3>
                <p className="margin-bottom--sm">
                  Statehouse gives you <strong>versioned state</strong> and{' '}
                  <strong>replay</strong> so you can see exactly what an agent
                  wrote and when. Run this:
                </p>
                <CodeBlock language="python">
                  {`from statehouse import Statehouse

client = Statehouse(url="localhost:50051")

# Write agent state (each write is versioned and immutable)
with client.begin_transaction() as tx:
    tx.write(
        agent_id="my-agent",
        key="research_context",
        value={"task": "Summarize report", "sources": ["doc1", "doc2"]},
    )

with client.begin_transaction() as tx:
    tx.write(
        agent_id="my-agent",
        key="research_context",
        value={
            "task": "Summarize report",
            "sources": ["doc1", "doc2"],
            "summary": "Key finding: emissions down 10%.",
        },
    )

# Read current state (with version number)
result = client.get_state(agent_id="my-agent", key="research_context")
print(f"Version {result.version}: {result.value}")
# Version 2: {'task': '...', 'sources': [...], 'summary': 'Key finding: ...'}

# Replay full history — audit trail of what the agent did
for event in client.replay(agent_id="my-agent"):
    for op in event.operations:
        print(f"  [{event.commit_ts}] {op.key} -> version {op.version}")`}
                </CodeBlock>
                <p className="margin-top--sm">
                  You get: <strong>transactions</strong> (all-or-nothing writes),{' '}
                  <strong>versions</strong> on every key, and{' '}
                  <strong>replay</strong> for debugging and compliance.
                </p>
              </div>

              <div className="text--center margin-top--xl margin-bottom--xl">
                <Link
                  className="button button--primary button--lg"
                  to="/docs/tutorials/overview"
                >
                  Start Tutorial
                </Link>
                <Link
                  className="button button--outline button--primary button--lg margin-left--md"
                  to="/docs/getting-started/installation"
                >
                  Get Started
                </Link>
              </div>

              <hr className="margin-vert--xl" />

              <h2>What is Statehouse?</h2>
              <p>
                Statehouse is a <strong>strongly consistent state and memory
                engine</strong> for AI agents and workflows. It provides
                durable, versioned, replayable state so agent-based systems can
                be debugged, audited, and trusted in production. It is
                self-hosted infrastructure, not a cloud service.
              </p>

              <h2>Why Statehouse?</h2>
              <p>
                Agents are stateful: they remember context, make decisions, and
                evolve over time. Statehouse makes that state{' '}
                <strong>boring, correct, and inspectable</strong> — with
                transactions, versions, and full replay instead of ad-hoc
                databases and JSON blobs.
              </p>
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
}
