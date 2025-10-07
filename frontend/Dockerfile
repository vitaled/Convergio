# Frontend Dockerfile for Convergio
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Install dependencies first for better caching
COPY package*.json ./
RUN npm ci --only=production=false

# Copy the rest of the application
COPY . .

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S svelte -u 1001
RUN chown -R svelte:nodejs /app
USER svelte

# Expose the port
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:4000 || exit 1

# Start the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "4000"]