/**
 * Shared type definitions and Zod schemas for Adobe Firefly MCP Hub.
 *
 * Provides type-safe request/response models for all Adobe APIs
 * with runtime validation using Zod.
 */

import { z } from "zod";

// ============================================
// Common Schemas
// ============================================

/**
 * Pagination schema for paginated API responses
 */
export const PaginationSchema = z.object({
    page: z.number().int().positive().default(1),
    pageSize: z.number().int().min(1).max(100).default(10),
});

export type Pagination = z.infer<typeof PaginationSchema>;

/**
 * Paginated response wrapper
 */
export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(
    itemSchema: T
) =>
    z.object({
        count: z.number().int().nonnegative().nullable(),
        next: z.string().url().nullable(),
        previous: z.string().url().nullable(),
        results: z.array(itemSchema),
        error: z.string().nullable().optional(),
    });

/**
 * Image source - either URL or base64
 */
export const ImageSourceSchema = z.discriminatedUnion("type", [
    z.object({
        type: z.literal("url"),
        url: z.string().url(),
    }),
    z.object({
        type: z.literal("base64"),
        base64: z.string(),
    }),
    z.object({
        type: z.literal("presignedUrl"),
        url: z.string().url(),
    }),
]);

export type ImageSource = z.infer<typeof ImageSourceSchema>;

/**
 * Storage reference for Photoshop/Lightroom APIs
 */
export const StorageRefSchema = z.object({
    href: z.string().url(),
    storage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
});

export type StorageRef = z.infer<typeof StorageRefSchema>;

// ============================================
// Firefly API Schemas
// ============================================

export const ContentClassSchema = z.enum(["photo", "art"]);
export type ContentClass = z.infer<typeof ContentClassSchema>;

export const OutputFormatSchema = z.enum(["jpeg", "png", "webp"]);
export type OutputFormat = z.infer<typeof OutputFormatSchema>;

export const AspectRatioSchema = z.enum([
    "1:1",
    "4:3",
    "3:4",
    "16:9",
    "9:16",
    "3:2",
    "2:3",
    "4:5",
    "5:4",
]);
export type AspectRatio = z.infer<typeof AspectRatioSchema>;

/**
 * Image size specification
 */
export const ImageSizeSchema = z.object({
    width: z.number().int().min(512).max(4096).default(1024),
    height: z.number().int().min(512).max(4096).default(1024),
});

export type ImageSize = z.infer<typeof ImageSizeSchema>;

/**
 * Style preset for image generation
 */
export const StylePresetSchema = z.object({
    presets: z.array(z.string()).optional(),
    imageReference: z
        .object({
            source: z.union([
                z.object({ url: z.string().url() }),
                z.object({ base64: z.string() }),
            ]),
        })
        .optional(),
    strength: z.number().min(0).max(1).default(0.5).optional(),
});

export type StylePreset = z.infer<typeof StylePresetSchema>;

/**
 * Structure reference for composition guidance
 */
export const StructureSchema = z.object({
    imageReference: z.object({
        source: z.union([
            z.object({ url: z.string().url() }),
            z.object({ base64: z.string() }),
        ]),
    }),
    strength: z.number().min(0).max(1).default(0.5),
});

export type Structure = z.infer<typeof StructureSchema>;

/**
 * Image generation request
 */
export const GenerateImageRequestSchema = z.object({
    prompt: z.string().min(1).max(10000),
    negativePrompt: z.string().max(10000).optional(),
    n: z.number().int().min(1).max(4).default(1),
    size: ImageSizeSchema.optional(),
    aspectRatio: AspectRatioSchema.optional(),
    seed: z.number().int().min(0).optional(),
    contentClass: ContentClassSchema.optional(),
    outputFormat: OutputFormatSchema.optional(),
    promptBiasingLocaleCode: z.string().optional(),
    style: StylePresetSchema.optional(),
    structure: StructureSchema.optional(),
});

export type GenerateImageRequest = z.infer<typeof GenerateImageRequestSchema>;

/**
 * Generated image result
 */
export const GeneratedImageSchema = z.object({
    url: z.string().url(),
    seed: z.number().int().optional(),
});

export type GeneratedImage = z.infer<typeof GeneratedImageSchema>;

/**
 * Image generation response
 */
export const GenerateImageResponseSchema = z.object({
    images: z.array(GeneratedImageSchema),
    contentClass: ContentClassSchema.optional(),
});

export type GenerateImageResponse = z.infer<typeof GenerateImageResponseSchema>;

/**
 * Image expansion request
 */
