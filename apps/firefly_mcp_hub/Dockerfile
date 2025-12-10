# Adobe Firefly MCP Hub - Multi-stage Docker Build
#
# Build: docker build -t firefly-mcp-hub .
# Run:   docker run -e FIREFLY_CLIENT_ID=xxx -e FIREFLY_CLIENT_SECRET=yyy firefly-mcp-hub

# ============================================
# Stage 1: Build
# ============================================
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev)
RUN npm ci

# Copy source code
COPY tsconfig.json ./
COPY src/ ./src/

# Build TypeScript
RUN npm run build

# ============================================
# Stage 2: Production Runtime
# ============================================
FROM node:22-alpine AS runtime

# Security: Run as non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser

WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app/logs

# Copy package files
COPY package.json package-lock.json* ./

# Install production dependencies only
RUN npm ci --omit=dev && npm cache clean --force

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Environment configuration
ENV NODE_ENV=production
ENV MCP_TRANSPORT=stdio
ENV MCP_LOGS_DIR=/app/logs

# Health check for HTTP mode
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD [ "node", "-e", "require('http').get('http://localhost:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))" ] || exit 0

# Default command
ENTRYPOINT ["node", "dist/index.js"]
