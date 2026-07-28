# Enterprise Readiness Checklist — Ops-Center

Research date: 2026-07-02. What enterprise buyers, procurement, and security teams actually require from an admin-console / infrastructure-management SaaS before purchase, and what best-in-class consoles (AWS, Stripe, Grafana Cloud, Vercel, Datadog) treat as table stakes — mapped against Ops-Center today.

## How buyers evaluate you

- Security reviews run on standardized questionnaires — SIG (18 risk domains) and CAIQ (~261 yes/no cloud-control questions) plus a custom VSQ. The recurring themes: data protection (encryption, access control, retention), detection/response (logging, alerting, IR), hygiene (patching, vuln mgmt, backups), governance (policies, ownership), and third-party surprises (subprocessors) ([PlatformSecurity on SIG/CAIQ](https://platformsecurity.com/blog/vendor-security-questionnaires-sig-caiq), [Bitsight CAIQ vs SIG](https://www.bitsight.com/blog/caiq-vs-sig-top-questionnaires-vendor-risk-assessment)).
- The near-universal engineering quartet is **SSO, SCIM, audit logs, RBAC** (+ orgs/tenant isolation); recommended build order RBAC → audit logs → SSO → SCIM-on-demand, because roles underpin everything and every enterprise asks for audit logs ([Hashorn](https://hashorn.com/blog/enterprise-ready-saas-sso-scim-audit-logs), [Clerk federated identity](https://clerk.com/articles/federated-identity-for-enterprise-saas-saml-oidc-and-scim)). SSO/SCIM/audit/RBAC are effectively universal for 500+-employee buyers; SOC 2, SLA, and data residency become consistent above ~$50k ACV ([WorkOS checklist](https://workos.com/blog/enterprise-readiness-checklist-2026), [guide](https://workos.com/guide/enterprise-readiness-checklist)).
- **SOC 2 Type II is the procurement shortcut**: security teams use the report to skip most of the questionnaire; frequently a contractual precondition; ~6–9 months to first report ([Secureframe](https://secureframe.com/blog/soc-2-compliance-checklist), [Drata](https://drata.com/learn/soc-2/checklist), [rfp.wiki due-diligence checklist](https://www.rfp.wiki/content/saas-vendor-due-diligence-security-compliance-checklist)).
- Questionnaires probe **pen-test recency and unresolved findings, MFA/SSO support, SDLC security, breach/vuln-disclosure process, security architecture docs** ([rfp.wiki](https://www.rfp.wiki/content/saas-vendor-due-diligence-security-compliance-checklist), [Auditive](https://blog.auditive.io/saas-due-diligence-checklist/)).
- Legal/privacy: a **GDPR Art. 28 DPA with a maintained, change-notified subprocessor list** is mandatory for any SaaS processing customer data; buyers also expect deletion/export rights, retention automation, EU processing options, and a 72-hour breach playbook ([Secure Privacy DPA guide](https://secureprivacy.ai/blog/data-processing-agreements-dpas-for-saas), [Drata GDPR for SaaS](https://drata.com/learn/gdpr/for-saas-compliance), [ComplyDog](https://complydog.com/blog/gdpr-compliance-checklist-complete-guide-b2b-saas-companies)).
- **SLAs must be measurable with remedies** — "99.9%" is meaningless without a measurement definition and credits ([Promise Legal](https://promise.legal/startup-legal-guide/contracts/vendor-contracts)). Grafana Cloud Pro publishes 99.5% and holds SOC 2 Type II / ISO 27001 / GDPR ([Grafana Cloud specs](https://invgate.com/itdb/grafana-cloud)).
- **Audit export + SIEM streaming is a procurement requirement, not a nice-to-have**: Vercel Enterprise ships CSV export plus real-time streams to Datadog/Splunk/S3/HTTP ([Vercel audit logs](https://vercel.com/docs/audit-log), [SIEM GA changelog](https://vercel.com/changelog/audit-logs-with-siem-integration-now-generally-available)); GitHub Enterprise streams audit events natively ([GitHub docs](https://docs.github.com/en/enterprise-cloud@latest/admin/monitoring-activity-in-your-enterprise/reviewing-audit-logs-for-your-enterprise/streaming-the-audit-log-for-your-enterprise)); buyers want both streaming and batch ([AuditKit](https://auditkit.dev/blog/siem-integration-audit-logs)).
- Grafana's enterprise tier = **SAML + SCIM (IdP-driven lifecycle, group→team mapping) + audit logging + RBAC** ([Grafana SCIM docs](https://grafana.com/docs/grafana/latest/setup-grafana/configure-access/configure-scim-provisioning/), [SCIM blog](https://grafana.com/blog/introducing-scim-provisioning-in-grafana-enterprise-grade-user-management-made-simple/), [audit docs](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/audit-grafana/)). ~98.8% of SaaS apps lack or paywall SCIM, so shipping it is a differentiator ([SSOJet](https://ssojet.com/blog/enterprise-ready-saas-checklist)).

## Console UX/IA table stakes (AWS, Stripe, Grafana, Vercel, Datadog)

- **Progressive disclosure**: one "is everything okay?" view first, drill-down on demand; semantic color (red only when action is required now); fast card render ([Lazarev dashboard UX](https://www.lazarev.agency/articles/dashboard-ux-design)).
- **Global cross-entity search** — Stripe's dashboard search spans customers, invoices, payouts, products; SQL-level export (Sigma) for power users ([Lazarev examples](https://www.lazarev.agency/articles/dashboard-ux-design)).
- **Consistency via a design system** — Datadog built DRUIDS because users expect tables, filters, time-pickers, and dropdowns to behave identically across the whole platform ([Datadog DRUIDS](https://www.datadoghq.com/blog/engineering/druids-the-design-system-that-powers-datadog/), [Figma case study](https://www.figma.com/customers/how-datadog-built-enterprise-platform-scaling-design-system/)).
- **Self-serve IT admin portal**: enterprise IT expects to configure SSO/SCIM/domains without a support ticket ([WorkOS](https://workos.com/blog/enterprise-readiness-checklist-2026)).
- **Explicit test/live mode separation** (Stripe's signature pattern) and first-class API keys, docs, webhooks in the console — developers evaluate the console as the product.
- **Public status page + trust center** — buyers check the status page pre-purchase and use it as SLA-credit evidence ([Vercel](https://vercel.com/docs/audit-log)-class vendors all publish one; see also [rfp.wiki](https://www.rfp.wiki/content/saas-vendor-due-diligence-security-compliance-checklist)).

## Requirement matrix

| Requirement | Why buyers ask | Ops-Center today | Gap size | Phase |
|---|---|---|---|---|
| SSO (vendor-hosted OIDC) | IT mandates centralized auth ([WorkOS](https://workos.com/guide/enterprise-readiness-checklist)) | Keycloak SSO live (Google/GitHub/MS) | Small | 2 |
| **Per-org customer IdP** (bring-your-own Okta/Entra SAML/OIDC) | To an enterprise, "SSO" means *their* IdP, not social login ([Clerk](https://clerk.com/articles/federated-identity-for-enterprise-saas-saml-oidc-and-scim)) | Missing — Keycloak supports brokering, no per-org wiring/UI | **Large** | 2 |
| SCIM provisioning/deprovisioning | Offboarding risk; IdP-driven lifecycle ([Grafana](https://grafana.com/blog/introducing-scim-provisioning-in-grafana-enterprise-grade-user-management-made-simple/), [SSOJet](https://ssojet.com/blog/enterprise-ready-saas-checklist)) | Missing | Large | 3 |
| MFA/2FA UI + org enforcement policy | Universal questionnaire item ([rfp.wiki](https://www.rfp.wiki/content/saas-vendor-due-diligence-security-compliance-checklist)) | Keycloak can enforce TOTP; no product UI/toggle | Medium | 2 |
| RBAC incl. custom roles | Admin/billing/viewer/auditor separation = buyer's data governance ([WorkOS](https://workos.com/blog/enterprise-readiness-checklist-2026)) | Fixed roles + org feature grants; no custom roles | Medium | 3 |
| In-app queryable audit log | Serves customer UI, support, and auditor ([Hashorn](https://hashorn.com/blog/enterprise-ready-saas-sso-scim-audit-logs)) | Audit log page exists | Small | 2 |
| **Audit export (CSV) + SIEM streaming** | SecOps must ingest into Splunk/Datadog; procurement hard requirement ([Vercel](https://vercel.com/changelog/audit-logs-with-siem-integration-now-generally-available), [AuditKit](https://auditkit.dev/blog/siem-integration-audit-logs)) | Missing (existing webhooks = possible transport) | **Large** | 2 |
| SOC 2 Type II report | The questionnaire shortcut; often contractual ([Secureframe](https://secureframe.com/blog/soc-2-compliance-checklist)) | Missing; 6–9 mo lead — start controls now | Large | 3 |
| Annual pen test + summary letter | Asked verbatim; unresolved-findings follow-up ([Auditive](https://blog.auditive.io/saas-due-diligence-checklist/)) | Missing (internal security-fix docs only) | Medium | 3 |
| DPA + published subprocessor list | GDPR Art. 28 mandatory; change notification required ([Secure Privacy](https://secureprivacy.ai/blog/data-processing-agreements-dpas-for-saas)) | Missing | Medium | 2 |
| GDPR erasure + data export | Legal right; buyers test it; retention automation expected ([Drata](https://drata.com/learn/gdpr/for-saas-compliance)) | Missing/partial (org-lifecycle delete exists) | Medium | 2 |
| Real ToS/Privacy Policy | Legal review is a binary purchase gate ([Promise Legal](https://promise.legal/startup-legal-guide/contracts/vendor-contracts)) | Placeholder text | Small effort, hard gate | 2 |
| Trust/security page | Self-serve for security reviewers pre-sales ([rfp.wiki](https://www.rfp.wiki/content/saas-vendor-due-diligence-security-compliance-checklist)) | Missing | Medium | 2 |
| Uptime SLA (measured, with credits) | No remedies = meaningless ([Promise Legal](https://promise.legal/startup-legal-guide/contracts/vendor-contracts)); Grafana 99.5% ([invgate](https://invgate.com/itdb/grafana-cloud)) | Monitoring + public /status SHIPPED; no SLA contract | Medium | 3 |
| Public status page + incident history | Pre-purchase check; SLA evidence | SHIPPED | None | — |
| Support tiers/SLAs + escalation path | Procurement scores response-time commitments ([rfp.wiki](https://www.rfp.wiki/content/saas-vendor-due-diligence-security-compliance-checklist)) | Missing | Medium | 3 |
| Production billing: real invoices, self-serve payment, usage visibility | Finance needs real invoices; usage-based needs metering transparency (Stripe pattern) | Lago+Stripe **test mode**; invoice PDF shipped; metering+quotas live | Medium | 2 |
| Live Stripe + tax handling | Cannot transact otherwise | Test mode only | Medium | 2 |
| BYOK / key custody story | Cost control + security review | SHIPPED (BYOK) | None | — |
| API + webhooks for automation | Enterprises script their vendors; consoles are API-first (AWS/Stripe) | Webhooks + API docs page exist | Small | 3 |
| Docs site (admin guide, API ref, runbooks) | Evaluators judge maturity by docs | API docs page only | Medium | 3 |
| Self-host installer polish | Their infra team runs it during eval | Partial (install.sh, rough) | Medium | 3 |
| Documented tenant-isolation architecture | Standard architecture-review question ([WorkOS](https://workos.com/blog/enterprise-readiness-checklist-2026)) | Orgs + grants exist; not written up for reviewers | Small | 2 |
| Data residency options | Consistent ask >$50k ACV ([WorkOS](https://workos.com/blog/enterprise-readiness-checklist-2026)) | Missing; self-host is the mitigating answer | Large (defer) | 3 |
| White-label / theming | Reseller/MSP buyers | SHIPPED | None | — |
| UX: truthful nav, no dead ends, honest data | One fake number poisons console trust ([Lazarev](https://www.lazarev.agency/articles/dashboard-ux-design)) | SHIPPED today (nav, 404s, mock purge, real extensions) | None | — |
| UX: global search across orgs/users/invoices | Stripe-pattern table stakes | Missing/partial | Medium | 3 |
| UX: consistent tables/filters/pickers | Datadog DRUIDS lesson ([DRUIDS](https://www.datadoghq.com/blog/engineering/druids-the-design-system-that-powers-datadog/)) | Partial — needs a consistency audit | Small | 3 |

## Top 10 highest-leverage items (ranked)

1. **Per-org customer IdP (SAML/OIDC via Keycloak org brokering)** — the single biggest "not enterprise-ready" verdict; Keycloak already supports brokering, so it's wiring + self-serve UI, not a platform build.
2. **Audit log export (CSV) + SIEM streaming** — hard procurement requirement and the cheapest large-gap close: audit log and webhook infra both already exist.
3. **Real ToS/Privacy + DPA + subprocessor page** — pure writing, zero code; legal review is a binary gate that blocks every deal until done.
4. **Live Stripe** — cannot take money in test mode; SLA credits and tiering presume real billing.
5. **2FA UI + org-level MFA enforcement toggle** — top-5 questionnaire item; Keycloak does the heavy lifting, needs product surface only.
6. **Trust/security page** — converts shipped work (status page, SSO, BYOK, audit log) into self-serve answers for security reviewers.
7. **GDPR erasure + export endpoints** — legal requirement; builds directly on the just-shipped user/org CRUD.
8. **Start SOC 2 controls now** — 6–9 month lead time means the clock starts only when you do; interim answer = security page + pen test.
9. **Contract an external pen test** — one engagement produces the letter questionnaires ask for and de-risks items 1–7.
10. **Docs site** — evaluators judge maturity by docs; prerequisite for support-SLA and self-host-installer credibility.

Phase 2 = revenue/trust blockers (first paying orgs). Phase 3 = scale/compliance (win the 500+-employee buyer).
