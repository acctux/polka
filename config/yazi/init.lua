-- ---------------------------------------------------------------------------
-- RECYCLE BIN
-- ---------------------------------------------------------------------------
require("recycle-bin"):setup({
	trash_dir = "~/.local/share/Trash/files", -- Uncomment to use specific directory
})

-- ---------------------------------------------------------------------------
-- MOUNTING
-- ---------------------------------------------------------------------------
require("gvfs"):setup({
	-- (Optional) Allowed keys to select device.
	which_keys = "1234567890qwertyuiopasdfghjklzxcvbnm-=[]\\;',./!@#$%^&*()_+{}|:\"<>?",
	-- (Optional) Save file.
	-- Default: ~/.config/yazi/gvfs.private
	save_path = os.getenv("HOME") .. "/.config/yazi/gvfs.private",
	-- (Optional) Save file for automount devices. Use with `automount-when-cd` action.
	-- Default: ~/.config/yazi/gvfs_automounts.private
	save_path_automounts = os.getenv("HOME") .. "/.config/yazi/gvfs_automounts.private",
	input_position = { "center", y = 0, w = 60 },
	-- (Optional) Select where to save passwords.
	-- Default: nil
	-- Available options: "keyring", "pass", or nil
	password_vault = "keyring",
	-- (Optional) Auto-save password after mount.
	-- Default: false
	save_password_autoconfirm = true,
})

-- ---------------------------------------------------------------------------
-- SHOW USER/GROUP OF FILES IN STATUS BAR
-- ---------------------------------------------------------------------------
Status:children_add(function()
	local h = cx.active.current.hovered
	if not h or ya.target_family() ~= "unix" then
		return ""
	end
	return ui.Line({
		ui.Span(ya.user_name(h.cha.uid) or tostring(h.cha.uid)):fg("magenta"),
		":",
		ui.Span(ya.group_name(h.cha.gid) or tostring(h.cha.gid)):fg("magenta"),
		" ",
	})
end, 500, Status.RIGHT)

-- ---------------------------------------------------------------------------
-- SHOW USERNAME AND HOSTNAME IN HEADER
-- ---------------------------------------------------------------------------
Header:children_add(function()
	if ya.target_family() ~= "unix" then
		return ""
	end
	return ui.Span(ya.user_name() .. "@" .. ya.host_name() .. ":"):fg("blue")
end, 500, Header.LEFT)

-- -- ---------------------------------------------------------------------------
-- -- SHOW SIZE AND DATE NEXT TO FILES AND DIRECTORIES
-- -- ---------------------------------------------------------------------------
function Linemode:size_and_mtime()
	local time = math.floor(self._file.cha.mtime or 0)
	if time == 0 then
		time = ""
	elseif os.date("%Y", time) == os.date("%Y") then
		time = os.date("%b %d %H:%M", time)
	else
		time = os.date("%b %d  %Y", time)
	end
	local size = self._file:size()
	return string.format("%s %s", size and ya.readable_size(size) or "-", time)
end

-- ---------------------------------------------------------------------------
-- BORDER
-- ---------------------------------------------------------------------------
require("full-border"):setup({
	-- Available values: ui.Border.PLAIN, ui.Border.ROUNDED
	type = ui.Border.ROUNDED,
})
