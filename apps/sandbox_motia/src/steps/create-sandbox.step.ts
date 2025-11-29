/**
 * Create Sandbox Step
 *
 * Creates an E2B sandbox for a fork execution.
 * Emits: sandbox-created | sandbox-creation-failed
 */

import { Sandbox } from '@e2b/sdk';
import { z } from 'zod';
import { STATE_KEYS, ForkStateSchema } from '../state/index.js';

// Input schema
const CreateSandboxInputSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  template: z.string().default('base'),
  timeoutSeconds: z.number().default(300),
  envs: z.record(z.string()).optional(),
});

type CreateSandboxInput = z.infer<typeof CreateSandboxInputSchema>;

// Output schemas
const SandboxCreatedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
  hostname: z.string().optional(),
});

const SandboxCreationFailedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  error: z.string(),
});

/**
 * Create Sandbox Step Definition
 *
 * This would be registered with Motia as:
 * ```typescript
 * import { step, emit, state } from 'motia';
 *
 * export default step('create-sandbox', createSandboxHandler);
 * ```
 */
export const createSandboxStep = {
  name: 'create-sandbox',
  subscribes: ['fork-started'],
  emits: ['sandbox-created', 'sandbox-creation-failed'],

  inputSchema: CreateSandboxInputSchema,
  outputSchemas: {
    'sandbox-created': SandboxCreatedSchema,
    'sandbox-creation-failed': SandboxCreationFailedSchema,
  },

  async handler(
    input: CreateSandboxInput,
    context: {
      emit: (event: string, data: unknown) => Promise<void>;
      state: {
        get: <T>(key: string) => Promise<T | null>;
        set: <T>(key: string, value: T) => Promise<void>;
      };
      logger: {
        info: (msg: string, data?: Record<string, unknown>) => void;
        error: (msg: string, data?: Record<string, unknown>) => void;
      };
    }
  ): Promise<void> {
    const { workflowId, forkNum, template, timeoutSeconds, envs } = input;
    const { emit, state, logger } = context;

    logger.info('Creating sandbox', { workflowId, forkNum, template });

    // Update fork state to running
    const forkKey = STATE_KEYS.fork(workflowId, forkNum);
    await state.set(forkKey, {
      forkNum,
      status: 'running',
      startedAt: new Date().toISOString(),
    } satisfies Partial<z.infer<typeof ForkStateSchema>>);

    try {
      // Prepare environment variables
      const sandboxEnvs: Record<string, string> = {
        ...envs,
      };

      // Pass through API keys if available
      if (process.env.ANTHROPIC_API_KEY) {
        sandboxEnvs.ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
      }
      if (process.env.GITHUB_TOKEN) {
        sandboxEnvs.GITHUB_TOKEN = process.env.GITHUB_TOKEN;
      }

      // Create sandbox
      const sandbox = await Sandbox.create({
        template,
        timeout: timeoutSeconds,
        envs: sandboxEnvs,
        metadata: {
          motiaWorkflowId: workflowId,
          forkNum: String(forkNum),
        },
      });

      // Get hostname for verification
      const hostname = sandbox.getHost(80);

      // Update fork state with sandbox ID
      await state.set(forkKey, {
        forkNum,
        sandboxId: sandbox.sandboxId,
        status: 'running',
        startedAt: new Date().toISOString(),
      } satisfies Partial<z.infer<typeof ForkStateSchema>>);

      // Store sandbox reference
      await state.set(STATE_KEYS.sandbox(sandbox.sandboxId), {
        sandboxId: sandbox.sandboxId,
        workflowId,
        forkNum,
        createdAt: new Date().toISOString(),
      });

      logger.info('Sandbox created', {
        workflowId,
        forkNum,
        sandboxId: sandbox.sandboxId,
      });

      // Emit success event
      await emit('sandbox-created', {
        workflowId,
        forkNum,
        sandboxId: sandbox.sandboxId,
        hostname,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);

      logger.error('Sandbox creation failed', {
        workflowId,
        forkNum,
        error: errorMessage,
      });

      // Update fork state to failed
      await state.set(forkKey, {
        forkNum,
        status: 'failed',
        error: errorMessage,
        completedAt: new Date().toISOString(),
      } satisfies Partial<z.infer<typeof ForkStateSchema>>);

      // Emit failure event
      await emit('sandbox-creation-failed', {
        workflowId,
        forkNum,
        error: errorMessage,
      });
    }
  },
};

export default createSandboxStep;
