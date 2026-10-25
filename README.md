# Cloud Architecture Casebook

[![ci](https://github.com/Monkmode-tech/cloud-architecture-casebook/actions/workflows/ci.yml/badge.svg)](https://github.com/Monkmode-tech/cloud-architecture-casebook/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/models-Python%203.12-3776AB?logo=python&logoColor=white)
![Diagrams](https://img.shields.io/badge/diagrams-Mermaid-FF3670?logo=mermaid&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

**Roles this project supports:** Cloud Solutions Architect · Cloud Architect · Cloud Security Architect · Pre-sales / Technical Consultant

## In plain terms (2-minute read)

**What this is.** The other repositories in my portfolio show I can *build* cloud systems. This one
shows how I *decide*: seven architecture case studies for hospitals, a bank, an e-commerce company
and enterprise IT, each written the way an architect presents to leadership. Each one covers the
business problem, the options considered, the decision and why, the risks, and what it costs.

**What makes it different.** The numbers are not typed into a document. They come from small
programs that calculate them from published AWS prices and SLAs, and every input is written down
with a reason. When someone asks "what if staffing doesn't go down?", I change one value and the
whole case updates. A test fails if any table drifts from its model.

**Three times the math changed my own conclusions**

| Original coursework claim | What the model showed | Why it matters to a business |
|---|---|---|
| Migrating MedTech to the cloud saves 20% | True at steady state (21%), but over 3 years it **breaks even around month 38**, and staffing decides it | The CFO hears the real payback curve up front, not a surprise in year 1 |
| The financial portal will reach 99.99% | **One region can't**: the managed services' SLAs cap it at ~99.97% (2.6 h/yr). Two regions can | It proves multi-region is required, not gold-plating, before money is spent |
| The security program returns 798% | Treating a breach as a probability gives **~240%**, and it **pays off if the yearly breach risk is above ~4–5%** | A board can approve a number that states its own assumptions |

**What this shows about how I work.** I check my own claims, turn opinions into numbers, and
explain trade-offs in language both engineers and executives can act on.

## The cases

| # | Case | Industry | Decision in one line | Built in |
|---|---|---|---|---|
| 1 | [Hybrid-first cloud strategy](cases/01-medicare-hybrid-cloud-strategy.md) | Healthcare | Latency-critical clinical systems stay near care sites; everything else moves to HIPAA-eligible cloud behind guardrails | [guardrails](https://github.com/Monkmode-tech/aws-security-guardrails-detection) |
| 2 | [Migrating 50 applications: 6 Rs + 3-year TCO](cases/02-medtech-migration-6rs-and-tco.md) | Healthcare | Migrate by portfolio; lead the business case with the payback curve, not a percentage | — |
| 3 | [Hybrid integration for a bank](cases/03-tfg-hybrid-integration.md) | Financial services | APIs for requests, events for reactions, CDC for data; one governed layer instead of point-to-point | [event-driven timesheet](https://github.com/Monkmode-tech/serverless-event-driven-timesheet), [hybrid network](https://github.com/Monkmode-tech/aws-azure-hybrid-network) |
| 4 | [Four nines, checked with arithmetic](cases/04-financial-portal-resilience.md) | Financial services | 99.99% forces two regions; composite-availability math proves it | [multi-region DR](https://github.com/Monkmode-tech/aws-multi-region-dr) |
| 5 | [Governing AWS + Azure through a 24-month transformation](cases/05-global-tech-lifecycle-governance.md) | Enterprise IT | Security and monitoring mature with the migration; measurable gates between phases | [guardrails](https://github.com/Monkmode-tech/aws-security-guardrails-detection), [DevSecOps](https://github.com/Monkmode-tech/eks-devsecops-pipeline) |
| 6 | [Elastic capacity for e-commerce](cases/06-global-ecommerce-scalability.md) | Retail | Stateless containers scaling on request count, with the database and CDN sized to match | [three-tier platform](https://github.com/Monkmode-tech/aws-secure-three-tier-platform) |
| 7 | [A security program a CFO can approve](cases/07-medsecure-security-investment.md) | Healthcare commerce | Cloud-native controls first, spend by data class, ROI stated with its break-even condition | [guardrails](https://github.com/Monkmode-tech/aws-security-guardrails-detection) |

Plus a [Well-Architected review of my own six builds](well-architected/portfolio-review.md): every
known weakness, ranked, with the fix.

## Technical summary

- **Executable models** (Python 3.12, standard library only) with JSON inputs:
  - [`tools/availability.py`](tools/availability.py): composite availability from published SLAs
    (serial = product, redundant = 1 − ∏(1 − a)), downtime budgets, truncation so 99.99995% never prints as 100%.
  - [`tools/tco.py`](tools/tco.py): 3-year stay-vs-migrate TCO with data growth, tiered storage, Savings Plan
    coverage ramps, dual running, one-time migration cost, break-even extrapolation and one-at-a-time sensitivity.
  - [`tools/security_roi.py`](tools/security_roi.py): ROSI from annualized loss expectancy, break-even breach
    probability and a sensitivity grid.
- **Docs generated from models:** `python3 -m tools.build` renders tables between
  `<!-- BEGIN GENERATED -->` markers; CI runs `--check` and fails on drift.
- **CI:** ruff, unit tests (including the "docs are up to date" test), a relative-link checker,
  and Mermaid CLI rendering of every diagram.
- **Templates:** [ADR](templates/adr.md) and [case study](templates/case-study.md) formats used throughout the portfolio.

## Where to look

| Skill | Evidence |
|---|---|
| Business-case and TCO modeling | [Case 2](cases/02-medtech-migration-6rs-and-tco.md), [`models/medtech-tco.json`](models/medtech-tco.json) |
| Reliability engineering (SLAs, SLOs, error budgets) | [Case 4](cases/04-financial-portal-resilience.md), [`tools/availability.py`](tools/availability.py) |
| Security risk quantification | [Case 7](cases/07-medsecure-security-investment.md) |
| Migration strategy (6 Rs, waves, gates) | [Case 2](cases/02-medtech-migration-6rs-and-tco.md), [Case 5](cases/05-global-tech-lifecycle-governance.md) |
| Integration architecture (API-led, event-driven, CDC) | [Case 3](cases/03-tfg-hybrid-integration.md) |
| Regulated industries (HIPAA, PCI DSS, SOC 2, GDPR) | Cases [1](cases/01-medicare-hybrid-cloud-strategy.md), [3](cases/03-tfg-hybrid-integration.md), [5](cases/05-global-tech-lifecycle-governance.md), [7](cases/07-medsecure-security-investment.md) |
| Self-critique against the Well-Architected Framework | [portfolio review](well-architected/portfolio-review.md) |

## Certification alignment

| Exam | Areas exercised |
|---|---|
| AWS Solutions Architect – Associate (SAA-C03) | Resilient and cost-optimized architectures, migration strategies |
| AWS Solutions Architect – Professional | Migration planning, TCO, multi-account governance, complex DR trade-offs |
| AWS Security – Specialty | Risk management, data protection, incident response, governance |

## Glossary (for non-technical readers)

| Term | Meaning |
|---|---|
| TCO | Total cost of ownership: everything a system costs over several years, not just the monthly bill |
| Break-even | The point where cumulative savings repay the cost of the change |
| SLA / availability | A provider's uptime commitment; 99.99% ≈ 53 minutes of downtime a year |
| RTO / RPO | How long recovery may take / how much recent data may be lost |
| 6 Rs | The six ways to move an application: rehost, replatform, repurchase, refactor, retire, retain |
| ROSI | Return on security investment |
| ADR | Architecture decision record: a short note of a decision, the options, and why |
| Well-Architected | AWS's framework for reviewing designs: operations, security, reliability, performance, cost, sustainability |

## Background

Built by **Caleb Tetteh** (M.S. Cloud Computing Systems, UMGC; B.S. Computer Science, Georgia Tech).
The cases come from my coursework: CLCS 615 *Cloud Services and Technologies*, CLCS 625
*Applications of Cloud Computing* and CLCS 645 *Cloud Infrastructure Planning and Design*. Each is
revised with models, current pricing and the lessons from building the rest of this portfolio.
The organizations are fictional course scenarios.
