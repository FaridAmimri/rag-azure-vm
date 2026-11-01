# Dockerfile - Image of the web interface (Next.js standalone server)
#
# Build (from the web/ folder):
#   docker build -t rag-azure-vm-web .
# Run (RAG_API_URL and RAG_API_KEY are given at run time, never copied into the image):
#   docker run --rm -p 3000:3000 --env-file .env.local rag-azure-vm-web

# Stage 1: install all the dependencies and build the app
FROM node:26-slim AS build

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

# Dependencies first: Docker caches this layer and reuses it
# as long as package-lock.json does not change
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: final image, only the standalone output (no source, no dev dependencies)
FROM node:26-slim

# HOSTNAME=0.0.0.0: listen on all interfaces, needed to be reachable from outside the container
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

# server.js does not copy public/ and .next/static/: they must be added by hand
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/public ./public
COPY --from=build --chown=node:node /app/.next/static ./.next/static

# Run as a non-root user: "node" already exists in the official image
USER node

EXPOSE 3000

CMD ["node", "server.js"]