export const ExpandImageRequestSchema = z.object({
    prompt: z.string().min(1).max(10000),
    image: z.object({
        source: z.union([
            z.object({ url: z.string().url() }),
            z.object({ base64: z.string() }),
        ]),
    }),
    size: z
        .object({
            width: z.number().int().min(512).max(4096).optional(),
            height: z.number().int().min(512).max(4096).optional(),
        })
        .optional(),
    placement: z
        .object({
            alignment: z
                .object({
                    horizontal: z.enum(["left", "center", "right"]).default("center"),
                    vertical: z.enum(["top", "center", "bottom"]).default("center"),
                })
                .optional(),
        })
        .optional(),
});

export type ExpandImageRequest = z.infer<typeof ExpandImageRequestSchema>;

/**
 * Generative fill request
 */
export const FillImageRequestSchema = z.object({
    prompt: z.string().min(1).max(10000),
    image: z.object({
        source: z.union([
            z.object({ url: z.string().url() }),
            z.object({ base64: z.string() }),
        ]),
    }),
    mask: z.object({
        source: z.union([
            z.object({ url: z.string().url() }),
            z.object({ base64: z.string() }),
        ]),
    }),
});

export type FillImageRequest = z.infer<typeof FillImageRequestSchema>;

/**
 * Background removal request
 */
export const RemoveBackgroundRequestSchema = z.object({
    image: z.object({
        source: z.union([
            z.object({ url: z.string().url() }),
            z.object({ base64: z.string() }),
        ]),
    }),
});

export type RemoveBackgroundRequest = z.infer<
    typeof RemoveBackgroundRequestSchema
>;

/**
 * Similar image generation request
 */
export const GenerateSimilarRequestSchema = z.object({
    image: z.object({
        source: z.union([
            z.object({ url: z.string().url() }),
            z.object({ base64: z.string() }),
        ]),
    }),
    prompt: z.string().optional(),
    n: z.number().int().min(1).max(4).default(1),
    similarity: z.number().min(0).max(1).default(0.5),
});

export type GenerateSimilarRequest = z.infer<
    typeof GenerateSimilarRequestSchema
>;

// ============================================
// Photoshop API Schemas
// ============================================

/**
 * Photoshop job status
 */
export const PhotoshopJobStatusSchema = z.enum([
    "pending",
    "running",
    "succeeded",
    "failed",
]);
export type PhotoshopJobStatus = z.infer<typeof PhotoshopJobStatusSchema>;

/**
 * Photoshop output configuration
 */
export const PhotoshopOutputSchema = z.object({
    href: z.string().url(),
    storage: z.enum(["azure", "dropbox", "external", "adobe"]).default("external"),
    type: z.enum(["image/jpeg", "image/png", "image/tiff", "image/vnd.adobe.photoshop"]).default("image/png"),
    quality: z.number().int().min(1).max(12).optional(),
    compression: z.enum(["none", "lzw", "zip", "rle"]).optional(),
    overwrite: z.boolean().default(true),
});

export type PhotoshopOutput = z.infer<typeof PhotoshopOutputSchema>;

/**
 * Photoshop action request
 */
export const PhotoshopActionRequestSchema = z.object({
    inputs: z.array(StorageRefSchema),
    outputs: z.array(PhotoshopOutputSchema),
    options: z
        .object({
            actions: z
                .array(
                    z.object({
                        href: z.string().url().optional(),
                        storage: z.enum(["azure", "dropbox", "external", "adobe"]).optional(),
                        actionJSON: z.array(z.record(z.unknown())).optional(),
                    })
                )
                .optional(),
        })
        .optional(),
});

export type PhotoshopActionRequest = z.infer<
    typeof PhotoshopActionRequestSchema
>;

/**
 * Photoshop rendition request
 */
export const PhotoshopRenditionRequestSchema = z.object({
    inputs: z.array(StorageRefSchema),
    outputs: z.array(PhotoshopOutputSchema),
});

export type PhotoshopRenditionRequest = z.infer<
    typeof PhotoshopRenditionRequestSchema
>;

/**
 * Photoshop text layer edit
 */
export const TextLayerEditSchema = z.object({
    name: z.string().optional(),
    id: z.number().int().optional(),
    text: z.object({
        content: z.string(),
        characterStyles: z
            .array(
                z.object({
                    from: z.number().int().optional(),
                    to: z.number().int().optional(),
                    fontSize: z.number().optional(),
                    fontName: z.string().optional(),
                    fontColor: z
                        .object({
                            red: z.number().int().min(0).max(255),
                            green: z.number().int().min(0).max(255),
                            blue: z.number().int().min(0).max(255),
                        })
                        .optional(),
                })
            )
            .optional(),
    }),
});

export type TextLayerEdit = z.infer<typeof TextLayerEditSchema>;

/**
 * Photoshop text edit request
 */
