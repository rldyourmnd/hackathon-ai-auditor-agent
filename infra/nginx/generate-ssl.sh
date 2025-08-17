#!/bin/sh
set -e

SSL_DIR="/etc/nginx/ssl"
mkdir -p "$SSL_DIR"

if [ -f "$SSL_DIR/nginx.crt" ] && [ -f "$SSL_DIR/nginx.key" ]; then
  echo "SSL already exists at $SSL_DIR"
  exit 0
fi

echo "Generating self-signed SSL certificate for development..."
# Generate private key and cert
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$SSL_DIR/nginx.key" \
  -out "$SSL_DIR/nginx.crt" \
  -subj "/CN=localhost"

chmod 600 "$SSL_DIR/nginx.key"
chmod 644 "$SSL_DIR/nginx.crt"

echo "SSL certificate generated successfully!"
