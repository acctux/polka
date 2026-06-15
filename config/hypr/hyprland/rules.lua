-- ######## Window rules ########

-- Disable blur for xwayland context menus
hl.window_rule({ match = { class = "^()$", title = "^()$" }, no_blur = true })

-- Floating
hl.window_rule({ match = { title = "^(Open File)(.*)$" }, center = true })
hl.window_rule({ match = { title = "^(Open File)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^(Select a File)(.*)$" }, center = true })
hl.window_rule({ match = { title = "^(Select a File)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^(Open Folder)(.*)$" }, center = true })
hl.window_rule({ match = { title = "^(Open Folder)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^(Save As)(.*)$" }, center = true })
hl.window_rule({ match = { title = "^(Save As)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^(Library)(.*)$" }, center = true })
hl.window_rule({ match = { title = "^(Library)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^(File Upload)(.*)$" }, center = true })
hl.window_rule({ match = { title = "^(File Upload)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^(.*)(wants to save)$" }, center = true })
hl.window_rule({ match = { title = "^(.*)(wants to save)$" }, float = true })
hl.window_rule({ match = { title = "^(.*)(wants to open)$" }, center = true })
hl.window_rule({ match = { title = "^(.*)(wants to open)$" }, float = true })
hl.window_rule({ match = { class = "^(pavucontrol)$" }, float = true })
hl.window_rule({
	match = { class = "^(pavucontrol)$" },
	size = { "(monitor_w*0.45)", "(monitor_h*0.45)" },
})
hl.window_rule({ match = { class = "^(pavucontrol)$" }, center = true })
hl.window_rule({ match = { class = "^(org.pulseaudio.pavucontrol)$" }, float = true })
hl.window_rule({
	match = { class = "^(org.pulseaudio.pavucontrol)$" },
	size = { "(monitor_w*0.45)", "(monitor_h*0.45)" },
})
hl.window_rule({ match = { class = "^(org.pulseaudio.pavucontrol)$" }, center = true })
hl.window_rule({ match = { class = "org.freedesktop.impl.portal.desktop.kde" }, float = true })
hl.window_rule({
	match = { class = "org.freedesktop.impl.portal.desktop.kde" },
	size = { "(monitor_w*0.60)", "(monitor_h*0.65)" },
})

-- Picture-in-Picture
hl.window_rule({ match = { title = "^([Pp]icture[-\\s]?[Ii]n[-\\s]?[Pp]icture)(.*)$" }, float = true })
hl.window_rule({ match = { title = "^([Pp]icture[-\\s]?[Ii]n[-\\s]?[Pp]icture)(.*)$" }, keep_aspect_ratio = true })
hl.window_rule({
	match = { title = "^([Pp]icture[-\\s]?[Ii]n[-\\s]?[Pp]icture)(.*)$" },
	move = { "(monitor_w*0.73)", "(monitor_h*0.72)" },
})
hl.window_rule({
	match = { title = "^([Pp]icture[-\\s]?[Ii]n[-\\s]?[Pp]icture)(.*)$" },
	size = { "(monitor_w*0.25)", "(monitor_h*0.25)" },
})
-- Picture-in-Picture
hl.window_rule({
	name = "Picture-in-Picture",
	match = {
		title = "^([Pp]icture[-\\s]?[Ii]n[-\\s]?[Pp]icture)(.*)$",
	},
	float = true,
	pin = true,
	focus_on_activate = false,
	no_initial_focus = true,
	suppress_event = "activate",
})
-- Screen sharing
hl.window_rule({ match = { title = ".*is sharing (a window|your screen).*" }, float = true })
hl.window_rule({ match = { title = ".*is sharing (a window|your screen).*" }, pin = true })
hl.window_rule({
	match = { title = ".*is sharing (a window|your screen).*" },
	move = { "(monitor_w*.5-window_w*.5)", "(monitor_h-window_h-12)" },
})
-- -- --- Tearing ---
-- hl.window_rule({ match = { title = ".*\\.exe" }, immediate = true })
-- hl.window_rule({ match = { class = "^(steam_app).*" }, immediate = true })
--
-- No shadow for tiled windows
hl.window_rule({ match = { float = 0 }, no_shadow = true })
-- No animations
hl.layer_rule({ match = { namespace = "gtk4-layer-shell" }, no_anim = true })
-- ######## Layer rules ########
hl.layer_rule({
	match = { namespace = "^(swaync-control-center)$" },
	blur = true,
	-- no_anim = true,
	blur_popups = true,
	ignore_alpha = 0.1,
})
hl.layer_rule({
	match = { namespace = "^(swaync-notification-window)$" },
	blur = true,
	blur_popups = true,
	ignore_alpha = 0.1,
})
hl.layer_rule({
	match = { namespace = "^(waybar)$" },
	blur = true,
	blur_popups = true,
	ignore_alpha = 0.1,
})
hl.layer_rule({
	match = { class = "^(fuzzel)$" },
	blur = true,
	blur_popups = true,
	ignore_alpha = 0.1,
})
hl.layer_rule({
	match = { namespace = "^(selection)$" },
	no_anim = true,
	blur = false,
})
-- ######## Window rules ########
hl.window_rule({
	match = { class = "^(org\\.pulseaudio\\.pavucontrol)$" },
	float = true,
	size = { 700, 600 },
})
hl.window_rule({
	match = { class = "^(satty)$" },
	float = true,
	size = { 700, 600 },
})
hl.window_rule({
	match = { class = "^(imv)$" },
	float = true,
	size = { 1000, 800 },
})
hl.window_rule({
	match = { class = "^(zenity)$" },
	float = true,
	center = true,
})
hl.window_rule({
	match = {
		title = "^(Authentication Required|Unlock Keyring|Login|qt-sudo)$",
	},
	float = true,
	center = true,
})
hl.window_rule({
	match = { title = "^Opening.*" },
	float = true,
	center = true,
})
hl.window_rule({
	match = { class = "^(xdg-desktop-portal-gtk)$" },
	float = true,
	center = true,
})
-- hl.window_rule({
-- 	match = { class = "^(org\\.gnome\\.Nautilus)$" },
-- 	float = true,
-- 	center = true,
-- })
hl.window_rule({
	match = { class = "^(org\\.gnome\\.baobab)$" },
	float = true,
	center = true,
	size = { 1000, 800 },
})

-- ######## Opacity overrides ########
hl.window_rule({
	match = { class = "^(steam_app_default)$" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { class = "^(com\\.ayugram\\.desktop)$" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { class = "^(eden)$" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { class = "^(Ryujinx)$" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { class = "^(mpv)$" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { class = "^(rpcs3)$" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { title = ".*YouTube.*" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { title = ".*Concept Videos.*" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { title = ".*FlickyStream.*" },
	opacity = "1.0 override",
})
hl.window_rule({
	match = { class = "^(virt-manager)$" },
	opacity = "1.0 override",
})
