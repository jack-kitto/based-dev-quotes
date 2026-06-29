#!/usr/bin/env bash
# Terminal MOTD — add this to your .bashrc / .zshrc
#
# One-liner version (paste into your shell config):
#   curl -sf https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1/today.json | jq -r '"  \"\(.text)\"\n    — \(.author)  [\(.categories | join(\", \"))]"' 2>/dev/null
#
# Or source this file:
#   source /path/to/motd.sh

_based_dev_quote() {
  local data
  data=$(curl -sf --connect-timeout 2 --max-time 5 \
    "https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1/today.json" 2>/dev/null)

  if [ -n "$data" ] && command -v jq &>/dev/null; then
    echo ""
    echo "$data" | jq -r '"  💬 \"\(.text)\"\n\n    — \(.author)  [\(.categories | join(\", \"))]"'
    echo ""
  fi
}

# Only run in interactive shells
if [[ $- == *i* ]]; then
  _based_dev_quote
fi
