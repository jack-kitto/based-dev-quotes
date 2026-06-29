#!/usr/bin/env bash
# based-dev-quotes — terminal quote of the day
#
# INSTALL (add to your .bashrc / .zshrc):
#   source <(curl -s https://raw.githubusercontent.com/jack-kitto/based-dev-quotes/main/cli/quote.sh)
#
# OR run ad-hoc:
#   bash <(curl -s https://raw.githubusercontent.com/jack-kitto/based-dev-quotes/main/cli/quote.sh)
#
# Requires: curl + jq (or python3 fallback)

QUOTE_URL="https://cdn.jsdelivr.net/gh/jack-kitto/based-dev-quotes@main/api/v1/today.json"

# Try jq first, fall back to python3
if command -v jq &>/dev/null; then
  DATA=$(curl -sf --connect-timeout 2 --max-time 5 "$QUOTE_URL" 2>/dev/null)
  if [ -z "$DATA" ]; then exit 0; fi
  TEXT=$(echo "$DATA" | jq -r '.text')
  AUTHOR=$(echo "$DATA" | jq -r '.author')
  CATEGORIES=$(echo "$DATA" | jq -r '.categories | join(", ")')
elif command -v python3 &>/dev/null; then
  DATA=$(curl -sf --connect-timeout 2 --max-time 5 "$QUOTE_URL" 2>/dev/null)
  if [ -z "$DATA" ]; then exit 0; fi
  TEXT=$(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['text'])")
  AUTHOR=$(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['author'])")
  CATEGORIES=$(echo "$DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(', '.join(d['categories']))")
else
  echo "⚠️  based-dev-quotes needs jq or python3"
  exit 1
fi

if [ -z "$TEXT" ] || [ "$TEXT" = "null" ]; then
  exit 0
fi

# Box drawing
COLS=$(tput cols 2>/dev/null || echo 80)
MAX_WIDTH=$((COLS < 76 ? COLS - 4 : 72))

echo ""
echo "  ┌$(printf '─%.0s' $(seq 1 $((MAX_WIDTH + 2))))┐"

# Word-wrap the quote text
echo "$TEXT" | fold -s -w "$MAX_WIDTH" | while IFS= read -r line; do
  printf "  │ %-${MAX_WIDTH}s │\n" "$line"
done

# Empty line
printf "  │ %-${MAX_WIDTH}s │\n" ""

# Author line
ATTR="— $AUTHOR"
printf "  │ %${MAX_WIDTH}s │\n" "$ATTR"

# Category line
printf "  │ %${MAX_WIDTH}s │\n" "[$CATEGORIES]"

echo "  └$(printf '─%.0s' $(seq 1 $((MAX_WIDTH + 2))))┘"
echo ""
