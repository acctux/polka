-- Enable spell checking
vim.opt_local.spell = true
vim.opt_local.spelllang = "en_us"

-- Append to 'formatoptions': 'a' = auto-wrap comments, 'w' = auto-wrap text
vim.opt_local.formatoptions:append("aw")

-- Keymap: <leader>x saves the file and closes the buffer
vim.keymap.set("n", "<leader>x", "ZZ", { noremap = true, silent = true, buffer = true })
