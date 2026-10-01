# QDoom project notes — 2026-10-01

## 0.3.0: Freedoom artwork upgrade

- User requested the closest Doom-style result permitted by available rights. Verified [Freedoom 0.13.0](https://freedoom.github.io/download.html) includes `COPYING.txt` granting redistribution and modification with its copyright, terms, disclaimer, and non-endorsement condition. Downloaded the official release to `/private/tmp` for conversion. The ZIP and standalone qplug carry the required notice; ZIP also carries original `CREDITS.txt`.
- `tools/build_freedoom_assets.py` reads `freedoom1.wad`, composites wall patches, downsamples four wall textures to 32 × 32 indexed samples, and embeds three monster and two shotgun frames as PNG data. Selected wall lumps: `STARTAN2`, `STARG1`, `TEKWALL1`, `REDWALL1`; sprites: `TROOA1`, `TROOB1`, `TROOE1`; weapon: `SHTGA0`, `SHTGB0`. The WAD is not distributed. No original Doom or QWolf3D material is included.
- Runtime wall rendering remains in four groups of 16 rays. Each ray draws 6, 10, or 14 sampled texture bands. Monster PNG images are SVG `<image>` elements behind depth-derived `<clipPath>` masks. Shotgun frame changes while firing. QWolf3D uses PNG-in-SVG for title art; this is an independent integration using Freedoom art.
- Local Lua harness passed initial render, firing, collision stress, reset, 500 live ticks, pause, PNG sprite clipping, and repeated frame cycles. Approximate max 14,900 Lua VM instructions per callback; P95 13,600; preview SVG 65,265 bytes. Base64 and Legend transfer are native operations and remain unmeasured. PNG and clip-path support need confirmation in Q-SYS Designer/Core.

The sections below record the earlier 0.2.0 implementation and inspection for historical context.

## Starting point and preservation

The repository already contained `QDoom.qplug` 0.1.1, `README.md`, `test.lua`, `preview.svg`, and an MIT `LICENSE`, with uncommitted changes. QDoom 0.2.0 uses the original gameplay and DDA idea as the starting point. No commit, push, or publication was made. The older `test.lua` is retained as a historical harness; `test_qdoom.py` exercises the current staged renderer.

## Uploaded QWolf3D inspection

- `IB-QSYS-QWOLF3D-1.0.0.qplug` is a roughly 1.3 MB UTF-8 text plugin with embedded source modules and asset tables. It sets a Q-SYS button Legend to JSON containing `DrawChrome:false` and Base64 `IconData` for generated SVG.
- Wall data contains 34 used 64-column textures. Each column stores palette indices as hexadecimal strings; decoded columns are cached. The loader processes 16 wall columns per call, then one sprite per call. Sprite data uses 73 column/post tables with direct RGB hex colors, half vertical resolution, and transparent omitted pixels. Weapon frame tables store precomputed RGB pixel arrays from VSWAP. Rendering scales strips to projected screen size, clamps walls to visible vertical ranges, and depth-tests sprites by column.
- DDA raycasting is divided into two phases (left/right groups), retaining wall fragments and depth data between calls. Sprites and weapon render when the wall phase completes; a complete SVG is retained for display. The code has adaptive texture/sprite levels of detail, a preallocated 16-entry visible-sprite info pool, and horizontal run-length merging of matching wall rectangles. Final SVG concatenation and Base64 encoding are still done in a completion callback, so batching does not bound every part of the work.
- A master timer calls gameplay each tick, with HUD every sixth tick and debug information every thirtieth. Control EventHandlers set movement/action state. The game includes doors and enemy behavior.
- Audio is optional in code but uses a 7-channel BinLoop mapping and files under `Audio/WOLF3D/` on Core media storage. The upload includes a separate WOLF3D audio folder and a Q-SYS demo design; no audio is needed for QDoom.
- No LICENSE or NOTICE file was present in the uploaded directory and no clear reuse grant was found in the plugin header. Code permission is therefore unconfirmed. Embedded Wolfenstein 3D VSWAP images and audio are a separate rights question. QDoom copies none of that code or art and keeps the uploaded files untouched.

## CCDoom / Pine3D

The Xella37 repositories are ComputerCraft projects. CCDoom uses Pine3D and ComputerCraft terminal/image/event APIs, while QDoom must emit SVG through a Q-SYS Legend. Their renderer would require a large output adaptation with no clear execution-budget benefit for this small game. No port was added. See the repository pages: [CCDoom](https://github.com/Xella37/CCDoom) and [Pine3D](https://github.com/Xella37/Pine3D).

## Implementation and test record

- 64 DDA rays at 320 × 180; procedural brick bands and three palette families. Four timer calls cast 16 rays each. Subsequent callbacks draw sprites/HUD, concatenate XML, Base64 encode, and assign the Legend. Timer interval is 0.05 seconds, yielding about 2.2 complete frames/s if busy.
- Original compact pixel strips represent monsters. A fixed four-enemy map bounds sprite work; sprite strips are depth-tested and run-merged vertically. Weapon flash/recoil are timed states. Input controls remain wired Q-SYS pins.
- Initial local run failed the pause assertion because 500 live ticks could end in death; the harness now resets before asserting pause. No plugin runtime error was observed.
- `python3 test_qdoom.py` passed control loading, firing/kills, movement/collision stress, reset, 500 live ticks, pause, a close sprite, and repeated render cycles. Max callback sampled around 7,800 Lua VM instructions; P95 around 5,200. Final preview SVG was 20,586 bytes. The local test substitutes Base64 with a capture function, so native encoding and Legend transfer are unmeasured.
- Designer/Core was unavailable. Required next test: install in Designer, run the same actions over a sustained session, verify one-button SVG rendering and UCI/external pin behavior, and inspect Debug Output for execution-limit errors.
