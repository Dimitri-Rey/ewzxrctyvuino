FROM nginx:alpine

# Copy frontend files
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY app.js /usr/share/nginx/html/

# Expose port
EXPOSE 80

# Nginx will start automatically
