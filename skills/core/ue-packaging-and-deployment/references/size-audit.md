# Size audit: shipped build, local disk, git/LFS repo

An "optimize size on disk" request covers three different sizes. Measure and report them separately. Only the first is what players download.

## 1. Shipped size: package one map

1. Compile the game target first (`Build.bat <Project> Win64 Development -project=<uproject> -waitmutex`). This catches editor-only API calls in seconds instead of after a long UAT run.
2. Package only the map under review, with the Editor closed or idle:
   ```
   RunUAT.bat BuildCookRun -project=<uproject> -noP4 -platform=Win64 -clientconfig=Development
     -build -cook -map=/Game/Path/To/Map -stage -pak -iostore -compressed
     -stagingdirectory=<Project>/Saved/StagedBuilds -unattended -utf8output
   ```
   - From git-bash, wrap it as `pwsh -NoProfile -Command "& 'C:\...\RunUAT.bat' ... *> '<log>'"` and run it in the background.
   - Read the log tail for `BUILD SUCCESSFUL` and `Cooked packages N`.
3. The content size is the `Content/Paks/*.ucas` file(s). The `.exe` and `.pdb` are Development-build overhead, not content.
4. Trim textures (max size, LOD bias) only if that number is a problem. Capping hero ground and foliage textures costs close-up quality.

## 2. Local disk (not shipped, not in git)

- Rank with `du -sm Saved/* Intermediate DerivedDataCache` before deleting anything.
- Agent output folders, e.g. `Saved/VibeUE/<Task>`:
  - Delete only folders nothing tracked refers to. Check with `git grep -l -I <FolderName>` across the repo, not just `docs/`; scripts can reference them too.
  - Keep folders cited by evidence docs and any checkpoint or migration data.
  - A raw GPU dump whose summary is already recorded in evidence JSON can go.
- Autosaves, crash dumps and the Fab download cache are safe once the Editor is closed.
- Don't bother deleting `Intermediate/Build`: it regrows on the next build and forces a full rebuild.
- Before deleting a Content folder, binary-grep the rest of `Content` and `Config` for its package path (`grep -rl --binary-files=binary "<Folder>" Content Config`, excluding the folder itself), and confirm it is untracked or unused.
- Every deletion is permanent. List the exact items and their sizes for the user before deleting.

## 3. Git and LFS repo

1. Find large binaries stored as plain git blobs: run `git check-attr filter` on `git ls-files '*.uasset' '*.umap'` and keep the files without `filter: lfs`.
   - Assets rewritten on every regenerate (PCG graphs, generated data) are the leak: each commit adds a full copy to history.
2. Add LFS rules to `.gitattributes`, then convert the existing files: `git add .gitattributes && git add --renormalize -- '<glob>' ...`.
   - Verify one file in `git diff --cached` shows as a roughly 130-byte pointer.
   - Commit the conversion separately. History is not rewritten.
3. Prune old LFS versions only with remote verification, and dry-run first:
   - `git lfs prune --dry-run --verify-remote`, then `git lfs prune --verify-remote`.
   - Unpushed and recent objects are retained.
   - Then run `git gc` and `git fsck --connectivity-only` (dangling blobs are harmless).
   - This is a destructive operation, so get the user's approval first.
