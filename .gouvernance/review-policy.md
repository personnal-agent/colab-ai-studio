# AI Code Review Policy

## Golden Rule of AI Review

> **An AI coding agent must NEVER approve its own code.**
> All changes must be reviewed by an independent AI engine, dedicated reviewer sub-agent, or human maintainer.

---

## 1. Operational Review Modes

### Mode A: Light Review (Local Development)
- **Use Case**: Fast local iterations, everyday developer tasks on local branches.
- **Workflow**:
  1. Implement changes within minimal scope.
  2. Run local tests, linters, and formatters.
  3. Trigger local AI review (via CLI e.g. `greptile review` or dedicated reviewer sub-agent).
  4. Fix 100% of actionable defects in a single batch before committing.
  5. Propose clean Conventional Commit message for human approval.

### Mode B: Strict Review (Dual-Layer Defense for PRs)
- **Use Case**: Pull requests, multi-module refactorings, security-sensitive features.
- **Workflow**:
  1. **Layer 1 (Local Pre-Delivery)**: Run local test suite and local reviewer agent. Fix all local findings.
  2. **Layer 2 (Cloud PR Review)**: Push dedicated branch and open PR using `PULL_REQUEST_TEMPLATE.md`.
  3. **Mandatory Full-Text Reading**: Read 100% of full-text comments from review bots (CodeRabbit, Greptile, Codex). Never rely solely on green CI checkmarks.
  4. **Thread Resolution**: Address and resolve 100% of review threads with follow-up commits.
  5. **Human Maintainer Sign-Off**: The human maintainer conducts final approval and performs the merge.

---

## 2. Review Quality Gate & Acceptance Criteria

Before declaring a review complete, verify:
- [ ] Code was reviewed by an entity distinct from the authoring agent.
- [ ] 0 blocking issues or critical defects remain unaddressed.
- [ ] Tests cover newly introduced logic and regression cases.
- [ ] No secrets, tokens, or private environment variables are committed.
- [ ] Full review feedback is documented in the commit/PR body.
