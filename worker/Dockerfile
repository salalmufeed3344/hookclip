FROM python:3.12-slim

# System deps:
# - ffmpeg: the video backbone (render + audio extraction + auto-editor +
#   whisperx's audio decoding, which shells out to the ffmpeg CLI).
# - nodejs + npm + chromium: the Remotion caption renderer
#   (remotion/render -> headless Chromium). Remotion always passes
#   --no-sandbox itself, so running as root in the container is fine.
# - fonts-dejavu-core + fonts-liberation: what Chromium renders the
#   Remotion captions with (DejaVu Sans is the caption font).
# - libsndfile1: torchaudio's soundfile backend (used by pyannote's audio
#   loading now that torchcodec is deliberately not installed — see
#   requirements.txt for why).
# - curl + unzip: fetch the NLTK tokenizer data WhisperX's alignment step
#   needs (nltk's own downloader is unreliable through proxies; curl is
#   not). NLTK 3.10+ REFUSES to load data from a group/world-writable
#   directory, so the data dir is chmodded go-w after extraction.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg nodejs npm chromium fonts-dejavu-core fonts-liberation libsndfile1 \
    curl unzip \
    && rm -rf /var/lib/apt/lists/*

# NLTK tokenizer data for WhisperX alignment (whisperx/alignment.py calls
# nltk.sent_tokenize; without this, transcribe_whisperx raises a
# LookupError and the job falls back to faster-whisper tiny).
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN mkdir -p $NLTK_DATA/tokenizers \
    && curl -sL --max-time 120 -o /tmp/punkt.zip https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip \
    && curl -sL --max-time 120 -o /tmp/punkt_tab.zip https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt_tab.zip \
    && unzip -o -q /tmp/punkt.zip -d $NLTK_DATA/tokenizers \
    && unzip -o -q /tmp/punkt_tab.zip -d $NLTK_DATA/tokenizers \
    && rm -f /tmp/punkt.zip /tmp/punkt_tab.zip \
    && chmod -R go-w $NLTK_DATA

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# Remotion project (animated captions). The lockfile pins the exact
# versions; typescript is a runtime dependency here (the .tsx sources
# are transpiled at render time), so --omit=dev is safe.
COPY remotion/package.json remotion/package-lock.json ./remotion/
RUN cd remotion && npm ci --omit=dev --no-audit --no-fund
COPY remotion/src remotion/remotion.config.ts remotion/tsconfig.json ./remotion/

# Persistent volume for the SQLite DB, sources, and clips.
VOLUME ["/data"]
ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1
# Chromium for Remotion. Playwright's cached browser is only available
# locally; in the image, use the apt-installed one.
ENV REMOTION_CHROMIUM_PATH=/usr/bin/chromium

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
