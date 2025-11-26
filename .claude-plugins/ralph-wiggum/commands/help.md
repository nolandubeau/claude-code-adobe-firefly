---
description: "Show Ralph Wiggum plugin help"
---

# Ralph Wiggum Plugin Help

The Ralph Wiggum plugin implements an iterative development methodology using continuous AI loops.

## Core Concept

"Ralph is a Bash loop" - a `while true` that feeds Claude the same prompt repeatedly. Each iteration, Claude sees:
- Its previous work in modified files
- Git history of changes
- The same prompt again

This creates a self-referential feedback loop for iterative improvement.

## Commands

### `/ralph-loop <PROMPT> [OPTIONS]`

Starts a Ralph loop in the current session.

**Options:**
- `--max-iterations <n>` - Stop after N iterations (safety limit)
- `--completion-promise '<text>'` - Phrase that signals completion

**Examples:**
```
/ralph-loop Build a REST API --max-iterations 500 --completion-promise 'ALL TESTS PASS'
/ralph-loop Fix the auth bug --max-iterations 20
/ralph-loop Refactor the cache layer --completion-promise 'REFACTORING COMPLETE'
```

### `/cancel-ralph`

Cancels the active Ralph loop.

## Completion Promises

To signal completion, output: `<promise>YOUR_PHRASE</promise>`

**CRITICAL:** Only output this when the statement is TRUE. Do not lie to exit.

## Best Use Cases

- Well-defined tasks with clear success criteria
- Projects requiring iterative refinement
- Tasks with automatic verification (tests, linters)

## Not Recommended For

- Tasks requiring human judgment
- One-shot operations
- Unclear success criteria

## Monitoring

```bash
# View current iteration
grep '^iteration:' .claude/ralph-loop.local.md

# View full state
head -10 .claude/ralph-loop.local.md
```
