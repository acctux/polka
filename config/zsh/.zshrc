source /usr/share/zsh/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
eval "$(mcfly init zsh)"
eval "$(starship init zsh)"
eval "$(zoxide init --cmd cd zsh)"
# eval "$(direnv hook zsh)"
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
HISTSIZE=10000
SAVEHIST=10000
HISTORY_IGNORE="(ls|ls *|exit|)"
setopt hist_ignore_all_dups
setopt hist_ignore_space
setopt inc_append_history
alias ls='eza -a --icons=always'
alias ll='eza -al --icons=always'
alias lt='eza -a --tree --level=1 --icons=always'
alias shutdown='systemctl poweroff'
alias grep='grep --color=auto'
alias mkdir='mkdir -pv'
alias cx='chmod +x'
alias lg='lazygit'
alias loggy='sudo systemctl restart logid'
alias dotsync='/home/nick/.local/bin/dotsync/dotsync.py'
pvim() {
  cd ~/Lit/Noah || return
  source .venv/bin/activate
  nvim
}
# Created by `pipx` on 2026-01-26 17:20:46
export PATH="$PATH:/home/nick/Polka/local/bin"
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	command yazi "$@" --cwd-file="$tmp"
	IFS= read -r -d '' cwd < "$tmp"
	[ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && builtin cd -- "$cwd"
	rm -f -- "$tmp"
}
