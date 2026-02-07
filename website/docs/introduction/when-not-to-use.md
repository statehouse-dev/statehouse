# When Not to Use Statehouse

Statehouse is intentionally focused. Here are cases where other solutions may be better.

## Not Suitable For

### High-Throughput OLTP

If you need:
- Millions of writes per second
- Sub-millisecond latency requirements
- High-frequency point lookups

Consider: Redis, PostgreSQL, or specialized databases.

### Distributed Systems

Statehouse MVP does not support:
- Multi-node clustering
- Replication
- Sharding
- Distributed consensus

If you need these, consider: CockroachDB, TiDB, or other distributed databases.

### SQL Queries

Statehouse is key-value only:
- No SQL interface
- No complex queries
- No joins or aggregations
- Prefix scans only

If you need SQL, use: PostgreSQL, MySQL, or another SQL database.

### Vector Search

Statehouse does not provide:
- Embedding storage
- Similarity search
- Vector indexes

If you need vector search, use: Pinecone, Weaviate, Qdrant, or another vector database.

### Multi-Tenancy

Statehouse MVP is designed for:
- Single-user deployments
- Trust-based access (local deployment)
- No authentication/authorization

If you need multi-tenancy, consider: PostgreSQL with row-level security, or wait for future Statehouse releases.

### Cloud SaaS

Statehouse is:
- Self-hosted only
- No managed service
- Infrastructure you run yourself

If you need a managed service, consider: Cloud databases or wait for future Statehouse releases.

## Alternatives by Use Case

| Need | Alternative |
|------|-------------|
| High-throughput writes | Redis, PostgreSQL |
| Distributed system | CockroachDB, TiDB |
| SQL queries | PostgreSQL, MySQL |
| Vector search | Pinecone, Weaviate |
| Managed service | Cloud databases |
| Simple caching | Redis, Memcached |

## When Statehouse Might Still Work

Even if you have some of these needs, Statehouse might still be suitable if:
- You can use Statehouse for agent state and other systems for other needs
- You're building an MVP and can add complexity later
- Strong consistency and replay are more important than scale

## Next Steps

- [When to Use Statehouse](when-to-use) - Understand ideal use cases
- [Design Philosophy](design-philosophy) - Learn about Statehouse's principles
