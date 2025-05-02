# Provenance helpers — load with:  source aliases.sh
function ss() { git status -sb && git rev-parse --abbrev-ref HEAD; }
function es() {
    repo=$(git rev-parse --show-toplevel)
    echo "$(date '+%Y-%m-%d %H:%M %Z')  –  $*" >> "$repo/SESSION_LOG.md"
    (cd "$repo" && git add -A && git commit -qm "$*")
    git -C "$repo" rev-parse HEAD
}
