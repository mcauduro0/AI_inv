# =============================================================================
# Frontend Application Dockerfile
# =============================================================================

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN npm install -g pnpm && pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN pnpm build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Install serve for static file serving
RUN npm install -g serve

# Copy built files
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Run the application
CMD ["serve", "-s", "dist", "-l", "3000"]
