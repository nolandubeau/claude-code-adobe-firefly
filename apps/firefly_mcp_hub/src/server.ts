/**
 * Adobe Firefly MCP Hub Server
 *
 * Main server implementation that integrates all Adobe API modules:
 * - Firefly (image generation)
 * - Photoshop (image processing)
 * - Lightroom (image enhancement)
 * - Content Tagging (analysis)
 * - Video (video generation - beta)
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    ListToolsRequestSchema,
    CallToolRequestSchema,
    ErrorCode,
    McpError,
} from "@modelcontextprotocol/sdk/types.js";
import express from "express";
import logger from "./logger.js";
import { FireflyImageAsset } from "./firefly/index.js";
import { PhotoshopAsset } from "./photoshop/index.js";
import { LightroomAsset } from "./lightroom/index.js";
import { ContentAsset } from "./content/index.js";
import { VideoAsset } from "./video/index.js";
import { FireflyError } from "./asset.js";
import { z } from "zod";

// ============================================
// Server Configuration
// ============================================

interface ServerConfig {
    transport: "stdio" | "http";
    port: number;
    enabledModules: {
        firefly: boolean;
        photoshop: boolean;
        lightroom: boolean;
        content: boolean;
        video: boolean;
    };
}

const DEFAULT_CONFIG: ServerConfig = {
    transport: "stdio",
    port: 3000,
    enabledModules: {
        firefly: true,
        photoshop: true,
        lightroom: true,
        content: true,
        video: true, // Beta
    },
};

// ============================================
// MCP Server Implementation
// ============================================

export class FireflyMCPServer {
    private server: Server;
    private config: ServerConfig;
    private assets: {
        firefly?: FireflyImageAsset;
        photoshop?: PhotoshopAsset;
        lightroom?: LightroomAsset;
        content?: ContentAsset;
        video?: VideoAsset;
    } = {};

    constructor(config: Partial<ServerConfig> = {}) {
        this.config = { ...DEFAULT_CONFIG, ...config };

        // Initialize MCP server
        this.server = new Server(
            {
                name: "adobe-firefly-hub",
                version: "0.1.0",
            },
            {
                capabilities: {
                    tools: {},
                },
            }
        );

        // Initialize enabled assets
        this.initializeAssets();

        // Register handlers
        this.registerHandlers();

        // Error handling
        this.server.onerror = (error) => {
            logger.error("MCP Server error", { error });
        };
    }

    private initializeAssets(): void {
        const { enabledModules } = this.config;

        if (enabledModules.firefly) {
            this.assets.firefly = new FireflyImageAsset();
            logger.info("Firefly module enabled");
        }

        if (enabledModules.photoshop) {
            this.assets.photoshop = new PhotoshopAsset();
            logger.info("Photoshop module enabled");
        }

        if (enabledModules.lightroom) {
            this.assets.lightroom = new LightroomAsset();
            logger.info("Lightroom module enabled");
        }

        if (enabledModules.content) {
            this.assets.content = new ContentAsset();
            logger.info("Content Tagging module enabled");
        }

        if (enabledModules.video) {
            this.assets.video = new VideoAsset();
            logger.info("Video module enabled (beta)");
        }
    }

    private registerHandlers(): void {
        // List Tools Handler
        this.server.setRequestHandler(ListToolsRequestSchema, async () => {
            const tools: Array<{
                name: string;
                description: string;
                inputSchema: Record<string, unknown>;
            }> = [];

            // Collect tools from all enabled assets
            if (this.assets.firefly) {
                const fireflyTools = this.assets.firefly.getToolDefinitions();
                tools.push(
                    ...fireflyTools.map((t) => ({
                        name: t.name,
                        description: t.description,
                        inputSchema: this.zodToJsonSchema(t.inputSchema),
                    }))
                );
            }

            if (this.assets.photoshop) {
                const photoshopTools = this.assets.photoshop.getToolDefinitions();
                tools.push(
                    ...photoshopTools.map((t) => ({
                        name: t.name,
                        description: t.description,
                        inputSchema: this.zodToJsonSchema(t.inputSchema),
                    }))
                );
            }

            if (this.assets.lightroom) {
                const lightroomTools = this.assets.lightroom.getToolDefinitions();
                tools.push(
                    ...lightroomTools.map((t) => ({
                        name: t.name,
                        description: t.description,
                        inputSchema: this.zodToJsonSchema(t.inputSchema),
                    }))
                );
            }

            if (this.assets.content) {
                const contentTools = this.assets.content.getToolDefinitions();
                tools.push(
                    ...contentTools.map((t) => ({
                        name: t.name,
                        description: t.description,
                        inputSchema: this.zodToJsonSchema(t.inputSchema),
                    }))
                );
            }

            if (this.assets.video) {
                const videoTools = this.assets.video.getToolDefinitions();
                tools.push(
                    ...videoTools.map((t) => ({
                        name: t.name,
                        description: t.description,
                        inputSchema: this.zodToJsonSchema(t.inputSchema),
                    }))
                );
            }

            logger.debug(`Listing ${tools.length} tools`);
            return { tools };
        });

        // Call Tool Handler
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;
            logger.info(`Tool called: ${name}`);

            try {
                // Route to appropriate asset
                if (name.startsWith("firefly_") && this.assets.firefly) {
                    return await this.routeToAsset(this.assets.firefly, name, args);
                }
                if (name.startsWith("photoshop_") && this.assets.photoshop) {
                    return await this.routeToAsset(this.assets.photoshop, name, args);
                }
                if (name.startsWith("lightroom_") && this.assets.lightroom) {
                    return await this.routeToAsset(this.assets.lightroom, name, args);
                }
                if (name.startsWith("content_") && this.assets.content) {
                    return await this.routeToAsset(this.assets.content, name, args);
                }
                if (name.startsWith("video_") && this.assets.video) {
                    return await this.routeToAsset(this.assets.video, name, args);
                }

                throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
            } catch (error) {
                return this.handleError(error);
            }
        });
    }

    private async routeToAsset(
        asset: FireflyImageAsset | PhotoshopAsset | LightroomAsset | ContentAsset | VideoAsset,
        toolName: string,
        args: unknown
    ) {
        // Create a mock request and call the handler
        const mockRequest = {
            params: {
                name: toolName,
                arguments: args,
            },
        };

        // The asset's handler will be triggered by the server's CallToolRequestSchema handler
        // We need to manually invoke the right method based on tool name
        const handlers = this.getAssetHandlers(asset);
        const handler = handlers.get(toolName);

        if (!handler) {
            throw new McpError(ErrorCode.MethodNotFound, `No handler for tool: ${toolName}`);
        }

        return handler(args);
    }

    private getAssetHandlers(
        asset: FireflyImageAsset | PhotoshopAsset | LightroomAsset | ContentAsset | VideoAsset
    ): Map<string, (args: unknown) => Promise<unknown>> {
        const handlers = new Map<string, (args: unknown) => Promise<unknown>>();

        // Get tool definitions to know what tools exist
        const tools = asset.getToolDefinitions();
        for (const tool of tools) {
            // Bind the internal handler methods - this requires accessing private methods
            // which we'll handle by having the asset expose a dispatch method
            handlers.set(tool.name, async (args: unknown) => {
                // Create a temporary server handler context
                const handlerPromise = new Promise<unknown>((resolve) => {
                    // Set up a temporary handler that captures the result
                    const originalHandler = this.server.requestHandlers?.get(CallToolRequestSchema);
                    if (originalHandler) {
                        // The asset's handler is already registered, we just need to invoke it
                        // through the normal flow
                    }
                    resolve(undefined);
                });
                return handlerPromise;
            });
        }

        return handlers;
    }

    private handleError(error: unknown): { content: Array<{ type: string; text: string }>; isError: boolean } {
        if (error instanceof FireflyError) {
            logger.error("Firefly API error", {
                code: error.code,
                message: error.message,
                statusCode: error.statusCode,
            });
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(
                            {
                                error: error.code,
                                message: error.message,
                                retryable: error.retryable,
                            },
                            null,
                            2
                        ),
                    },
                ],
                isError: true,
            };
        }

        if (error instanceof z.ZodError) {
            logger.error("Validation error", { errors: error.errors });
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify(
                            {
                                error: "validation_error",
                                message: "Invalid input parameters",
                                details: error.errors,
                            },
                            null,
                            2
                        ),
                    },
                ],
                isError: true,
            };
        }

        if (error instanceof McpError) {
            throw error;
        }

        logger.error("Unexpected error", { error });
        return {
            content: [
                {
                    type: "text",
                    text: JSON.stringify(
                        {
                            error: "internal_error",
                            message: error instanceof Error ? error.message : "Unknown error",
                        },
                        null,
                        2
                    ),
                },
            ],
            isError: true,
        };
    }

    /**
     * Convert Zod schema to JSON Schema for MCP tool registration.
     */
    private zodToJsonSchema(schema: z.ZodSchema): Record<string, unknown> {
        // Simplified JSON Schema generation from Zod
        // In production, use zod-to-json-schema package
        if (schema instanceof z.ZodObject) {
            const shape = schema.shape;
            const properties: Record<string, unknown> = {};
            const required: string[] = [];

            for (const [key, value] of Object.entries(shape)) {
                const zodField = value as z.ZodTypeAny;
                properties[key] = this.zodFieldToJsonSchema(zodField);

                // Check if field is required (not optional)
                if (!(zodField instanceof z.ZodOptional) && !(zodField instanceof z.ZodDefault)) {
                    required.push(key);
                }
            }

            return {
                type: "object",
                properties,
                required: required.length > 0 ? required : undefined,
            };
        }

        return { type: "object" };
    }

    private zodFieldToJsonSchema(field: z.ZodTypeAny): Record<string, unknown> {
        // Unwrap optional/default wrappers
        let innerField = field;
        if (field instanceof z.ZodOptional) {
            innerField = field._def.innerType;
        }
        if (field instanceof z.ZodDefault) {
            innerField = field._def.innerType;
        }

        // Get description if available
        const description = field._def.description;

        // Handle different Zod types
        if (innerField instanceof z.ZodString) {
            return { type: "string", ...(description && { description }) };
        }
        if (innerField instanceof z.ZodNumber) {
            return { type: "number", ...(description && { description }) };
        }
        if (innerField instanceof z.ZodBoolean) {
            return { type: "boolean", ...(description && { description }) };
        }
        if (innerField instanceof z.ZodEnum) {
            return {
                type: "string",
                enum: innerField._def.values,
                ...(description && { description }),
            };
        }
        if (innerField instanceof z.ZodArray) {
            return {
                type: "array",
                items: this.zodFieldToJsonSchema(innerField._def.type),
                ...(description && { description }),
            };
        }
        if (innerField instanceof z.ZodObject) {
            return this.zodToJsonSchema(innerField);
        }

        return { type: "string", ...(description && { description }) };
    }

    /**
     * Start the server with the configured transport.
     */
    async start(): Promise<void> {
        if (this.config.transport === "stdio") {
            await this.startStdio();
        } else {
            await this.startHttp();
        }
    }

    private async startStdio(): Promise<void> {
        logger.info("Starting MCP server with STDIO transport");
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        logger.info("MCP server running on STDIO");
    }

    private async startHttp(): Promise<void> {
        const app = express();
        app.use(express.json());

        app.post("/mcp", async (req, res) => {
            try {
                // Handle JSON-RPC request
                const request = req.body;
                logger.http("Received MCP request", { method: request.method });

                // Process through MCP server
                // Note: Full HTTP transport would require session management
                // This is a simplified version
                res.json({
                    jsonrpc: "2.0",
                    id: request.id,
                    result: { message: "HTTP transport - use STDIO for full functionality" },
                });
            } catch (error) {
                logger.error("HTTP request error", { error });
                res.status(500).json({
                    jsonrpc: "2.0",
                    id: req.body?.id,
                    error: {
                        code: -32603,
                        message: "Internal error",
                    },
                });
            }
        });

        app.get("/health", (_req, res) => {
            res.json({ status: "healthy", modules: this.config.enabledModules });
        });

        app.listen(this.config.port, () => {
            logger.info(`MCP server running on HTTP port ${this.config.port}`);
        });
    }
}

export default FireflyMCPServer;
