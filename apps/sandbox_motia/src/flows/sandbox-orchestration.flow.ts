/**
 * Sandbox Orchestration Flow
 *
 * This flow orchestrates the complete lifecycle of sandbox fork execution:
 *
 * Event Flow:
 * ```
 * orchestration-requested
 *         │
 *         ▼
 *    [orchestrate]
 *         │
 *         ▼
 *    fork-started (N events)
 *         │
 *         ▼
 *   [create-sandbox]
 *         │
 *         ├──────────────────┐
 *         ▼                  ▼
 *  sandbox-created    sandbox-creation-failed
 *         │                  │
 *         ▼                  │
 *   [health-check]           │
 *         │                  │
 *         ├──────────┐       │
 *         ▼          ▼       │
 *  health-passed  health-failed
 *         │          │       │
 *         ▼          │       │
 *    [run-agent]     │       │
 *         │          │       │
 *         ├──────────┤       │
 *         ▼          ▼       ▼
 *  agent-completed agent-failed
 *         │          │
 *         ├──────────┤
 *         ▼          ▼
 *   [record-metrics]
 *         │
 *         ▼
 *  [cleanup-sandbox]
 *         │
 *         ▼
 *   sandbox-cleaned
 *         │
 *         ▼
 *  [check-completion]
 *         │
 *         ▼
 *  orchestration-completed
 * ```
 */

import createSandboxStep from '../steps/create-sandbox.step.js';
import runAgentStep from '../steps/run-agent.step.js';
import cleanupSandboxStep from '../steps/cleanup-sandbox.step.js';
import healthCheckStep from '../steps/health-check.step.js';
import { orchestrateStep, checkCompletionStep } from '../steps/orchestrate.step.js';
import recordMetricsStep from '../steps/record-metrics.step.js';

/**
 * Flow definition for Motia
 *
 * In a real Motia app, this would be exported as the default flow
 * and automatically discovered by the Motia runtime.
 */
export const sandboxOrchestrationFlow = {
  name: 'sandbox-orchestration',
  description: 'Orchestrate parallel sandbox fork execution with durability',

  // All steps in this flow
  steps: [
    orchestrateStep,
    createSandboxStep,
    healthCheckStep,
    runAgentStep,
    recordMetricsStep,
    cleanupSandboxStep,
    checkCompletionStep,
  ],

  // Entry points - events that can start this flow
  entryPoints: ['orchestration-requested'],

  // Terminal events - events that indicate flow completion
  terminalEvents: ['orchestration-completed'],

  // Flow configuration
  config: {
    // Retry configuration for all steps
    retry: {
      maxAttempts: 3,
      initialDelayMs: 1000,
      backoffMultiplier: 2,
      maxDelayMs: 30000,
    },

    // Timeout configuration
    timeout: {
      stepTimeoutMs: 7200000, // 2 hours default
    },

    // Rate limiting for concurrent step executions
    rateLimit: {
      maxConcurrent: 5,
      windowMs: 1000,
    },
  },
};

/**
 * Alternative: Programmatic flow definition
 *
 * For more complex flows, you can define them programmatically:
 */
export function createSandboxOrchestrationFlow(options: {
  maxConcurrent?: number;
  retryAttempts?: number;
}) {
  return {
    ...sandboxOrchestrationFlow,
    config: {
      ...sandboxOrchestrationFlow.config,
      rateLimit: {
        ...sandboxOrchestrationFlow.config.rateLimit,
        maxConcurrent: options.maxConcurrent ?? 5,
      },
      retry: {
        ...sandboxOrchestrationFlow.config.retry,
        maxAttempts: options.retryAttempts ?? 3,
      },
    },
  };
}

export default sandboxOrchestrationFlow;
