/**
 * State management for sandbox orchestration.
 *
 * Motia provides a unified key-value state store that persists
 * across step executions and survives failures.
 */

import { z } from 'zod';

// Schema definitions for state
export const ForkStatusSchema = z.enum([
  'pending',
  'running',
  'success',
  'failed',
  'timeout',
  'cancelled',
  'budget_exceeded',
]);

export type ForkStatus = z.infer<typeof ForkStatusSchema>;

export const ForkStateSchema = z.object({
  forkNum: z.number(),
  sandboxId: z.string().optional(),
  status: ForkStatusSchema,
  costUsd: z.number().default(0),
  inputTokens: z.number().default(0),
  outputTokens: z.number().default(0),
  durationSeconds: z.number().default(0),
  error: z.string().optional(),
  startedAt: z.string().optional(),
  completedAt: z.string().optional(),
});

export type ForkState = z.infer<typeof ForkStateSchema>;

export const OrchestrationStateSchema = z.object({
  workflowId: z.string(),
  repoUrl: z.string(),
  branch: z.string(),
  prompt: z.string(),
  numForks: z.number(),
  model: z.string().default('sonnet'),
  maxConcurrent: z.number().default(5),
  timeoutSeconds: z.number().default(7200),
  budgetLimitUsd: z.number().optional(),
  forks: z.array(ForkStateSchema).default([]),
  totalCostUsd: z.number().default(0),
  completedCount: z.number().default(0),
  failedCount: z.number().default(0),
  paused: z.boolean().default(false),
  cancelled: z.boolean().default(false),
  startedAt: z.string(),
  completedAt: z.string().optional(),
});

export type OrchestrationState = z.infer<typeof OrchestrationStateSchema>;

// State keys
export const STATE_KEYS = {
  orchestration: (workflowId: string) => `orchestration:${workflowId}`,
  fork: (workflowId: string, forkNum: number) =>
    `fork:${workflowId}:${forkNum}`,
  sandbox: (sandboxId: string) => `sandbox:${sandboxId}`,
  metrics: (workflowId: string) => `metrics:${workflowId}`,
} as const;

// Metrics state
export const MetricsStateSchema = z.object({
  workflowId: z.string(),
  totalForks: z.number(),
  completedForks: z.number(),
  failedForks: z.number(),
  totalCostUsd: z.number(),
  avgDurationSeconds: z.number(),
  lastUpdated: z.string(),
});

export type MetricsState = z.infer<typeof MetricsStateSchema>;
