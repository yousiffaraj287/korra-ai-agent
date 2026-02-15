# ============================================================
# DOCKERFILE FOR KORRA FRONTEND (NEXT.JS UI)
# ============================================================
# File: Dockerfile.frontend
# Author: Yousif Faraj
# Email: yfaraj0454@sdsu.edu
# Course: COMPE 475 – Microprocessors
# Institution: San Diego State University
# Module: 06 - Korra - Tools, MCP Server and User Interface
# Section: 9 - Full Stack Containerization
# Date Created: October 21, 2025
# Version: 1.0
#
# Description:
#     Dockerfile for building and running the Korra Next.js frontend
#     used for LangGraph’s Agent Chat UI interface.
#
#     Key features:
#         • Multi-stage build for optimized image size
#         • Uses Node.js 20 Alpine for lightweight performance
#         • Integrates API URL build argument for backend connection
#         • Production-ready configuration on port 3000
#         • Compatible with docker-compose networking
#
# Build:
#     docker build -t korra-frontend -f Dockerfile.frontend .
#
# Run:
#     docker run -p 3000:3000 korra-frontend
#
# Usage with Docker Compose:
#     See docker-compose.yml in project root
# ============================================================

# ============================================================
# BUILD STAGE
# ============================================================
# Use Node.js 20 Alpine base image (smaller)
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install pnpm (package manager)
# pnpm is required for installing dependencies efficiently with caching support.
RUN npm install -g pnpm

# Copy package files
# Copy only dependency manifests first to leverage Docker layer caching.
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
# Installs exactly the versions listed in pnpm-lock.yaml for consistent builds.
RUN pnpm install --frozen-lockfile

# Copy source code
# Copies all remaining project files into the container workspace.
COPY . .

# Build argument for API URL (can be overridden)
# Allows the frontend to dynamically connect to backend (port 2024) during container builds.
ARG NEXT_PUBLIC_API_URL=http://localhost:2024
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build the Next.js application for production
# Compiles and optimizes static assets for the final container.
RUN pnpm build

# ============================================================
# PRODUCTION STAGE
# ============================================================
# Use another small Node.js Alpine image for serving built app
FROM node:20-alpine AS runner

# Set working directory
WORKDIR /app

# Install pnpm in production stage
# pnpm is installed again for managing any runtime dependencies.
RUN npm install -g pnpm

# Copy built application from builder stage
# Copies compiled Next.js artifacts only, minimizing image size.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./

# Expose Next.js port
# Port 3000 is the default for Next.js; it matches the docker-compose service mapping.
EXPOSE 3000

# Set production environment variables
# NODE_ENV ensures Next.js runs optimized; HOSTNAME 0.0.0.0 makes it accessible externally.
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start Next.js server
# server.js launches the built app inside the container (entry point of Next.js).
CMD ["node", "server.js"]
