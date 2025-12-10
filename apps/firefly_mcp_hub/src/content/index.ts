/**
 * Content Tagging API Module - Content Analysis Tools
 *
 * Provides MCP tools for Adobe Content Tagging API:
 * - Auto-tagging (keyword extraction)
 * - Color extraction (dominant colors)
 * - Content classification
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { FireflyAsset, getCredentials, FireflyError } from "../asset.js";
import { ContentTag, ExtractedColor, FireflyErrorCode } from "../types.js";
import logger from "../logger.js";

// ============================================
// Constants
// ============================================

const CONTENT_API_BASE = "https://cis.adobe.io";

// ============================================
// Tool Input Schemas
// ============================================

const AutoTagInputSchema = z.object({
    imageUrl: z.string().url().optional().describe("URL of the image to analyze"),
    imageBase64: z.string().optional().describe("Base64-encoded image data"),
    includeTags: z.boolean().default(true).describe("Include content tags in response"),
    includeColors: z.boolean().default(false).describe("Include dominant colors in response"),
    threshold: z.number().min(0).max(1).default(0.5).describe("Minimum confidence threshold (0-1)"),
    topN: z.number().int().min(1).max(50).default(10).describe("Maximum number of tags to return"),
});

const ExtractColorsInputSchema = z.object({
    imageUrl: z.string().url().optional().describe("URL of the image to analyze"),
    imageBase64: z.string().optional().describe("Base64-encoded image data"),
    numColors: z.number().int().min(1).max(20).default(5).describe("Number of colors to extract"),
});

// ============================================
// Response Types
// ============================================

interface ContentAnalysisResponse {
    tags?: Array<{
        name: string;
        confidence: number;
    }>;
    colors?: Array<{
        color: { red: number; green: number; blue: number };
        percentage: number;
    }>;
}

// ============================================
// Content Asset Implementation
// ============================================

export class ContentAsset extends FireflyAsset {
    constructor(clientId?: string, clientSecret?: string) {
        const creds =
            clientId && clientSecret
                ? { clientId, clientSecret }
                : getCredentials();
        super(creds.clientId, creds.clientSecret, CONTENT_API_BASE);
    }

    registerTools(server: Server): void {
        server.setRequestHandler(CallToolRequestSchema, async (request) => {
            switch (request.params.name) {
                case "content_auto_tag":
                    return this.handleAutoTag(request.params.arguments);
                case "content_extract_colors":
                    return this.handleExtractColors(request.params.arguments);
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
                name: "content_auto_tag",
                description:
                    "Automatically generate descriptive tags/keywords for an image using AI. " +
                    "Returns tags with confidence scores for content discovery and SEO.",
                inputSchema: AutoTagInputSchema,
            },
            {
                name: "content_extract_colors",
                description:
                    "Extract dominant colors from an image. Returns RGB values, hex codes, " +
                    "and percentage coverage for each color.",
                inputSchema: ExtractColorsInputSchema,
            },
        ];
    }

    // ============================================
    // Tool Handlers
    // ============================================

    private async handleAutoTag(args: unknown) {
        const input = AutoTagInputSchema.parse(args);

        if (!input.imageUrl && !input.imageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either imageUrl or imageBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Auto-tagging image", { topN: input.topN });

        const body: Record<string, unknown> = {
            data: {
                source: input.imageUrl
                    ? { url: input.imageUrl }
                    : { base64: input.imageBase64 },
            },
            params: {
                include_tags: input.includeTags,
                include_colors: input.includeColors,
                threshold: input.threshold,
                top_n: input.topN,
            },
        };

        const result = await this.post<ContentAnalysisResponse>(
            "/services/v2/analyze",
            body
        );

        // Format response
        const response: {
            tags?: ContentTag[];
            colors?: Array<ExtractedColor & { hex: string }>;
        } = {};

        if (result.tags) {
            response.tags = result.tags.map((t) => ({
                name: t.name,
                confidence: t.confidence,
            }));
        }

        if (result.colors) {
            response.colors = result.colors.map((c) => ({
                color: c.color,
                hex: this.rgbToHex(c.color.red, c.color.green, c.color.blue),
                percentage: c.percentage,
            }));
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify(response, null, 2),
                },
            ],
        };
    }

    private async handleExtractColors(args: unknown) {
        const input = ExtractColorsInputSchema.parse(args);

        if (!input.imageUrl && !input.imageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either imageUrl or imageBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Extracting colors", { numColors: input.numColors });

        const body: Record<string, unknown> = {
            data: {
                source: input.imageUrl
                    ? { url: input.imageUrl }
                    : { base64: input.imageBase64 },
            },
            params: {
                include_tags: false,
                include_colors: true,
                top_n: input.numColors,
            },
        };

        const result = await this.post<ContentAnalysisResponse>(
            "/services/v2/colors",
            body
        );

        const colors = (result.colors ?? []).map((c) => ({
            color: c.color,
            hex: this.rgbToHex(c.color.red, c.color.green, c.color.blue),
            percentage: c.percentage,
        }));

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify({ colors }, null, 2),
                },
            ],
        };
    }

    // ============================================
    // Helper Methods
    // ============================================

    private rgbToHex(r: number, g: number, b: number): string {
        return (
            "#" +
            [r, g, b]
                .map((x) => {
                    const hex = x.toString(16);
                    return hex.length === 1 ? "0" + hex : hex;
                })
                .join("")
        );
    }
}

export default ContentAsset;
