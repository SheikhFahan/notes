# Scaling — Flash Reference

## What is scalability?
Ability of a system to handle increased load by **adding resources** without a full architectural overhaul.

---

## Load metrics (measure these first)

| Metric | What it is |
|--------|------------|
| **RPS** | API calls per second |
| **Concurrent users** | Users active at same time |
| **Throughput** | Data transferred per unit time (e.g. GB/s) |
| **QPS** | Database queries per second |
| **Message rate** | Messages through queues per second |

---

## Good vs bad scaling (response time under load)

| Load | Response time | Verdict |
|------|----------------|--------|
| 2x → ~same or slightly up | **Excellent** — sublinear, caching works |
| 10x → linear increase | **Acceptable** — predictable |
| 10x → spike / timeout | **Critical** — bottleneck or breaking point |

**Goal:** Linear or sublinear degradation; avoid superlinear spikes.

---

## Vertical scaling (scale up)

**Definition:** Add more power to the **same** machine (more CPU, RAM, SSD, network).

- **Pros:** Simple, no code change, low latency, no distributed complexity.
- **Cons:** Hardware ceiling, single point of failure, cost curve (bigger = more than 2× cost), upgrade downtime.
- **Use when:** DB before sharding, strong consistency, early-stage, predictable moderate growth.

---

## Horizontal scaling (scale out)

**Definition:** Add **more machines**; load balancer distributes traffic.

- **Pros:** No hard limit, fault tolerance, often cheaper, can place nodes near users.
- **Cons:** Complexity, data consistency, network latency, **stateless** app servers usually required.

---

## Stateless vs stateful

| Stateless | Stateful |
|-----------|----------|
| No session on server; any server can serve any request | Session on one server → all requests must go there |
| Session in shared store (Redis, JWT, S3) | Sticky sessions; hotspots; hard to remove servers |
| **Easy to scale** | **Hard to scale** |

**Make stateless:** Redis/Memcached for sessions, JWT, object storage (S3) for files.

---

## Scaling by tier

| Tier | Ease | Main levers |
|------|------|-------------|
| **App** | Easiest | Stateless + LB + auto-scale + multi-AZ |
| **Database** | Hardest | Read replicas, sharding, or NoSQL |
| **Cache** | Easy | Redis Cluster, consistent hashing, cache-aside |
| **Queues** | Easy | Decouple producers/consumers; partition (e.g. Kafka) |

---

## Database scaling (by bottleneck)

- **Read-heavy (10:1–100:1 read:write):** **Read replicas** — primary writes, replicas read. Trade-off: replication lag.
- **Write-heavy or huge data:** **Sharding** — partition by key (range / hash / directory). Trade-off: no cross-shard queries, rebalancing is hard.
- **Need both / flexibility:** Sharding + replicas, or consider **NoSQL** (built-in sharding, eventual consistency, no joins).

**Sharding strategies:** Range (A–H, I–P…), Hash (key mod N), Directory (lookup table).

---

## Caching

- Cache can do ~100× DB throughput (e.g. Redis 100k+ ops/s).
- **Cache-aside:** App → cache → on miss → DB → populate cache.
- Scale cache: Redis Cluster, consistent hashing.

---

## Message queues

- Decouple producers and consumers; scale each independently.
- Buffer spikes; consumers process at their own rate.
- Kafka: partition topics for parallel consumption.

---

## Example: 0 → millions (stages)

| Stage | Users | Change | Next bottleneck |
|-------|--------|--------|------------------|
| 1 | 0–10K | Single server (app + DB) | CPU/memory contention |
| 2 | 10K–100K | DB on separate server | DB read load |
| 3 | 100K–500K | Add Redis cache | Single app server |
| 4 | 500K–2M | LB + multiple stateless app servers | DB again |
| 5 | 2M–10M | Read replicas (primary writes, replicas read) | Write throughput |
| 6 | 10M+ | Sharding (partition by user ID etc.) | Cross-shard queries, rebalancing |

---

## One-line takeaways

- **Vertical:** Same box, bigger box; simple but capped.
- **Horizontal:** More boxes; needs stateless design and data strategy.
- **Always find the bottleneck** before scaling (more app servers don’t help if DB is the limit).
- **Patterns:** LB, caching, async queues, read replicas, sharding show up in almost every scalable system.
- Scalability = handle more load; **availability** = stay up when things fail (next topic).
