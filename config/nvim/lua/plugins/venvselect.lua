return {
  "linux-cultist/venv-selector.nvim",
  ft = { "python" }, -- lazy-load only for Python files
  keys = {
    { "<leader>cv", "<cmd>VenvSelect<cr>", desc = "Select Python virtual environment" },
  },
  dependencies = {
    { "nvim-mini/mini.nvim" }, -- mini-pick comes from mini.nvim
    { "nvim-lua/plenary.nvim" }, -- required utility library
  },
  opts = {
    options = {
      picker = "mini-pick", -- USE MINI-PICK as picker backend
      selected_venv_marker_icon = "✔",
      selected_venv_marker_color = "#0000FF",
      picker_columns = { "marker", "search_icon", "search_name", "search_result" },
      statusline_func = {
        lualine = function()
          local venv_path = require("venv-selector").venv()
          if not venv_path or venv_path == "" then
            return ""
          end
          local venv_name = vim.fn.fnamemodify(venv_path, ":t")
          return "🐍 " .. venv_name .. " "
        end,
      },
    },
  },
}
