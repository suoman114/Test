# --- deps: 의존성 설치 ---
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# --- builder: Next.js 빌드 (standalone) ---
FROM node:20-slim AS builder
WORKDIR /app
# 브라우저 번들에 박히는 공개 API 주소. 리버스 프록시 사용 시 "" (상대경로).
ARG NEXT_PUBLIC_API_BASE=""
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- runner: 런타임 ---
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
# 서버 컴포넌트가 컨테이너 네트워크에서 백엔드를 찾는 기본 주소 (compose 에서 덮어씀).
ENV INTERNAL_API_BASE=http://backend:8000
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
