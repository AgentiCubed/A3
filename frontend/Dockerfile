# Frontend dev image. Production builds use `next build` + `next start`; this
# image targets the compose dev workflow (hot reload via mounted volume).
FROM node:22-alpine

WORKDIR /app

# Install deps first for layer caching.
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
