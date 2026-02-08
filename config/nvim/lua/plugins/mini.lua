return {
  "nvim-mini/mini.nvim",
  version = "*",
  config = function()
    -- Better Around/Inside textobjects
    -- Examples:
    --  - va)  - [V]isually select [A]round [)]paren
    --  - yinq - [Y]ank [I]nside [N]ext [Q]uote
    --  - ci'  - [C]hange [I]nside [']quote
    require("mini.ai").setup({ n_lines = 500 })
    -- Add/delete/replace surroundings (brackets, quotes, etc.)
    -- - saiw) - [S]urround [A]dd [I]nner [W]ord [)]Paren
    -- - sd'   - [S]urround [D]elete [']quotes
    -- - sr)'  - [S]urround [R]eplace [)] [']
    require("mini.surround").setup()
    require("mini.sessions").setup()
    require("mini.pairs").setup()
    require("mini.hipatterns").setup()
    require("mini.move").setup({
      mappings = {
        --  Visual mode.  Alt (Meta) + hjkl.
        left = "<M-h>",
        right = "<M-l>",
        down = "<M-j>",
        up = "<M-k>",
        -- Move current line in Normal mode
        line_left = "<M-h>",
        line_right = "<M-l>",
        line_down = "<M-j>",
        line_up = "<M-k>",
      },
      options = {
        reindent_linewise = true,
      },
    })
  end,
}
