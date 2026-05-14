terminal = "uwsm app -- kitty"
fileManager = "kitty --hold yazi"
browser = "firedragon"
textEditor = "kitty --hold nvim"
officeSoftware = "libreoffice"
volumeMixer = "pavucontrol"
taskManager = "kitty btop"
--##################################################
-- MODIFIERS (already implicit in Lua, but kept for reference)
--##################################################
local mainMod = "SUPER"
local shiftMod = "SUPER + SHIFT"
hl.config({
	input = {
		kb_layout = "us,ru,ua",
		numlock_by_default = true,
		follow_mouse = 1,
		sensitivity = 0.3,
		touchpad = {
			natural_scroll = false,
		},
	},
})
hl.device({
	name = "logitech-mx-master-3s",
	sensitivity = -0.8,
	scroll_factor = 0.9,
})
--##################################################
-- KEYBOARD LANGUAGE SWITCH
--##################################################
hl.bind(
	"ALT + SPACE",
	hl.dsp.exec_cmd("hyprctl switchxkblayout at-translated-set-2-keyboard next && pkill -RTMIN+6 waybar"),
	{ description = "Language switch" }
)

--##################################################
-- APP LAUNCH BINDINGS
--##################################################
-- hl.bind(mainMod .. " + M", hl.dsp.exec_cmd("uwsm stop"))
hl.bind(mainMod .. " + SPACE", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(browser))
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(textEditor))
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd("fuzzel"))
hl.bind(shiftMod .. " + R", hl.dsp.exec_cmd("pkill -SIGUSR1 waybar"))
hl.bind(shiftMod .. " + E", hl.dsp.exec_cmd("nautilus"))
hl.bind(shiftMod .. " + T", hl.dsp.exec_cmd("~/.local/bin/keyboard/osk_handle.sh"))

--##################################################
-- WINDOW FOCUS AND SWITCHING
--##################################################
-- hl.bind("ALT + Tab", hl.dsp.focus({ cycle = true }))
-- hl.bind("ALT + SHIFT + Tab", hl.dsp.focus({ cycle = true, reverse = true }))

hl.bind(mainMod .. " + G", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + D", hl.dsp.layout("togglesplit"))
hl.bind(shiftMod .. " + D", hl.dsp.window.pseudo())
hl.bind(
	mainMod .. " + F",
	hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }),
	{ description = "Fullscreen" }
)
hl.bind(mainMod .. " + Escape", hl.dsp.window.close(), { description = "Close" })
hl.bind(shiftMod .. " + Escape", hl.dsp.exec_cmd("hyprctl kill"), { description = "Forcefully zap a window" })

--##################################################
-- FUNCTION KEYS (OSD style bindings)
--##################################################
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("swayosd-client --playerctl next"))
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("swayosd-client --playerctl previous"))
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("swayosd-client --input-volume mute-toggle"))
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("swayosd-client --output-volume mute-toggle"))
hl.bind(
	"XF86AudioRaiseVolume",
	hl.dsp.exec_cmd("swayosd-client --output-volume +5 --max-volume 100"),
	{ repeating = true }
)
hl.bind(
	"XF86AudioLowerVolume",
	hl.dsp.exec_cmd("swayosd-client --output-volume -5 --max-volume 100"),
	{ repeating = true }
)
hl.bind(
	"XF86MonBrightnessUp",
	hl.dsp.exec_cmd("swayosd-client --brightness raise --device amdgpu_bl1"),
	{ repeating = true }
)
hl.bind(
	"XF86MonBrightnessDown",
	hl.dsp.exec_cmd("swayosd-client --brightness lower --device amdgpu_bl1"),
	{ repeating = true }
)
hl.bind("Caps_Lock", hl.dsp.exec_cmd("swayosd-client --caps-lock"))
hl.bind("Num_Lock", hl.dsp.exec_cmd("swayosd-client --num-lock"))
hl.bind("Scroll_Lock", hl.dsp.exec_cmd("swayosd-client --scroll-lock"))

