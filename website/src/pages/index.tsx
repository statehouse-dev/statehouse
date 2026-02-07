import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import CodeBlock from '@theme/CodeBlock';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary')}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={clsx('margin-top--lg')}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/introduction/what-is-statehouse">
            Read the Docs
          </Link>
          <Link
            className="button button--outline button--secondary button--lg margin-left--md"
            href="https://github.com/statehouse-dev/statehouse">
            View on GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title}`}
      description="Strongly consistent state and memory engine for AI agents and workflows">
      <HomepageHeader />
      <main>
        <div className="container margin-top--xl margin-bottom--xl">
          <div className="row">
            <div className="col col--8 col--offset-2">
              <h2>What is Statehouse?</h2>
              <p>
                Statehouse is a strongly consistent state and memory engine designed for AI agents, workflows, and automation systems.
                It provides durable, versioned, replayable state with clear semantics, so agent-based systems can be debugged, audited, and trusted in production.
              </p>

              <h2>Why Statehouse?</h2>
              <p>
                Modern AI agents and automation systems are fundamentally stateful: they make decisions, remember context, evolve over time, and retry, branch, and recover.
                Statehouse exists to make agent state boring, correct, and inspectable.
              </p>

              <h2>Quick Start</h2>
              <CodeBlock language="python">
{`from statehouse import Statehouse

# Connect to daemon
client = Statehouse(url="localhost:50051")

# Write state
with client.begin_transaction() as tx:
    tx.write(
        agent_id="my-agent",
        key="memory",
        value={"fact": "Paris is the capital of France"},
    )

# Read state
result = client.get_state(agent_id="my-agent", key="memory")
print(result.value)  # {"fact": "Paris is the capital of France"}

# Replay events
for event in client.replay(agent_id="my-agent"):
    print(f"[{event.commit_ts}] Transaction {event.txn_id}")`}
              </CodeBlock>

              <div className="margin-top--lg">
                <Link
                  className="button button--primary button--lg"
                  to="/docs/getting-started/installation">
                  Get Started
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
}
