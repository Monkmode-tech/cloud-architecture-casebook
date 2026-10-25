# Case 2: Migrating 50 healthcare applications: 6 Rs, waves and an honest TCO

> **Client:** MedTech Solutions (fictional, CLCS 625 *Applications of Cloud Computing*, Unit 6)
> **My role:** migration architect
> **Decision in one line:** migrate by portfolio, not by server. The 20% cost target holds at
> steady state, but the three-year view breaks even only in about month 38, and the CFO should hear that up front.

## The situation

MedTech runs 50 interconnected healthcare applications on ~120 VMs across two aging data centers.
It holds 200 TB of patient data growing 20–25% a year, on a flat network with no centralized
monitoring and no defined recovery targets. Remote care is growing faster than the infrastructure can follow.

## Portfolio strategy (6 Rs)

| R | Applications | Why |
|---|---|---|
| **Rehost** | Scheduling, internal apps | Low risk, quick wins; builds team confidence |
| **Replatform** | EHR and imaging | Managed databases and object storage improve security and performance without a rewrite |
| **Repurchase** | Billing → SaaS | Removes a PCI/HIPAA-heavy system from the estate |
| **Refactor** | Telehealth | The one workload that must scale elastically and serve remote users |
| **Retire** | Outdated internal tools (≈10%) | Every retired app is attack surface and cost removed |
| **Retain** | High-risk legacy modules | Stability first; revisit after the platform is proven |

Low-risk systems move first. Critical clinical systems move only after the platform has passed its gate.

## Roadmap (18 months) and team

| Phase | Duration | Engineers | Security | Compliance | Gate to proceed |
|---|---|---|---|---|---|
| 1 Foundation | 3 mo | 2 | 1 | 1 | Landing zone, MFA, logging, BAAs |
| 2 Low-risk rehost | 3 mo | 3 | 1 | 1 | Performance baselines met; rollback rehearsed |
| 3 Clinical replatform | 6 mo | 4 | 2 | 1 | DR test meets RTO < 2 h / RPO < 15 min |
| 4 Refactor telehealth | 4 mo | 3 | 1 | 1 | Load test at 2× peak |
| 5 Optimize & exit DCs | 2 mo | 2 | 1 | 1 | Data centers decommissioned |

## Three-year TCO: stay vs. migrate

The model is in [`models/medtech-tco.json`](../models/medtech-tco.json) and
[`tools/tco.py`](../tools/tco.py). Change an assumption, run `python3 -m tools.build`, and these tables update.

<!-- BEGIN GENERATED: tco:models/medtech-tco.json -->
| | Year 1 | Year 2 | Year 3 | 3-year total |
|---|---|---|---|---|
| Stay on-premises | $1.43M | $1.44M | $1.45M | $4.32M |
| Migrate to AWS | $1.98M | $1.24M | $1.15M | $4.38M |
| Cumulative saving | -$556k | -$363k | -$62k | |

**Break-even:** about month 38 (at the year-3 run rate) · **3-year saving:** -1% · **Steady-state (year 3) saving:** 21% (target: 20%)

<details><summary>Year-3 cost breakdown</summary>

| Stay on-premises | | Migrate to AWS | |
|---|---|---|---|
| Hardware refresh (amortized) | $120k | Compute (after rightsizing, Savings Plans) | $123k |
| Storage (amortized, grows with data) | $71k | Storage (tiered: EBS / S3 / Glacier) | $74k |
| Data center space & power | $180k | Data transfer out | $11k |
| Network / WAN | $90k | Backups | $73k |
| Software licenses | $150k | Network (Direct Connect, NAT, endpoints) | $60k |
| Operations staff | $840k | Security & operations tooling | $34k |
|  |  | AWS Support | $26k |
|  |  | SaaS replacing retired apps | $120k |
|  |  | Operations staff | $630k |
|  |  | Migration (one-time: partners, training, tooling) | — |
|  |  | Dual running (on-prem not yet retired, excl. staff) | — |

</details>

**Sensitivity**: 3-year saving when one assumption moves (others unchanged):

