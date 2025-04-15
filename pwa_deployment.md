# SGK Export Progressive Web App (PWA) Documentation

This document explains how the Progressive Web App (PWA) features were implemented and how to maintain them.

## What is a PWA?

A Progressive Web App is a web application that can be installed on user devices and offers some native app-like features:

- Works offline or with poor network connectivity
- Can be installed on home screens
- Loads quickly and reliably
- Sends push notifications (if implemented)

## Implementation Details

The SGK Export app has been enhanced with the following PWA features:

1. **Web App Manifest**: Located at `app/static/manifest.json`, defines how the app appears when installed.
2. **Service Worker**: Located at `app/static/sw.js`, handles caching and offline functionality.
3. **Install Prompt**: Code in `app/static/js/main.js` that shows an install banner to users.
4. **Offline Page**: A dedicated page shown when the app is used offline (`app/templates/offline.html`).
5. **PWA Icons**: Various sizes of app icons for different devices and contexts.

## Getting Started with the PWA Features

### 1. Generating Icons

We've included a script to generate all necessary PWA icons from your logo:

```bash
# Make the script executable (if not already)
chmod +x create_pwa_icons.sh

# Run the script
./create_pwa_icons.sh
```

This script requires ImageMagick to be installed on your system. If not already installed:

- macOS: `brew install imagemagick`
- Ubuntu: `sudo apt-get install imagemagick`

### 2. Testing PWA Features

To test PWA features, you need to access the app via HTTPS or localhost, as service workers only work in these environments for security reasons.

1. Run the app locally:
   ```bash
   python app.py
   ```

2. Open Chrome DevTools (F12) and go to the "Application" tab.
3. Under "Application" you'll find sections for "Manifest", "Service Workers", and "Storage".
4. Check that the manifest is loaded correctly and the service worker is registered.

### 3. Testing Offline Functionality

1. In Chrome DevTools, go to the "Network" tab.
2. Check the "Offline" checkbox to simulate being offline.
3. Reload the page - you should see the offline page or cached content instead of a network error.

## Maintenance and Updates

### Updating the Service Worker

When you make changes to your app that should be available offline, update the `CACHE_NAME` constant in `sw.js`:

```javascript
const CACHE_NAME = 'sgk-cache-v2'; // Increment version number
```

This will trigger a new cache to be created and the old one to be deleted.

### Updating the Manifest

If you need to change how the installed app appears (name, colors, etc.), edit `app/static/manifest.json`.

### Updating Icons

If you update your app logo, run the icon generation script again to update all sizes.

## Additional Resources

- [Web App Manifest Documentation](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Service Workers Documentation](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Google's PWA Checklist](https://web.dev/pwa-checklist/)
- [Lighthouse Tool](https://developers.google.com/web/tools/lighthouse) - For auditing PWA compliance

## Troubleshooting

### Service Worker Not Updating

If changes to your service worker don't seem to be taking effect:

1. In Chrome DevTools > Application > Service Workers, click "Unregister" 
2. Reload the page
3. Clear site data in Chrome DevTools > Application > Clear Storage

### Manifest Not Loading

If the manifest isn't being detected:

1. Check that the MIME type is correct (`application/manifest+json`)
2. Verify the path in the `<link>` tag in `base.html`
3. Make sure the manifest is valid JSON 