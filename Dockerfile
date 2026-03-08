# ---------- Build Stage ----------
FROM node:18-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

# We use ARG to allow passing the AWS Public IP for the API URL during build time
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV GENERATE_SOURCEMAP=false
ENV NODE_OPTIONS=--max_old_space_size=512

RUN npm run build

# ---------- Serve Stage ----------
FROM nginx:alpine

# Copy built react files to nginx html serving directory
COPY --from=build /app/build /usr/share/nginx/html

# Overwrite default nginx config to support React client-side routing
RUN echo "server { listen 80; root /usr/share/nginx/html; index index.html; location / { try_files \$uri \$uri/ /index.html; } }" > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
