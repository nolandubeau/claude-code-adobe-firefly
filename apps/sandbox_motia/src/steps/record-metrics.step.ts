/**
 * Record Metrics Step
 *
 * Records metrics for completed forks.
 * Emits: metrics-recorded
 */

import { z } from 'zod';
import { STATE_KEYS, MetricsStateSchema, type MetricsState } from '../state/index.js';

// Input schema
const RecordMetricsInputSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  status: z.string(),
  costUsd: z.number(),
  inputTokens: z.number(),
  outputTokens: z.number(),
  durationSeconds: z.number(),
});

type RecordMetricsInput = z.infer<typeof RecordMetricsInputSchema>;

// Output schema
const MetricsRecordedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  metricsUpdated: z.boolean(),
});

/**
 * Record Metrics Step Definition
 */
export const recordMetricsStep = {
  name: 'record-metrics',
  subscribes: ['agent-completed', 'agent-failed'],
  emits: ['metrics-recorded'],

  inputSchema: RecordMetricsInputSchema,
  outputSchemas: {
    'metrics-recorded': MetricsRecordedSchema,
  },

  async handler(
    input: RecordMetricsInput,
    context: {
      emit: (event: string, data: unknown) => Promise<void>;
      state: {
        get: <T>(key: string) => Promise<T | null>;
        set: <T>(key: string, value: T) => Promise<void>;
      };
      logger: {
        info: (msg: string, data?: Record<string, unknown>) => void;
      };
    }
  ): Promise<void> {
    const { workflowId, forkNum, status, costUsd, durationSeconds } = input;
    const { emit, state, logger } = context;

    logger.info('Recording metrics', { workflowId, forkNum, status, costUsd });

    // Get existing metrics
    const metricsKey = STATE_KEYS.metrics(workflowId);
    let metrics = await state.get<MetricsState>(metricsKey);

    if (!metrics) {
      metrics = {
        workflowId,
        totalForks: 0,
        completedForks: 0,
        failedForks: 0,
        totalCostUsd: 0,
        avgDurationSeconds: 0,
        lastUpdated: new Date().toISOString(),
      };
    }

    // Update metrics
    metrics.totalForks++;
    if (status === 'success') {
      metrics.completedForks++;
    } else {
      metrics.failedForks++;
    }
    metrics.totalCostUsd += costUsd;

    // Update average duration
    const totalDuration =
      metrics.avgDurationSeconds * (metrics.totalForks - 1) + durationSeconds;
    metrics.avgDurationSeconds = totalDuration / metrics.totalForks;

    metrics.lastUpdated = new Date().toISOString();

    // Save updated metrics
    await state.set(metricsKey, metrics);

    logger.info('Metrics updated', {
      workflowId,
      totalForks: metrics.totalForks,
      completedForks: metrics.completedForks,
      failedForks: metrics.failedForks,
      totalCostUsd: metrics.totalCostUsd,
    });

    await emit('metrics-recorded', {
      workflowId,
      forkNum,
      metricsUpdated: true,
    });
  },
};

export default recordMetricsStep;
