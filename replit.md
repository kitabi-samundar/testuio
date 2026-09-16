# Icecast Radio Backends

A production-grade internet radio backend that streams YouTube audio directly to a local Icecast server via FFmpeg — zero downloads, all in memory.

## Run & Operate

- `bash start-replit.sh` — start Icecast (port 8000) and the FastAPI backend (port 5000)
- The workflow `Start application` is configured to run the same command automatically
- API docs: `https://<your-replit-domain>/docs`
- Icecast admin/status: `http://localhost:8000/status.xsl`

## Stack

- Python 3.12 + FastAPI + Uvicorn
- Pydantic Settings for env-driven configuration
- FFmpeg (libmp3lame) → local Icecast mount `/stream`
- yt-dlp for in-memory URL extraction
- AutoDJ, user request queue, watchdog, metadata updates

## Where things live

- `main.py` — FastAPI app and lifespan startup
- `app/` — radio backend modules
- `icecast-replit.xml` — Icecast configuration tuned for Replit
- `start-replit.sh` — Replit run script
- `requirements.txt` — Python dependencies

## Configuration

Managed through Replit environment variables (shared). Required/sensitive:

- `ICECAST_PASSWORD` — source password (stored as a Replit Secret)
- `YOUTUBE_COOKIES` — raw Netscape-format `cookies.txt` contents (stored as a Replit Secret)

Other non-secret vars are set in Replit env, including `ICECAST_HOST`, `ICECAST_PORT`, `ICECAST_MOUNT`, `AUTODJ_PLAYLISTS`, `AUDIO_BITRATE`, etc. See `.env.example` in the source for the full list.

## User preferences

- None yet — populate here as the user gives explicit guidance.

## YouTube cookies

YouTube playback uses the raw Netscape-format cookie export stored in the
`YOUTUBE_COOKIES` secret. OAuth2 authentication is not used by the application.
Restart the service after updating the secret.

## iOS / Safari stream

iOS AVFoundation cannot use the Icecast ICY protocol on port 8000. A `/stream` proxy endpoint is available on the FastAPI port (5000) that re-serves the MP3 bytes over plain HTTP with standard headers. Use that URL for mobile listeners.

## Gotchas

- Icecast XML and the FastAPI backend both expect the same `ICECAST_PASSWORD`. If you change one, change the other and restart the workflow.
- The iOS-friendly stream mount was added to `icecast-replit.xml` with a larger `burst-size` and `client-timeout` to reduce rebuffering on mobile networks.
- YouTube cookies can be supplied directly via the `YOUTUBE_COOKIES` secret using the raw Netscape `cookies.txt` contents. `YOUTUBE_COOKIES_B64` remains supported for compatibility.

## Streaming flow

`POST /play` accepts either a YouTube URL or a search query. yt-dlp resolves
the source without downloading it, keeps the source request headers with the
queued track, and FFmpeg opens the direct URL with those headers using
real-time decoding and reconnect options. FFmpeg decodes each track to PCM;
the persistent encoder transcodes that PCM to MP3 and keeps one Icecast
connection open across track changes. AutoDJ repeats configured playlist URLs
and falls back to a short generated silence track when a source is temporarily
unavailable.

## Pointers

- See `radio-backend/README.md` (original) for full API documentation and troubleshooting.
