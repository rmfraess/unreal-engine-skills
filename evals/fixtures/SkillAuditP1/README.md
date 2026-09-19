# UE 5.8.2 P1 contract probe

From the repository root (Windows, Python, installed UE 5.8.2 / CL 56702186):

```bash
UE_ENGINE_ROOT='C:/Program Files/Epic Games/UE_5.8' python evals/fixtures/SkillAuditP1/run.py
```

The runner builds this isolated editor target with UHT/UBT, launches a fresh headless
editor, waits for completion, and checks the newly exported automation result.
It does not open or change any production project. Generated output stays ignored;
UBT/engine tools may also use their normal system caches and trace locations.

Compile checks cover the submix-effect signature, functional-test cleanup signature,
thread-safe shared-pointer default, and a native `FDelegateHandle` member in a reflected
owner. The editor test covers case-insensitive string assertions, quaternion composition
(including a wrong-order control), and nested reflected UObject reachability through GC
(including collection after clearing the reference). It also checks Enhanced Input
bool/vector getter conversions and stale weak-pointer map identity using the engine's
explicit `TWeakObjectPtrMapKeyFuncs`, including an ordinary-equality control.
Transient unregistered mesh components check missing-socket world/component-space
transforms and ISM custom-data preservation versus reset when the float count changes.
These are CPU data checks, not rendered-mesh or material verification.

The probe also compiles the Niagara Data Channel context-writer signature and initializes
its access context; it does not publish to a channel asset. It parses project/plugin
descriptor keys in memory, including rejection of a version pin on a disabled plugin,
and compiles/links the supported stat group/extern/definition macros in one translation unit.
It does not test plugin discovery, activation, packaging, or cross-file stat linkage.

An in-memory save round trip checks ordinary/SaveGame/Transient property behavior,
confirms the stock loader leaves `ArIsSaveGame` false and does not invoke the local-player
`HandlePostLoad` hook, and rejects empty input. A standalone timer manager verifies that a
next-tick handle can be cleared. No save slot is written, and no world timer is advanced;
these checks do not prove cooked redirects, migration, disk persistence, or timer cadence.

The same probe compiles both `UFUNCTION(CallInEditor)` and
`UFUNCTION(meta=(CallInEditor="true"))`, then checks their reflected metadata and zero
parameter size. Both satisfy the Details button's metadata predicate in UE 5.8.2;
the audit's assertion that the metadata form is malformed is not a verified P1 fix.

Logs/results: `Saved/Build.log`, `Saved/Probe.log`, `Saved/Report/index.json`.
`-nullrhi` deliberately excludes rendering. This is representative contract evidence,
not exhaustive verification of every skill example, audio playback, functional-test
actor cleanup, packaging, multiplayer, or third-party UDS/UDW assets.
