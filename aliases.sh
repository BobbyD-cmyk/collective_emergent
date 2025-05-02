# Path-agnostic provenance helpers
function ss() { git -C "$(git rev-parse --show-toplevel)" status -sb; }
function es() {
  repo=$(git rev-parse --show-toplevel)
  echo "$(date '+%Y-%m-%d %H:%M %Z') — $*" >> "$repo/SESSION_LOG.md"
  git -C "$repo" add -A && git -C "$repo" commit -qm "$*"
  git -C "$repo" rev-parse --short HEAD
}
