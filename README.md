# SE2 SDK Asset Browser

A Blender 5.2 LTS extension for browsing and importing assets from a local Space Engineers 2 Mod SDK installation. The extension package contains code only.

1. In Blender, open Preferences → Get Extensions and choose Install from Disk. Select the release ZIP.
2. In the 3D View, press N and open the SE2 Assets tab.
3. Click Find or Rescan SDK. For a manual setup, point the add-on preferences to the SDK's GameData/Vanilla/Assets directory.
4. Search Blocks, Production, Materials, or Decals. Use Category and Size together on the model tabs. Size is the SDK folder label converted to metres, and Unspecified means the path has no numeric size folder. Clear a filter field to show all values. Double-click a row or use Import Selected Asset. Enable alternate stages to find LODs and other variants.

Models import into a named collection with the meshes and decal geometry supplied in their FBX. The extension resolves supported material definitions against local SDK textures. VRAGE shader effects and runtime decal definitions require separate support. The browser uses a searchable list, with no thumbnail gallery in this version.

The local SDK must remain available for texture links. Keep the SDK files and any generated or imported game content out of the source repository.

Source code is licensed under GPL-3.0-or-later. Game assets belong to their respective rights holders.

## Install and update inside Blender

1. Open **Edit → Preferences → Get Extensions → Repositories**.
2. Choose **+ → Add Remote Repository** and paste this URL:

   `https://bushcoda.github.io/se2-sdk-asset-browser/index.json`

3. Sync the repository, then search for **SE2 SDK Asset Browser** and install it.
4. For future releases, sync and use Blender’s extension update controls.

If you previously installed from a ZIP, disable the disk-installed copy before enabling the repository copy. Run **Find or Rescan SDK** in the **SE2 Assets** tab to set up the new copy.

## Publish a new version

Bump the version in the extension manifest, then build and validate the ZIP with Blender. Replace the previous ZIP in `docs/` and regenerate the feed with `blender --command extension server-generate --repo-dir docs --html`. Commit the source, new ZIP, and regenerated index together. GitHub Pages publishes from `main:/docs`.