| Assumption | Low case | High case |
|---|---|---|
| Cloud ops staff stays at 6 FTE vs drops to 4 | -16% | 3% |
| No Savings Plans vs aggressive coverage (50/90/90%) | -4% | -1% |
| Migration one-time cost $700k vs $300k | -7% | 2% |
| Slow exit (90/40/10% dual running) vs fast (50/10/0%) | -8% | 3% |
| Data growth 30%/yr vs 15%/yr | -2% | -1% |
<!-- END GENERATED -->

### What the numbers say

1. **The 20% target is real at steady state** (year 3: 21%). The coursework claim holds.
2. **Over three years it's roughly break-even.** Year 1 carries ~$450k of one-time migration cost
   *and* about 70% of the data-center bill, because nothing can be switched off until the last wave.
3. **Staffing is the swing factor**: it moves the 3-year result more than Savings Plans, migration
   cost or data growth combined. If operations headcount doesn't change, the migration is a cost
   increase. The business case must say what those people will do instead (platform engineering,
   security, FinOps), or it isn't a business case.
4. **The fastest lever under architecture control is the exit speed.** Shortening dual running
   (50/10/0%) is worth more than aggressive Savings Plans.

### Assumptions (challenge these)

<!-- BEGIN GENERATED: assumptions:models/medtech-tco.json -->
| Input | Why this value |
|---|---|
| `data_tb, data_growth` | 200 TB growing 20-25%/yr (coursework: MedTech current state); 22% used |
| `hardware_refresh_capex` | 12 virtualization hosts + SAN controllers + switches due for refresh (aging infrastructure), ~$600k over a 5-year life |
| `storage_cost_per_tb` | Enterprise SAN, ~$1,200 per usable TB over 5 years |
| `facilities_per_year` | Two data centers: space, power, cooling, physical security |
| `licenses_per_year` | Virtualization, backup, OS and monitoring licenses (virtualization pricing rose sharply after 2024) |
| `ops_fte 6 -> 4.5` | Infrastructure staff; cloud removes hardware/facility work but adds platform, FinOps and security work - a 25% reduction, not 50% |
| `instances 96` | 120 VMs minus retired tools (10% of apps) and the billing system moved to SaaS (Repurchase) |
| `avg_instance_monthly $140` | Blended on-demand price after rightsizing (mix of 2-4 vCPU instances, some Windows) |
| `savings_plan 30% at 30/70/80% coverage` | 1-year Compute Savings Plans bought only once usage is measured (coursework: 'no commitment until baseline known') |
| `storage tiers` | Imaging archive is 60% of data and needs millisecond access, so Glacier Instant Retrieval rather than Deep Archive |
| `egress 10 TB/month` | Telehealth, image viewing by referring clinics, partner feeds |
| `security_ops 10%, support 7%` | GuardDuty, Security Hub, Config, CloudTrail, CloudWatch; Business support tier |
| `migration_one_time $450k` | Partner assistance, training (coursework resource plan), migration tooling, extra testing |
| `dual_running 70% / 20% / 0%` | Data centers can't be switched off until the last wave (18-month roadmap); staff counted once |
<!-- END GENERATED -->

## Security, DR and validation

- HIPAA controls: AES-256 at rest, TLS 1.2+, MFA, RBAC, segmentation (ending the flat network),
  continuous monitoring, audit logging, and BAAs with providers.
- DR targets: **99.99% availability, RTO < 2 h, RPO < 15 min** for clinical systems. Downtime is
  costly (the coursework cited ~$9,000 per minute).
- Every wave is validated with functional, performance, DR simulation, compliance and UAT tests,
  with a rehearsed rollback (restore, switch back, data recovery).

## What I'd do differently now

- **Lead with the TCO model, not a percentage.** "20% cheaper" without the dual-running curve
  sets up the migration to look like a failure in year 1.
- **Write the staff plan into the business case.** Name the roles, the retraining and the timing.
- **Use AWS Migration Acceleration Program credits and Migration Evaluator data** to replace the
  instance-count assumptions with measured utilization.
- **Treat 99.99% as a per-tier target.** Four nines for *every* clinical system is expensive;
  Case 4 shows what four nines actually requires.