export const PhotoshopTextRequestSchema = z.object({
    inputs: z.array(StorageRefSchema),
    outputs: z.array(PhotoshopOutputSchema),
    options: z.object({
        layers: z.array(TextLayerEditSchema),
    }),
});

export type PhotoshopTextRequest = z.infer<typeof PhotoshopTextRequestSchema>;

/**
 * Photoshop smart object replacement
 */
export const SmartObjectEditSchema = z.object({
    name: z.string().optional(),
    id: z.number().int().optional(),
    input: StorageRefSchema,
});

export type SmartObjectEdit = z.infer<typeof SmartObjectEditSchema>;

/**
 * Photoshop smart object request
 */
export const PhotoshopSmartObjectRequestSchema = z.object({
    inputs: z.array(StorageRefSchema),
    outputs: z.array(PhotoshopOutputSchema),
    options: z.object({
        layers: z.array(SmartObjectEditSchema),
    }),
});

export type PhotoshopSmartObjectRequest = z.infer<
    typeof PhotoshopSmartObjectRequestSchema
>;

/**
 * Photoshop job response
 */
export const PhotoshopJobResponseSchema = z.object({
    jobId: z.string().optional(),
    _links: z
        .object({
            self: z.object({ href: z.string() }).optional(),
        })
        .optional(),
});

export type PhotoshopJobResponse = z.infer<typeof PhotoshopJobResponseSchema>;

/**
 * Photoshop job status response
 */
export const PhotoshopJobStatusResponseSchema = z.object({
    jobId: z.string(),
    status: PhotoshopJobStatusSchema,
    created: z.string().optional(),
    modified: z.string().optional(),
    outputs: z
        .array(
            z.object({
                status: PhotoshopJobStatusSchema,
                _links: z
                    .object({
                        self: z.object({ href: z.string().url() }).optional(),
                    })
                    .optional(),
                errors: z
                    .object({
                        type: z.string().optional(),
                        title: z.string().optional(),
                        code: z.string().optional(),
                    })
                    .optional(),
            })
        )
        .optional(),
    errors: z
        .array(
            z.object({
                type: z.string().optional(),
                title: z.string().optional(),
                code: z.string().optional(),
            })
        )
        .optional(),
});

export type PhotoshopJobStatusResponse = z.infer<
    typeof PhotoshopJobStatusResponseSchema
>;

// ============================================
// Lightroom API Schemas
// ============================================

/**
 * Lightroom auto-tone request
 */
export const LightroomAutoToneRequestSchema = z.object({
    inputs: StorageRefSchema,
    outputs: z.array(PhotoshopOutputSchema),
});

export type LightroomAutoToneRequest = z.infer<
    typeof LightroomAutoToneRequestSchema
>;

/**
 * Lightroom preset request
 */
export const LightroomPresetRequestSchema = z.object({
    inputs: StorageRefSchema,
    outputs: z.array(PhotoshopOutputSchema),
    options: z.object({
        preset: z.union([
            StorageRefSchema,
            z.object({ presetName: z.string() }),
        ]),
    }),
});

export type LightroomPresetRequest = z.infer<
    typeof LightroomPresetRequestSchema
>;

/**
 * Lightroom XMP settings request
 */
export const LightroomXmpRequestSchema = z.object({
    inputs: StorageRefSchema,
    outputs: z.array(PhotoshopOutputSchema),
    options: z.object({
        xmp: z.string(), // XMP sidecar content
    }),
});

export type LightroomXmpRequest = z.infer<typeof LightroomXmpRequestSchema>;

/**
 * Lightroom edit request with adjustments
 */
export const LightroomEditRequestSchema = z.object({
    inputs: StorageRefSchema,
    outputs: z.array(PhotoshopOutputSchema),
    options: z.object({
        Exposure: z.number().min(-5).max(5).optional(),
        Contrast: z.number().min(-100).max(100).optional(),
        Highlights: z.number().min(-100).max(100).optional(),
        Shadows: z.number().min(-100).max(100).optional(),
        Whites: z.number().min(-100).max(100).optional(),
        Blacks: z.number().min(-100).max(100).optional(),
        Clarity: z.number().min(-100).max(100).optional(),
        Dehaze: z.number().min(-100).max(100).optional(),
        Vibrance: z.number().min(-100).max(100).optional(),
        Saturation: z.number().min(-100).max(100).optional(),
        Sharpness: z.number().min(0).max(150).optional(),
        ColorNoiseReduction: z.number().min(0).max(100).optional(),
        NoiseReduction: z.number().min(0).max(100).optional(),
        SharpenDetail: z.number().min(0).max(100).optional(),
        SharpenEdgeMasking: z.number().min(0).max(100).optional(),
        WhiteBalance: z.enum(["As Shot", "Auto", "Daylight", "Cloudy", "Shade", "Tungsten", "Fluorescent", "Flash"]).optional(),
        Tint: z.number().min(-150).max(150).optional(),
        Temperature: z.number().min(2000).max(50000).optional(),
    }),
});