--##################################################
-- SCREENSHOTS
--##################################################
--"grim -o \"$(hyprctl activeworkspace -j | jq -r '.monitor')\""
hl.bind(mainMod .. " + PRINT", hl.dsp.exec_cmd("hyprshot -m window"))
hl.bind(shiftMod .. " + PRINT", hl.dsp.exec_cmd("hyprshot -m region"))
hl.bind(mainMod .. " + Z", hl.dsp.exec_cmd("~/.local/bin/ocr/maim.sh"))

--##################################################
-- WORKSPACES
--##################################################
for i = 1, 4 do
	hl.bind(mainMod .. " + " .. i, hl.dsp.focus({ workspace = i }))
	hl.bind(shiftMod .. " + " .. i, hl.dsp.window.move({ workspace = i, follow = false }))
end
hl.bind(mainMod .. " + Tab", hl.dsp.focus({ workspace = "r+1" }))
hl.bind(mainMod .. " + SHIFT + Tab", hl.dsp.focus({ workspace = "r-1" }))

--#/# bind = SUPER + ←/↑/→/↓,, -- Focus in direction
for i = 1, 4 do
	local arrowkey = { "Left", "Right", "Up", "Down", "BracketLeft", "BracketRight" }
	local focusdir = { "l", "r", "u", "d", "l", "r" }
	hl.bind("SUPER + " .. arrowkey[i], hl.dsp.focus({ direction = focusdir[i] }))
end

--#/# bind = SUPER + SHIFT, ←/↑/→/↓,, -- Move in direction
for i = 1, 4 do
	local arrowkey = { "Left", "Right", "Up", "Down" }
	local focusdir = { "l", "r", "u", "d" }
	hl.bind("SUPER + SHIFT + " .. arrowkey[i], hl.dsp.window.move({ direction = focusdir[i] }))
end

--# Window split ratio
--#/# binde = SUPER, ;/',, -- Adjust split ratio
hl.bind("SUPER + Semicolon", hl.dsp.layout("splitratio -0.1"), { repeating = true })
hl.bind("SUPER + Apostrophe", hl.dsp.layout("splitratio +0.1"), { repeating = true })

----##! Workspace
----# We use raw keycodes because some keyboard layouts register number keys as different chars. The codes can be verified with `wev`
--for i = 1, 10 do
--	local numberkey = { 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 }
--	hl.bind("SUPER + code:" .. numberkey[i], hl.dsp.focus({ workspace = i }))
--end
----# keypad numbers
--for i = 1, 10 do
--	local numpadkey = { 87, 88, 89, 83, 84, 85, 79, 80, 81, 90 }
--	hl.bind("SUPER + code:" .. numpadkey[i], hl.dsp.focus({ workspace = i }))
--end
--##################################################
-- MOUSE
--##################################################
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.resize(), { mouse = true, description = "Move" })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.drag(), { mouse = true, description = "Resize" })
hl.bind(mainMod .. " + mouse:274", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "+1" }), { mouse = true, bypass = true })
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "-1" }), { mouse = true, bypass = true })
hl.bind(shiftMod .. " + mouse_up", hl.dsp.window.move({ workspace = "r+1", follow = true }))
hl.bind(shiftMod .. " + mouse_down", hl.dsp.window.move({ workspace = "r-1", follow = true }))
hl.bind(mainMod .. " + mouse_right", hl.dsp.focus({ workspace = "+1" }))
hl.bind(mainMod .. " + mouse_left", hl.dsp.focus({ workspace = "-1" }))
hl.bind(shiftMod .. " + mouse_right", hl.dsp.window.move({ workspace = "r+1", follow = true }))
hl.bind(shiftMod .. " + mouse_left", hl.dsp.window.move({ workspace = "r-1", follow = true }))
hl.bind("ALT + mouse:272", hl.dsp.window.drag(), { mouse = true }) -- ALT + LMB: Move a window by dragging more than 10px.
hl.bind("ALT + mouse:272", hl.dsp.window.resize(), { mouse = true }) -- ALT + LMB: Floats a window by clicking
