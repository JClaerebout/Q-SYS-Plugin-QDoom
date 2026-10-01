local time=0
Timer={Now=function()return time end,New=function()return {Start=function(self)self.running=true end,Stop=function(self)self.running=false end} end}
local svg
Crypto={Base64Encode=function(s) svg=s;return s end}
package.preload.rapidjson=function()return {encode=function(t)return t.IconData end}end
-- Design metadata is evaluated without runtime Controls.
dofile('QDoom.qplug')
local definitions=GetControls();local layout=GetControlLayout();Controls={}
for _,c in ipairs(definitions)do assert(layout[c.Name],c.Name);Controls[c.Name]={Boolean=false,String=''}end
local function center(name)
 local c=layout[name]
 return c.Position[1]+c.Size[1]/2,c.Position[2]+c.Size[2]/2
end
local forwardX,forwardY=center('Forward')
local backX,backY=center('Backward')
local leftX=center('StrafeLeft')
local rightX=center('StrafeRight')
assert(forwardX==backX and forwardY<backY and leftX<backX and backX<rightX,'movement pad layout')
local turnLeftX=center('TurnLeft')
local turnRightX=center('TurnRight')
local fireX=center('Fire')
assert(rightX<turnLeftX and turnLeftX<turnRightX and turnRightX<fireX,'play controls layout')
assert(layout.Fire.Size[1]>layout.Forward.Size[1] and layout.Run.Position[2]>layout.Fire.Position[2]+layout.Fire.Size[2],'fire and settings layout')
local function press(n,v)Controls[n].Boolean=v;Controls[n].EventHandler(Controls[n])end
local function tick(n)for i=1,n do time=time+.2;QDoomTimer.EventHandler()end end
dofile('QDoom.qplug')
assert(svg:find('<svg'));assert(not QDoomTimer.running)
assert(svg:find('PRESS RUN TO PLAY'),'startup prompt')
press('Run',true)
assert(not svg:find('PRESS RUN TO PLAY'),'startup prompt clears when running')
press('Fire',true);press('Fire',false);tick(3);press('Fire',true);press('Fire',false)
assert(svg:find('KILLS 1/4'),'visible enemy must die after two shots')
for i=1,100 do press('Forward',true);press('Forward',false);tick(1) end
assert(not Controls.Info.String:find('Stopped:'))
press('Reset',true);press('Reset',false)
assert(svg:find('HEALTH 100'));assert(svg:find('KILLS 0/4'))
press('StepMode',false);press('Forward',true);press('Fire',true);tick(500);press('Forward',false);press('Fire',false)
assert(not Controls.Info.String:find('Stopped:'))
press('Run',false);assert(not QDoomTimer.running)
assert(svg:find('PAUSED %- PRESS RUN'),'pause prompt')
press('Reset',true);press('Reset',false)
-- Frame the nearest monster close enough for its silhouette and face to show.
press('StepMode',true);press('Run',true)
for i=1,6 do press('Forward',true);press('Forward',false) end
assert(svg:find('#d05b38'),'preview should show monster horns')
local f=assert(io.open('preview.svg','w'));f:write(svg);f:close()
print('PASS: design layout, startup, firing/kill, collision stress, reset, 500 live ticks, pause, SVG export')
