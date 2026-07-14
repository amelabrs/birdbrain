# Publishing BirdBrain to Google Play Store

BirdBrain is a PWA (Progressive Web App). The Play Store path uses a **Trusted Web Activity (TWA)** — a native Android shell that loads your HTTPS URL. The tool is **PWABuilder** (free, by Microsoft).

---

## Prerequisites

- [ ] Google Play Developer account — one-time $25 fee at [play.google.com/console](https://play.google.com/console)
- [ ] BirdBrain live at its Render HTTPS URL
- [ ] `/.well-known/assetlinks.json` served by the app (already set up — see below)

---

## What's already done in this repo

| What | Where |
|------|-------|
| Manifest served at `/manifest.json` | `backend/app.py` → `GET /manifest.json` |
| Digital Asset Links served at `/.well-known/assetlinks.json` | `backend/app.py` → `GET /.well-known/assetlinks.json` |
| Asset links file with signing fingerprint | `frontend/assetlinks.json` |
| PNG icons (192×192 and 512×512) | `frontend/icon-192.png`, `frontend/icon-512.png` |

---

## Steps to regenerate the Android package (e.g. after an update)

### 1. Wake up Render

The free tier sleeps after 15 minutes of inactivity. PWABuilder will time out if the app is asleep.

Open `https://birdbrain-m6mk.onrender.com` in a browser and wait for it to fully load before proceeding.

### 2. Run PWABuilder

1. Go to [pwabuilder.com](https://pwabuilder.com)
2. Enter `https://birdbrain-m6mk.onrender.com`
3. Click **Start** — it will scan the manifest and service worker
4. Click **Package for Stores** → **Android**
5. Leave all settings at their defaults and click **Generate Package**
6. Wait ~45 seconds for the build to complete, then download the zip

### 3. What's in the zip

| File | Purpose |
|------|---------|
| `app-release-signed.aab` | Upload this to Google Play Console |
| `app-release-signed.apk` | Install this on your phone to test |
| `assetlinks.json` | Digital Asset Links — paste into repo if fingerprint changes |
| `signing-key-info.txt` | **Keep this safe.** Needed to sign future updates. |

> **Important:** Store `signing-key-info.txt` somewhere safe (not in the repo). If you lose the signing key you cannot update the app on Play Store.

### 4. Update assetlinks.json (only if fingerprint changed)

If you generated a new signing key, open `assetlinks.json` from the zip and replace the contents of `frontend/assetlinks.json` in this repo. Then push to GitHub — Render will redeploy automatically.

Verify it's live at: `https://birdbrain-m6mk.onrender.com/.well-known/assetlinks.json`

### 5. Test the APK on your phone

1. Transfer `app-release-signed.apk` to your Android phone (email, AirDrop, USB cable)
2. Open the file on your phone → you'll be prompted to allow "Install from unknown sources" once
3. Install and open the app
4. **It should open with no browser URL bar.** That's the TWA working correctly.
5. If a URL bar is visible, `assetlinks.json` isn't live yet — wait a few minutes and try again

---

## Submitting to Google Play Console

1. Go to [play.google.com/console](https://play.google.com/console) → **Create app**
2. Fill in:
   - **App name**: BirdBrain — Karnataka Birds
   - **Default language**: English
   - **App or game**: App
   - **Free or paid**: Free
3. Complete the store listing:
   - Short description (max 80 chars): *Spaced repetition bird ID quiz for Karnataka, India*
   - Full description: describe the Leitner box system, the 43 Karnataka birds, offline support
   - Screenshots: at least 2 phone screenshots (minimum 320px on shorter side)
   - Feature graphic: 1024×500px banner image
   - Icon: 512×512px PNG (use `icon-512.png`)
4. Upload the bundle: **Release** → **Production** → **Create new release** → upload `app-release-signed.aab`
5. Fill in content rating questionnaire (Education / General audience)
6. Set up pricing & distribution (Free, India at minimum)
7. Submit for review — typically takes 1–3 days for a new app

---

## Current package details

| Field | Value |
|-------|-------|
| Package name | `com.onrender.birdbrain_m6mk.twa` |
| SHA-256 fingerprint | `AF:D7:79:91:67:66:E6:D3:06:7B:D3:95:35:56:7D:C9:5C:C0:0D:61:DF:FE:2D:46:60:EA:A1:72:01:B0:AF:55` |
| Signing key generated | 2026-07-14 via PWABuilder |

---

## Troubleshooting

**PWABuilder says "manifest not found"**
The Render app was asleep. Visit the Render URL first, wait for it to load, then retry PWABuilder.

**App shows a browser URL bar after install**
`/.well-known/assetlinks.json` isn't reachable or has the wrong fingerprint. Check that `https://birdbrain-m6mk.onrender.com/.well-known/assetlinks.json` returns the correct JSON. Wait for Render to finish deploying after any push.

**Play Console rejects the AAB**
Make sure you're uploading the `.aab` file (App Bundle), not the `.apk`. Play Store requires AAB for new apps.
