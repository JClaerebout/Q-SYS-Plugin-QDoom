local time=0
Timer={Now=function()return time end,New=function()return {Start=function(self)self.running=true end,Stop=function(self)self.running=false end} end}
local svg
Crypto={Base64Encode=function(s) svg=s;return s end}
package.preload.rapidjson=function()return {encode=function(t)return t.IconData end}end
-- Design metadata is evaluated without runtime Controls.
dofile('QDoom.qplug')
local definitions=GetControls();local layout=GetControlLayout();Controls={}
for _,c in ipairs(definitions)do assert(layout[c.Name],c.Name);Controls[c.Name]={Boolean=false,String=''}end
local function press(n,v)Controls[n].Boolean=v;Controls[n].EventHandler(Controls[n])end
local function tick(n)for i=1,n do time=time+.2;QDoomTimer.EventHandler()end end
dofile('QDoom.qplug')
assert(svg:find('<svg'));assert(not QDoomTimer.running)
press('Run',true)
press('Fire',true);press('Fire',false);tick(3);press('Fire',true);press('Fire',false)
assert(svg:find('KILLS 1/4'),'visible enemy must die after two shots')
for i=1,100 do press('Forward',true);press('Forward',false);tick(1) end
assert(not Controls.Info.String:find('Stopped:'))
press('Reset',true);press('Reset',false)
assert(svg:find('HEALTH 100'));assert(svg:find('KILLS 0/4'))
press('StepMode',false);press('Forward',true);press('Fire',true);tick(500);press('Forward',false);press('Fire',false)
assert(not Controls.Info.String:find('Stopped:'))
press('Run',false);assert(not QDoomTimer.running)
press('Reset',true);press('Reset',false)
local f=assert(io.open('preview.svg','w'));f:write(svg);f:close()
print('PASS: design layout, startup, firing/kill, collision stress, reset, 500 live ticks, pause, SVG export')
