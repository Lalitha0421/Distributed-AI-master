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

# Expose the standard HTTP port
EXPOSE 80

# Use a custom Nginx config to handle React Router if needed
# (Optional: If you add routing later, we can add a custom nginx.conf)
CMD ["nginx", "-g", "daemon off;"]
