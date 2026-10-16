# Contributing to Colab AI Studio

Thank you for your interest in contributing to **Colab AI Studio**!

## How to Contribute

1. **Fork the Repository**: Create a personal fork of the repository on GitHub.
2. **Clone your Fork**: Clone your fork to your local machine and ensure Git hooks are active (`git config core.hooksPath .githooks`).
3. **Create a Dedicated Branch**: `git checkout -b <type>/<slug>` (e.g., `feat/brand-compiler`).
4. **Follow Coding Standards**:
   - **Backend (Python 3.10+)**: Write typed FastAPI/Pydantic v2 code, check syntax (`python3 -m py_compile`) and lint (`ruff check`), and route all JSON/media I/O through `JSONDocumentStore` and `MediaFileStore`.
   - **Frontend (React 18+ / TypeScript 5+)**: Write strict TypeScript without `any` or linter suppressions, verify types (`npm --prefix frontend run typecheck`) and lint (`npm --prefix frontend run lint`).
   - **Tests**: Follow strict Red-Green-Refactor TDD and run `pytest tests/ -q && npm --prefix frontend test -- --run`.
5. **Commit Changes**: Use Conventional Commits (`feat(scope): ...`, `fix(scope): ...`, `docs(scope): ...`).
6. **Submit a Pull Request**: Push your branch and open a Pull Request targeting `main` using `.github/PULL_REQUEST_TEMPLATE.md`.

## Code Standards & Integrity

- **Zero-slop policy**: Maintain clean layered architecture (`ARCHITECTURE.md`), no dead code, no circular dependencies, and no suppressed linter or type-checker rules (`# noqa`, `# type: ignore`, `eslint-disable`, `@ts-ignore`).
- **Test coverage**: Every modified or newly added line must be covered by automated tests (`100%` patch coverage target, `90%` project target).
