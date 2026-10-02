"""Local Q-SYS mock and Lua instruction estimate for QDoom."""
import os
import sys
import base64
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".test-deps"))
sys.path.insert(0, "/private/tmp/qdoom-test-deps")
from lupa import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
path = os.path.abspath("QDoom.qplug").replace("\\", "\\\\").replace("'", "\\'")
lua.execute("""
clock=0
Timer={Now=function() return clock end,New=function()
  return {Start=function(self) self.running=true end,Stop=function(self) self.running=false end}
end}
Crypto={Base64Encode=function(s) lastSVG=s;return s end}
""")
lua.execute(f"dofile('{path}')")
lua.execute("""
Controls={}
for _,d in ipairs(GetControls()) do Controls[d.Name]={Boolean=false,String='',Legend=''} end
""")
lua.execute(f"dofile('{path}')")
assert lua.eval("QDoomTimer.running")
lua.execute("""
function press(n,v) local c=Controls[n];c.Boolean=v;c.EventHandler(c) end
function callback(dt)
  clock=clock+dt
  local count=0
  debug.sethook(function() count=count+100 end,'',100)
  QDoomTimer.EventHandler()
  debug.sethook()
  return count
end
""")
callback = lua.eval("callback")
press = lua.eval("press")
counts = []


def ticks(n, dt=0.05):
    for _ in range(n):
        counts.append(callback(dt))
        assert not lua.eval("Controls.Info.String:find('Stopped:')")


ticks(10)
assert "PRESS RUN TO PLAY" in lua.eval("lastSVG")
press("Run", True)
ticks(10)
assert "PRESS RUN TO PLAY" not in lua.eval("lastSVG")
assert 'data-weapon="handgun"' in lua.eval("lastSVG")
for _ in range(2):
    press("Fire", True)
    press("Fire", False)
    # Capture each assembled frame: effects must survive the staged renderer.
    shot_frames = []
    for tick in range(55):
        ticks(1)
        shot_frames.append(lua.eval("lastSVG"))
    assert any('data-effect="muzzle-flash"' in frame for frame in shot_frames)
    for name in ('PISGB0', 'PISGC0', 'PISGD0', 'PISGE0', 'PISGA0'):
        assert any(f'data-frame="{name}"' in frame for frame in shot_frames), name
    assert any('data-effect="blood-hit"' in frame for frame in shot_frames)
assert "KILLS 1/4" in lua.eval("lastSVG")
assert 'data-effect="corpse"' in lua.eval("lastSVG")
assert 'data-effect="blood-pool"' in lua.eval("lastSVG")
ticks(40)
assert 'data-effect="corpse"' in lua.eval("lastSVG")
assert 'data-effect="muzzle-flash"' not in lua.eval("lastSVG")
for _ in range(100):
    press("Forward", True)
    press("Forward", False)
    ticks(1)
assert lua.eval("p==nil")  # Game state remains private.
press("Reset", True)
press("Reset", False)
ticks(10)
assert "HEALTH 100" in lua.eval("lastSVG")
assert "KILLS 0/4" in lua.eval("lastSVG")
assert 'data-effect="corpse"' not in lua.eval("lastSVG")
assert 'data-effect="blood-pool"' not in lua.eval("lastSVG")
press("StepMode", False)
press("Forward", True)
press("Fire", True)
ticks(500)
press("Forward", False)
press("Fire", False)
press("Reset", True)
press("Reset", False)
press("Run", False)
ticks(10)
assert "PAUSED - PRESS RUN" in lua.eval("lastSVG")
press("Reset", True)
press("Reset", False)
press("StepMode", True)
press("Run", True)
for _ in range(6):
    press("Forward", True)
    press("Forward", False)
ticks(10)
assert 'data:image/png;base64,' in lua.eval("lastSVG")
assert 'clipPath id="monster' in lua.eval("lastSVG")
root = ET.fromstring(lua.eval("lastSVG"))
images = root.findall(".//{http://www.w3.org/2000/svg}image")
assert len(images) >= 2
for image in images:
    payload = image.attrib["href"].split(",", 1)[1]
    assert base64.b64decode(payload).startswith(b"\x89PNG\r\n\x1a\n")
