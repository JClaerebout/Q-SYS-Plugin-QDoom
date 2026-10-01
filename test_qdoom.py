"""Local Q-SYS mock and Lua instruction estimate for QDoom."""
import os
import sys
import base64
import xml.etree.ElementTree as ET

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
for _ in range(2):
    press("Fire", True)
    press("Fire", False)
    ticks(10)
assert "KILLS 1/4" in lua.eval("lastSVG")
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
print(f"PASS: controls, firing, collision stress, reset, 500 live ticks, pause, sprite and repeated frames")
print(f"Max callback ~{max(counts):,} Lua VM instructions; P95 ~{sorted(counts)[int(len(counts)*.95)]:,}; SVG {len(lua.eval('lastSVG')):,} bytes")
