/**
 * Lightroom API Module - Image Enhancement Tools
 *
 * Provides MCP tools for Adobe Lightroom API operations:
 * - Auto-tone adjustment
 * - Auto-straighten (horizon correction)
 * - Apply presets
 * - Apply XMP settings
 * - Custom edit adjustments
 *
 * Note: Lightroom APIs are asynchronous like Photoshop.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { FireflyAsset, getCredentials } from "../asset.js";
import { PhotoshopJobStatusResponse, PhotoshopJobResponse } from "../types.js";
import logger from "../logger.js";

// ============================================
// Constants
// ============================================

const LIGHTROOM_API_BASE = "https://image.adobe.io";
const JOB_POLL_INTERVAL = 2000;
const JOB_MAX_WAIT = 300000;

// ============================================
// Tool Input Schemas
// ============================================

const StorageRefInputSchema = z.object({
    href: z.string().url().describe("Pre-signed URL to the file"),
    storage: z
        .enum(["azure", "dropbox", "external", "adobe"])
        .default("external")
        .describe("Storage type"),
});

const OutputConfigInputSchema = z.object({
    href: z.string().url().describe("Pre-signed URL for output"),
    storage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    type: z
        .enum(["image/jpeg", "image/png", "image/dng"])
        .default("image/jpeg")
        .describe("Output format"),
    quality: z.number().int().min(1).max(12).optional().describe("JPEG quality (1-12)"),
    overwrite: z.boolean().default(true).describe("Overwrite existing file"),
});

const AutoToneInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    waitForCompletion: z.boolean().default(true),
});

const AutoStraightenInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    waitForCompletion: z.boolean().default(true),
});

const ApplyPresetInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    presetHref: z.string().url().optional().describe("URL to .xmp preset file"),
    presetName: z.string().optional().describe("Built-in preset name"),
    waitForCompletion: z.boolean().default(true),
});

const ApplyXmpInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    xmp: z.string().describe("XMP sidecar settings content"),
    waitForCompletion: z.boolean().default(true),
});

const EditImageInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    adjustments: z
        .object({
            Exposure: z.number().min(-5).max(5).optional().describe("Exposure (-5 to 5)"),
            Contrast: z.number().min(-100).max(100).optional().describe("Contrast (-100 to 100)"),
            Highlights: z.number().min(-100).max(100).optional().describe("Highlights (-100 to 100)"),
            Shadows: z.number().min(-100).max(100).optional().describe("Shadows (-100 to 100)"),
            Whites: z.number().min(-100).max(100).optional().describe("Whites (-100 to 100)"),
            Blacks: z.number().min(-100).max(100).optional().describe("Blacks (-100 to 100)"),
            Clarity: z.number().min(-100).max(100).optional().describe("Clarity (-100 to 100)"),
            Dehaze: z.number().min(-100).max(100).optional().describe("Dehaze (-100 to 100)"),
            Vibrance: z.number().min(-100).max(100).optional().describe("Vibrance (-100 to 100)"),
            Saturation: z.number().min(-100).max(100).optional().describe("Saturation (-100 to 100)"),
            Sharpness: z.number().min(0).max(150).optional().describe("Sharpness (0 to 150)"),
            ColorNoiseReduction: z.number().min(0).max(100).optional().describe("Color noise reduction"),
            NoiseReduction: z.number().min(0).max(100).optional().describe("Luminance noise reduction"),
            WhiteBalance: z
                .enum(["As Shot", "Auto", "Daylight", "Cloudy", "Shade", "Tungsten", "Fluorescent", "Flash"])
                .optional()
                .describe("White balance preset"),
            Temperature: z.number().min(2000).max(50000).optional().describe("Color temperature (Kelvin)"),
            Tint: z.number().min(-150).max(150).optional().describe("Tint (-150 to 150)"),
        })
        .describe("Lightroom adjustment values"),
    waitForCompletion: z.boolean().default(true),
});

const JobStatusInputSchema = z.object({
    jobId: z.string().describe("Job ID to check status for"),
});

// ============================================
// Lightroom Asset Implementation
// ============================================

export class LightroomAsset extends FireflyAsset {
    constructor(clientId?: string, clientSecret?: string) {
        const creds =
            clientId && clientSecret
                ? { clientId, clientSecret }
                : getCredentials();
        super(creds.clientId, creds.clientSecret, LIGHTROOM_API_BASE);
    }

    registerTools(server: Server): void {
        server.setRequestHandler(CallToolRequestSchema, async (request) => {
            switch (request.params.name) {
                case "lightroom_auto_tone":
                    return this.handleAutoTone(request.params.arguments);
                case "lightroom_auto_straighten":
                    return this.handleAutoStraighten(request.params.arguments);
                case "lightroom_apply_preset":
                    return this.handleApplyPreset(request.params.arguments);
                case "lightroom_apply_xmp":
                    return this.handleApplyXmp(request.params.arguments);
                case "lightroom_edit":
                    return this.handleEdit(request.params.arguments);
                case "lightroom_job_status":
                    return this.handleJobStatus(request.params.arguments);
                default:
                    return undefined as never;
            }
        });
    }

    getToolDefinitions(): Array<{
        name: string;
        description: string;
        inputSchema: z.ZodSchema;
    }> {
        return [
            {
                name: "lightroom_auto_tone",
                description:
                    "Automatically adjust tone and exposure of an image using Lightroom's AI. " +
                    "Analyzes the image and applies optimal adjustments.",
                inputSchema: AutoToneInputSchema,
            },
            {
                name: "lightroom_auto_straighten",
                description:
                    "Automatically straighten an image by correcting the horizon line. " +
                    "Uses AI to detect and correct tilted horizons.",
                inputSchema: AutoStraightenInputSchema,
            },
            {
                name: "lightroom_apply_preset",
                description:
                    "Apply a Lightroom preset to an image. Provide either a URL to a .xmp preset file " +
                    "or use a built-in preset name.",
                inputSchema: ApplyPresetInputSchema,
            },
            {
                name: "lightroom_apply_xmp",
                description:
                    "Apply XMP sidecar settings to an image. Provide the full XMP content string " +
                    "to apply all contained adjustments.",
                inputSchema: ApplyXmpInputSchema,
            },
            {
                name: "lightroom_edit",
                description:
                    "Apply custom Lightroom adjustments to an image. Supports exposure, contrast, " +
                    "highlights, shadows, white balance, and more.",
                inputSchema: EditImageInputSchema,
            },
            {
                name: "lightroom_job_status",
                description:
                    "Check the status of an async Lightroom job. Returns status, progress, " +
                    "output URLs (if complete), or error details (if failed).",
                inputSchema: JobStatusInputSchema,
            },
        ];
    }

    // ============================================
    // Tool Handlers
    // ============================================

    private async handleAutoTone(args: unknown) {
        const input = AutoToneInputSchema.parse(args);
        logger.info("Applying auto-tone");

        const body: Record<string, unknown> = {
            inputs: { href: input.inputHref, storage: input.inputStorage },
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/lrService/autoTone",
            body
        );

        if (input.waitForCompletion && response.jobId) {
            const result = await this.waitForJob(response.jobId);
            return this.formatJobResult(result);
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ jobId: response.jobId, status: "pending" }, null, 2),
                },
            ],
        };
    }

    private async handleAutoStraighten(args: unknown) {
        const input = AutoStraightenInputSchema.parse(args);
        logger.info("Applying auto-straighten");

        const body: Record<string, unknown> = {
            inputs: { href: input.inputHref, storage: input.inputStorage },
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/lrService/autoStraighten",
            body
        );

        if (input.waitForCompletion && response.jobId) {
            const result = await this.waitForJob(response.jobId);
            return this.formatJobResult(result);
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ jobId: response.jobId, status: "pending" }, null, 2),
                },
            ],
        };
    }

    private async handleApplyPreset(args: unknown) {
        const input = ApplyPresetInputSchema.parse(args);
        logger.info("Applying preset");

        const body: Record<string, unknown> = {
            inputs: { href: input.inputHref, storage: input.inputStorage },
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
            options: {
                preset: input.presetHref
                    ? { href: input.presetHref, storage: "external" }
                    : { presetName: input.presetName },
            },
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/lrService/presets",
            body
        );

        if (input.waitForCompletion && response.jobId) {
            const result = await this.waitForJob(response.jobId);
            return this.formatJobResult(result);
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ jobId: response.jobId, status: "pending" }, null, 2),
                },
            ],
        };
    }

    private async handleApplyXmp(args: unknown) {
        const input = ApplyXmpInputSchema.parse(args);
        logger.info("Applying XMP settings");

        const body: Record<string, unknown> = {
            inputs: { href: input.inputHref, storage: input.inputStorage },
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
            options: {
                xmp: input.xmp,
            },
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/lrService/xmp",
            body
        );

        if (input.waitForCompletion && response.jobId) {
            const result = await this.waitForJob(response.jobId);
            return this.formatJobResult(result);
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ jobId: response.jobId, status: "pending" }, null, 2),
                },
            ],
        };
    }

    private async handleEdit(args: unknown) {
        const input = EditImageInputSchema.parse(args);
        logger.info("Applying Lightroom edits", {
            adjustments: Object.keys(input.adjustments),
        });

        const body: Record<string, unknown> = {
            inputs: { href: input.inputHref, storage: input.inputStorage },
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
            options: input.adjustments,
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/lrService/edit",
            body
        );

        if (input.waitForCompletion && response.jobId) {
            const result = await this.waitForJob(response.jobId);
            return this.formatJobResult(result);
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ jobId: response.jobId, status: "pending" }, null, 2),
                },
            ],
        };
    }

    private async handleJobStatus(args: unknown) {
        const input = JobStatusInputSchema.parse(args);
        logger.info("Checking Lightroom job status", { jobId: input.jobId });

        const result = await this.get<PhotoshopJobStatusResponse>(
            `/lrService/status/${input.jobId}`
        );

        return this.formatJobResult(result);
    }

    // ============================================
    // Helper Methods
    // ============================================

    private async waitForJob(jobId: string): Promise<PhotoshopJobStatusResponse> {
        return this.pollJobStatus<PhotoshopJobStatusResponse>(
            jobId,
            "/lrService/status",
            {
                pollInterval: JOB_POLL_INTERVAL,
                maxWaitTime: JOB_MAX_WAIT,
                successStatuses: ["succeeded"],
                failureStatuses: ["failed"],
            }
        );
    }

    private formatJobResult(result: PhotoshopJobStatusResponse) {
        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify(result, null, 2),
                },
            ],
        };
    }
}

export default LightroomAsset;
