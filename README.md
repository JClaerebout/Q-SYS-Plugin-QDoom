# QDoom

QDoom 0.1.1 is a small Doom-style SVG shooter for Q-SYS Designer. It draws a 320 × 180 scene, enemies, crosshair, and mini-map directly in SVG. The plugin includes one map and needs no game assets, downloads, or external services.

## Install

1. Double-click [QDoom.qplug](QDoom.qplug) on a Windows machine with Q-SYS Designer, or copy it to `Documents\QSC\Q-Sys Designer\Plugins`.
2. Restart Designer if needed. Find **Fun → QDoom** in the plugin inventory and add it to a design.
3. Start emulation with **F6**, open the component, and press **Run**.

When updating an existing installation, remove the old component and add a fresh QDoom component. Existing components can retain embedded plugin code from the previous version.

## Play

QDoom starts in **StepMode**. Tap the movement or turn buttons to move in fixed steps. Enemies wait in this mode, which makes play practical when UI updates are slow. Aim with the crosshair and press **Fire** twice to defeat an enemy; walls block shots.

Turn off **StepMode** for live play. Hold movement buttons to move while enemies approach and damage you. **Run** pauses or resumes the timer; **Reset** starts a new game. On the mini-map, green marks the player and red marks enemies.

| Control | Action |
| --- | --- |
| `Forward`, `Backward` | Move along the viewing direction |
| `StrafeLeft`, `StrafeRight` | Move sideways |
| `TurnLeft`, `TurnRight` | Rotate the view |
| `Fire` | Shoot at an enemy under the crosshair |
| `Reset` | Restore health and enemies |
| `Run` | Start or pause updates |
| `StepMode` | Switch between tap-to-move and live play |

## Use in a UCI

Copy `Screen`, `Info`, and the input controls to your UCI. Keep `Screen` at a **16:9** aspect ratio. Use momentary buttons for movement and firing, and toggle buttons for `Run` and `StepMode`. There is no keyboard capture or sound.

## Implementation and testing

QDoom is an original raycaster. It is not a port of Doom, CCDoom, or Pine3D, and includes no assets or source from those projects. The plugin renders 80 wall columns and original SVG enemies, then sends the SVG to `Screen.Legend` as Base64 encoded `IconData`. It uses Q-SYS `Timer.Now()`, `Timer.New()`, `rapidjson`, and `Crypto.Base64Encode`; EzSVG itself is not required. `Info` reports Lua frame generation time and SVG size, not measured UCI frame rate. The live timer runs at 5 Hz.

The included [test.lua](test.lua) is a mocked Q-SYS harness covering control layout, initial render, firing, movement and collision, reset, live ticks, and pause. It can be run with a compatible Lua interpreter from this directory. A prior local run used `texlua`; actual Designer, Core, and TSC behavior still needs validation.

Version 0.1.1 replaced tiny-step wall sampling with bounded grid DDA traversal. A local mocked callback benchmark measured about 195,900 → 23,800 instructions at its maximum across the same gameplay test, excluding native encoding cost. Actual Q-SYS execution budget still requires Designer validation.

If Designer reports an error, capture the Debug Output and Designer version. If `Screen` is blank while `Info` increments, capture the `Screen` display and its UCI style settings.

Q-SYS references: [SVG display API](https://help.qsys.com/q-sys_9.7/Content/Control_Scripting/Using_Lua_in_Q-Sys/EzSVG.htm) · [Basic Plugin Framework](https://help.qsys.com/DeveloperHelp/Content/Code_Examples/Basic_Plugin_Framework.htm)

## License

MIT. See [LICENSE](LICENSE).
