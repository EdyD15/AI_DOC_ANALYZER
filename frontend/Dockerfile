# --- Build stage ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Backend URL baked into the static build (e.g. https://aidocanalyzer-production.up.railway.app)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Serve stage ---
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Templated config: the base image's entrypoint runs envsubst on
# *.template files, substituting ${PORT} before nginx starts.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Railway sets $PORT at runtime; default to 80 for local/Docker Compose use.
ENV PORT=80
EXPOSE 80
