---
name: 3d-model
description: Make 3D assets for a Three.js / WebGL scene from a reference image. Generated photos (an image model; image to image keeps variants consistent) become meshes by TRELLIS (a whole object with vertex colour, for furniture and ornaments) or MoGe-2 (single-view geometry, for reliefs and surfaces); the results are simplified, sized, split into materials and packed as glTF (gltf-transform, meshopt). Use when asked to model, generate or replace an object, ornament, relief, texture or sky for a 3D scene, or to turn a reference picture into scene assets.
---

# 3D models from a reference image

**Machine-specific values** go in `doc.local.md` in this skill's folder (ignored by git through `*.local.*`). It gives the values for:

- `<venv-trellis>`, `<venv-depth>`: the two venvs;
- `<trellis-dir>`, `<moge-src>`, `<moge-pt>`: TRELLIS, MoGe-2 and its weights;
- `<generated>`: where generated sources live;
- the image API's key variable (never print its value), the proxy and the GPU.

If it is missing, ask the user where TRELLIS, MoGe and the generated sources are, and write it.

This skill describes a working method. It was developed for a WebGL room scene (furniture, ornaments, reliefs, skies); the scripts that ran it live in that project. For explainer videos, the assets feed **isometric-animation** (Three.js), or a 3D shot rendered in Remotion with `@remotion/three`.

## The pipeline

1. **Reference**: the user's picture of the scene, for example a panorama of the room. Read off its layout, objects and materials. Close-ups give the detail for ornaments.
2. **Photos**: one generated image per asset, kept outside the repo with a JSON of the prompts. Keep the generator **idempotent and cheap to rerun**:
   - **Keep what exists**: an existing image is kept, since each call is paid; `--force` makes a new one.
   - **Space and retry calls**: about 3 s apart, and a failed call is retried once.
   - **Asset table**: a table of assets with `kind` (`object` | `relief` | `texture`), `prompt`, and optional `size` and `ref`.
3. **3D**, by one of the methods in the next section.
4. **Pack**: simplify, size, assign materials and compress into one `.glb` (section "Packing").
5. **Look at it**: a quick point-splat preview of each mesh, then real renders in the app (last section).

## Which method?

