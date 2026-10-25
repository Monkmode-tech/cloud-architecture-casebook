# Well-Architected review of my own portfolio

An architect who can't find the weaknesses in their own designs will miss them in everyone else's.
This is a review of the six systems I built, against the six
[AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
pillars. Ratings: ● strong · ◐ adequate for its purpose · ○ known gap.

| Project | Operational excellence | Security | Reliability | Performance | Cost | Sustainability |
|---|---|---|---|---|---|---|
| [Secure three-tier platform](https://github.com/Monkmode-tech/aws-secure-three-tier-platform) | ● runbook, alarms, smoke/load tests | ● WAF, KMS, managed secrets, private tiers | ◐ Multi-AZ, but a single NAT gateway in dev | ● request + CPU autoscaling, ARM64 | ● budget, single NAT, teardown | ● Graviton |
| [AWS ↔ Azure hybrid network](https://github.com/Monkmode-tech/aws-azure-hybrid-network) | ● 11-check validation script | ● no public IPs, pinned crypto, NSG deny-all | ◐ two tunnels, but the Azure gateway is active-standby | ◐ VpnGw1AZ ≈ 650 Mbps ceiling | ● torn down after each session | ◐ |
| [Multi-region DR](https://github.com/Monkmode-tech/aws-multi-region-dr) | ● game day measures RTO/RPO | ◐ no WAF on the HTTP API | ● two regions, backups, Vault Lock, restore drill | ● serverless | ● ≈ $12/month idle | ● serverless |
| [Security guardrails](https://github.com/Monkmode-tech/aws-security-guardrails-detection) | ● simulations, playbooks | ● CIS/FSBP, auto-remediation, ABAC | ◐ remediation Lambdas have DLQs, but one account | ● | ◐ Config + Security Hub scale with resource count | ◐ |
| [EKS DevSecOps pipeline](https://github.com/Monkmode-tech/eks-devsecops-pipeline) | ● GitOps, every change gated | ◐ signatures verified in **Audit** mode, not Enforce | ◐ multi-AZ nodes; one cluster | ● | ○ EKS control plane ≈ $73/month before nodes | ● ARM64 nodes |
| [Event-driven timesheet](https://github.com/Monkmode-tech/serverless-event-driven-timesheet) | ● e2e, DLQ and replay drills | ◐ no WAF; MFA optional for HR | ◐ single region (internal app, 99.5% target) | ● p95 alarm at 300 ms | ● ≈ $3/month idle | ● serverless |

## Highest-risk items and the fix for each

| # | Project | Risk | Fix | Effort |
|---|---|---|---|---|
| 1 | EKS pipeline | Unsigned images are only *reported*, not blocked | Flip the Kyverno `verify-image-signatures` policy to Enforce after one clean release (the runbook already has the steps) | S |
| 2 | Timesheet | HR, who sees pay rates, can sign in without MFA | Require TOTP for the `hr` group (pre-authentication Lambda check) or federate HR through an IdP that enforces MFA | S |
| 3 | DR / Timesheet | Public HTTP APIs have throttling but no WAF | CloudFront + AWS WAF in front (HTTP APIs can't attach WAF directly) | M |
| 4 | Hybrid network | Azure VPN gateway maintenance causes a brief outage | Active-active Azure gateway (two public IPs, four tunnels, ECMP over BGP) | M |
| 5 | Security guardrails | Single account: a compromised admin can disable the controls | AWS Organizations: delegated security account, SCPs that deny disabling CloudTrail/GuardDuty/Config | L |
| 6 | Three-tier platform | Single NAT gateway in dev is an AZ-level single point of failure for egress | Already a variable: set `single_nat_gateway = false` (one NAT per AZ) in any production environment | S |
| 7 | All | Canary releases not automated | Lambda aliases + CodeDeploy (serverless); Argo Rollouts (EKS) | M |

## Cross-cutting observations

- **Security is consistently the strongest pillar**: keyless CI (OIDC), customer-managed keys,
  least-privilege roles, and checkov with every exception justified inline.
- **Cost is designed in, not bolted on**: each repo has a `docs/cost.md` with a monthly figure, and
  the serverless designs stay under $15/month idle.
- **The common gap is the organization layer.** Every project assumes one account. The next step for
  the whole portfolio is a multi-account landing zone (Control Tower or Organizations + SCPs) with
  the guardrails project as the security account.
