# SE2 SDK Asset Browser

A Blender 5.2 LTS extension for browsing and importing assets from a local Space Engineers 2 Mod SDK installation. The extension package contains code only.

1. In Blender, open Preferences → Get Extensions and choose Install from Disk. Select the release ZIP.
2. In the 3D View, press N and open the SE2 Assets tab.
3. Click Find or Rescan SDK. For a manual setup, point the add-on preferences to the SDK's GameData/Vanilla/Assets directory.
4. Search Models, Materials, or Decals. Double-click a row or use Import Selected Asset. Enable alternate stages to find LODs and other variants.

Models import into a named collection with the meshes and decal geometry supplied in their FBX. The extension resolves supported material definitions against local SDK textures. VRAGE shader effects and runtime decal definitions require separate support. The browser uses a searchable list, with no thumbnail gallery in this version.

The local SDK must remain available for texture links. Keep the SDK files and any generated or imported game content out of the source repository.

Source code is licensed under GPL-3.0-or-later. Game assets belong to their respective rights holders.
