# === Stage 1: Build React App ===
FROM node:16-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build production React app
RUN npm run build

# === Stage 2: Serve dengan Nginx ===
FROM nginx:alpine

# Copy build hasil dari stage 1
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80 (default nginx)
EXPOSE 80

# Nginx jalan otomatis (default CMD dari nginx image)
CMD ["nginx", "-g", "daemon off;"]