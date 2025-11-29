/**
 * Cleanup Sandbox Step
 *
 * Kills an E2B sandbox after fork completion.
 * Emits: sandbox-cleaned
 */

import { Sandbox } from '@e2b/sdk';
import { z } from 'zod';
import { STATE_KEYS } from '../state/index.js';

// Input schema
const CleanupSandboxInputSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
});

type CleanupSandboxInput = z.infer<typeof CleanupSandboxInputSchema>;

// Output schema
const SandboxCleanedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
  success: z.boolean(),
});

/**
 * Cleanup Sandbox Step Definition
 */
export const cleanupSandboxStep = {
  name: 'cleanup-sandbox',
  subscribes: ['agent-completed', 'agent-failed', 'sandbox-creation-failed'],
  emits: ['sandbox-cleaned'],

  inputSchema: CleanupSandboxInputSchema,
  outputSchemas: {
    'sandbox-cleaned': SandboxCleanedSchema,
  },

  async handler(
    input: CleanupSandboxInput,
    context: {
      emit: (event: string, data: unknown) => Promise<void>;
      state: {
        get: <T>(key: string) => Promise<T | null>;
        set: <T>(key: string, value: T) => Promise<void>;
        delete: (key: string) => Promise<void>;
      };
      logger: {
        info: (msg: string, data?: Record<string, unknown>) => void;
        warn: (msg: string, data?: Record<string, unknown>) => void;
      };
    }
  ): Promise<void> {
    const { workflowId, forkNum, sandboxId } = input;
    const { emit, state, logger } = context;

    logger.info('Cleaning up sandbox', { workflowId, forkNum, sandboxId });

    let success = true;

    try {
      // Kill the sandbox
      await Sandbox.kill(sandboxId);
      logger.info('Sandbox killed', { sandboxId });
    } catch (error) {
      // Sandbox might already be dead - that's fine
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      logger.warn('Sandbox cleanup warning', {
        sandboxId,
        error: errorMessage,
      });
      success = true; // Still consider it success if already gone
    }

    // Remove sandbox state
    try {
      await state.delete(STATE_KEYS.sandbox(sandboxId));
    } catch {
      // Ignore state deletion errors
    }

    // Emit cleanup event
    await emit('sandbox-cleaned', {
      workflowId,
      forkNum,
      sandboxId,
      success,
    });
  },
};

export default cleanupSandboxStep;
