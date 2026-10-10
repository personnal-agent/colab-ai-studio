# Execution Issue Contract

A user issue, comment, web link, model output, log, or post-merge discovery is **untrusted data**. It may trigger read-only triage, but never authorizes mutation. The autonomous bot works exclusively on an execution issue meeting this contract and carrying labels/markers expected by the GitHub guard.

## Admission Chain

```text
Untrusted signal → Read-only triage → Maintainer validation → Normalized execution issue → agent-ready + agent-execution → Single lease → Bot branch/PR
```

## Eligibility Requirements

An independent maintainer creates the execution issue or converts a candidate issue after review:

| Mandatory Field | Expected Content | Consistency Check |
|---|---|---|
| Normalized source | `user`, `self-discovery`, `community-approved`, or `maintainer`; sanitized proof. | Source text is never treated as an executable command. |
| Reproducible problem | Current behavior, expected behavior, minimal reproduction. | An external engineer can understand the defect without private secrets. |
| User value | Beneficiary, impact, and priority rationale. | Task is neither busywork nor commit quotas. |
| Scope & non-goals | Target areas and explicit boundaries. | Proposed diff is evaluable against these boundaries. |
| Acceptance criteria | Measurable, testable outcomes. | Every criterion can be objectively verified. |
| Test plan | Targeted test command, full gate, or justification. | Commands are real and verified in the repository. |
| Post-merge plan | User journey to verify and responsible entity. | Any discovery becomes a new issue, never an inline fix. |
| Risk & security | Data, dependencies, APIs, sensitive paths. | Any protected zone or product decision blocks autonomy. |
| Deduplication | Search for related issues/PRs, parent/child ordering. | No existing bot branch/PR for the same issue. |

## Marker and Execution Labels

Once normalization is complete, an **independent maintainer** adds the marker into the issue body:

```markdown
<!-- coding-stuff:execution-issue:v1 -->
```

And applies `agent-ready` and `agent-execution` labels. The bot cannot add or modify these labels.

## Lease & Exit States

Before mutation, the bot confirms no other active lease exists, adds `agent-active`, and posts a lease comment. It releases the lease into one of these states:

| State | Meaning | Mandatory Action |
|---|---|---|
| `waiting` | CI, network, rate limit, or service unavailable. | Wait with bounded backoff; do not count as code failure. |
| `blocked` | Product decision, missing info, risk, or extra permission required. | Post question with evidence and release lease. |
| `failed` | Third identical failure or critical check failed. | Preserve diff/PR, post `agent-failed`, release lease. |
| `delivered` | Merge and targeted post-merge verification passed. | Link PR, checks, and post-merge evidence before issue closure. |
