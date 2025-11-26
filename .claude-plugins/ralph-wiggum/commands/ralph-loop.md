---
description: "Start Ralph Wiggum loop in current session"
allowed-tools: ["Bash", "Read"]
---

# Ralph Loop Command

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/setup-ralph-loop.sh" $ARGUMENTS
```

Read the completion promise from the state file after the script runs:

```bash
if [[ -f .claude/ralph-loop.local.md ]]; then
  COMPLETION_PROMISE=$(sed -n '/^---$/,/^---$/{/^---$/d; p;}' .claude/ralph-loop.local.md | grep '^completion_promise:' | sed 's/completion_promise: *//' | sed 's/^"\(.*\)"$/\1/')
  echo "COMPLETION_PROMISE=$COMPLETION_PROMISE"
fi
```

## CRITICAL INSTRUCTION

If a completion promise was set, you may ONLY output `<promise>THE_PROMISE</promise>` when the statement is **completely and unequivocally TRUE**.

Do NOT output false statements to exit the loop, even if you think you should exit.

Your previous work is visible in the files you've modified and in git history. Use this to iterate and improve.

Now work on the task. The Ralph loop will continue until you either:
1. Reach the max iterations limit
2. Output the completion promise (when it's TRUE)
