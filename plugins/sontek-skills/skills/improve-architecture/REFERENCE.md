# Reference

## Dependency Categories

When assessing a candidate for deepening, classify its dependencies:

### 1. In-process

Pure computation, in-memory state, no I/O. Always deepenable — just merge the modules and test directly.

### 2. Local-substitutable

Dependencies that have local test stand-ins (e.g., PGLite for Postgres, in-memory filesystem). Deepenable if the test substitute exists. The deepened module is tested with the local stand-in running in the test suite.

### 3. Remote but owned (Ports & Adapters)

Your own services across a network boundary (microservices, internal APIs). Define a port (interface) at the module boundary. The deep module owns the logic; the transport is injected. Tests use an in-memory adapter. Production uses the real HTTP/gRPC/queue adapter.

Recommendation shape: "Define a shared interface (port), implement an HTTP adapter for production and an in-memory adapter for testing, so the logic can be tested as one deep module even though it's deployed across a network boundary."

### 4. True external (Mock)

Third-party services (Stripe, Twilio, etc.) you don't control. Mock at the boundary. The deepened module takes the external dependency as an injected port, and tests provide a mock implementation.

## Testing Strategy

The core principle: **replace, don't layer.**

- Old unit tests on shallow modules are waste once boundary tests exist — delete them
- Write new tests at the deepened module's interface boundary
- Tests assert on observable outcomes through the public interface, not internal state
- Tests should survive internal refactors — they describe behavior, not implementation

## Naming the Friction (APOSD red flags)

The exploration in Step 1 is friction-driven, not checklist-driven — but when you name a candidate, reach for precise vocabulary so the user knows *why* it's worth deepening. Three complexity symptoms tell you how bad it is: **change amplification** (a simple change forces edits in many places), **cognitive load** (you must know too much to work here), and **unknown unknowns** (it's not even obvious what a change would touch — the worst). The structural red flags that produce them:

| Red flag | One-line detection |
|---|---|
| **Shallow module** | Interface nearly as complex as the implementation it hides |
| **Classitis** | Many small classes, each doing little — the friction of bouncing between files |
| **Information leakage** | The same design knowledge (format, ordering, constant) lives in two modules; they change together |
| **Temporal decomposition** | Module boundaries mirror execution order (step1/step2/step3), forcing a fixed call sequence |
| **Pass-through method** | A method that only forwards arguments to another with the same signature |
| **Conjoined methods** | You can't understand one method without reading another's implementation |
| **Shallow split** | A split left both halves with interface ≈ implementation, reusable only together |

**Before naming a red flag, steel-man it.** What's the best argument it's intentional? An adapter, facade, or decorator where thinness *is* the point, or an injected seam that exists for testing, is not a defect. When depth and cohesion conflict, prefer cohesion — a focused shallow module beats a bloated deep one. Never call length alone complexity.

## Naming the Solution (GoF patterns — when one genuinely fits)

When a deepened interface maps cleanly onto a named Gang-of-Four pattern, name it — it gives the design a shared vocabulary and a known shape. But a pattern is indirection, and indirection is a cost. Name a pattern only when **all three** hold: the problem is genuinely recurring (not a one-off), the flexibility outweighs the extra classes, and the team can maintain it. If a straightforward solution works, recommend that instead.

| Symptom in the current code | Pattern direction |
|---|---|
| `if/else` / `switch` on object **type** (≥3 branches, still growing) | Strategy, Visitor |
| `if/else` / `switch` on object **state**, transitions scattered | State |
| Telescoping constructors / positional-arg soup | Builder |
| Subclass explosion for feature combinations | Decorator, Strategy, Bridge |
| `new ConcreteClass()` scattered through callers | Factory Method, Abstract Factory |
| Subsystem complexity leaking into callers | Facade |
| Manual state propagation to many dependents | Observer |

Always pair the pattern with its **counter-indicator** when you present it ("Strategy *if* a third payment type is actually coming; if these two are the whole domain, the conditional is simpler"). Patterns applied speculatively are pattern-mania — the worst outcome here is a deepened module that's also over-engineered.

## Issue Template

<issue-template>

## Problem

Describe the architectural friction:

- Which modules are shallow and tightly coupled
- What integration risk exists in the seams between them
- Why this makes the codebase harder to navigate and maintain

## Proposed Interface

The chosen interface design:

- Interface signature (types, methods, params)
- Usage example showing how callers use it
- What complexity it hides internally

## Dependency Strategy

Which category applies and how dependencies are handled:

- **In-process**: merged directly
- **Local-substitutable**: tested with [specific stand-in]
- **Ports & adapters**: port definition, production adapter, test adapter
- **Mock**: mock boundary for external services

## Testing Strategy

- **New boundary tests to write**: describe the behaviors to verify at the interface
- **Old tests to delete**: list the shallow module tests that become redundant
- **Test environment needs**: any local stand-ins or adapters required

## Implementation Recommendations

Durable architectural guidance that is NOT coupled to current file paths:

- What the module should own (responsibilities)
- What it should hide (implementation details)
- What it should expose (the interface contract)
- How callers should migrate to the new interface

</issue-template>