with open("preview.svg", "w") as f:
    f.write(lua.eval("lastSVG"))
# Exercise both families through the same visible enemy slot. Access private
# state only through the harness, without adding runtime debug controls.
lua.execute("""
function upvalue(fn, wanted)
  for i=1,100 do
    local name,value=debug.getupvalue(fn,i)
    if not name then break end
    if name==wanted then return value end
  end
  error('Missing upvalue '..wanted)
end
testEnemies=upvalue(upvalue(Controls.Reset.EventHandler,'reset'),'enemies')
""")
for kind, family, pain, corpse in ((1, 'TROO', 'TROOH1', 'TROOM0'),
                                   (2, 'SARG', 'SARGH1', 'SARGN0')):
    press("Reset", True)
    press("Reset", False)
    lua.execute(f"testEnemies=upvalue(upvalue(Controls.Reset.EventHandler,'reset'),'enemies'); testEnemies[1].kind={kind}")
    ticks(20)
    assert f'data-monster="{family}"' in lua.eval("lastSVG")
    for expected in (pain, corpse):
        press("Fire", True)
        press("Fire", False)
        frames = []
        for _ in range(35):
            ticks(1)
            frames.append(lua.eval("lastSVG"))
        assert any(f'data-pose="{expected}"' in frame for frame in frames), expected
    assert "KILLS 1/4" in lua.eval("lastSVG")
# Complete each level through real shots, positioning the player beside each
# monster with harness-only access to private state.
press("Reset", True)
press("Reset", False)
for level, total in ((1, 4), (2, 6)):
    lua.execute("""
    testReset=upvalue(Controls.Reset.EventHandler,'reset')
    testEnemies=upvalue(testReset,'enemies')
    testPlayer=upvalue(testReset,'p')
    testMap=upvalue(testReset,'map')
    """)
    assert len(lua.globals().testEnemies) == total
    # All spawns must be open and reachable from the player spawn.
    rows = list(lua.globals().testMap.values())
    start = (int(lua.globals().testPlayer.x), int(lua.globals().testPlayer.y))
    reachable, pending = {start}, [start]
    while pending:
        x, y = pending.pop()
        for nx, ny in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
            if 0 <= ny < len(rows) and 0 <= nx < len(rows[ny]) and rows[ny][nx] == '0' and (nx, ny) not in reachable:
                reachable.add((nx, ny))
                pending.append((nx, ny))
    for enemy in lua.globals().testEnemies.values():
        assert (int(enemy.x), int(enemy.y)) in reachable
    for index in range(1, total+1):
        lua.execute(f"local e=testEnemies[{index}]; testPlayer.x=e.x-.25; testPlayer.y=e.y; testPlayer.a=0")
        for _ in range(2):
            press("Fire", True)
            press("Fire", False)
            ticks(40)
    assert f"LEVEL {level}" in lua.eval("lastSVG")
    assert f"KILLS {total}/{total}" in lua.eval("lastSVG")
    assert ("CLEAR - FIRE FOR LV2" if level == 1 else "YOU WIN - RESET") in lua.eval("lastSVG")
    press("Fire", True)
    press("Fire", False)
    ticks(20)
    if level == 1:
        assert "LEVEL 2" in lua.eval("lastSVG")
        assert "HEALTH 100" in lua.eval("lastSVG")
        assert "KILLS 0/6" in lua.eval("lastSVG")
        assert 'data-effect="corpse"' not in lua.eval("lastSVG")
    else:
        assert "YOU WIN - RESET" in lua.eval("lastSVG")
press("Reset", True)
press("Reset", False)
ticks(20)
assert "LEVEL 1" in lua.eval("lastSVG")
assert "KILLS 0/4" in lua.eval("lastSVG")
print(f"PASS: controls, firing, collision stress, reset, 500 live ticks, pause, sprite, repeated frames and two-level progression")
print(f"Max callback ~{max(counts):,} Lua VM instructions; P95 ~{sorted(counts)[int(len(counts)*.95)]:,}; SVG {len(lua.eval('lastSVG')):,} bytes")
