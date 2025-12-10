/**
 * Base Asset class for Adobe Firefly MCP Hub.
 *
 * Provides unified authentication, request handling, retry logic,
 * and job polling for all Adobe API modules.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { jwtDecode } from "jwt-decode";
import logger from "./logger.js";
import { FireflyErrorCode, FireflyErrorDetails } from "./types.js";

// ============================================
// Configuration Types
// ============================================

interface TokenCache {
    accessToken: string;
    expiresAt: number;
}

interface RequestOptions {
    method?: "GET" | "POST" | "PUT" | "DELETE";
    body?: Record<string, unknown>;
    headers?: Record<string, string>;
    timeout?: number;
}

interface RetryConfig {
    maxRetries: number;
    baseDelay: number;
    maxDelay: number;
}

// ============================================
// Custom Error Class
// ============================================

export class FireflyError extends Error {
    public readonly code: FireflyErrorCode;
    public readonly statusCode?: number;
    public readonly retryable: boolean;
    public readonly details?: Record<string, unknown>;

    constructor(details: FireflyErrorDetails) {
        super(details.message);
        this.name = "FireflyError";
        this.code = details.code;
        this.statusCode = details.statusCode;
        this.retryable = details.retryable;
        this.details = details.details;
    }

    static fromResponse(statusCode: number, responseBody: string): FireflyError {
        let code = FireflyErrorCode.UNKNOWN;
        let message = `API request failed with status ${statusCode}`;
        let retryable = false;

        switch (statusCode) {
            case 400:
                code = FireflyErrorCode.INVALID_REQUEST;
                message = `Invalid request: ${responseBody}`;
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
                    message = "Adobe server error";
                    retryable = true;
                }
        }

        return new FireflyError({
            code,
            message,
            statusCode,
            retryable,
            details: { responseBody },
        });
    }
}

// ============================================
// Base Asset Class
// ============================================

/**
 * Abstract base class for all Adobe API asset modules.
 *
 * Handles:
 * - OAuth2 client credentials authentication
 * - Request retries with exponential backoff
 * - Token caching and automatic refresh
 * - Job polling for async APIs
 */
export abstract class FireflyAsset {
    protected readonly clientId: string;
    protected readonly clientSecret: string;
    protected readonly apiBase: string;
    protected readonly authUrl: string =
        "https://ims-na1.adobelogin.com/ims/token/v3";
    protected readonly scopes: string = "openid,AdobeID,firefly_api,ff_apis";
    protected readonly retryConfig: RetryConfig;

    private tokenCache: TokenCache | null = null;

    constructor(
        clientId: string,
        clientSecret: string,
        apiBase: string = "https://firefly-api.adobe.io",
        retryConfig?: Partial<RetryConfig>
    ) {
        this.clientId = clientId;
        this.clientSecret = clientSecret;
        this.apiBase = apiBase;
        this.retryConfig = {
            maxRetries: retryConfig?.maxRetries ?? 3,
            baseDelay: retryConfig?.baseDelay ?? 1000,
            maxDelay: retryConfig?.maxDelay ?? 8000,
        };
    }

    /**
     * Register tools with the MCP server.
     * Must be implemented by each asset module.
     */
    abstract registerTools(server: Server): void;

    // ============================================
    // Authentication
    // ============================================

