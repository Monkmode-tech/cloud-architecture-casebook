# Case 4: Four nines for a financial customer portal, checked with arithmetic

> **Client:** a financial-services customer portal (CLCS 625, Unit 2: cloud-agnostic resilience design)
> **My role:** reliability architect
> **Decision in one line:** 99.99% is impossible in one region with these managed services, so
> the design must be multi-region. The math proves it before anyone buys anything.

## The situation

A three-tier customer portal (web, application, database) must deliver **99.99% availability**
(≈ 53 minutes of downtime a year), **RTO 15 minutes** and **RPO 5 minutes**, and survive both
component failures and a full regional outage.

## The design

- Two regions behind health-checked global DNS. Each region runs multiple AZs.
- Stateless web and app tiers behind regional load balancers, with a WAF.
- An API gateway with rate limits. **Circuit breakers** and timeouts on every dependency.
- **Bulkheads:** separate compute pools and database connection limits per tier, so one exhausted
  resource can't take down the others.
- **Queue-based load leveling** for asynchronous work.
- Database: synchronous replication across AZs, asynchronous cross-region replication with lag < 5 min.
- Encrypted backups in object storage, quarterly failover tests, runbooks.

## Is 99.99% actually achievable? Composite availability

Serial dependencies multiply (every one must be up). Redundant copies multiply their *failure*
probabilities. The tables below are generated from published AWS SLAs by
[`tools/availability.py`](../tools/availability.py). The same method is applied to designs from my
portfolio for comparison.

<!-- BEGIN GENERATED: availability:models/availability.json -->
| Design | Serial chain (per region) | One region | Regions | Composite ceiling | Downtime ceiling | Target | Meets? |
|---|---|---|---|---|---|---|---|
| Three-tier web app, one region (portfolio P1) | ALB (99.99%) → ECS on Fargate (99.99%) → RDS Multi-AZ (99.95%) | 99.930% | 1 | **99.930%** | 6.1 h/yr | 99.9% | yes |
| Financial portal, one region (Case 4) | Route 53 (100%) → ALB (99.99%) → ECS on Fargate (99.99%) → Aurora (99.99%) | 99.970% | 1 | **99.970%** | 2.6 h/yr | 99.99% | **no** |
| Financial portal, two regions (Case 4) | Route 53 (100%) → ALB (99.99%) → ECS on Fargate (99.99%) → Aurora (99.99%) | 99.970% | 2 | **99.999991%** | 3 s/yr | 99.99% | yes |
| Serverless API, one region | API Gateway (99.95%) → Lambda (99.95%) → DynamoDB global table (99.999%) | 99.89% | 1 | **99.89%** | 8.9 h/yr | 99.95% | **no** |
| Serverless warm standby, two regions (portfolio P3) | API Gateway (99.95%) → Lambda (99.95%) → DynamoDB global table (99.999%) | 99.89% | 2 | **99.99989%** | 32 s/yr | 99.95% | yes |
| Internal timesheet app, one region (portfolio P6) | API Gateway (99.95%) → Lambda (99.95%) → DynamoDB (99.99%) | 99.89% | 1 | **99.89%** | 9.6 h/yr | 99.5% | yes |
<!-- END GENERATED -->

### What the numbers say

1. **One region tops out at about 99.97%**, roughly 2.6 hours of downtime a year at the SLA
   ceiling. That is 3× more than the 53-minute budget, so the requirement *forces* multi-region.
   It isn't gold-plating.
2. **Two regions raise the theoretical ceiling far above four nines.** Reality is lower: the
   formula assumes independent failures and instant failover. Detection time (≈ 30 s with 10-second
   health checks), correlated failures (a bad deploy to both regions) and human error eat that margin.
   That's why the design still needs canary deploys, region-by-region releases and game days.
3. **The single-region serverless API misses 99.95% too**, which is why my DR project
   ([aws-multi-region-dr](https://github.com/Monkmode-tech/aws-multi-region-dr)) runs in two regions.

## Recovery timing

| Failure | Detection | Recovery | Within target? |
|---|---|---|---|
| Instance or AZ | Load balancer health checks: seconds | Orchestrator replaces tasks: 5–10 min of degraded capacity, no outage | ✓ |
| Database primary | Managed failover: ~1–2 min | Automatic | ✓ RTO |
| Region | Global health checks: 2–5 min (30 s with fast checks) | Traffic shifts; surviving region scales | ✓ RTO 15 min; RPO set by replication lag (< 5 min) |

## What I'd do differently now

- **Do the arithmetic in the first review**, as above, instead of asserting "99.99%" in prose.
- **Active-active or warm standby, decided by the RPO.** RPO 5 minutes allows asynchronous
  replication and warm standby. Active-active for writes needs conflict handling the coursework
  design didn't address. I built and measured the warm-standby version in
  [aws-multi-region-dr](https://github.com/Monkmode-tech/aws-multi-region-dr).
- **Make health checks test a real dependency.** Failover decisions should rest on a check of a real
  dependency (a database read), not just "the web server answers". My DR project's `/health` does that.
- **Budget the errors, not just the nines:** a 99.99% SLO means ≈ 4.3 minutes of allowed downtime a
  month. Track that error budget, and freeze risky deploys when it's spent.
