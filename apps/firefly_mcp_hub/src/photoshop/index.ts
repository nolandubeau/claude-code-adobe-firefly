/**
 * Photoshop API Module - Async Image Processing Tools
 *
 * Provides MCP tools for Adobe Photoshop API operations:
 * - Apply Photoshop actions
 * - Create image renditions
 * - Edit text layers
 * - Smart object replacement
 * - Background removal
 * - Product crop (smart cropping)
 * - Document manifest extraction
 *
 * Note: Photoshop APIs are asynchronous - operations return a job ID
 * that must be polled for completion.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { FireflyAsset, getCredentials, FireflyError } from "../asset.js";
import {
    PhotoshopJobStatusResponse,
    PhotoshopJobResponse,
    FireflyErrorCode,
} from "../types.js";
import logger from "../logger.js";

// ============================================
// Constants
// ============================================

const PHOTOSHOP_API_BASE = "https://image.adobe.io";
const JOB_POLL_INTERVAL = 2000;
const JOB_MAX_WAIT = 300000; // 5 minutes

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
        .enum(["image/jpeg", "image/png", "image/tiff", "image/vnd.adobe.photoshop"])
        .default("image/png")
        .describe("Output format"),
    quality: z.number().int().min(1).max(12).optional().describe("JPEG quality (1-12)"),
    overwrite: z.boolean().default(true).describe("Overwrite existing file"),
});

const ApplyActionsInputSchema = z.object({
    inputs: z.array(StorageRefInputSchema).describe("Input PSD/image files"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    actionsUrl: z.string().url().optional().describe("URL to .atn actions file"),
    actionsJson: z
        .array(z.record(z.unknown()))
        .optional()
        .describe("ActionJSON commands"),
    waitForCompletion: z.boolean().default(true).describe("Wait for job to complete"),
});

const CreateRenditionInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source PSD/image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output rendition configurations"),
    waitForCompletion: z.boolean().default(true),
});

const EditTextInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source PSD"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    layers: z
        .array(
            z.object({
                name: z.string().optional().describe("Layer name to target"),
                id: z.number().int().optional().describe("Layer ID to target"),
                text: z.object({
                    content: z.string().describe("New text content"),
                    fontSize: z.number().optional().describe("Font size"),
                    fontName: z.string().optional().describe("Font family name"),
                    fontColor: z
                        .object({
                            red: z.number().int().min(0).max(255),
                            green: z.number().int().min(0).max(255),
                            blue: z.number().int().min(0).max(255),
                        })
                        .optional()
                        .describe("Font color RGB"),
                }),
            })
        )
        .describe("Text layer edits"),
    waitForCompletion: z.boolean().default(true),
});

const SmartObjectInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source PSD"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputs: z.array(OutputConfigInputSchema).describe("Output configurations"),
    layers: z
        .array(
            z.object({
                name: z.string().optional().describe("Smart object layer name"),
                id: z.number().int().optional().describe("Smart object layer ID"),
                replacementHref: z.string().url().describe("URL to replacement content"),
                replacementStorage: z
                    .enum(["azure", "dropbox", "external", "adobe"])
                    .default("external"),
            })
        )
        .describe("Smart object replacements"),
    waitForCompletion: z.boolean().default(true),
});

const RemoveBackgroundPsInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to source image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputHref: z.string().url().describe("Pre-signed URL for output"),
    outputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputType: z.enum(["image/png"]).default("image/png"),
    waitForCompletion: z.boolean().default(true),
});

const ProductCropInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to product image"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputHref: z.string().url().describe("Pre-signed URL for output"),
    outputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    outputType: z.enum(["image/jpeg", "image/png"]).default("image/png"),
    waitForCompletion: z.boolean().default(true),
});

const GetManifestInputSchema = z.object({
    inputHref: z.string().url().describe("Pre-signed URL to PSD file"),
    inputStorage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    waitForCompletion: z.boolean().default(true),
});

const JobStatusInputSchema = z.object({
    jobId: z.string().describe("Job ID to check status for"),
});

// ============================================
// Photoshop Asset Implementation
// ============================================

export class PhotoshopAsset extends FireflyAsset {
    constructor(clientId?: string, clientSecret?: string) {
        const creds =
            clientId && clientSecret
                ? { clientId, clientSecret }
                : getCredentials();
        super(creds.clientId, creds.clientSecret, PHOTOSHOP_API_BASE);
    }

    registerTools(server: Server): void {
        server.setRequestHandler(CallToolRequestSchema, async (request) => {
            switch (request.params.name) {
                case "photoshop_apply_actions":
                    return this.handleApplyActions(request.params.arguments);
                case "photoshop_create_rendition":
                    return this.handleCreateRendition(request.params.arguments);
                case "photoshop_edit_text":
                    return this.handleEditText(request.params.arguments);
                case "photoshop_smart_object":
                    return this.handleSmartObject(request.params.arguments);
                case "photoshop_remove_background":
                    return this.handleRemoveBackground(request.params.arguments);
                case "photoshop_product_crop":
                    return this.handleProductCrop(request.params.arguments);
                case "photoshop_get_manifest":
                    return this.handleGetManifest(request.params.arguments);
                case "photoshop_job_status":
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
                name: "photoshop_apply_actions",
                description:
                    "Apply Photoshop actions to images. Actions can be provided as a URL to a .atn file " +
                    "or as ActionJSON commands. Supports batch processing of multiple inputs.",
                inputSchema: ApplyActionsInputSchema,
            },
            {
                name: "photoshop_create_rendition",
                description:
                    "Create image renditions from PSD files. Generate multiple output formats and sizes " +
                    "from a single source file.",
                inputSchema: CreateRenditionInputSchema,
            },
            {
                name: "photoshop_edit_text",
                description:
                    "Edit text layers in a PSD file. Change text content, font, size, and color " +
                    "programmatically. Target layers by name or ID.",
                inputSchema: EditTextInputSchema,
            },
            {
                name: "photoshop_smart_object",
                description:
                    "Replace smart object contents in a PSD file. Update linked assets while " +
                    "preserving layer effects and transformations.",
                inputSchema: SmartObjectInputSchema,
            },
            {
                name: "photoshop_remove_background",
                description:
                    "Remove background from an image using Photoshop's AI-powered subject selection. " +
                    "Returns a PNG with transparent background.",
                inputSchema: RemoveBackgroundPsInputSchema,
            },
            {
                name: "photoshop_product_crop",
                description:
                    "Smart crop product images for e-commerce. Automatically detects the product " +
                    "and crops to optimal framing.",
                inputSchema: ProductCropInputSchema,
            },
            {
                name: "photoshop_get_manifest",
                description:
                    "Extract the document manifest from a PSD file. Returns layer structure, " +
                    "dimensions, color mode, and other document information.",
                inputSchema: GetManifestInputSchema,
            },
            {
                name: "photoshop_job_status",
                description:
                    "Check the status of an async Photoshop job. Returns status, progress, " +
                    "output URLs (if complete), or error details (if failed).",
                inputSchema: JobStatusInputSchema,
            },
        ];
    }

    // ============================================
    // Tool Handlers
    // ============================================

    private async handleApplyActions(args: unknown) {
        const input = ApplyActionsInputSchema.parse(args);
        logger.info("Applying Photoshop actions", { inputCount: input.inputs.length });

        const body: Record<string, unknown> = {
            inputs: input.inputs.map((i) => ({ href: i.href, storage: i.storage })),
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
        };

        if (input.actionsUrl || input.actionsJson) {
            body.options = {
                actions: [
                    {
                        ...(input.actionsUrl && { href: input.actionsUrl }),
                        ...(input.actionsJson && { actionJSON: input.actionsJson }),
                    },
                ],
            };
        }

        const response = await this.post<PhotoshopJobResponse>(
            "/pie/psdService/actionJSON",
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

    private async handleCreateRendition(args: unknown) {
        const input = CreateRenditionInputSchema.parse(args);
        logger.info("Creating renditions");

        const body: Record<string, unknown> = {
            inputs: [{ href: input.inputHref, storage: input.inputStorage }],
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/pie/psdService/renditionCreate",
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

    private async handleEditText(args: unknown) {
        const input = EditTextInputSchema.parse(args);
        logger.info("Editing text layers", { layerCount: input.layers.length });

        const body: Record<string, unknown> = {
            inputs: [{ href: input.inputHref, storage: input.inputStorage }],
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
            options: {
                layers: input.layers.map((l) => ({
                    ...(l.name && { name: l.name }),
                    ...(l.id && { id: l.id }),
                    text: {
                        content: l.text.content,
                        ...(l.text.fontSize || l.text.fontName || l.text.fontColor
                            ? {
                                  characterStyles: [
                                      {
                                          ...(l.text.fontSize && { fontSize: l.text.fontSize }),
                                          ...(l.text.fontName && { fontName: l.text.fontName }),
                                          ...(l.text.fontColor && { fontColor: l.text.fontColor }),
                                      },
                                  ],
                              }
                            : {}),
                    },
                })),
            },
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/pie/psdService/text",
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

    private async handleSmartObject(args: unknown) {
        const input = SmartObjectInputSchema.parse(args);
        logger.info("Replacing smart objects", { layerCount: input.layers.length });

        const body: Record<string, unknown> = {
            inputs: [{ href: input.inputHref, storage: input.inputStorage }],
            outputs: input.outputs.map((o) => ({
                href: o.href,
                storage: o.storage,
                type: o.type,
                quality: o.quality,
                overwrite: o.overwrite,
            })),
            options: {
                layers: input.layers.map((l) => ({
                    ...(l.name && { name: l.name }),
                    ...(l.id && { id: l.id }),
                    input: {
                        href: l.replacementHref,
                        storage: l.replacementStorage,
                    },
                })),
            },
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/pie/psdService/smartObject",
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

    private async handleRemoveBackground(args: unknown) {
        const input = RemoveBackgroundPsInputSchema.parse(args);
        logger.info("Removing background (Photoshop)");

        const body: Record<string, unknown> = {
            input: { href: input.inputHref, storage: input.inputStorage },
            output: {
                href: input.outputHref,
                storage: input.outputStorage,
                overwrite: true,
            },
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/pie/psdService/removeBackground",
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

    private async handleProductCrop(args: unknown) {
        const input = ProductCropInputSchema.parse(args);
        logger.info("Applying product crop");

        const body: Record<string, unknown> = {
            input: { href: input.inputHref, storage: input.inputStorage },
            output: {
                href: input.outputHref,
                storage: input.outputStorage,
                overwrite: true,
            },
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/pie/psdService/productCrop",
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

    private async handleGetManifest(args: unknown) {
        const input = GetManifestInputSchema.parse(args);
        logger.info("Getting PSD manifest");

        const body: Record<string, unknown> = {
            inputs: [{ href: input.inputHref, storage: input.inputStorage }],
        };

        const response = await this.post<PhotoshopJobResponse>(
            "/pie/psdService/documentManifest",
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
        logger.info("Checking job status", { jobId: input.jobId });

        const result = await this.get<PhotoshopJobStatusResponse>(
            `/pie/psdService/status/${input.jobId}`
        );

        return this.formatJobResult(result);
    }

    // ============================================
    // Helper Methods
    // ============================================

    private async waitForJob(jobId: string): Promise<PhotoshopJobStatusResponse> {
        return this.pollJobStatus<PhotoshopJobStatusResponse>(
            jobId,
            "/pie/psdService/status",
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

export default PhotoshopAsset;
