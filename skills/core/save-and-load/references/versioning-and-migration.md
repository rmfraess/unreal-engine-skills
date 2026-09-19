# Versioning and migration — full reference

Deep dive for [../SKILL.md](../SKILL.md). Covers save versioning strategies, field migration
patterns, `ULocalPlayerSaveGame` versioning hooks, backward compatibility rules, and platform
considerations. Grounded in UE 5.8
(`Engine/Source/Runtime/Engine/Classes/GameFramework/SaveGame.h`).

## Why versioning is non-optional

UE's tagged property serializer is tolerant of **schema additions**: a property that is present
in the save but missing in the current class is silently ignored on load; a property present in
the class but absent from the save gets its C++ default value. This makes adding fields safe.

Schema **removals and renames** require an explicit compatibility decision. Keep a temporary
`UPROPERTY` with the old serialized name for value conversion unless redirects have been
verified in the actual loading path and cooked target. The binary tagged loader enables
property redirects when cooked data is not required or `ArIsSaveGame` is set, and excludes
archives loading from cooked packages (`Class.cpp:1622,1688-1698`). The stock
`LoadGameFromMemory`/slot path does not set `ArIsSaveGame` (`GameplayStatics.cpp:2484-2485`),
so an editor test alone does not establish packaged compatibility. A redirect for a pure
rename can be configured as follows, subject to those gates:

```ini
[CoreRedirects]
+PropertyRedirects=(OldName="MySaveGame.Health",NewName="MySaveGame.MaxHealth")
```

Use a version migration when the value semantics change; a redirect alone only changes the
property name mapping. Without a redirect or retained field, the old value is not found.

## Version field convention

```cpp
UCLASS()
class MYGAME_API UMySaveGame : public USaveGame
{
    GENERATED_BODY()
public:
    // Always first; increment when schema changes in a breaking way.
    UPROPERTY() int32 SaveVersion = 1;

    // Current schema fields:
    UPROPERTY() float MaxHealth = 100.f;
    UPROPERTY() float CurrentHealth = 100.f;

    // Deprecated fields — keep for one version cycle so old saves can migrate:
    UPROPERTY() float Health = 0.f;  // retain the serialized v1 name for migration

    void MigrateAfterLoad();
};
```

Call a migration method explicitly after validating the result of generic
`UGameplayStatics` loading, before the rest of the game reads the data. The stock memory/slot
loader constructs and serializes the object; it does not invoke `UObject::PostLoad`:

```cpp
void UMySaveGame::MigrateAfterLoad()
{
    if (SaveVersion < 2)
    {
        // v1 stored a single "Health" field; v2 splits into Max/Current.
        MaxHealth     = 100.f;
        CurrentHealth = Health;
        SaveVersion   = 2;
    }
    // Add further version steps as needed:
    // if (SaveVersion < 3) { ... SaveVersion = 3; }
}
```

Keep the old serialized property name until no supported save version needs conversion, or
use a redirect proven in the target loader and build. Adding `_Deprecated` to a property name
is itself a rename; it does not recover the old value automatically. Remove the old field or
redirect only after the supported-save window no longer includes those files.

## Backward compatibility rules

| Change | Safe? | Notes |
|---|---|---|
| Add a new `UPROPERTY` | Yes | Missing fields default to C++ initializer value |
| Remove a `UPROPERTY` | No | Old saves carry the field; new code ignores it. No data loss, but migration is impossible after removal |
| Rename a `UPROPERTY` | Migration or verified redirect required | Preserve the old serialized name for conversion, or test redirects in the actual cooked loader |
| Change a `UPROPERTY` type | Migration required | The old tagged value may not be compatible with the new type; version-gate and test the actual old bytes |
| Change a `USTRUCT` field | Treat as rename | USTRUCT fields follow the same rules as UPROPERTY |
| Add a new slot | Yes | Existing slots are unaffected |

## ULocalPlayerSaveGame versioning

`ULocalPlayerSaveGame` provides a structured version hook pattern. Its
`LoadOrCreateSaveGameForLocalPlayer` helpers initialize the player association and invoke
the hooks; generic `UGameplayStatics` loading only deserializes the object and requires
explicit initialization before relying on those hooks.

