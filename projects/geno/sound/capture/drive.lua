-- Generic driver: reads schedule from env-ish config file work/sched.txt
-- lines: "S e buttons"  hold buttons (comma list) for frames [S,e)
--        "shot N"       screenshot every N frames
--        "stop F"       stop at frame F
--        "load path"    load savestate at start
--        "save F path"  save state at frame F
--        "dumpspc F path" dump ARAM+DSP+regs at frame F
local W = "@SMRPG_WORK@/"   -- capture.sh writes a copy with the work folder filled in
local cfgpath = W .. "sched.txt"
local holds, saves, dumps = {}, {}, {}
local shotEvery, stopAt, loadPath, tag = 0, 600, nil, "run"
for line in io.lines(cfgpath) do
  local a, b, c = line:match("^(%S+)%s*(%S*)%s*(%S*)")
  if a == "shot" then shotEvery = tonumber(b)
  elseif a == "stop" then stopAt = tonumber(b)
  elseif a == "tag" then tag = b
  elseif a == "load" then loadPath = b
  elseif a == "save" then saves[tonumber(b)] = c
  elseif a == "dumpspc" then dumps[tonumber(b)] = c
  elseif a and tonumber(a) then table.insert(holds, {tonumber(a), tonumber(b), c})
  end
end
local f = 0
local loaded = (loadPath == nil)
local function writeFile(p, s) local h = io.open(p, "wb"); h:write(s); h:close() end
local function dumpSpc(p)
  local t = {}
  for i = 0, 65535 do t[#t+1] = string.char(emu.read(i, emu.memType.spcRam)) end
  local d = {}
  for i = 0, 127 do d[#d+1] = string.char(emu.read(i, emu.memType.spcDspRegisters)) end
  writeFile(p .. ".aram", table.concat(t))
  writeFile(p .. ".dsp", table.concat(d))
  local st = emu.getState()
  local h = io.open(p .. ".state.txt", "w")
  local keys = {}
  for k, v in pairs(st) do if tostring(k):match("^spc") or tostring(k):match("^dsp") then keys[#keys+1] = k end end
  table.sort(keys)
  for _, k in ipairs(keys) do h:write(k .. "=" .. tostring(st[k]) .. "\n") end
  h:close()
end
emu.addEventCallback(function()
  local want = {}
  for _, hd in ipairs(holds) do
    if f >= hd[1] and f < hd[2] then
      for btn in hd[3]:gmatch("[^,]+") do want[btn] = true end
    end
  end
  emu.setInput(want, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  if not loaded then
    local h = io.open(loadPath, "rb"); local s = h:read("a"); h:close()
    emu.loadSavestate(s); loaded = true; return
  end
  f = f + 1
  if shotEvery > 0 and f % shotEvery == 0 then
    writeFile(string.format("%sshots/%s_%06d.png", W, tag, f), emu.takeScreenshot())
  end
  if saves[f] then writeFile(saves[f], emu.createSavestate()) end
  if dumps[f] then dumpSpc(dumps[f]) end
  if f >= stopAt then emu.stop(0) end
end, emu.eventType.endFrame)
