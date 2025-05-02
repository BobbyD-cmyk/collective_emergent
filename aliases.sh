repo="$HOME/Documents/collective_emergent"        # fixed repo root

function ss() { git -C "$repo" status -sb; }

function es() {
  echo "$(date '+%Y-%m-%d %H:%M %Z') — $*" >> "$repo/SESSION_LOG.md"
  git -C "$repo" add -A && git -C "$repo" commit -qm "$*"
  git -C "$repo" rev-parse --short HEAD
}