| Use | Method | Why |
|---|---|---|
| A free-standing object seen from several sides: furniture, an ornament, a plant's pot | **TRELLIS** (image to 3D, `TRELLIS-image-large`) | A closed mesh with vertex colour, about 1 min per object. Its faces are soft and lumpy, with no fine detail. |
| A relief on a wall, a bust seen from the front, a surface's shape (a tufted cushion top) | **MoGe-2** (`moge-2-vitl-normal`: point map and normals from one photo) | Sharp detail and normals from the photo's own view. It falls apart into strips when seen more than about 30° off that view: make a second photo turned towards the viewer instead. |
| A flat glowing pattern, a sign, a glyph | neither: draw it (a font's outline, extruded) | Image generators misdraw symbols. |
| Something round and precise: a record, a drum table, a lathe profile | neither: build it procedurally in the scene code | Exact shape, its own UVs (anisotropy, textures). |

## Prompt patterns that worked

- **TRELLIS objects**: "Studio product photograph of a single …, the whole object in frame filling 80 %, a three-quarter view from the front-left, camera slightly above, centred, plain pure white seamless background, soft even studio light, soft contact shadow only, nothing else in the image". TRELLIS takes the object's front as +z, so a three-quarter view still faces it the right way.
- **White or pale objects** (books, a marble base, silver-green leaves): use a **mid-grey** background instead of white, or the cut-out loses parts.
- **MoGe reliefs**: "seen exactly from the front, orthographic, centred, filling 85 %, soft even light from the front-left, gentle shading that shows the relief, plain neutral mid-grey seamless background". Busts: frontal, symmetric, on a small socle.
- **Image to image for variants**: send an existing asset's image as the reference, with "The very same … as in the reference image, unchanged in its layout, at <hour>". Generate the reference first. A set of window skies made this way showed one consistent city.
- **Panoramas that repeat** around a room (a sky cylinder with a mirrored wrap): avoid a single distinctive feature such as a moon. Each one shows up several times; a moon showed as two.
- **Textures**: "seamless tileable … seen straight from above, flat and evenly lit, no seams, no reflections". Then make it tile anyway: blend it with a copy shifted by half.
- **Size**: the image model used (seedream-5.0-lite) wants at least **3.69 MP**. 3072×1024 was rejected; use 3840×1280 for a 3:1 sky and 2048×2048 for squares.

## TRELLIS: photo → mesh

- **Cut-out first**:
  - Resize to 1024² and cut out with **rembg** (`u2net`). Save the RGBA and look at it: a white object on white can lose parts.
  - If rembg still drops pale parts, add a mask of what differs from the backdrop's colour (its largest blob, holes filled) to rembg's.
  - Giving TRELLIS an RGBA image skips its own rembg call.
- **Loading without the full stack**: TRELLIS can run without its text pipeline (open3d) and its renderers' CUDA extensions. A small loader skipped those and replaced kaolin's `check_tensor` with a no-op, since there were no kaolin wheels for that torch.
- **Format**: request `mesh` only. The mesh decoder's FlexiCubes surface carries **vertex colour** (`vertex_attrs[:, :3]`); there is no texture without the gaussian decoder and nvdiffrast.
- **Axes**: its output is z-up. Make it y-up as TRELLIS's `to_glb` does: `v @ [[1,0,0],[0,0,-1],[0,1,0]]`.
- **Size of the output**: about 1 unit across, 0.3–1.4 M triangles. On an RTX 3090: about 10 GB peak, 45–100 s per object, plus about 1 min to load the model. Run it in the background, one GPU job at a time.
- **Winding**: its surfaces are **not wound one way**. Render them `DoubleSide`: culled, a chair's shell showed through to its cushion and looked like glass. A signed volume tells you nothing here.

## MoGe-2: photo → relief or surface

- **Depth**: run MoGe-2 on the photo (2500–3600 tokens: a few seconds per photo) and keep `points` (H, W, 3, camera space: x right, y down, z forward), `normal` and `mask`. Load the model once for a batch.
- **Relief mesh**:
  - Build a grid over the mask, cut where the depth jumps, and sweep the outline back to a flat back.
  - Write positions, UVs and indices, plus an **object-space** normal map from MoGe's normals. In three.js, use `normalMapType: ObjectSpaceNormalMap`, with a uniform node scale only.
- **Surfaces** (for example a tufted top):
  1. Fit a plane by SVD and grow the region by distance to the plane and by normal angle.
  2. Resample onto the plane's frame.
  3. **Integrate the normals** (Frankot-Chellappa, mirrored so they are periodic). For shallow relief this is much cleaner than MoGe's depth.
  4. Take out the broad shape with a quadratic, then mirror and average with the object's own symmetry.
- **A glow mask for a raised pattern**:
  1. Fit the panel's plane robustly: refit to the nearest 60 % of points, a few times.
  2. Take the height in front of the plane and smoothstep it. Use the result as the emissive map.
  - A colour mask (the pattern's gold) covered only about 0.6 % of the area; the height mask worked.

## Packing (gltf-transform)

- **Per object**:
  - **Weld**, then **simplify** with meshopt (`simplifyPrimitive`, `ratio = target triangles / n`, `error 0.004`).
  - **Size** it by one axis to metres: its base on y 0, centred in x and z.
- **Materials from the vertex colour**:
  - **Tests**: a list of tests per object on a triangle's mean colour, its height and its radius as fractions of the object's height. The first test that matches wins. For example, brass is `r − b > 0.18`, a pot is "below 0.4 of the height", foliage is green.
  - **Measure first**: before writing the tests, print each part's `r − b` and brightness per height band, and its radius per height band (where a pot's rim ends, where a trunk is). Brass is rarely in the colour you guess: a cream fabric is warm too.
  - **Vertex colour**: keep it only where the material wants it (foliage, books).
- **Metal bases**: make the band at the foot taller, raise everything above it, smooth it (Laplacian, a few passes) for a clean reflection, and give it its own material.
- **Pack**:
  - `prune` with `keepAttributes`, and `keepLeaves` if leaf nodes carry textures;
  - `reorder`, `quantize`, `EXTMeshoptCompression` (FILTER);
  - WebP textures (`EXT_texture_webp`).
- **At runtime**: replace each packed material with a hand-tuned one, chosen by a tag in `extras`.

## Gotchas

- **UV orientation**: glTF images are **not flipped** (`flipY` false): v points down the image. To map a photo onto a cylinder, set `repeat.y` negative with an offset. A relief's UVs need `v = 1 − v` when packed.
- **Quantizing**: `quantize` **skips texcoords outside 0..1**, with a warning. Tiling UVs stay float; only UVs already in 0..1 are quantized.
- **Self-built textures**: for a canvas or `DataTexture` you build yourself (glyph maps), set `flipY` deliberately, and keep linear data (normal, anisotropy, masks) in `NoColorSpace`.
- **No UVs on TRELLIS output**: an emissive map has nothing to sit on. Detail without UVs (leather grain) has to be computed in the shader from object-space noise.
- **Distinct parts**: an object with distinct parts (a record and its label, a stand) is better built procedurally than classified out of a TRELLIS blob.

## Checking quickly

- **Point-splat preview** of a `.glb` without the app: load it with trimesh and project the vertex colours orthographically from +z, +x, −z, −x and the top, shaded by the normal's z. Put the views side by side; they show whether the object faces +z and whether parts were lost.
- **Cut-out first**: put the raw photo and its RGBA cut-out side by side before running TRELLIS. A bad cut-out means a bad mesh.
- **In the app**: headless Chrome on the real GPU (`--use-gl=angle --use-angle=gl-egl --ignore-gpu-blocklist`). Set the camera from script, hide HUD and GUI, and take screenshots of fixed views before and after each change.
