/**
 * Adobe Firefly API Client
 *
 * This client handles authentication and API calls to Adobe Firefly Services
 * with comprehensive error handling, retry logic, and input validation.
 *
 * Reference: https://developer.adobe.com/firefly-services/docs/
 */

/**
 * Error codes for categorizing Firefly API errors.
 */
export enum FireflyErrorCode {
  AUTH_FAILED = "auth_failed",
  INVALID_CREDENTIALS = "invalid_credentials",
  TOKEN_EXPIRED = "token_expired",
  RATE_LIMITED = "rate_limited",
  INVALID_REQUEST = "invalid_request",
  INVALID_IMAGE = "invalid_image",
  IMAGE_TOO_LARGE = "image_too_large",
  CONTENT_POLICY = "content_policy",
  SERVER_ERROR = "server_error",
  NETWORK_ERROR = "network_error",
  TIMEOUT = "timeout",
  VALIDATION_ERROR = "validation_error",
  UNKNOWN = "unknown",
}

/**
 * Custom error class for Firefly API errors.
 */
export class FireflyError extends Error {
  constructor(
    message: string,
    public code: FireflyErrorCode,
    public statusCode?: number,
    public responseBody?: string,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = "FireflyError";
  }

  /**
   * Create an appropriate error from an HTTP response.
   */
  static fromResponse(statusCode: number, responseBody: string): FireflyError {
    let code = FireflyErrorCode.UNKNOWN;
    let retryable = false;
    let message = `API request failed: ${statusCode}`;

    switch (statusCode) {
      case 400:
        code = FireflyErrorCode.INVALID_REQUEST;
        message = "Invalid request parameters";
        break;
      case 401:
        code = FireflyErrorCode.TOKEN_EXPIRED;
        message = "Authentication token expired";
        retryable = true;
        break;
      case 403:
        code = FireflyErrorCode.CONTENT_POLICY;
        message = "Request blocked by content policy";
        break;
      case 413:
        code = FireflyErrorCode.IMAGE_TOO_LARGE;
        message = "Image exceeds maximum size";
        break;
      case 429:
        code = FireflyErrorCode.RATE_LIMITED;
        message = "Rate limit exceeded";
        retryable = true;
        break;
      default:
        if (statusCode >= 500) {
          code = FireflyErrorCode.SERVER_ERROR;
          message = "Adobe Firefly server error";
          retryable = true;
        }
    }

    return new FireflyError(message, code, statusCode, responseBody, retryable);
  }
}

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
  private maxRetries: number;

  private static readonly AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3";
  private static readonly API_BASE = "https://firefly-api.adobe.io";
  private static readonly SCOPES = "openid,AdobeID,firefly_api,ff_apis";
  private static readonly RETRY_DELAYS = [1000, 2000, 4000]; // Exponential backoff

  constructor(clientId: string, clientSecret: string, maxRetries: number = 3) {
    this.clientId = clientId;
    this.clientSecret = clientSecret;
    this.maxRetries = maxRetries;
  }

  /**
   * Sleep for a specified number of milliseconds.
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Authenticate with Adobe IMS and get an access token.
   */
  private async authenticate(forceRefresh: boolean = false): Promise<string> {
    // Return cached token if still valid (with 60s buffer)
    if (!forceRefresh && this.accessToken && Date.now() < this.tokenExpiry - 60000) {
      return this.accessToken;
    }

    const params = new URLSearchParams({
      grant_type: "client_credentials",
      client_id: this.clientId,
      client_secret: this.clientSecret,
      scope: FireflyClient.SCOPES,
    });

    let response: Response;
    try {
      response = await fetch(FireflyClient.AUTH_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: params.toString(),
      });
    } catch (error) {
      throw new FireflyError(
        `Network error during authentication: ${error}`,
        FireflyErrorCode.NETWORK_ERROR
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      if (response.status === 401) {
        throw new FireflyError(
          "Invalid client credentials",
          FireflyErrorCode.INVALID_CREDENTIALS,
          response.status,
          errorText
        );
      }
      throw new FireflyError(
        `Authentication failed: ${response.status} - ${errorText}`,
        FireflyErrorCode.AUTH_FAILED,
        response.status,
        errorText
      );
    }

    const data = (await response.json()) as TokenResponse;
    this.accessToken = data.access_token;
    this.tokenExpiry = Date.now() + data.expires_in * 1000;

    return this.accessToken;
  }

  /**
   * Make an authenticated API request with retry logic.
   */
  private async makeRequest<T>(
    endpoint: string,
    body: Record<string, unknown>,
    retryCount: number = 0
  ): Promise<T> {
    const token = await this.authenticate();

    let response: Response;
    try {
      response = await fetch(`${FireflyClient.API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "x-api-key": this.clientId,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
    } catch (error) {
      // Network error - retry if possible
      if (retryCount < this.maxRetries) {
        const delay = FireflyClient.RETRY_DELAYS[Math.min(retryCount, FireflyClient.RETRY_DELAYS.length - 1)];
        console.error(`Network error, retrying in ${delay}ms (${retryCount + 1}/${this.maxRetries})...`);
        await this.sleep(delay);
        return this.makeRequest<T>(endpoint, body, retryCount + 1);
      }
      throw new FireflyError(
        `Network error: ${error}`,
        FireflyErrorCode.NETWORK_ERROR,
        undefined,
        undefined,
        true
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      const error = FireflyError.fromResponse(response.status, errorText);

      // Handle token expiry with re-auth
      if (error.code === FireflyErrorCode.TOKEN_EXPIRED && retryCount === 0) {
        console.error("Token expired, refreshing and retrying...");
        await this.authenticate(true);
        return this.makeRequest<T>(endpoint, body, retryCount + 1);
      }

      // Retry on retryable errors
      if (error.retryable && retryCount < this.maxRetries) {
        const delay = FireflyClient.RETRY_DELAYS[Math.min(retryCount, FireflyClient.RETRY_DELAYS.length - 1)];
        console.error(`Retryable error (${error.code}), waiting ${delay}ms before retry (${retryCount + 1}/${this.maxRetries})...`);
        await this.sleep(delay);
        return this.makeRequest<T>(endpoint, body, retryCount + 1);
      }

      throw error;
    }

    return response.json() as Promise<T>;
  }

  /**
   * Validate that at least one image source is provided.
   */
  private validateImageSource(
    imageUrl?: string,
    imageBase64?: string,
    fieldName: string = "image"
  ): void {
    if (!imageUrl && !imageBase64) {
      throw new FireflyError(
        `Either ${fieldName}Url or ${fieldName}Base64 must be provided`,
        FireflyErrorCode.VALIDATION_ERROR
      );
    }
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