```cpp
UCLASS()
class MYGAME_API UMyPlayerSave : public ULocalPlayerSaveGame
{
    GENERATED_BODY()
public:
    // Return the current schema version — increment on every breaking change.
    virtual int32 GetLatestDataVersion() const override { return 3; }

    // Called after a successful load from disk; SavedDataVersion holds
    // the version the file was written with.
    virtual void HandlePostLoad() override
    {
        Super::HandlePostLoad();

        if (GetSavedDataVersion() < 2)
        {
            // migrate v1 → v2
        }
        if (GetSavedDataVersion() < 3)
        {
            // migrate v2 → v3
        }
        // SavedDataVersion is updated to GetLatestDataVersion() automatically before save.
    }

    virtual void ResetToDefault() override
    {
        Super::ResetToDefault();
        // Set all fields back to their new-game defaults.
    }
};
```

Key `ULocalPlayerSaveGame` accessors (SaveGame.h):
- `GetSavedDataVersion()` — the version stored in the file (what it was last saved as).
- `GetLatestDataVersion()` — override to return your current version; defaults to 0.
- `GetInvalidDataVersion()` — returns -1; the initial value for a brand-new (never-saved) object.
- `WasLoaded()` — true if this instance came from disk rather than being freshly created.
- `HandlePostLoad()` — migration hook; called after load, not after create.
- `HandlePreSave()` / `HandlePostSave(bool)` — hooks around the save operation.

`SaveGameToSlotForLocalPlayer()` and `AsyncSaveGameToSlotForLocalPlayer()` return request
acceptance, not the platform-write result. Use `HandlePostSave(bool bSuccess)` or inspect
`WasLastSaveSuccessful()` after completion; the generic async delegate reports `bSuccess`.

## Detecting first-run vs. corrupt save

```cpp
// On sync load:
UMySaveGame* Loaded = Cast<UMySaveGame>(
    UGameplayStatics::LoadGameFromSlot(TEXT("Slot0"), 0));

if (!Loaded)
{
    // Null: the slot was absent, the platform read failed, the data was empty, or the
    // serialized class could not be resolved. Create a fresh save only after deciding how
    // to preserve/report a possibly unreadable existing slot.
    // Create a fresh save:
    Loaded = Cast<UMySaveGame>(
        UGameplayStatics::CreateSaveGameObject(UMySaveGame::StaticClass()));
}
else if (Loaded->SaveVersion > CURRENT_VERSION)
{
    // Save is from a newer build — handle gracefully (warn, reset, or error).
}
else
{
    Loaded->MigrateAfterLoad(); // explicit: generic loading does not invoke PostLoad
}
```

`LoadGameFromSlot` does not provide a game-level checksum or migration-success result. Treat a
non-null object as engine-level construction only; validate a magic/version/checksum field before
applying state that must not be silently lost.

`ISaveGameSystem::DoesSaveGameExistWithResult` returns `ESaveExistsResult::Corrupt` on some
platforms when the file exists but is unreadable. Use this to distinguish "no save" from
"corrupted save" when you need to display a different message to the player.

## Per-slot versioning for multiple profiles

When a game has multiple save slots, each slot independently tracks its version. If a player
loads an old slot and the game has been updated, migration runs for that slot. New slots start at
the current version. A reliable pattern:

- Embed `SaveVersion` at the top of every `USaveGame` subclass.
- When writing a new slot for the first time, set `SaveVersion = CURRENT_VERSION`.
- On any load, check `SaveVersion` before reading any other field.

## Platform considerations

**PC:** Saves are plain `.sav` files in `Saved/SaveGames/`; they persist between game updates as
long as the project's `Saved/` folder is not cleared. Steam Cloud Sync can replicate them to
other machines, which may introduce version skew between machines.

**Console:** Each platform's save system manages versioning independently at the OS level. The
engine's `ISaveGameSystem` wrapper handles the I/O, but you are still responsible for internal
schema versioning. Some platforms can pre-load saves to reduce perceived load time — your
`HandlePostLoad` migration will still run, so keep it fast.

**UE version upgrades:** UE's own internal serialization format may change across engine
versions. Epic handles this at the engine level (the save file header includes engine version
metadata); your `SaveVersion` field is for *your* schema, independent of the engine version.

## Enumerated version constants (recommended pattern)

```cpp
namespace ESaveVersion
{
    enum Type : int32
    {
        Initial      = 1,
        SplitHealth  = 2,   // v2: split Health → MaxHealth + CurrentHealth
        AddedGuild   = 3,   // v3: added GuildMembership array
        Latest       = AddedGuild,
    };
}
```

Use named constants instead of raw integers so migration steps are self-documenting and
reviewable. Check `SaveVersion < ESaveVersion::SplitHealth` rather than `SaveVersion < 2`.
