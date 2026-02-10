-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
vim.lsp.enable("ty")
vim.lsp.enable("ruff")
vim.lsp.enable("yamlls")
vim.lsp.enable("rust_analyzer")
vim.lsp.enable("tailwindcss")
vim.lsp.enable("jsonls")
vim.lsp.enable("lua_ls")
vim.lsp.enable("bashls")
vim.lsp.enable("tombi")
local toggle_inlay_hints = function()
  if vim.lsp.inlay_hint.is_enabled() then
    vim.lsp.inlay_hint.enable(false)
  else
    vim.lsp.inlay_hint.enable(true)
  end
end
vim.keymap.set("n", "<leader>ci", toggle_inlay_hints, { noremap = true, silent = true, desc = "Toggle inlay hints" })
