---
description: "Cancel active Ralph Wiggum loop"
allowed-tools: ["Bash"]
hide-from-slash-command-tool: "true"
---

# Cancel Ralph

```bash
if [[ -f .claude/ralph-loop.local.md ]]; then
  ITERATION=$(grep '^iteration:' .claude/ralph-loop.local.md | sed 's/iteration: *//')
  echo "FOUND_LOOP=true"
  echo "ITERATION=$ITERATION"
else
  echo "FOUND_LOOP=false"
fi
```

If FOUND_LOOP=false: Report "No active Ralph loop found."

If FOUND_LOOP=true:
1. Run: `rm .claude/ralph-loop.local.md`
2. Report: "Cancelled Ralph loop (was at iteration N)" where N is the ITERATION value.
