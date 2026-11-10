---
name: ue-niagara-custom-modules
description: Build Niagara scratch-pad modules and emitter interactions in Unreal Engine 5.8. Use for custom particle attributes, attribute readers, collision-driven secondary effects, texture sampling, or reusable rain and waterfall behaviors.
metadata:
  engine-version: "5.8"
  category: vfx-audio
---

# Niagara custom modules

Use `ue-niagara-vfx` for the system/emitter model. Add a custom module when a built-in module cannot express the required behavior clearly, or when a repeated graph deserves one consistent interface. A scratch-pad module is useful for local exploration; promote stable, shared behavior to a reusable Niagara module only when more than one effect needs it.

## Stage and parameter map

Choose the stage by when the value must change: emitter setup for emitter-level state, Particle Spawn for each new particle, Particle Update for per-frame motion, and an event handler for event-driven secondary particles. Inputs should state units and meaning; outputs should write the intended namespace and attribute. Inspect upstream and downstream writes to the same attribute. Niagara stack order matters: a later module can replace position, velocity, size, or color and make an earlier calculation appear broken.

Keep a custom graph narrow. For example, a follower module can read leader-particle position through a Particle Attribute Reader, combine it with a per-particle offset, and write the follower position. Define the leader emitter binding and behavior when no valid leader exists. Ensure both emitters use compatible simulation targets and that the data is available at the stage where it is read. Do not assume an emitter name, particle ID, or event stream is valid merely because the graph compiles.

## Event-driven secondary effects

For rain splashes or other contact effects, a collision event can spawn a smaller secondary emitter at the contact position. Confirm the selected event handler, source emitter, persistent-ID requirements where applicable, and CPU/GPU support in the current UE version and emitter setup. Bound events per frame and particles per event; dense rain should not create an unbounded splash system. Use collision position and normal to orient a splash or ripple, then let size and opacity decay independently. If GPU simulation or platform constraints make events unsuitable, use an alternate visual method rather than depending on an unsupported event path.

For a waterfall, separate large-scale flowing shape from falling droplets, foam, splashes, and optional caustic or refraction details only where each contributes to the intended view. A moving UV material may carry most of the flow at lower particle cost. Collision-driven accents belong near contact surfaces; their spawn rate should reflect visible water contact, not the entire waterfall area.

Texture sampling is another data source, not a required asset pipeline. Map particle position or authored UV into the texture's coordinate space, sample the intended channel, and decide whether it drives spawn density, color, size, or motion. Verify UV origin, wrapping, filtering, and missing-texture behavior. Prefer a simple analytic mask when it serves the same purpose.

## Verification

Test the module at zero and high spawn rates, with missing inputs and changing emitter transforms. Watch both the written attributes and the rendered result. If particles stop moving after adding a mesh-following or location module, look for a later position or velocity write before retuning forces.

For scratch-pad input authoring, warm the original module's stack view before editing, apply the graph, and check that the actual stack exposes each expected editable input exactly once; connected pins and a clean compile alone do not establish that the stack sees them. Set an input value, add and wire another input, apply again, and confirm both the expanded input set and the original value survive; a no-op reapply alone does not test signature changes. When apply broadcasts for multiple scripts, warm and edit two modules before one apply, set and read back distinct overrides, then edit both again and verify both input lists and values survive. Keep a disposable system's editor open and its module selected while adding an input, then inspect the visible stack without reopening; a data-only topology query cannot prove the open view refreshed. When testing a wiring change on a duplicated system, first inspect an unmodified duplicate as a control: duplication itself can make previously missing stack inputs appear, so a passing modified copy does not prove the wiring fixed them. Use descriptive Custom HLSL pin names rather than `In` and `Out`, and read back their actual names before wiring: Niagara can sanitize reserved identifiers.

When implementing a C++ scratch-apply workflow, follow the target engine's native apply notification: after editing a scratch script, `FNiagaraEditorModule::Get().ScriptApplied(Scratch, FGuid())` refreshes dependent stack state. In UE 5.8, this notification made inputs visible in a previously warmed stack without duplicating the asset; test the exact original module and compile diagnostics. Inspect and disclose the notification's side effects: engine listeners may reinitialize running instances, including on repeated broadcasts, so avoid assuming apply is harmless for live previews. Do not assume a graph-change notification or recompilation refreshes the stack, and do not invoke `RefreshFromExternalChanges()` blindly: pin reallocation can assert during signature changes. Verify the event and ordering against the target engine source.

## References & source material

- UE 5.8 source: `Engine/Plugins/FX/Niagara/Source/Niagara/Classes/NiagaraScript.h` (`UNiagaraScript`).
- UE 5.8 source: `Engine/Plugins/FX/Niagara/Source/Niagara/Classes/NiagaraDataInterfaceParticleRead.h` (`UNiagaraDataInterfaceParticleRead`).
- UE 5.8 source: `Engine/Plugins/FX/Niagara/Source/Niagara/Classes/NiagaraDataInterfaceTexture.h` (`UNiagaraDataInterfaceTexture`).
