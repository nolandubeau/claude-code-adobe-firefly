#!/usr/bin/env node
/**
 * Adobe Firefly MCP Hub - Entry Point
 *
 * CLI application that starts the MCP server for Adobe Firefly Services.
 *
 * Usage:
 *   npx @anthropic/firefly-mcp-hub [options]
 *
 * Options:
 *   --transport <stdio|http>  Transport type (default: stdio)
 *   --port <number>           HTTP port (default: 3000)
 *   --logs-dir <path>         Log directory
 *   --disable-photoshop       Disable Photoshop module
 *   --disable-lightroom       Disable Lightroom module
 *   --disable-content         Disable Content Tagging module
 *   --disable-video           Disable Video module (beta)
 *
 * Environment Variables:
 *   FIREFLY_CLIENT_ID         Adobe Developer Console client ID (required)
 *   FIREFLY_CLIENT_SECRET     Adobe Developer Console client secret (required)
 *   MCP_TRANSPORT             Transport type
 *   MCP_HTTP_PORT             HTTP port
 *   MCP_LOG_LEVEL             Log level (error, warn, info, debug)
 *   MCP_LOGS_DIR              Log directory
 */

import { FireflyMCPServer } from "./server.js";
import { createLogger } from "./logger.js";

// ============================================
// CLI Argument Parsing
// ============================================

interface CLIArgs {
    transport: "stdio" | "http";
    port: number;
    logsDir?: string;
    disablePhotoshop: boolean;
    disableLightroom: boolean;
    disableContent: boolean;
    disableVideo: boolean;
}

function parseArgs(): CLIArgs {
    const args = process.argv.slice(2);
    const parsed: CLIArgs = {
        transport: (process.env.MCP_TRANSPORT as "stdio" | "http") || "stdio",
        port: parseInt(process.env.MCP_HTTP_PORT || "3000", 10),
        logsDir: process.env.MCP_LOGS_DIR,
        disablePhotoshop: false,
        disableLightroom: false,
        disableContent: false,
        disableVideo: false,
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        const next = args[i + 1];

        switch (arg) {
            case "--transport":
                if (next === "stdio" || next === "http") {
                    parsed.transport = next;
                    i++;
                }
                break;
            case "--port":
                parsed.port = parseInt(next ?? "3000", 10);
                i++;
                break;
            case "--logs-dir":
                parsed.logsDir = next;
                i++;
                break;
            case "--disable-photoshop":
                parsed.disablePhotoshop = true;
                break;
            case "--disable-lightroom":
                parsed.disableLightroom = true;
                break;
            case "--disable-content":
                parsed.disableContent = true;
                break;
            case "--disable-video":
                parsed.disableVideo = true;
                break;
            case "--help":
            case "-h":
                printHelp();
                process.exit(0);
            case "--version":
            case "-v":
                console.log("0.1.0");
                process.exit(0);
        }
    }

    return parsed;
}

function printHelp(): void {
    console.log(`
Adobe Firefly MCP Hub

A Model Context Protocol server providing unified access to Adobe Firefly Services:
- Firefly API (image generation, expand, fill, similar, style transfer)
- Photoshop API (actions, renditions, text editing, smart objects)
- Lightroom API (auto-tone, presets, adjustments)
- Content Tagging API (auto-tagging, color extraction)
- Video API (text-to-video, image-to-video) [beta]

Usage:
  npx @anthropic/firefly-mcp-hub [options]

Options:
  --transport <stdio|http>  Transport type (default: stdio)
  --port <number>           HTTP port when using http transport (default: 3000)
  --logs-dir <path>         Directory for log files
  --disable-photoshop       Disable Photoshop API module
  --disable-lightroom       Disable Lightroom API module
  --disable-content         Disable Content Tagging module
  --disable-video           Disable Video API module (beta)
  -h, --help                Show this help message
  -v, --version             Show version number

Environment Variables:
  FIREFLY_CLIENT_ID         Adobe Developer Console client ID (required)
  FIREFLY_CLIENT_SECRET     Adobe Developer Console client secret (required)
  MCP_TRANSPORT             Transport type (stdio or http)
  MCP_HTTP_PORT             HTTP port
  MCP_LOG_LEVEL             Log level (error, warn, info, debug)
  MCP_LOGS_DIR              Log directory

Examples:
  # Start with STDIO transport (for MCP clients)
  FIREFLY_CLIENT_ID=xxx FIREFLY_CLIENT_SECRET=yyy npx @anthropic/firefly-mcp-hub

  # Start with HTTP transport
  npx @anthropic/firefly-mcp-hub --transport http --port 8080

  # Start with only Firefly module
  npx @anthropic/firefly-mcp-hub --disable-photoshop --disable-lightroom --disable-content --disable-video

For more information, visit: https://developer.adobe.com/firefly-services/
`);
}

// ============================================
// Main Entry Point
// ============================================

async function main(): Promise<void> {
    const args = parseArgs();

    // Initialize logger with custom directory if specified
    if (args.logsDir) {
        createLogger(args.logsDir);
    }

    // Validate credentials
    if (!process.env.FIREFLY_CLIENT_ID || !process.env.FIREFLY_CLIENT_SECRET) {
        console.error(
            "Error: FIREFLY_CLIENT_ID and FIREFLY_CLIENT_SECRET environment variables are required."
        );
        console.error(
            "\nGet credentials at: https://developer.adobe.com/console/"
        );
        console.error("Run with --help for more information.");
        process.exit(1);
    }

    // Create and start server
    const server = new FireflyMCPServer({
        transport: args.transport,
        port: args.port,
        enabledModules: {
            firefly: true,
            photoshop: !args.disablePhotoshop,
            lightroom: !args.disableLightroom,
            content: !args.disableContent,
            video: !args.disableVideo,
        },
    });

    // Handle shutdown
    process.on("SIGINT", () => {
        console.log("\nShutting down...");
        process.exit(0);
    });

    process.on("SIGTERM", () => {
        process.exit(0);
    });

    await server.start();
}

// Run
main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});
