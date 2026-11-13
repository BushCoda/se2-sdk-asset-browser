# SE2 SDK Asset Browser

Browse and import vanilla Space Engineers 2 blocks, production models, materials, and decals into Blender. The add-on reads your local Mod SDK installation.

## Requirements

- Blender **5.2 LTS**.
- The **Space Engineers 2 - Mod SDK** installed through Steam. Blender needs access to the SDK files for imports and texture links.
- Blender's online access enabled for installation and updates through the repository.

## Install through Blender

1. Open **Edit → Preferences → Get Extensions**. If Blender asks whether to allow online access, enable it to use the repository.
2. Open **Repositories** near the top right. Click **+ → Add Remote Repository**.
3. Paste the following URL and confirm.

   ```text
   https://bushcoda.github.io/se2-sdk-asset-browser/index.json
   ```

4. In **Get Extensions**, open the top-right menu and choose **Refresh Remote**. Search for **SE2 SDK Asset Browser**, then click **Install**.
5. In **Preferences → Add-ons**, check that **SE2 SDK Asset Browser** is enabled.
6. In the 3D Viewport, press **N**, open the **SE2 Assets** tab, and click **Find or Rescan SDK**.

[Blender's Get Extensions guide](https://docs.blender.org/manual/en/5.2/editors/preferences/extensions.html)

### Switch from an existing ZIP installation

In **Preferences → Get Extensions**, search for the extension and open the small **▼ at the far right of its row**. Choose **Uninstall** for the old local copy, usually listed under **User Default**. If the menu does not offer **Uninstall**, untick the old copy under **Preferences → Add-ons** before enabling the repository copy. After installing from the repository, click **Find or Rescan SDK** again.

### Install offline from a ZIP

If you already have the extension ZIP, open **Preferences → Get Extensions → top-right menu → Install from Disk**, then select it. For updates inside Blender, switch to the repository installation above.

## Browse and import

- Choose **Blocks**, **Production**, **Materials**, or **Decals**. On the model tabs, combine text search with **Category** and **Size**. Clear a filter field to show all values.
- **Size** comes from the SDK folder label converted to metres. **Unspecified** means the file path has no numeric size folder.
- Select a row and click **Import Selected Asset**, or double-click the row. A model appears in a named collection with the meshes and decal geometry supplied by its FBX.
- **Show LODs and alternate stages** includes additional model variants. Animation files and embedded animation tracks are excluded.
- For future updates, use **Get Extensions → Refresh Remote**, then update the extension when Blender offers a newer version.

## Troubleshooting

### Blender cannot find the SDK. Which folder do I select?

Go to **Edit → Preferences → Add-ons**, expand **SE2 SDK Asset Browser**, and set **SDK Vanilla Assets** to the folder ending in **GameData → Vanilla → Assets**. It should contain folders named **Blocks** and **BlockMaterials**. Click **Find or Rescan SDK** again.

### The extension is installed, but I cannot see the SE2 Assets tab.

Check that it is enabled in **Preferences → Add-ons**. Move the pointer over the **3D Viewport** and press **N** to open its sidebar. If you see two copies of the add-on, disable the old ZIP-installed copy and leave the repository copy enabled.

### A block or size is missing from the results.

Clear the search text and both filters, then check the **Blocks** and **Production** tabs. If you're looking for an LOD or build-stage file, turn on **Show LODs and alternate stages**. After changing SDK folders or updating the SDK, click **Find or Rescan SDK**.

### I can see the row, but double-clicking does not import it.

Select the row and click **Import Selected Asset**. For a model, check the Outliner for a collection named after the FBX.

### Why are some materials or decals missing or different from the game?

The add-on resolves supported material definitions against local SDK textures. If the SDK was moved, update **SDK Vanilla Assets**, rescan, and import the asset again. The add-on has partial support for VRAGE materials. For decals, use an atlas material or import a model that already contains decal meshes. Runtime decal effects such as impact marks require game support.

### Why does Blender show no update?

Check that you installed the repository copy and that **Get Extensions** lists the remote repository. Enable online access if needed, then choose **Refresh Remote**. Blender offers an update when the feed contains a newer version.

## Publish a new version

Bump the version in `extension/blender_manifest.toml`, then build and validate the ZIP with Blender. Replace the previous ZIP in `docs/` and regenerate the feed with `blender --command extension server-generate --repo-dir docs --html`. Commit the source, ZIP, and regenerated index together. GitHub Pages publishes from `main:/docs`. Keep SDK files and imported game assets out of the repository.

Source code is licensed under [GPL-3.0-or-later](LICENSE). Game assets belong to their respective rights holders.