    /**
     * Authenticate with Adobe IMS and get access token.
     */
    protected async authenticate(forceRefresh = false): Promise<string> {
        // Return cached token if valid
        if (!forceRefresh && this.tokenCache) {
            const now = Date.now();
            // Refresh 60 seconds before expiry
            if (this.tokenCache.expiresAt - 60000 > now) {
                return this.tokenCache.accessToken;
            }
        }

        logger.debug("Authenticating with Adobe IMS...");

        const params = new URLSearchParams({
            grant_type: "client_credentials",
            client_id: this.clientId,
            client_secret: this.clientSecret,
            scope: this.scopes,
        });

        try {
            const response = await fetch(this.authUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: params.toString(),
            });

            if (!response.ok) {
                const text = await response.text();
                if (response.status === 401) {
                    throw new FireflyError({
                        code: FireflyErrorCode.INVALID_CREDENTIALS,
                        message: "Invalid client credentials",
                        statusCode: 401,
                        retryable: false,
                    });
                }
                throw new FireflyError({
                    code: FireflyErrorCode.AUTH_FAILED,
                    message: `Authentication failed: ${text}`,
                    statusCode: response.status,
                    retryable: false,
                });
            }

            const data = (await response.json()) as {
                access_token: string;
                expires_in: number;
            };

            this.tokenCache = {
                accessToken: data.access_token,
                expiresAt: Date.now() + data.expires_in * 1000,
            };

            // Try to decode JWT for logging
            try {
                const decoded = jwtDecode(data.access_token);
                logger.debug("Authentication successful", {
                    expiresIn: data.expires_in,
                    sub: (decoded as Record<string, unknown>).sub,
                });
            } catch {
                logger.debug("Authentication successful", {
                    expiresIn: data.expires_in,
                });
            }

            return this.tokenCache.accessToken;
        } catch (error) {
            if (error instanceof FireflyError) {
                throw error;
            }
            throw new FireflyError({
                code: FireflyErrorCode.NETWORK_ERROR,
                message: `Network error during authentication: ${error}`,
                retryable: true,
            });
        }
    }

    /**
     * Get current token expiry time for monitoring.
     */
    protected getTokenExpiry(): Date | null {
        return this.tokenCache ? new Date(this.tokenCache.expiresAt) : null;
    }

    // ============================================
    // Request Handling
    // ============================================

    /**
     * Make an authenticated API request with retry logic.
     */
    protected async request<T>(
        endpoint: string,
        options: RequestOptions = {},
        retryCount = 0
    ): Promise<T> {
        const token = await this.authenticate();
        const url = `${this.apiBase}${endpoint}`;
        const method = options.method ?? "POST";

        const headers: Record<string, string> = {
            Authorization: `Bearer ${token}`,
            "x-api-key": this.clientId,
            "Content-Type": "application/json",
            ...options.headers,
        };

        const controller = new AbortController();
        const timeout = options.timeout ?? 60000;
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            logger.http(`${method} ${endpoint}`, {
                hasBody: !!options.body,
            });

            const response = await fetch(url, {
                method,
                headers,
                body: options.body ? JSON.stringify(options.body) : undefined,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const text = await response.text();
                const error = FireflyError.fromResponse(response.status, text);

                // Handle token expiry
                if (error.code === FireflyErrorCode.TOKEN_EXPIRED && retryCount === 0) {
                    logger.info("Token expired, refreshing and retrying...");
                    await this.authenticate(true);
                    return this.request<T>(endpoint, options, retryCount + 1);
                }

                // Retry on retryable errors
                if (error.retryable && retryCount < this.retryConfig.maxRetries) {
                    const delay = this.calculateBackoff(retryCount);
                    logger.warn(
                        `Retryable error (${error.code}), waiting ${delay}ms before retry ${retryCount + 1}/${this.retryConfig.maxRetries}...`
                    );
                    await this.sleep(delay);
                    return this.request<T>(endpoint, options, retryCount + 1);
                }

                throw error;
            }

            return (await response.json()) as T;
        } catch (error) {
            clearTimeout(timeoutId);

            if (error instanceof FireflyError) {
                throw error;
            }

            // Handle abort/timeout
            if (error instanceof Error && error.name === "AbortError") {
                if (retryCount < this.retryConfig.maxRetries) {
                    const delay = this.calculateBackoff(retryCount);
                    logger.warn(
                        `Request timed out, waiting ${delay}ms before retry ${retryCount + 1}/${this.retryConfig.maxRetries}...`
                    );
                    await this.sleep(delay);
                    return this.request<T>(endpoint, options, retryCount + 1);
                }
                throw new FireflyError({
                    code: FireflyErrorCode.TIMEOUT,
                    message: "Request timed out",
                    retryable: true,
                });
            }

            // Handle network errors
            if (retryCount < this.retryConfig.maxRetries) {
                const delay = this.calculateBackoff(retryCount);
                logger.warn(
                    `Network error, waiting ${delay}ms before retry ${retryCount + 1}/${this.retryConfig.maxRetries}...`
                );
                await this.sleep(delay);
                return this.request<T>(endpoint, options, retryCount + 1);
            }

            throw new FireflyError({
                code: FireflyErrorCode.NETWORK_ERROR,
                message: `Network error: ${error}`,
                retryable: true,
            });
        }
    }

    /**
     * Make a GET request.
     */
    protected async get<T>(
        endpoint: string,
        headers?: Record<string, string>
    ): Promise<T> {
        return this.request<T>(endpoint, { method: "GET", headers });
    }

    /**
     * Make a POST request.
     */
    protected async post<T>(
        endpoint: string,
        body: Record<string, unknown>,
        headers?: Record<string, string>
    ): Promise<T> {
        return this.request<T>(endpoint, { method: "POST", body, headers });
    }

    // ============================================
    // Job Polling (for Async APIs)
    // ============================================

    /**
     * Poll for job completion (used by Photoshop/Lightroom async APIs).
     */
    protected async pollJobStatus<T>(
        jobId: string,
        statusEndpoint: string,
        options: {
            pollInterval?: number;
            maxWaitTime?: number;
            successStatuses?: string[];
            failureStatuses?: string[];
        } = {}
    ): Promise<T> {
        const {
            pollInterval = 2000,
            maxWaitTime = 300000, // 5 minutes default
            successStatuses = ["succeeded", "COMPLETED"],
            failureStatuses = ["failed", "FAILED"],
        } = options;

        const startTime = Date.now();
        let lastStatus = "";

        logger.info(`Polling job ${jobId}...`);

        while (Date.now() - startTime < maxWaitTime) {
            const result = await this.get<T & { status: string }>(
                `${statusEndpoint}/${jobId}`
            );

            if (result.status !== lastStatus) {
                logger.info(`Job ${jobId} status: ${result.status}`);
                lastStatus = result.status;
            }

            if (successStatuses.includes(result.status)) {
                logger.info(`Job ${jobId} completed successfully`);
                return result;
            }

            if (failureStatuses.includes(result.status)) {
                throw new FireflyError({
                    code: FireflyErrorCode.JOB_FAILED,
                    message: `Job ${jobId} failed with status: ${result.status}`,
                    retryable: false,
                    details: result as unknown as Record<string, unknown>,
                });
            }

            await this.sleep(pollInterval);
        }

        throw new FireflyError({
            code: FireflyErrorCode.TIMEOUT,
            message: `Job ${jobId} timed out after ${maxWaitTime}ms`,
            retryable: true,
        });
    }

    // ============================================
    // Utility Methods
    // ============================================

    /**
     * Calculate exponential backoff delay.
     */
    private calculateBackoff(retryCount: number): number {
        const delay = Math.min(
            this.retryConfig.baseDelay * Math.pow(2, retryCount),
            this.retryConfig.maxDelay
        );
        // Add jitter (0-25%)
        return delay + Math.random() * delay * 0.25;
    }

    /**
     * Sleep for specified milliseconds.
     */
    private sleep(ms: number): Promise<void> {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}

// ============================================
// Factory Function
// ============================================

/**
 * Get credentials from environment.
 */
export function getCredentials(): { clientId: string; clientSecret: string } {
    const clientId = process.env.FIREFLY_CLIENT_ID;
    const clientSecret = process.env.FIREFLY_CLIENT_SECRET;

    if (!clientId || !clientSecret) {
        throw new FireflyError({
            code: FireflyErrorCode.INVALID_CREDENTIALS,
            message:
                "FIREFLY_CLIENT_ID and FIREFLY_CLIENT_SECRET environment variables are required",
            retryable: false,
        });
    }

    return { clientId, clientSecret };
}
