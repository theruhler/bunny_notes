# Bunny Notes iPhone Web App

This folder contains a touch-first web app version of Bunny Notes that runs well on iPhone Safari and can be added to the home screen.

When deployed with GitHub Pages, the app can be opened directly from the hosted URL and reinstalled later without your computer running.

## Run locally

From the Bunny_Notes project root:

```bash
python3 -m http.server 8080
```

Open:

- http://localhost:8080/iphone-web/

On iPhone (same Wi-Fi):

- http://YOUR_COMPUTER_IP:8080/iphone-web/

## Install on iPhone home screen

1. Open the app URL in Safari.
2. Tap Share.
3. Tap Add to Home Screen.

## Notes

- Swipe left and right to move between messages.
- Tap the bunny or message to get a new note.
- Use New Bunny to shuffle artwork.
- Settings screen includes font size, signature toggle, and theme color.
- App supports a simple local PIN lock on startup.

## Do I need to keep a server running?

- You need a server for initial load/install and for updates.
- After loading once, the app can run offline from the home screen via cached assets.
- iPhone may clear site data occasionally, which would require loading from a server again.

If you do not want your computer running a server, host this folder on a static site (for example GitHub Pages or Cloudflare Pages), then install from that URL once.

## GitHub Pages deployment

This repository includes a GitHub Actions workflow at [.github/workflows/pages.yml](../.github/workflows/pages.yml) that publishes the iPhone app automatically on every push to `main`.

Deployment flow:

- Source files stay in `iphone-web/`
- The workflow copies `iphone-web/`, `bunny1.png`, and `assets/` into the published Pages site
- Your phone can reinstall or refresh from the GitHub Pages URL at any time

Important privacy note:

- Standard GitHub Pages sites are typically publicly reachable by URL even if the source repository is private, unless your GitHub plan provides private Pages access.
