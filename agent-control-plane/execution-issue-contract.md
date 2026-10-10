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

## Lease Acquisition & Exit States

### Exclusive Per-Issue Lease Acquisition
To prevent race conditions where concurrent bot runs for the same issue both observe an inactive state and mutate the repository in parallel, bots must acquire an exclusive per-issue guard before checking or adding `agent-active` and prior to any repository mutation:
1. **Per-Issue Execution Guard**: An atomic per-issue concurrency lock (e.g., GitHub Actions concurrency group scoped strictly to the issue number `concurrency: group: agent-execution-${{ issue.number }}, cancel-in-progress: false`, or an atomic conditional API check) ensures that concurrent runs for the same issue are serialized. Concurrent runs cannot both acquire the guard simultaneously.
2. **Independent Parallel Execution Across Issues**: Concurrency locks are scoped exclusively to individual issue numbers (`agent-execution-${issue_number}`). Distinct issues run concurrently and independently without contention.
3. **Lease Verification & Claim**: Within the exclusive per-issue guard, the bot verifies that `agent-active` is absent and that no active lease comment exists. It then applies the `agent-active` label, posts a lease comment referencing the workflow run ID, and proceeds to execution. If `agent-active` is already present, the run aborts immediately without mutation.

### Exit States

Upon completion or termination, the bot releases the lease into one of these states:

| State | Meaning | Mandatory Action |
|---|---|---|
| `waiting` | CI, network, rate limit, or service unavailable. | Wait with bounded backoff; do not count as code failure. |
| `blocked` | Product decision, missing info, risk, or extra permission required. | Post question with evidence and release lease. |
| `failed` | Third identical failure or critical check failed. | Preserve diff/PR, post `agent-failed`, release lease. |
| `delivered` | Merge and targeted post-merge verification passed. | Link PR, checks, and post-merge evidence before issue closure. |
