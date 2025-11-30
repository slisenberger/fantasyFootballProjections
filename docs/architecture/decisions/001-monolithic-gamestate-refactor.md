# 1. Refactor Monolithic GameState

Date: 2025-11-30

## Status

Accepted

## Context

The `engine/game.py` file contains a `GameState` class that has grown to over 900 lines. It violates the Single Responsibility Principle by handling:
1.  **State Management:** Tracking scores, clock, yard line, possession.
2.  **Simulation Logic:** Executing plays (`advance_snap`), determining outcomes.
3.  **Model Integration:** Loading and sampling from KDEs and Regressions.
4.  **Rule Enforcement:** Applying scoring rules (`score.py` logic overlaps here).

This tight coupling makes it difficult to:
*   Unit test specific mechanics (e.g., clock runoff) without instantiating the entire engine.
*   Swap out simulation components (e.g., trying a new `PassStrategy`).
*   Reason about the system flow.

## Decision

We will refactor `GameState` into three distinct components, following the "Builder-Runner-State" pattern:

1.  **`State` (Data Class):** A pure data container representing the snapshot of a game at time $t$. It will have no dependencies on models or random number generators. It should be serializable.
    *   *Responsibilities:* Field position, score, clock, down/distance, timeouts.

2.  **`GameBuilder` (Factory):** Responsible for initializing the `State` and loading/injecting necessary models (Strategy objects).
    *   *Responsibilities:* Loading `pbp_data`, initializing Estimators, injecting KDEs.

3.  **`GameRunner` (The Engine):** The execution loop that mutates the `State`.
    *   *Responsibilities:* `advance_snap()`, `play_game()`, applying `Strategy` objects to the `State`.

## Consequences

### Positive
*   **Testability:** `State` can be easily mocked. Strategies can be tested in isolation.
*   **Maintainability:** Files will be smaller and focused.
*   **Flexibility:** Easier to implement alternative simulation rules (e.g., College rules, Overtime rules) by swapping the Runner or Strategies.

### Negative
*   **Complexity:** More files and classes to manage.
*   **Refactoring Cost:** Significant effort to untangle the current "God Class".
*   **Performance:** Potential slight overhead from object passing, though likely negligible compared to Python loop overhead.

## Compliance
All future engine modifications must adhere to this separation. Logic should not be added directly to the data container (`State`).
