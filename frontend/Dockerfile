# ── Phase 1: Builder ──
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (caching layer)
COPY package*.json ./
RUN npm ci

# Copy source and build the optimized production app
COPY . .
RUN npm run build

# ── Phase 2: Production Server ──
FROM nginx:stable-alpine

# Copy the build output to Nginx's default public directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the standard HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
