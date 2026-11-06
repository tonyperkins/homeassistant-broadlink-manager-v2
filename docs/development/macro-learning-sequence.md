# Macro Learning Sequence — Design Sketch (Issue #58)

Status: planned, next release cycle. This is a sketch, not a final spec.

## Goal

Let a user queue a list of command names for a device, then learn them
one-by-one in a guided loop: the app waits for each remote button press,
captures the code, and offers confirm / test / redo / skip before moving to
the next command. Removes the per-command modal round-trips when setting up
several devices.

Reporter's example (https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues/58)
shows the multi-device end state: a manifest of devices, each with a command
list, walked through learning sequentially.

## Scope

### v1 (single device)

- New "Learn Sequence" mode in the CommandLearner flow (or a sibling modal).
- Queue builder: add command names from three sources —
  built-in suggested commands, "From Your Other Devices" suggestions
  (already implemented via `getOtherDeviceCommands`), and free-text custom
  entry. Allow reorder/remove before starting.
- Learning loop, driven entirely by the frontend over existing endpoints:
  1. `POST /api/commands/learn` for the current queue item (same payload the
     single-command path sends today).
  2. Wait for capture via the existing pending/check-pending machinery
     (`POST /api/commands/check-pending` + reload).
  3. Per-item result screen: captured state, [Test] (existing
     `POST /api/commands/test`), [Redo], [Skip], then advance.
- Queue progress display: item list with per-item status icons
  (done / error / skipped / pending), mirroring the existing
  learned-commands list styling.
- Cancel mid-queue: stops after the current capture completes (never
  mid-learning, to avoid orphaning a learn session on the blaster).

### v2 (multi-device, defer until v1 is validated)

- Device picker or "create device on the fly" step before the queue builder.
- Sequence chaining across devices; between devices show a device-ready
  checkpoint (aim the blaster at the next unit).
- Possible manifest import (the reporter's YAML-ish example) — but note the
  JSON command import already covers "define devices + commands with codes";
  the manifest case is "define devices + command names to learn."

## Non-goals

- No backend orchestration of the sequence (no new batch endpoint in v1).
  Chaining existing single-command endpoints keeps the backend unchanged
  and the failure model simple.
- No background/parallel learning — one command at a time, as today.

## Key edge cases

- RF learning is a two-step sweep/capture flow; the sequence item must
  reuse the direct RF learning states, not assume single-shot IR.
- Failed capture (learn timeout / firmware error -4): mark error, offer
  retry; do not block the rest of the queue.
- Skipped commands should be easy to revisit (e.g. re-run sequence showing
  only missing commands — the queue builder can default to commands not yet
  learned on the device).
- Re-learning an existing name overwrites silently today; keep that
  behavior but surface "already learned" in the queue builder.
- State sync: after each capture, commands arrive asynchronously from
  Broadlink storage into devices.json — reuse loadLearnedCommands(true)
  polling; do not optimistically mark success without a captured code.

## Implementation notes

- Frontend-only for v1; all endpoints exist:
  - learn: `POST /api/commands/learn`
  - poll/sync: `POST /api/commands/check-pending`, `GET /api/commands/managed/<id>` style reloads
  - test: `POST /api/commands/test`
- Suggested starting point: extract the single-command learn lifecycle from
  CommandLearner.vue into a composable (e.g. `useCommandLearning`) so the
  sequence loop and the existing single-command form share one code path.
- Reuse `getOtherDeviceCommands` (`frontend/src/utils/commandSuggestions.js`)
  as a queue-builder source — its pure-function tests already cover the
  name-gathering logic.
- Backend change candidates (only if v1 hits friction): a batch-learn
  endpoint that accepts a command list and reports per-item status, so the
  frontend loop survives page reloads mid-sequence.

## Test plan

- Unit: queue state machine — advance on success, retry on error, skip,
  cancel-after-current, RF vs IR item typing (pure logic, framework-free
  tests like `frontend/test/commandSuggestions.test.mjs`).
- Integration (Flask client): none required for v1 if backend untouched;
  add endpoint tests only if a batch endpoint lands.
- Manual: 3-command IR sequence on a real device; RF item mid-sequence;
  timeout on one item then continue; cancel during capture.
