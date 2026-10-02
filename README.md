# QDoom 0.3.0

QDoom is a small, playable Doom-style corridor shooter for Q-SYS. The installable [QDoom.qplug](QDoom.qplug) embeds its map, eight wall textures, two animated monster types, a compact handgun, and SVG renderer. No separate assets, audio files, or network service are needed at runtime.

## Install and play

1. Double-click `QDoom.qplug`. QSysPluginHelper will prompt you to install the plugin.
2. Add **Fun → QDoom** to a design and start emulation. Open the component and press **Run**.
3. Keep **StepMode** on for touchscreen use: tap movement or turn controls, aim, and press **Fire** twice per monster. Turn StepMode off to hold controls for live movement and enemy AI. **Reset** restores health and enemies.

Copy `Screen`, `Info`, and the input pins to a UCI. Keep `Screen` at 16:9. The same controls are exposed for external wiring. `Run` and `StepMode` are toggles; the other buttons are momentary. The mini-map marks the player green and monsters red. If replacing an older component, remove and re-add it; existing components can retain embedded plugin code.

The game has two levels. Clear the four monsters in level one, then press **Fire** again to enter a new map with six monsters and full health. Clear level two to win. The HUD shows the current level; **Reset** restarts the game at level one.

## Rendering and assets

The original grid DDA raycaster casts 64 rays into a 320 × 180 SVG. An offline converter samples eight Freedoom wall textures into compact 32 × 32 indexed maps. Lua selects wall texture columns and draws 6–14 colored bands per column, depending on distance. Freedoom monster PNG frames are embedded inside the SVG and clipped against the wall depth buffer. The handgun uses embedded Freedoom pistol frames with recoil and a muzzle flash. Hits add red blood; dead monsters remain as Freedoom corpse sprites with blood pools until Reset. Shot flashes and hit bursts are retained until a frame renders them. A single `Screen` button receives SVG as Base64 `IconData` in its Legend.

A 20 Hz timer handles input and gameplay, then assembles each requested image over nine callbacks: setup, four groups of 16 wall columns, sprites/HUD, SVG concatenation, Base64 encoding, and Legend assignment. A complete image appears at most about every 0.45 seconds. Changes made during assembly trigger another image. The game remains a raycaster rather than a port of the original Doom engine, CCDoom, Pine3D, or QWolf3D.

All runtime artwork is embedded in the `.qplug`. The source images came from **Freedoom 0.13.0**: wall textures `STARTAN2`, `STARG1`, `TEKWALL1`, `REDWALL1`, `COMPTALL`, `STONE2`, `BROWNPIP`, `METAL1`; monster families `TROO` and `SARG`, each with four walking poses, a pain pose, and a corpse; and pistol frames `PISGA0` through `PISGE0` plus `PISFA0`. Both monster types take two shots; each appears twice on the map. The conversion script is [tools/build_freedoom_assets.py](tools/build_freedoom_assets.py). To rebuild its asset block, supply the official Freedoom 0.13.0 `freedoom1.wad` and Pillow. The WAD is not needed to install or play QDoom.

## Local validation and remaining Q-SYS checks

`python test_qdoom.py` uses `lupa` (installed normally or into `.test-deps`). It checks plugin loading, controls, firing, collision stress, reset, 500 live ticks, pause, sprite clipping, and repeated rendering. With both monster types and eight textures, the measured maximum was about 14,900 Lua VM instructions in one timer callback; the preview SVG was about 68 KB. The harness also verifies both families render their pain and corpse poses. Native Base64 encoding and Legend transfer are not represented by the VM count. These measurements do not establish compliance with the Q-SYS execution budget.

Designer/Core was unavailable here. Validate the `.qplug` in Designer emulation and on the target Core: SVG display, PNG and clipping support, step/live controls, UCI and external pin behavior, pause/reset, and long play without `Max execution limits exceeded`. Record the Designer version and Debug Output if a problem occurs.

## Attribution and rights

QDoom's Lua gameplay and rendering code is original and covered by [LICENSE](LICENSE) (MIT). Embedded art is derived from the [Freedoom project](https://freedoom.github.io/about.html) and retains its separate [BSD-style license](FREEDOOM-COPYING.txt) and [credits](FREEDOOM-CREDITS.txt). The full Freedoom license notice is also embedded in `QDoom.qplug` so the standalone plugin carries it. No original Doom or QWolf3D assets or source are included. See [PROJECT_NOTES.md](PROJECT_NOTES.md) for the inspection, decisions, and tests.