export type LightroomEditRequest = z.infer<typeof LightroomEditRequestSchema>;

// ============================================
// Content Tagging API Schemas
// ============================================

/**
 * Content tagging request
 */
export const ContentTaggingRequestSchema = z.object({
    data: z.object({
        source: z.union([
            z.object({ url: z.string().url() }),
            z.object({ base64: z.string() }),
        ]),
    }),
    params: z
        .object({
            include_tags: z.boolean().default(true),
            include_colors: z.boolean().default(true),
            threshold: z.number().min(0).max(1).default(0.5),
            top_n: z.number().int().min(1).max(50).default(10),
        })
        .optional(),
});

export type ContentTaggingRequest = z.infer<typeof ContentTaggingRequestSchema>;

/**
 * Content tag result
 */
export const ContentTagSchema = z.object({
    name: z.string(),
    confidence: z.number().min(0).max(1),
});

export type ContentTag = z.infer<typeof ContentTagSchema>;

/**
 * Color result
 */
export const ExtractedColorSchema = z.object({
    color: z.object({
        red: z.number().int().min(0).max(255),
        green: z.number().int().min(0).max(255),
        blue: z.number().int().min(0).max(255),
    }),
    hex: z.string(),
    percentage: z.number().min(0).max(1),
});

export type ExtractedColor = z.infer<typeof ExtractedColorSchema>;

/**
 * Content tagging response
 */
export const ContentTaggingResponseSchema = z.object({
    tags: z.array(ContentTagSchema).optional(),
    colors: z.array(ExtractedColorSchema).optional(),
});

export type ContentTaggingResponse = z.infer<
    typeof ContentTaggingResponseSchema
>;

// ============================================
// Video API Schemas
// ============================================

/**
 * Video generation status
 */
export const VideoJobStatusSchema = z.enum([
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
]);
export type VideoJobStatus = z.infer<typeof VideoJobStatusSchema>;

/**
 * Video generation request
 */
export const GenerateVideoRequestSchema = z.object({
    prompt: z.string().min(1).max(10000),
    image: z
        .object({
            source: z.union([
                z.object({ url: z.string().url() }),
                z.object({ base64: z.string() }),
            ]),
        })
        .optional(), // Optional: for image-to-video
    duration: z.number().min(1).max(10).default(4), // Duration in seconds
    aspectRatio: z.enum(["16:9", "9:16", "1:1"]).default("16:9"),
    cameraMotion: z
        .object({
            type: z.enum(["pan", "zoom", "tilt", "static"]).optional(),
            direction: z.enum(["left", "right", "up", "down", "in", "out"]).optional(),
            strength: z.number().min(0).max(1).optional(),
        })
        .optional(),
    seed: z.number().int().min(0).optional(),
});

export type GenerateVideoRequest = z.infer<typeof GenerateVideoRequestSchema>;

/**
 * Video generation job response
 */
export const VideoJobResponseSchema = z.object({
    jobId: z.string(),
    status: VideoJobStatusSchema,
});

export type VideoJobResponse = z.infer<typeof VideoJobResponseSchema>;

/**
 * Video generation status response
 */
export const VideoStatusResponseSchema = z.object({
    jobId: z.string(),
    status: VideoJobStatusSchema,
    progress: z.number().min(0).max(100).optional(),
    outputs: z
        .array(
            z.object({
                url: z.string().url(),
                duration: z.number().optional(),
                width: z.number().int().optional(),
                height: z.number().int().optional(),
            })
        )
        .optional(),
    error: z
        .object({
            code: z.string(),
            message: z.string(),
        })
        .optional(),
});

export type VideoStatusResponse = z.infer<typeof VideoStatusResponseSchema>;

// ============================================
// Error Types
// ============================================

export enum FireflyErrorCode {
    AUTH_FAILED = "auth_failed",
    INVALID_CREDENTIALS = "invalid_credentials",
    TOKEN_EXPIRED = "token_expired",
    RATE_LIMITED = "rate_limited",
    INVALID_REQUEST = "invalid_request",
    IMAGE_TOO_LARGE = "image_too_large",
    CONTENT_POLICY = "content_policy",
    SERVER_ERROR = "server_error",
    NETWORK_ERROR = "network_error",
    TIMEOUT = "timeout",
    JOB_FAILED = "job_failed",
    UNKNOWN = "unknown",
}

export interface FireflyErrorDetails {
    code: FireflyErrorCode;
    message: string;
    statusCode?: number;
    retryable: boolean;
    details?: Record<string, unknown>;
}
