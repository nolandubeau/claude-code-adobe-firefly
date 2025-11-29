/**
 * Run Agent Step
 *
 * Executes Claude Code agent in a sandbox.
 * Emits: agent-completed | agent-failed
 */

import { Sandbox } from '@e2b/sdk';
import { z } from 'zod';
import { STATE_KEYS, ForkStateSchema, type ForkStatus } from '../state/index.js';

// Input schema
const RunAgentInputSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
  repoUrl: z.string(),
  branch: z.string(),
  prompt: z.string(),
  model: z.string().default('sonnet'),
  maxTurns: z.number().default(100),
});

type RunAgentInput = z.infer<typeof RunAgentInputSchema>;

// Output schemas
const AgentCompletedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
  costUsd: z.number(),
  inputTokens: z.number(),
  outputTokens: z.number(),
  output: z.string().optional(),
});

const AgentFailedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
  error: z.string(),
});

// System prompt template
const SYSTEM_PROMPT_TEMPLATE = `You are an AI assistant executing tasks in an isolated E2B sandbox environment.

## Context
- Repository: {{repoUrl}}
- Branch: {{branch}}
- Fork Number: {{forkNum}}

## Instructions
1. Clone the repository and checkout the specified branch
2. Complete the user's task
3. Commit your changes with descriptive messages
4. Push to the remote branch

## Guidelines
- Always verify your changes work before committing
- Use meaningful commit messages
- Handle errors gracefully
`;

/**
 * Run Agent Step Definition
 */
export const runAgentStep = {
  name: 'run-agent',
  subscribes: ['sandbox-created'],
  emits: ['agent-completed', 'agent-failed'],

  inputSchema: RunAgentInputSchema,
  outputSchemas: {
    'agent-completed': AgentCompletedSchema,
    'agent-failed': AgentFailedSchema,
  },

  async handler(
    input: RunAgentInput,
    context: {
      emit: (event: string, data: unknown) => Promise<void>;
      state: {
        get: <T>(key: string) => Promise<T | null>;
        set: <T>(key: string, value: T) => Promise<void>;
      };
      logger: {
        info: (msg: string, data?: Record<string, unknown>) => void;
        error: (msg: string, data?: Record<string, unknown>) => void;
        debug: (msg: string, data?: Record<string, unknown>) => void;
      };
    }
  ): Promise<void> {
    const {
      workflowId,
      forkNum,
      sandboxId,
      repoUrl,
      branch,
      prompt,
      model,
      maxTurns,
    } = input;
    const { emit, state, logger } = context;

    logger.info('Running agent', { workflowId, forkNum, sandboxId, model });

    const forkKey = STATE_KEYS.fork(workflowId, forkNum);
    const startTime = Date.now();

    try {
      // Connect to sandbox
      const sandbox = await Sandbox.connect(sandboxId);

      // Clone repository
      logger.debug('Cloning repository', { repoUrl, branch });

      const cloneCmd = `git clone ${repoUrl} /workspace && cd /workspace && git checkout -b ${branch} origin/${branch} 2>/dev/null || git checkout ${branch}`;

      const cloneResult = await sandbox.commands.run(cloneCmd, {
        timeout: 300, // 5 minutes for clone
      });

      if (cloneResult.exitCode !== 0) {
        logger.debug('Clone warning', { stderr: cloneResult.stderr });
      }

      // Prepare Claude command
      const escapedPrompt = prompt.replace(/'/g, "'\"'\"'");

      const claudeCmd = `cd /workspace && echo '${escapedPrompt}' | claude -p \\
        --model ${model} \\
        --max-turns ${maxTurns} \\
        --dangerously-skip-permissions \\
        --output-format json 2>&1`;

      logger.info('Executing Claude agent', { model, maxTurns });

      // Execute Claude CLI
      const result = await sandbox.commands.run(claudeCmd, {
        cwd: '/workspace',
        timeout: maxTurns * 60, // ~1 minute per turn max
      });

      const durationSeconds = (Date.now() - startTime) / 1000;

      // Parse result for cost info
      let costUsd = 0;
      let inputTokens = 0;
      let outputTokens = 0;

      // Try to extract JSON with cost info
      const jsonMatch = result.stdout?.match(/\{[^{}]*"cost"[^{}]*\}/);
      if (jsonMatch) {
        try {
          const costData = JSON.parse(jsonMatch[0]);
          costUsd = costData.cost || 0;
          inputTokens = costData.input_tokens || 0;
          outputTokens = costData.output_tokens || 0;
        } catch {
          // Ignore parse errors
        }
      }

      const success = result.exitCode === 0;
      const status: ForkStatus = success ? 'success' : 'failed';

      // Update fork state
      await state.set(forkKey, {
        forkNum,
        sandboxId,
        status,
        costUsd,
        inputTokens,
        outputTokens,
        durationSeconds,
        error: success ? undefined : result.stderr,
        completedAt: new Date().toISOString(),
      } satisfies Partial<z.infer<typeof ForkStateSchema>>);

      logger.info('Agent execution completed', {
        workflowId,
        forkNum,
        status,
        costUsd,
        durationSeconds,
      });

      if (success) {
        await emit('agent-completed', {
          workflowId,
          forkNum,
          sandboxId,
          costUsd,
          inputTokens,
          outputTokens,
          output: result.stdout?.slice(0, 10000),
        });
      } else {
        await emit('agent-failed', {
          workflowId,
          forkNum,
          sandboxId,
          error: result.stderr || 'Agent execution failed',
        });
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      const durationSeconds = (Date.now() - startTime) / 1000;

      logger.error('Agent execution failed', {
        workflowId,
        forkNum,
        error: errorMessage,
      });

      // Update fork state
      await state.set(forkKey, {
        forkNum,
        sandboxId,
        status: 'failed',
        durationSeconds,
        error: errorMessage,
        completedAt: new Date().toISOString(),
      } satisfies Partial<z.infer<typeof ForkStateSchema>>);

      await emit('agent-failed', {
        workflowId,
        forkNum,
        sandboxId,
        error: errorMessage,
      });
    }
  },
};

export default runAgentStep;
