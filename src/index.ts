#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { FireflyClient } from "./firefly-client.js";

const FIREFLY_CLIENT_ID = process.env.FIREFLY_CLIENT_ID;
const FIREFLY_CLIENT_SECRET = process.env.FIREFLY_CLIENT_SECRET;

if (!FIREFLY_CLIENT_ID || !FIREFLY_CLIENT_SECRET) {
  console.error(
    "Error: FIREFLY_CLIENT_ID and FIREFLY_CLIENT_SECRET environment variables are required"
  );
  process.exit(1);
}

const fireflyClient = new FireflyClient(
  FIREFLY_CLIENT_ID,
  FIREFLY_CLIENT_SECRET
);

const tools: Tool[] = [
  {
    name: "generate_image",
    description:
      "Generate an image using Adobe Firefly AI based on a text prompt. Returns a URL to the generated image.",
    inputSchema: {
      type: "object",
      properties: {
        prompt: {
          type: "string",
          description:
            "The text prompt describing the image to generate. Be descriptive for best results.",
        },
        negativePrompt: {
          type: "string",
          description:
            "Optional text describing what should NOT appear in the image.",
        },
        width: {
          type: "number",
          description:
            "Width of the generated image in pixels. Defaults to 1024.",
          default: 1024,
        },
        height: {
          type: "number",
          description:
            "Height of the generated image in pixels. Defaults to 1024.",
          default: 1024,
        },
        numVariations: {
          type: "number",
          description: "Number of image variations to generate (1-4). Defaults to 1.",
          default: 1,
          minimum: 1,
          maximum: 4,
        },
        contentClass: {
          type: "string",
          enum: ["photo", "art"],
          description:
            "The content class for the generated image. 'photo' for photorealistic, 'art' for artistic styles.",
        },
        style: {
          type: "string",
          description:
            "Optional style preset to apply to the generated image.",
        },
      },
      required: ["prompt"],
    },
  },
  {
    name: "expand_image",
    description:
      "Expand an existing image beyond its current boundaries using Adobe Firefly's generative expand feature.",
    inputSchema: {
      type: "object",
      properties: {
        imageUrl: {
          type: "string",
          description: "URL of the source image to expand.",
        },
        imageBase64: {
          type: "string",
          description:
            "Base64-encoded image data (alternative to imageUrl).",
        },
        prompt: {
          type: "string",
          description:
            "Text prompt describing what should appear in the expanded area.",
        },
        targetWidth: {
          type: "number",
          description: "Target width of the expanded image in pixels.",
        },
        targetHeight: {
          type: "number",
          description: "Target height of the expanded image in pixels.",
        },
        placement: {
          type: "object",
          properties: {
            horizontalAlign: {
              type: "string",
              enum: ["left", "center", "right"],
              description: "Horizontal alignment of the original image.",
            },
            verticalAlign: {
              type: "string",
              enum: ["top", "center", "bottom"],
              description: "Vertical alignment of the original image.",
            },
          },
        },
      },
      required: ["prompt"],
    },
  },
  {
    name: "fill_image",
    description:
      "Fill or replace a portion of an image using Adobe Firefly's generative fill feature with a mask.",
    inputSchema: {
      type: "object",
      properties: {
        imageUrl: {
          type: "string",
          description: "URL of the source image to fill.",
        },
        imageBase64: {
          type: "string",
          description:
            "Base64-encoded image data (alternative to imageUrl).",
        },
        maskUrl: {
          type: "string",
          description:
            "URL of the mask image. White areas will be filled, black areas preserved.",
        },
        maskBase64: {
          type: "string",
          description: "Base64-encoded mask image data.",
        },
        prompt: {
          type: "string",
          description:
            "Text prompt describing what should appear in the filled area.",
        },
      },
      required: ["prompt"],
    },
  },
  {
    name: "remove_background",
    description:
      "Remove the background from an image using Adobe Firefly, leaving only the main subject.",
    inputSchema: {
      type: "object",
      properties: {
        imageUrl: {
          type: "string",
          description: "URL of the image to remove background from.",
        },
        imageBase64: {
          type: "string",
          description:
            "Base64-encoded image data (alternative to imageUrl).",
        },
      },
      required: [],
    },
  },
  {
    name: "generate_similar_images",
    description:
      "Generate images similar to a reference image using Adobe Firefly.",
    inputSchema: {
      type: "object",
      properties: {
        referenceImageUrl: {
          type: "string",
          description: "URL of the reference image to base generations on.",
        },
        referenceImageBase64: {
          type: "string",
          description: "Base64-encoded reference image data.",
        },
        prompt: {
          type: "string",
          description:
            "Optional text prompt to guide the similar image generation.",
        },
        numVariations: {
          type: "number",
          description: "Number of variations to generate (1-4). Defaults to 1.",
          default: 1,
          minimum: 1,
          maximum: 4,
        },
        similarity: {
          type: "number",
          description:
            "How similar the generated images should be to the reference (0-1). Higher values = more similar.",
          default: 0.5,
          minimum: 0,
          maximum: 1,
        },
      },
      required: [],
    },
  },
  {
    name: "apply_style_transfer",
    description:
      "Apply the style of a reference image to generate new content with that visual style.",
    inputSchema: {
      type: "object",
      properties: {
        styleImageUrl: {
          type: "string",
          description: "URL of the image whose style should be applied.",
        },
        styleImageBase64: {
          type: "string",
          description: "Base64-encoded style reference image.",
        },
        prompt: {
          type: "string",
          description:
            "Text prompt describing the content to generate with the applied style.",
        },
        styleStrength: {
          type: "number",
          description:
            "How strongly to apply the style (0-1). Higher values = stronger style influence.",
          default: 0.7,
          minimum: 0,
          maximum: 1,
        },
      },
      required: ["prompt"],
    },
  },
];

