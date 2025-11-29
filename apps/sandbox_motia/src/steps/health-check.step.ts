/**
 * Health Check Step
 *
 * Verifies sandbox is healthy before agent execution.
 * Emits: health-check-passed | health-check-failed
 */

import { Sandbox } from '@e2b/sdk';
import { z } from 'zod';

// Input schema
const HealthCheckInputSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
});

type HealthCheckInput = z.infer<typeof HealthCheckInputSchema>;

// Output schemas
const HealthCheckPassedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
  isRunning: z.boolean(),
  responseTimeMs: z.number(),
});

const HealthCheckFailedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  sandboxId: z.string(),
  error: z.string(),
});

/**
 * Health Check Step Definition
 */
export const healthCheckStep = {
  name: 'health-check',
  subscribes: ['sandbox-created'],
  emits: ['health-check-passed', 'health-check-failed'],

  inputSchema: HealthCheckInputSchema,
  outputSchemas: {
    'health-check-passed': HealthCheckPassedSchema,
    'health-check-failed': HealthCheckFailedSchema,
  },

  async handler(
    input: HealthCheckInput,
    context: {
      emit: (event: string, data: unknown) => Promise<void>;
      logger: {
        info: (msg: string, data?: Record<string, unknown>) => void;
        error: (msg: string, data?: Record<string, unknown>) => void;
      };
    }
  ): Promise<void> {
    const { workflowId, forkNum, sandboxId } = input;
    const { emit, logger } = context;

    logger.info('Running health check', { workflowId, forkNum, sandboxId });

    const startTime = Date.now();

    try {
      // Connect to sandbox
      const sandbox = await Sandbox.connect(sandboxId);

      // Check if running
      const isRunning = await sandbox.isRunning();

      if (!isRunning) {
        await emit('health-check-failed', {
          workflowId,
          forkNum,
          sandboxId,
          error: 'Sandbox is not running',
        });
        return;
      }

      // Try a simple command to verify responsiveness
      const result = await sandbox.commands.run('echo health_check', {
        timeout: 10,
      });

      const responseTimeMs = Date.now() - startTime;

      if (result.exitCode !== 0) {
        await emit('health-check-failed', {
          workflowId,
          forkNum,
          sandboxId,
          error: `Health check command failed: ${result.stderr}`,
        });
        return;
      }

      logger.info('Health check passed', {
        workflowId,
        forkNum,
        sandboxId,
        responseTimeMs,
      });

      await emit('health-check-passed', {
        workflowId,
        forkNum,
        sandboxId,
        isRunning,
        responseTimeMs,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);

      logger.error('Health check failed', {
        workflowId,
        forkNum,
        sandboxId,
        error: errorMessage,
      });

      await emit('health-check-failed', {
        workflowId,
        forkNum,
        sandboxId,
        error: errorMessage,
      });
    }
  },
};

export default healthCheckStep;
