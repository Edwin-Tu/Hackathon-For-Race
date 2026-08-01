# ---- Build stage ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build   # 產生 .next (Next.js 靜態產出) 或 .next folder

# ---- Production stage ----
FROM nginx:stable-alpine
COPY --from=builder /app/.next /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
