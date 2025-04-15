#!/bin/bash

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "Error: ImageMagick is not installed. Please install it first."
    echo "On macOS: brew install imagemagick"
    echo "On Ubuntu: sudo apt-get install imagemagick"
    exit 1
fi

# Set source logo path
SOURCE_LOGO="app/static/images/SGKlogo.png"

# Check if source logo exists
if [ ! -f "$SOURCE_LOGO" ]; then
    echo "Error: Source logo not found at $SOURCE_LOGO"
    exit 1
fi

# Create icons directory if it doesn't exist
mkdir -p app/static/images/icons

# Generate PWA icons in different sizes
echo "Generating PWA icons from $SOURCE_LOGO..."

# Standard icons
convert "$SOURCE_LOGO" -resize 72x72 app/static/images/icons/icon-72x72.png
convert "$SOURCE_LOGO" -resize 96x96 app/static/images/icons/icon-96x96.png
convert "$SOURCE_LOGO" -resize 128x128 app/static/images/icons/icon-128x128.png
convert "$SOURCE_LOGO" -resize 144x144 app/static/images/icons/icon-144x144.png
convert "$SOURCE_LOGO" -resize 152x152 app/static/images/icons/icon-152x152.png
convert "$SOURCE_LOGO" -resize 192x192 app/static/images/icons/icon-192x192.png
convert "$SOURCE_LOGO" -resize 384x384 app/static/images/icons/icon-384x384.png
convert "$SOURCE_LOGO" -resize 512x512 app/static/images/icons/icon-512x512.png

# Create maskable icon (with padding)
convert "$SOURCE_LOGO" -resize 196x196 -background white -gravity center -extent 196x196 app/static/images/icons/maskable-icon.png

# iOS splash screens
convert "$SOURCE_LOGO" -resize 320x320 -background white -gravity center -extent 640x1136 app/static/images/icons/splash-640x1136.png
convert "$SOURCE_LOGO" -resize 375x375 -background white -gravity center -extent 750x1334 app/static/images/icons/splash-750x1334.png
convert "$SOURCE_LOGO" -resize 414x414 -background white -gravity center -extent 1242x2208 app/static/images/icons/splash-1242x2208.png
convert "$SOURCE_LOGO" -resize 375x375 -background white -gravity center -extent 1125x2436 app/static/images/icons/splash-1125x2436.png
convert "$SOURCE_LOGO" -resize 768x768 -background white -gravity center -extent 1536x2048 app/static/images/icons/splash-1536x2048.png
convert "$SOURCE_LOGO" -resize 834x834 -background white -gravity center -extent 1668x2224 app/static/images/icons/splash-1668x2224.png
convert "$SOURCE_LOGO" -resize 1024x1024 -background white -gravity center -extent 2048x2732 app/static/images/icons/splash-2048x2732.png

# Create screenshots directory
mkdir -p app/static/images/screenshots

# Create a placeholder screenshot
convert -size 1280x720 -background white -gravity center -pointsize 36 \
    -fill black label:"SGK Global Shipping Dashboard" app/static/images/screenshots/dashboard.png

echo "PWA icons and splash screens generated successfully!"
echo "You may need to install ImageMagick and run this script to generate the actual icons." 