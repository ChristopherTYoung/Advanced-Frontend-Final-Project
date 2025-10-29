# Multi-stage Dockerfile for the Vite `web_controller` app
#  - Build step uses Node + pnpm to produce `dist`
#  - Production step serves the static site with nginx

### Build stage
FROM node:18-alpine AS build
WORKDIR /app

# Enable corepack and prepare pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package manifest(s) first for better caching
COPY package.json pnpm-lock.yaml* ./

# Install dependencies (falls back to non-locked install if lock missing)
RUN if [ -f pnpm-lock.yaml ]; then pnpm install --frozen-lockfile --prefer-offline; else pnpm install; fi

# Copy source and run build
COPY . .
RUN pnpm build

### Production stage
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Optionally expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
