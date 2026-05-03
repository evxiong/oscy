# syntax=docker/dockerfile:1

FROM node:22-slim AS base


# Install dependencies
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci


# Build app
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG BUILD_LOCAL_API_HOST

RUN --mount=type=secret,id=build_env \
    set -a && \
    . /run/secrets/build_env && \
    set +a && \
    export LOCAL_API_HOST="${BUILD_LOCAL_API_HOST}" && \
    npm run build


# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

# Force ISR for static segments by deleting HTML generated at build time
# https://github.com/vercel/next.js/discussions/46544
RUN rm ./.next/server/app/*.html

USER node

EXPOSE 3000

CMD ["node", "server.js"]