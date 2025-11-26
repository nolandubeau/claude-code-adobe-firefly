/**
 * Adobe Firefly API Client
 *
 * This client handles authentication and API calls to Adobe Firefly Services.
 * Reference: https://developer.adobe.com/firefly-services/docs/
 */

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface GenerateImageOptions {
  prompt: string;
  negativePrompt?: string;
  width?: number;
  height?: number;
  numVariations?: number;
  contentClass?: "photo" | "art";
  style?: string;
}

interface ExpandImageOptions {
  imageUrl?: string;
  imageBase64?: string;
  prompt: string;
  targetWidth?: number;
  targetHeight?: number;
  placement?: {
    horizontalAlign?: "left" | "center" | "right";
    verticalAlign?: "top" | "center" | "bottom";
  };
}

interface FillImageOptions {
  imageUrl?: string;
  imageBase64?: string;
  maskUrl?: string;
  maskBase64?: string;
  prompt: string;
}

interface RemoveBackgroundOptions {
  imageUrl?: string;
  imageBase64?: string;
}

interface GenerateSimilarOptions {
  referenceImageUrl?: string;
  referenceImageBase64?: string;
  prompt?: string;
  numVariations?: number;
  similarity?: number;
}

interface StyleTransferOptions {
  styleImageUrl?: string;
  styleImageBase64?: string;
  prompt: string;
  styleStrength?: number;
}

interface GeneratedImage {
  url: string;
  seed?: number;
}

interface FireflyResponse {
  images: GeneratedImage[];
  contentClass?: string;
}

export class FireflyClient {
  private clientId: string;
  private clientSecret: string;
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;

  private static readonly AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3";
  private static readonly API_BASE = "https://firefly-api.adobe.io";
  private static readonly SCOPES = "openid,AdobeID,firefly_api,ff_apis";

  constructor(clientId: string, clientSecret: string) {
    this.clientId = clientId;
    this.clientSecret = clientSecret;
  }

  private async authenticate(): Promise<string> {
    // Return cached token if still valid
    if (this.accessToken && Date.now() < this.tokenExpiry - 60000) {
      return this.accessToken;
    }

    const params = new URLSearchParams({
      grant_type: "client_credentials",
      client_id: this.clientId,
      client_secret: this.clientSecret,
      scope: FireflyClient.SCOPES,
    });

    const response = await fetch(FireflyClient.AUTH_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params.toString(),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Authentication failed: ${response.status} - ${errorText}`);
    }

    const data = (await response.json()) as TokenResponse;
    this.accessToken = data.access_token;
    this.tokenExpiry = Date.now() + data.expires_in * 1000;

    return this.accessToken;
  }

  private async makeRequest<T>(
    endpoint: string,
    body: Record<string, unknown>
  ): Promise<T> {
    const token = await this.authenticate();

    const response = await fetch(`${FireflyClient.API_BASE}${endpoint}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "x-api-key": this.clientId,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API request failed: ${response.status} - ${errorText}`);
    }

    return response.json() as Promise<T>;
  }

  /**
   * Generate images from a text prompt
   */
  async generateImage(options: GenerateImageOptions): Promise<FireflyResponse> {
    const body: Record<string, unknown> = {
      prompt: options.prompt,
      n: options.numVariations ?? 1,
      size: {
        width: options.width ?? 1024,
        height: options.height ?? 1024,
      },
    };

    if (options.negativePrompt) {
      body.negativePrompt = options.negativePrompt;
    }

    if (options.contentClass) {
      body.contentClass = options.contentClass;
    }

    if (options.style) {
      body.style = { presets: [options.style] };
    }

    return this.makeRequest<FireflyResponse>("/v3/images/generate", body);
  }

  /**
   * Expand an image beyond its current boundaries
   */
  async expandImage(options: ExpandImageOptions): Promise<FireflyResponse> {
    const body: Record<string, unknown> = {
      prompt: options.prompt,
    };

    if (options.imageUrl) {
      body.image = { source: { url: options.imageUrl } };
    } else if (options.imageBase64) {
      body.image = { source: { base64: options.imageBase64 } };
    }

    if (options.targetWidth || options.targetHeight) {
      body.size = {
        width: options.targetWidth,
        height: options.targetHeight,
      };
    }

    if (options.placement) {
      body.placement = {
        alignment: {
          horizontal: options.placement.horizontalAlign ?? "center",
          vertical: options.placement.verticalAlign ?? "center",
        },
      };
    }

    return this.makeRequest<FireflyResponse>("/v3/images/expand", body);
  }

  /**
   * Fill or replace portions of an image using a mask
   */
  async fillImage(options: FillImageOptions): Promise<FireflyResponse> {
    const body: Record<string, unknown> = {
      prompt: options.prompt,
    };

    if (options.imageUrl) {
      body.image = { source: { url: options.imageUrl } };
    } else if (options.imageBase64) {
      body.image = { source: { base64: options.imageBase64 } };
    }

    if (options.maskUrl) {
      body.mask = { source: { url: options.maskUrl } };
    } else if (options.maskBase64) {
      body.mask = { source: { base64: options.maskBase64 } };
    }

    return this.makeRequest<FireflyResponse>("/v3/images/fill", body);
  }

  /**
   * Remove the background from an image
   */
  async removeBackground(
    options: RemoveBackgroundOptions
  ): Promise<{ output: { url: string } }> {
    const body: Record<string, unknown> = {};

    if (options.imageUrl) {
      body.image = { source: { url: options.imageUrl } };
    } else if (options.imageBase64) {
      body.image = { source: { base64: options.imageBase64 } };
    }

    return this.makeRequest<{ output: { url: string } }>(
      "/v2/images/cutout",
      body
    );
  }

  /**
   * Generate images similar to a reference image
   */
  async generateSimilarImages(
    options: GenerateSimilarOptions
  ): Promise<FireflyResponse> {
    const body: Record<string, unknown> = {
      n: options.numVariations ?? 1,
    };

    if (options.referenceImageUrl) {
      body.image = { source: { url: options.referenceImageUrl } };
    } else if (options.referenceImageBase64) {
      body.image = { source: { base64: options.referenceImageBase64 } };
    }

    if (options.prompt) {
      body.prompt = options.prompt;
    }

    if (options.similarity !== undefined) {
      body.similarity = options.similarity;
    }

    return this.makeRequest<FireflyResponse>("/v3/images/generate-similar", body);
  }

  /**
   * Apply style from a reference image to generated content
   */
  async applyStyleTransfer(
    options: StyleTransferOptions
  ): Promise<FireflyResponse> {
    const body: Record<string, unknown> = {
      prompt: options.prompt,
    };

    if (options.styleImageUrl) {
      body.style = {
        imageReference: { source: { url: options.styleImageUrl } },
        strength: options.styleStrength ?? 0.7,
      };
    } else if (options.styleImageBase64) {
      body.style = {
        imageReference: { source: { base64: options.styleImageBase64 } },
        strength: options.styleStrength ?? 0.7,
      };
    }

    return this.makeRequest<FireflyResponse>("/v3/images/generate", body);
  }
}
