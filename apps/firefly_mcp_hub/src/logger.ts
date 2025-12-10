/**
 * Winston logger configuration for Adobe Firefly MCP Hub.
 *
 * Provides structured logging with file and console transports,
 * configurable log levels, and production-ready formatting.
 */

import winston from "winston";
import path from "path";
import fs from "fs";

const LOG_LEVELS = {
    error: 0,
    warn: 1,
    info: 2,
    http: 3,
    debug: 4,
} as const;

const LOG_COLORS = {
    error: "red",
    warn: "yellow",
    info: "green",
    http: "magenta",
    debug: "blue",
};

winston.addColors(LOG_COLORS);

/**
 * Create and configure the logger instance.
 *
 * @param logsDir - Directory for log files (default: /app/logs or ./logs)
 * @param level - Minimum log level (default: info)
 * @returns Configured winston logger
 */
export function createLogger(
    logsDir?: string,
    level: string = "info"
): winston.Logger {
    const logDirectory =
        logsDir ||
        (process.env.NODE_ENV === "production" ? "/app/logs" : "./logs");

    // Ensure log directory exists
    if (!fs.existsSync(logDirectory)) {
        fs.mkdirSync(logDirectory, { recursive: true });
    }

    const timestampFormat = winston.format.timestamp({
        format: "YYYY-MM-DD HH:mm:ss",
    });

    const fileFormat = winston.format.combine(
        timestampFormat,
        winston.format.errors({ stack: true }),
        winston.format.json()
    );

    const consoleFormat = winston.format.combine(
        timestampFormat,
        winston.format.colorize({ all: true }),
        winston.format.printf(({ timestamp, level, message, ...meta }) => {
            const metaStr = Object.keys(meta).length
                ? ` ${JSON.stringify(meta)}`
                : "";
            return `${timestamp} [${level}]: ${message}${metaStr}`;
        })
    );

    const transports: winston.transport[] = [
        // Error log file - warnings and errors
        new winston.transports.File({
            filename: path.join(logDirectory, "error.log"),
            level: "warn",
            format: fileFormat,
            maxsize: 10 * 1024 * 1024, // 10MB
            maxFiles: 5,
        }),
        // Combined log file - all messages
        new winston.transports.File({
            filename: path.join(logDirectory, "firefly-mcp.log"),
            format: fileFormat,
            maxsize: 10 * 1024 * 1024,
            maxFiles: 5,
        }),
    ];

    // Add console transport for non-production environments
    if (process.env.NODE_ENV !== "production") {
        transports.push(
            new winston.transports.Console({
                format: consoleFormat,
            })
        );
    }

    return winston.createLogger({
        level,
        levels: LOG_LEVELS,
        defaultMeta: { service: "firefly-mcp-hub" },
        transports,
        exitOnError: false,
    });
}

// Default logger instance
export const logger = createLogger(
    process.env.MCP_LOGS_DIR,
    process.env.MCP_LOG_LEVEL || "info"
);

export default logger;