const server = new Server(
  {
    name: "adobe-firefly",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "generate_image": {
        const result = await fireflyClient.generateImage({
          prompt: args?.prompt as string,
          negativePrompt: args?.negativePrompt as string | undefined,
          width: (args?.width as number) ?? 1024,
          height: (args?.height as number) ?? 1024,
          numVariations: (args?.numVariations as number) ?? 1,
          contentClass: args?.contentClass as "photo" | "art" | undefined,
          style: args?.style as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "expand_image": {
        const result = await fireflyClient.expandImage({
          imageUrl: args?.imageUrl as string | undefined,
          imageBase64: args?.imageBase64 as string | undefined,
          prompt: args?.prompt as string,
          targetWidth: args?.targetWidth as number | undefined,
          targetHeight: args?.targetHeight as number | undefined,
          placement: args?.placement as {
            horizontalAlign?: "left" | "center" | "right";
            verticalAlign?: "top" | "center" | "bottom";
          } | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "fill_image": {
        const result = await fireflyClient.fillImage({
          imageUrl: args?.imageUrl as string | undefined,
          imageBase64: args?.imageBase64 as string | undefined,
          maskUrl: args?.maskUrl as string | undefined,
          maskBase64: args?.maskBase64 as string | undefined,
          prompt: args?.prompt as string,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "remove_background": {
        const result = await fireflyClient.removeBackground({
          imageUrl: args?.imageUrl as string | undefined,
          imageBase64: args?.imageBase64 as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "generate_similar_images": {
        const result = await fireflyClient.generateSimilarImages({
          referenceImageUrl: args?.referenceImageUrl as string | undefined,
          referenceImageBase64: args?.referenceImageBase64 as string | undefined,
          prompt: args?.prompt as string | undefined,
          numVariations: (args?.numVariations as number) ?? 1,
          similarity: (args?.similarity as number) ?? 0.5,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "apply_style_transfer": {
        const result = await fireflyClient.applyStyleTransfer({
          styleImageUrl: args?.styleImageUrl as string | undefined,
          styleImageBase64: args?.styleImageBase64 as string | undefined,
          prompt: args?.prompt as string,
          styleStrength: (args?.styleStrength as number) ?? 0.7,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error occurred";
    return {
      content: [
        {
          type: "text",
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Adobe Firefly MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
