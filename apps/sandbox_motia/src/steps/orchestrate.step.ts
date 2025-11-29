/**
 * Orchestrate Step
 *
 * Main orchestration step that starts fork executions.
 * Handles rate limiting and parallel execution.
 * Emits: fork-started | orchestration-completed
 */

import { z } from 'zod';
import {
  STATE_KEYS,
  OrchestrationStateSchema,
  type OrchestrationState,
} from '../state/index.js';

// Input schema - start orchestration
const StartOrchestrationInputSchema = z.object({
  workflowId: z.string(),
  repoUrl: z.string(),
  branch: z.string(),
  prompt: z.string(),
  numForks: z.number().default(1),
  model: z.string().default('sonnet'),
  maxConcurrent: z.number().default(5),
  timeoutSeconds: z.number().default(7200),
  budgetLimitUsd: z.number().optional(),
});

type StartOrchestrationInput = z.infer<typeof StartOrchestrationInputSchema>;

// Output schemas
const ForkStartedSchema = z.object({
  workflowId: z.string(),
  forkNum: z.number(),
  template: z.string(),
  timeoutSeconds: z.number(),
});

const OrchestrationCompletedSchema = z.object({
  workflowId: z.string(),
  totalForks: z.number(),
  successfulForks: z.number(),
  failedForks: z.number(),
  totalCostUsd: z.number(),
  durationSeconds: z.number(),
});

/**
 * Start Orchestration Step
 */
export const orchestrateStep = {
  name: 'orchestrate',
  subscribes: ['orchestration-requested'],
  emits: ['fork-started', 'orchestration-completed'],

  inputSchema: StartOrchestrationInputSchema,
  outputSchemas: {
    'fork-started': ForkStartedSchema,
    'orchestration-completed': OrchestrationCompletedSchema,
  },

  async handler(
    input: StartOrchestrationInput,
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
    const {
      workflowId,
      repoUrl,
      branch,
      prompt,
      numForks,
      model,
      maxConcurrent,
      timeoutSeconds,
      budgetLimitUsd,
    } = input;
    const { emit, state, logger } = context;

    logger.info('Starting orchestration', {
      workflowId,
      numForks,
      maxConcurrent,
    });

    // Initialize orchestration state
    const orchestrationState: OrchestrationState = {
      workflowId,
      repoUrl,
      branch,
      prompt,
      numForks,
      model,
      maxConcurrent,
      timeoutSeconds,
      budgetLimitUsd,
      forks: [],
      totalCostUsd: 0,
      completedCount: 0,
      failedCount: 0,
      paused: false,
      cancelled: false,
      startedAt: new Date().toISOString(),
    };

    await state.set(
      STATE_KEYS.orchestration(workflowId),
      orchestrationState
    );

    // Start forks with rate limiting
    // In Motia, we emit events for each fork to start
    // The event system handles rate limiting automatically
    for (let i = 1; i <= numForks; i++) {
      const forkBranch = numForks > 1 ? `${branch}-${i}` : branch;

      // Initialize fork state
      orchestrationState.forks.push({
        forkNum: i,
        status: 'pending',
        costUsd: 0,
        inputTokens: 0,
        outputTokens: 0,
        durationSeconds: 0,
      });

      // Emit fork-started event
      await emit('fork-started', {
        workflowId,
        forkNum: i,
        template: 'base',
        timeoutSeconds,
      });

      logger.info('Fork started', { workflowId, forkNum: i, branch: forkBranch });
    }

    // Update state with all forks initialized
    await state.set(
      STATE_KEYS.orchestration(workflowId),
      orchestrationState
    );
  },
};

/**
 * Check Completion Step
 *
 * Checks if all forks have completed and emits orchestration-completed.
 */
export const checkCompletionStep = {
  name: 'check-completion',
  subscribes: ['sandbox-cleaned'],
  emits: ['orchestration-completed'],

  async handler(
    input: { workflowId: string; forkNum: number },
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
    const { workflowId } = input;
    const { emit, state, logger } = context;

    // Get orchestration state
    const orchState = await state.get<OrchestrationState>(
      STATE_KEYS.orchestration(workflowId)
    );

    if (!orchState) {
      logger.info('Orchestration state not found', { workflowId });
      return;
    }

    // Count completed forks
    let completedCount = 0;
    let failedCount = 0;
    let totalCostUsd = 0;

    for (let i = 1; i <= orchState.numForks; i++) {
      const forkState = await state.get<{
        status: string;
        costUsd?: number;
      }>(STATE_KEYS.fork(workflowId, i));

      if (forkState) {
        if (forkState.status === 'success') {
          completedCount++;
        } else if (
          forkState.status === 'failed' ||
          forkState.status === 'timeout'
        ) {
          failedCount++;
        }
        totalCostUsd += forkState.costUsd || 0;
      }
    }

    // Update orchestration state
    orchState.completedCount = completedCount;
    orchState.failedCount = failedCount;
    orchState.totalCostUsd = totalCostUsd;

    await state.set(STATE_KEYS.orchestration(workflowId), orchState);

    // Check if all forks are done
    const totalDone = completedCount + failedCount;
    if (totalDone >= orchState.numForks) {
      const startTime = new Date(orchState.startedAt).getTime();
      const durationSeconds = (Date.now() - startTime) / 1000;

      orchState.completedAt = new Date().toISOString();
      await state.set(STATE_KEYS.orchestration(workflowId), orchState);

      logger.info('Orchestration completed', {
        workflowId,
        totalForks: orchState.numForks,
        successfulForks: completedCount,
        failedForks: failedCount,
        totalCostUsd,
        durationSeconds,
      });

      await emit('orchestration-completed', {
        workflowId,
        totalForks: orchState.numForks,
        successfulForks: completedCount,
        failedForks: failedCount,
        totalCostUsd,
        durationSeconds,
      });
    }
  },
};

export default orchestrateStep;
