# Bulk rename and folder moves

Recipe for renaming or moving many assets, maps, actor labels and the text that names them, while keeping the build identical. Do it in this order; each step names its check.

## 0. Scope and baseline (Editor open, nothing dirty)

- List the targets with the Asset Registry: `get_assets_by_path('/Game', True)`, filtered by regex on `asset_name`. Write `(old_path, new_path, class)` rows to a scratch `rename-plan.json`.
- Build new names with a regex. Then check for clashes **case-insensitively against every asset name in `/Game`**, not only the renamed set: a stripped prefix can collide with the vendor asset it was copied from (e.g. `SM_Rock_01`). Resolve a clash or an overly generic result with a descriptive word, not a code. `assert` that the new names are unique.
- Packages to delete: `get_referencers` on each one, filtered to paths outside the deleted set, must be empty. Delete them with `git rm` while the Editor is closed.
- Baseline to scratch JSON for each map: actor count, class `Counter`, labels, and ISM instance totals per mesh name. Also count components whose `static_mesh` is None.

## 1. Map and folder moves: the user does them in the Content Browser

`rename_asset` on a `World` is auto-cancelled (see SKILL.md). Before the handover:
- In each map being moved, set `enable_nanite` False on every `LandscapeProxy` that has it on, then save with `LevelEditorSubsystem.save_current_level()`. Record which landscapes you changed.
- `EditorLoadingAndSavingUtils.new_blank_map(False)` so no open map is inside the moving folder.
- Give numbered steps: which subfolders to Ctrl-select, the target folder, **Move Here**, OK on prompts, no **Save All**, and paste any save warning back.
- When the user says done, **check the disk** (`find Content/<target> -name '*.umap'`) and the registry for every expected final path. Drags get skipped, and a rename leaves the map in its old folder.
- Save any packages the move left dirty (they're the move's referencer fix-ups) with `EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)`.

## 2. Non-map assets: rename by script

`EditorAssetLibrary.rename_asset(old, new)` works for ordinary assets, and a new path in it also moves them. Test one first, then batch:
- Loop over the plan, skipping rows whose new path exists or old path is gone, so the call is resumable. Append `ok old new` to a scratch log and flush each row. Break after about 90 renames in the first call to measure speed. About 270 per call fits; MCP may report `timed_out` while the work still completes, so re-check the remaining count rather than retrying blindly.
- Then `EditorLoadingAndSavingUtils.save_dirty_packages(True, True)`.

## 3. Redirectors (5.8 Python has no `fixup_referencers`)

1. Collect redirectors: `ARFilter(class_paths=[TopLevelAssetPath('/Script/CoreUObject','ObjectRedirector')], package_paths=['/Game'], recursive_paths=True)`.
2. Collect the referencers of those redirectors, excluding the redirectors themselves. Moves made in the Content Browser already fix most of them; usually only a few meshes or skeletons remain.
3. Run `save_asset(ref, only_if_is_dirty=False)` on each referencer. Loading resolves the redirector, so the resave writes the new path. Then `scan_files_synchronous([full .uasset paths], True)`, because the registry keeps listing the old dependency until a rescan.
4. Re-query. When nothing outside the redirector set refers to them, run `delete_asset` on each one. Expect about 0.35 s per delete. Confirm that 0 are left.

## 4. Actor labels and Outliner folders

For each map: `load_level` it (it must not be dirty, or a prompt appears) and rewrite `set_actor_label` and `set_folder_path` with the same naming rules as the assets. Check that no duplicate labels result, then `save_current_level()` before loading the next map. Keep names that refer to a real in-world thing (a road named after a place) and report them.

## 5. Turn landscape Nanite back on

Setting `enable_nanite` True does not build the mesh. `save_current_level()` does, because `ALandscapeProxy::PreSave` rebuilds Nanite and blocks until it finishes. Verify that the `LandscapeNaniteComponent`'s `static_mesh` path now lives inside the new map package.

## 6. Text: scripts, C++, config, LFS, docs, issues

- `git grep -I -l` for the old tokens outside history folders. Apply the plan's name map with a whole-word regex, longest name first (`(?<![A-Za-z0-9_])(...)(?![A-Za-z0-9_])`), then the path-prefix replacements. A folder rename plus an asset rename can compose wrongly (old map path → `<newfolder>/<newname>` instead of `Maps/<newname>`), so check every `/Game/...` literal afterwards.
- Also rename generator f-strings (`f"{FOLDER}/SM_QR_X_{i}"`), label constants the scripts look up (`get_actor_label() == ...`), script filenames with `git mv` plus their imports, and intermediate file names.
- Sweep **asset properties that hold names as strings**, which no redirector fixes: PCG node settings that look actors up by label (dump each node's settings and grep for old tokens), DataTable/DataAsset name fields, Blueprint string defaults. Update them in the same pass as the labels.
- Extract every `/Game/[A-Za-z0-9_/.]+` literal from Scripts, Source and Config, and check `does_asset_exist or does_directory_exist` for each. The only acceptable misses are f-string prefixes and engine-stock config rules.
- Run `python -m py_compile` on the scripts. For LFS, update the patterns, then `git check-attr filter` on the new files.
- Update open issue bodies with old names via `gh issue edit --body`. Pin links to deleted files to a commit.

## 7. Verify and commit

- Close the Editor with nothing dirty, then build the Editor and Game targets. From bash, write a `.bat` that `call`s `Build.bat <Target> Win64 Development -Project="..." -WaitMutex` and run it with `cmd.exe /c <winpath>`. Inline quoting through `cmd.exe //c` silently runs nothing, so require `Result: Succeeded` in the log.
- Cold-launch on the new startup map. Compare against the baseline: actor counts, class counters, per-mesh instance totals mapped through the rename plan, 0 None meshes, 0 redirectors, and 0 old-name assets apart from deliberate keeps.
- Saved PCG output proves nothing about the graph still working: run Generate on each renamed map's PCG components with `auto_save=false`, compare per-mesh totals with the baseline, then discard (reload) instead of saving. Custom PCG elements often log their own accepted/rejected counts; compare those too, because a by-name lookup that finds nothing degrades output silently instead of erroring.
- Grep the cold-launch log for `Failed to compile Material`, `Requires valid texture`, `Failed to find object` and `when precaching Nanite Assembly`. Material-function texture slots and Nanite Assembly part lists can keep dead old paths that no redirector fixes, and they only show as default-checkerboard materials or missing branches at render time. For each hit, find the renamed target (`does_asset_exist`, folder listing), point the reference at it, and recapture the same view.
- Look at the result in the Editor viewport: a broken shared material (checkerboard ground, unmasked effects) passes every count-based check.
- Run the project tests with `Automation RunTests <Prefix>.`, throttling off, and grep the log for `Test Completed. Result=` and `Queue Empty`.
- Stage only the task paths (old folder, new folder, touched referencers, text files), and leave out other sessions' untracked content. Commit dead-package deletions, the rename, and doc/history deletions as separate commits.
