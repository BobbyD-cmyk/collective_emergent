# provenance helpers
function ss() { repo=$(git rev-parse --show-toplevel); git -C "$repo" status -sb; }
function es() {
    repo=$(git rev-parse --show-toplevel)
    echo "$(date '+%Y-%m-%d %H:%M %Z') – $*" >> "$repo/SESSION_LOG.md"
    git -C "$repo" add -A
    git -C "$repo" commit -qm "$*"
    git -C "$repo" rev-parse HEAD
}
