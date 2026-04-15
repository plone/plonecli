#!/usr/bin/env bash
input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "unknown model"')
output_style=$(echo "$input" | jq -r '.output_style.name // empty')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

# Build status parts
parts=()

# Model
parts+=("$model")

# Context window
if [ -n "$used_pct" ] && [ -n "$remaining_pct" ]; then
  ctx=$(printf "ctx: %.0f%% used / %.0f%% left" "$used_pct" "$remaining_pct")
  parts+=("$ctx")
fi

# Output style / thinking
if [ -n "$output_style" ] && [ "$output_style" != "default" ]; then
  parts+=("style: $output_style")
fi

# Join with separator
result=""
for part in "${parts[@]}"; do
  if [ -z "$result" ]; then
    result="$part"
  else
    result="$result | $part"
  fi
done

echo "$result"
