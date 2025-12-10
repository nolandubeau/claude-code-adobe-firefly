/**
 * Video API Module - Video Generation Tools (Beta)
 *
 * Provides MCP tools for Adobe Firefly Video API:
 * - Text-to-video generation
 * - Image-to-video animation
 * - Video generation status checking
 *
 * Note: Video APIs are in beta and subject to change.
 * Video generation is async and may take several minutes.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { FireflyAsset, getCredentials, FireflyError } from "../asset.js";
import { VideoJobResponse, VideoStatusResponse, FireflyErrorCode } from "../types.js";
import logger from "../logger.js";

// ============================================
// Constants
// ============================================

const VIDEO_API_BASE = "https://firefly-api.adobe.io";
const VIDEO_POLL_INTERVAL = 5000; // 5 seconds - video takes longer
const VIDEO_MAX_WAIT = 600000; // 10 minutes

// ============================================
// Tool Input Schemas
// ============================================

const TextToVideoInputSchema = z.object({
    prompt: z.string().min(1).max(10000).describe("Text description of the video to generate"),
    duration: z.number().min(1).max(10).default(4).describe("Video duration in seconds (1-10)"),
    aspectRatio: z
        .enum(["16:9", "9:16", "1:1"])
        .default("16:9")
        .describe("Video aspect ratio"),
    cameraMotion: z
        .object({
            type: z
                .enum(["pan", "zoom", "tilt", "static"])
                .optional()
                .describe("Type of camera motion"),
            direction: z
                .enum(["left", "right", "up", "down", "in", "out"])
                .optional()
                .describe("Direction of motion"),
            strength: z
                .number()
                .min(0)
                .max(1)
                .optional()
                .describe("Motion intensity (0-1)"),
        })
        .optional()
        .describe("Camera motion settings"),
    seed: z.number().int().optional().describe("Seed for deterministic output"),
    waitForCompletion: z
        .boolean()
        .default(false)
        .describe("Wait for video to complete (can take several minutes)"),
});

const ImageToVideoInputSchema = z.object({
    prompt: z.string().min(1).max(10000).describe("Text description of the animation"),
    imageUrl: z.string().url().optional().describe("URL of the source image"),
    imageBase64: z.string().optional().describe("Base64-encoded source image"),
    duration: z.number().min(1).max(10).default(4).describe("Video duration in seconds"),
    cameraMotion: z
        .object({
            type: z
                .enum(["pan", "zoom", "tilt", "static"])
                .optional()
                .describe("Type of camera motion"),
            direction: z
                .enum(["left", "right", "up", "down", "in", "out"])
                .optional()
                .describe("Direction of motion"),
            strength: z
                .number()
                .min(0)
                .max(1)
                .optional()
                .describe("Motion intensity (0-1)"),
        })
        .optional()
        .describe("Camera motion settings"),
    seed: z.number().int().optional().describe("Seed for deterministic output"),
    waitForCompletion: z.boolean().default(false),
});

const VideoStatusInputSchema = z.object({
    jobId: z.string().describe("Video generation job ID"),
    waitForCompletion: z
        .boolean()
        .default(false)
        .describe("Wait for job to complete"),
});

// ============================================
// Video Asset Implementation
// ============================================

export class VideoAsset extends FireflyAsset {
    constructor(clientId?: string, clientSecret?: string) {
        const creds =
            clientId && clientSecret
                ? { clientId, clientSecret }
                : getCredentials();
        super(creds.clientId, creds.clientSecret, VIDEO_API_BASE);
    }

    registerTools(server: Server): void {
        server.setRequestHandler(CallToolRequestSchema, async (request) => {
            switch (request.params.name) {
                case "video_text_to_video":
                    return this.handleTextToVideo(request.params.arguments);
                case "video_image_to_video":
                    return this.handleImageToVideo(request.params.arguments);
                case "video_get_status":
                    return this.handleGetStatus(request.params.arguments);
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
                name: "video_text_to_video",
                description:
                    "[BETA] Generate a video from a text prompt using Adobe Firefly Video Model. " +
                    "Creates 1080p video clips up to 10 seconds. Note: Generation may take several minutes.",
                inputSchema: TextToVideoInputSchema,
            },
            {
                name: "video_image_to_video",
                description:
                    "[BETA] Animate a static image into a video using AI. " +
                    "Provide a source image and describe the motion/animation to apply.",
                inputSchema: ImageToVideoInputSchema,
            },
            {
                name: "video_get_status",
                description:
                    "Check the status of a video generation job. Returns progress, " +
                    "completion status, and video URL when ready.",
                inputSchema: VideoStatusInputSchema,
            },
        ];
    }

    // ============================================
    // Tool Handlers
    // ============================================

    private async handleTextToVideo(args: unknown) {
        const input = TextToVideoInputSchema.parse(args);
        logger.info("Generating text-to-video", {
            prompt: input.prompt.slice(0, 50),
            duration: input.duration,
        });

        const body: Record<string, unknown> = {
            prompt: input.prompt,
            duration: input.duration,
            aspectRatio: input.aspectRatio,
        };

        if (input.cameraMotion) {
            body.cameraMotion = input.cameraMotion;
        }

        if (input.seed !== undefined) {
            body.seed = input.seed;
        }

        const response = await this.post<VideoJobResponse>(
            "/v3/video/generate",
            body
        );

        if (input.waitForCompletion) {
            const result = await this.waitForVideoJob(response.jobId);
            return this.formatVideoResult(result);
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify(
                        {
                            jobId: response.jobId,
                            status: response.status,
                            message:
                                "Video generation started. Use video_get_status to check progress. " +
                                "Generation typically takes 2-5 minutes.",
                        },
                        null,
                        2
                    ),
                },
            ],
        };
    }

    private async handleImageToVideo(args: unknown) {
        const input = ImageToVideoInputSchema.parse(args);

        if (!input.imageUrl && !input.imageBase64) {
            throw new FireflyError({
                code: FireflyErrorCode.INVALID_REQUEST,
                message: "Either imageUrl or imageBase64 must be provided",
                retryable: false,
            });
        }

        logger.info("Generating image-to-video", {
            prompt: input.prompt.slice(0, 50),
            duration: input.duration,
        });

        const body: Record<string, unknown> = {
            prompt: input.prompt,
            duration: input.duration,
            image: {
                source: input.imageUrl
                    ? { url: input.imageUrl }
                    : { base64: input.imageBase64 },
            },
        };

        if (input.cameraMotion) {
            body.cameraMotion = input.cameraMotion;
        }

        if (input.seed !== undefined) {
            body.seed = input.seed;
        }

        const response = await this.post<VideoJobResponse>(
            "/v3/video/animate",
            body
        );

        if (input.waitForCompletion) {
            const result = await this.waitForVideoJob(response.jobId);
            return this.formatVideoResult(result);
        }

        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify(
                        {
                            jobId: response.jobId,
                            status: response.status,
                            message:
                                "Image-to-video generation started. Use video_get_status to check progress.",
                        },
                        null,
                        2
                    ),
                },
            ],
        };
    }

    private async handleGetStatus(args: unknown) {
        const input = VideoStatusInputSchema.parse(args);
        logger.info("Checking video job status", { jobId: input.jobId });

        if (input.waitForCompletion) {
            const result = await this.waitForVideoJob(input.jobId);
            return this.formatVideoResult(result);
        }

        const result = await this.get<VideoStatusResponse>(
            `/v3/video/status/${input.jobId}`
        );

        return this.formatVideoResult(result);
    }

    // ============================================
    // Helper Methods
    // ============================================

    private async waitForVideoJob(jobId: string): Promise<VideoStatusResponse> {
        return this.pollJobStatus<VideoStatusResponse>(
            jobId,
            "/v3/video/status",
            {
                pollInterval: VIDEO_POLL_INTERVAL,
                maxWaitTime: VIDEO_MAX_WAIT,
                successStatuses: ["COMPLETED"],
                failureStatuses: ["FAILED"],
            }
        );
    }

    private formatVideoResult(result: VideoStatusResponse) {
        const response: Record<string, unknown> = {
            jobId: result.jobId,
            status: result.status,
        };

        if (result.progress !== undefined) {
            response.progress = `${result.progress}%`;
        }

        if (result.outputs && result.outputs.length > 0) {
            response.videos = result.outputs.map((o) => ({
                url: o.url,
                duration: o.duration,
                resolution: o.width && o.height ? `${o.width}x${o.height}` : undefined,
            }));
        }

        if (result.error) {
            response.error = result.error;
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
}

export default VideoAsset;
