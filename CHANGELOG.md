# Changelog

## 0.2.1

- Browse, preview, and import assembled Light Armour shapes from the SDK's composite recipes. Individual armour face FBXs are under alternate stages.
- Match FBX metadata IDs to block model definitions where available. Group categories by function and block family, using SDK paths when a definition link is unavailable.
- Armour geometry uses the SDK face meshes. Game-specific tiled armour shading is pending. The 2.5 m round corner does not pass the closed-edge check.

## 0.2.0 · Local milestone included in 0.2.1

- Added a selected-model panel with SDK path, category, size, and, after preview generation, mesh bounds and a summary of mesh and material names.
- Added on-demand model thumbnails rendered in a separate Blender process and cached locally. The thumbnails show geometry with neutral shading.

## 0.1.1

- Split Blocks and Production into separate tabs and added category and size filters.
- Limited model browsing to block and armour folders, excluded animation paths, and disabled embedded animation imports.
- Added a GitHub Pages feed for installing and updating through Blender.

## 0.1.0

- Initial preview with SDK detection, text search, and model, material, and decal browsing.
- Added on-demand FBX import and local texture links for supported SDK materials.
