/**
 * Firefly API Module - Image Generation Tools
 *
 * Provides MCP tools for Adobe Firefly's generative image APIs:
 * - Text-to-image generation (Firefly Image Model 4)
 * - Image expansion (generative expand/outpainting)
 * - Generative fill (inpainting)
 * - Background removal
 * - Similar image generation
 * - Style transfer
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { FireflyAsset, getCredentials, FireflyError } from "../asset.js";
import {
    GenerateImageRequestSchema,
    GenerateImageResponseSchema,
    ExpandImageRequestSchema,
    FillImageRequestSchema,
    RemoveBackgroundRequestSchema,
    GenerateSimilarRequestSchema,
    GeneratedImage,
    FireflyErrorCode,
} from "../types.js";
import logger from "../logger.js";

// ============================================
// Tool Input Schemas (for MCP tool definitions)
// ============================================

const GenerateImageInputSchema = z.object({
    prompt: z.string().describe("Text description of the image to generate"),
    negativePrompt: z
        .string()
        .optional()
        .describe("Text describing what should NOT appear in the image"),
    width: z.number().int().min(512).max(4096).default(1024).describe("Width in pixels"),
    height: z.number().int().min(512).max(4096).default(1024).describe("Height in pixels"),
    numVariations: z.number().int().min(1).max(4).default(1).describe("Number of variations to generate"),
    contentClass: z.enum(["photo", "art"]).optional().describe("Content type: photo for photorealistic, art for artistic"),
    seed: z.number().int().optional().describe("Seed for deterministic output"),
    aspectRatio: z.string().optional().describe("Aspect ratio e.g. '16:9', '1:1' (alternative to width/height)"),
    outputFormat: z.enum(["jpeg", "png"]).optional().describe("Output format"),
    style: z.string().optional().describe("Style preset name to apply"),
});

const ExpandImageInputSchema = z.object({
    prompt: z.string().describe("Text describing what should appear in the expanded area"),
    imageUrl: z.string().url().optional().describe("URL of the source image"),
    imageBase64: z.string().optional().describe("Base64-encoded source image (alternative to URL)"),
    targetWidth: z.number().int().min(512).max(4096).optional().describe("Target width of expanded image"),
    targetHeight: z.number().int().min(512).max(4096).optional().describe("Target height of expanded image"),
    horizontalAlign: z.enum(["left", "center", "right"]).default("center").describe("Horizontal alignment of original"),
    verticalAlign: z.enum(["top", "center", "bottom"]).default("center").describe("Vertical alignment of original"),
});

const FillImageInputSchema = z.object({
    prompt: z.string().describe("Text describing what should appear in the masked area"),
    imageUrl: z.string().url().optional().describe("URL of the source image"),
    imageBase64: z.string().optional().describe("Base64-encoded source image"),
    maskUrl: z.string().url().optional().describe("URL of mask image (white = fill, black = preserve)"),
    maskBase64: z.string().optional().describe("Base64-encoded mask image"),
});

const RemoveBackgroundInputSchema = z.object({
    imageUrl: z.string().url().optional().describe("URL of the image to process"),
    imageBase64: z.string().optional().describe("Base64-encoded image data"),
});

const GenerateSimilarInputSchema = z.object({
    referenceImageUrl: z.string().url().optional().describe("URL of the reference image"),
    referenceImageBase64: z.string().optional().describe("Base64-encoded reference image"),
    prompt: z.string().optional().describe("Optional text to guide generation"),
    numVariations: z.number().int().min(1).max(4).default(1).describe("Number of variations"),
    similarity: z.number().min(0).max(1).default(0.5).describe("How similar (0-1, higher = more similar)"),
});

const StyleTransferInputSchema = z.object({
    prompt: z.string().describe("Text describing the content to generate"),
    styleImageUrl: z.string().url().optional().describe("URL of the style reference image"),
    styleImageBase64: z.string().optional().describe("Base64-encoded style image"),
    styleStrength: z.number().min(0).max(1).default(0.7).describe("Style strength (0-1)"),
});

// ============================================
// Firefly Asset Implementation
// ============================================

export class FireflyImageAsset extends FireflyAsset {
    constructor(clientId?: string, clientSecret?: string) {
        const creds = clientId && clientSecret
            ? { clientId, clientSecret }
            : getCredentials();
        super(creds.clientId, creds.clientSecret, "https://firefly-api.adobe.io");
    }

    /**
     * Register all Firefly image tools with the MCP server.
     */
    registerTools(server: Server): void {
        // Generate Image Tool
        server.setRequestHandler(CallToolRequestSchema, async (request) => {
            if (request.params.name === "firefly_generate_image") {
                return this.handleGenerateImage(request.params.arguments);
            }
            if (request.params.name === "firefly_expand_image") {
                return this.handleExpandImage(request.params.arguments);
            }
            if (request.params.name === "firefly_fill_image") {
                return this.handleFillImage(request.params.arguments);
            }
            if (request.params.name === "firefly_remove_background") {
                return this.handleRemoveBackground(request.params.arguments);
            }
            if (request.params.name === "firefly_generate_similar") {
                return this.handleGenerateSimilar(request.params.arguments);
            }
            if (request.params.name === "firefly_style_transfer") {
                return this.handleStyleTransfer(request.params.arguments);
            }
            // Return undefined to let other handlers process
            return undefined as never;
        });
    }

    /**
     * Get tool definitions for this asset.
     */
    getToolDefinitions(): Array<{
        name: string;
        description: string;
        inputSchema: z.ZodSchema;
    }> {
        return [
            {
                name: "firefly_generate_image",
                description:
                    "Generate images from a text prompt using Adobe Firefly AI (Image Model 4). " +
                    "Creates high-quality images up to 2K resolution with control over style, composition, and content class.",
                inputSchema: GenerateImageInputSchema,
            },
            {
                name: "firefly_expand_image",
                description:
                    "Expand an image beyond its current boundaries using generative AI (outpainting). " +
                    "Specify target dimensions and alignment to control where the original image appears.",
                inputSchema: ExpandImageInputSchema,
            },
            {
                name: "firefly_fill_image",
                description:
                    "Fill or replace portions of an image using a mask and generative AI (inpainting). " +
                    "White areas in the mask will be filled, black areas preserved.",
                inputSchema: FillImageInputSchema,
            },
            {
                name: "firefly_remove_background",
                description:
                    "Remove the background from an image, leaving only the main subject with a transparent background.",
                inputSchema: RemoveBackgroundInputSchema,
            },
            {
                name: "firefly_generate_similar",
                description:
                    "Generate images similar to a reference image. Control similarity level and optionally guide with a text prompt.",
                inputSchema: GenerateSimilarInputSchema,
            },
            {
                name: "firefly_style_transfer",
                description:
                    "Apply the visual style of a reference image to generate new content. " +
                    "Provide a style reference image and describe what to create with that style.",
                inputSchema: StyleTransferInputSchema,
            },
        ];
    }

    // ============================================
    // Tool Handlers
    // ============================================

    private async handleGenerateImage(args: unknown) {
        const input = GenerateImageInputSchema.parse(args);
        logger.info("Generating image", { prompt: input.prompt.slice(0, 50) });

        const body: Record<string, unknown> = {
            prompt: input.prompt,
            n: input.numVariations,
        };

        if (input.aspectRatio) {
            body.aspectRatio = input.aspectRatio;
        } else {
            body.size = { width: input.width, height: input.height };
        }

        if (input.negativePrompt) body.negativePrompt = input.negativePrompt;
        if (input.contentClass) body.contentClass = input.contentClass;
        if (input.seed !== undefined) body.seed = input.seed;
        if (input.outputFormat) body.outputFormat = input.outputFormat;
        if (input.style) body.style = { presets: [input.style] };

        const result = await this.post<{ images: GeneratedImage[]; contentClass?: string }>(
            "/v3/images/generate",
            body
        );

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify(
                        {
                            images: result.images,
                            contentClass: result.contentClass,
                        },
                        null,
                        2
                    ),
                },
            ],
        };
    }

    private async handleExpandImage(args: unknown) {
        const input = ExpandImageInputSchema.parse(args);

        if (!input.imageUrl && !input.imageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either imageUrl or imageBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Expanding image", { prompt: input.prompt.slice(0, 50) });

        const body: Record<string, unknown> = {
            prompt: input.prompt,
            image: {
                source: input.imageUrl
                    ? { url: input.imageUrl }
                    : { base64: input.imageBase64 },
            },
            placement: {
                alignment: {
                    horizontal: input.horizontalAlign,
                    vertical: input.verticalAlign,
                },
            },
        };

        if (input.targetWidth || input.targetHeight) {
            body.size = {
                ...(input.targetWidth && { width: input.targetWidth }),
                ...(input.targetHeight && { height: input.targetHeight }),
            };
        }

        const result = await this.post<{ images: GeneratedImage[] }>(
            "/v3/images/expand",
            body
        );

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ images: result.images }, null, 2),
                },
            ],
        };
    }

    private async handleFillImage(args: unknown) {
        const input = FillImageInputSchema.parse(args);

        if (!input.imageUrl && !input.imageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either imageUrl or imageBase64 must be provided",
                retryable: false,
            });
        }

        if (!input.maskUrl && !input.maskBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either maskUrl or maskBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Filling image", { prompt: input.prompt.slice(0, 50) });

        const body: Record<string, unknown> = {
            prompt: input.prompt,
            image: {
                source: input.imageUrl
                    ? { url: input.imageUrl }
                    : { base64: input.imageBase64 },
            },
            mask: {
                source: input.maskUrl
                    ? { url: input.maskUrl }
                    : { base64: input.maskBase64 },
            },
        };

        const result = await this.post<{ images: GeneratedImage[] }>(
            "/v3/images/fill",
            body
        );

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ images: result.images }, null, 2),
                },
            ],
        };
    }

    private async handleRemoveBackground(args: unknown) {
        const input = RemoveBackgroundInputSchema.parse(args);

        if (!input.imageUrl && !input.imageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either imageUrl or imageBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Removing background");

        const body: Record<string, unknown> = {
            image: {
                source: input.imageUrl
                    ? { url: input.imageUrl }
                    : { base64: input.imageBase64 },
            },
        };

        const result = await this.post<{ output: { url: string } }>(
            "/v2/images/cutout",
            body
        );

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ url: result.output.url }, null, 2),
                },
            ],
        };
    }

    private async handleGenerateSimilar(args: unknown) {
        const input = GenerateSimilarInputSchema.parse(args);

        if (!input.referenceImageUrl && !input.referenceImageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either referenceImageUrl or referenceImageBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Generating similar images", { similarity: input.similarity });

        const body: Record<string, unknown> = {
            n: input.numVariations,
            similarity: input.similarity,
            image: {
                source: input.referenceImageUrl
                    ? { url: input.referenceImageUrl }
                    : { base64: input.referenceImageBase64 },
            },
        };

        if (input.prompt) {
            body.prompt = input.prompt;
        }

        const result = await this.post<{ images: GeneratedImage[] }>(
            "/v3/images/generate-similar",
            body
        );

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ images: result.images }, null, 2),
                },
            ],
        };
    }

    private async handleStyleTransfer(args: unknown) {
        const input = StyleTransferInputSchema.parse(args);

        if (!input.styleImageUrl && !input.styleImageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either styleImageUrl or styleImageBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Applying style transfer", { prompt: input.prompt.slice(0, 50) });

        const body: Record<string, unknown> = {
            prompt: input.prompt,
            style: {
                strength: input.styleStrength,
                imageReference: {
                    source: input.styleImageUrl
                        ? { url: input.styleImageUrl }
                        : { base64: input.styleImageBase64 },
                },
            },
        };

        const result = await this.post<{ images: GeneratedImage[] }>(
            "/v3/images/generate",
            body
        );

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ images: result.images }, null, 2),
                },
            ],
        };
    }
}

export default FireflyImageAsset;
