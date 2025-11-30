# Action Plan: Documentation Modernization (Docs-as-Code) - Prioritized

This plan transforms the project's documentation from a collection of stale markdown files into a "Living Knowledge Base" powered by type hints, automated generation, and Architectural Decision Records (ADRs).

## Tier 1: High ROI / Immediate (The "Force Multipliers")
*These actions drastically improve developer velocity and AI-assistance capabilities immediately, with minimal setup cost.*

### Step 1.1: Retrofit Type Hints (The Foundation)
*   **Context:** The critique highlights that "semantically accessible" code relies on robust type hints.
*   **Action:** Systematically apply Python type hints (`typing`) to all function signatures and class attributes.
*   **Tooling:** Use `mypy` in strict mode to identify gaps.
*   **Workflow:**
    1.  Target `engine/game.py` and `stats/players.py` first (Core Logic).
    2.  Use AI assistance to infer types for complex DF transformations.
    3.  **Definition of Done:** `mypy --ignore-missing-imports` passes on core modules.
*   **Status:** **[Done]**

### Step 3.1: Architectural Memory (ADRs)
*   **Goal:** Capture *why* decisions were made, preventing the "Chesterton's Fence" problem during the refactor.
*   **Action:** Create `docs/architecture/decisions/` and populate it as we make decisions.
*   **Immediate Tasks:**
    *   `001-monolithic-gamestate-refactor.md`
    *   `002-bayesian-estimators.md`
    *   `003-xgboost-migration.md`
*   **Status:** **[Done]**

### Step 4.1: The AI Context Map (`llms.txt`)
*   **Goal:** Create a high-density entry point for AI Agents (like Gemini/Copilot) to understand the project instantly.
*   **Action:** Create a root-level file designed specifically for RAG consumption.
*   **Content:** Condensed project structure, key architectural patterns ("Trilogy of Simulation"), and command reference.
*   **Status:** **[Done]**

---

## Tier 2: High Value / As-We-Go (The "Good Hygiene")
*These should be integrated into the refactoring workflow. Don't stop everything to do them, but don't merge code without them.*

### Step 1.2: Structured Docstrings (Google Style)
*   **Context:** Docstrings are currently sporadic or unstructured.
*   **Action:** Enforce the **Google Docstring Style** for all public interfaces *touched during refactoring*.
*   **Details:**
    *   Must include `Args`, `Returns`, and `Raises` sections.
    *   **Crucial:** The `Args` section must describe the *shape* of DataFrames if a DF is passed.
*   **Enforcement (As-We-Go):** Implement a `pre-commit` hook to run `ruff --select D` (or `pydocstyle`) on staged files. This ensures new/modified code is compliant.
*   **Status:** **[Done]**

### Step 3.2: Migration of Legacy Docs
*   **Action:** Refactor existing MD files into the new structure.
*   **Details:**
    *   `hypotheses.md` -> `docs/architecture/hypotheses_log.md`
    *   `ROADMAP.md` -> `docs/project/roadmap.md`
    *   `BENCHMARKS.md` -> `docs/guides/benchmarking.md`
*   **Status:** **[Done]**

---

## Tier 3: Nice-to-Have / Polish (The "Professional Grade")
*These provide a polished experience but block neither development nor understanding. Defer until the codebase stabilizes.*

### Step 2.1 & 2.2: Setup MkDocs Material & mkdocstrings
*   **Action:** Initialize a static site generator to compile the docs into HTML.
*   **Benefit:** Beautiful, searchable documentation site.
*   **Timing:** Post-refactor.

### Step 2.3: CI/CD Integration (The Quality Gate)
*   **Action:** Add strict documentation checks to the pipeline.
*   **Tooling:** `interrogate` (for overall coverage) and `pydocstyle` (for explicit format checks).
*   **Timing:** Enable `interrogate` as non-blocking warnings first (e.g., `fail-under=current_coverage`), then strictly enforce once coverage is high. `pydocstyle` can run as a blocking check, complementing the pre-commit hook.

## Git Commit Strategy

### Tier 1: High ROI / Immediate
- **Commit 1.1:** `docs(types): retrofit type hints for core engine/stats`
- **Commit 1.2:** `docs(adr): init ADR structure and add refactor decisions`
- **Commit 1.3:** `docs(rag): add llms.txt context map`

### Tier 2: High Value / As-We-Go
- **Commit 2.1:** `docs(api): enforce Google-style docstrings on new modules`
- **Commit 2.2:** `docs(legacy): migrate hypotheses and roadmap to new structure`

### Tier 3: Nice-to-Have / Polish
- **Commit 3.1:** `docs(site): init MkDocs and mkdocstrings configuration`
- **Commit 3.2:** `ci(docs): add interrogate and pydocstyle gates`