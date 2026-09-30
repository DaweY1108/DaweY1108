"""Generates dist/meme.svg: a random r/ProgrammerHumor meme, or a programming joke card as fallback."""
import base64, io, json, os, sys, textwrap, urllib.request
from xml.sax.saxutils import escape

UA = {"User-Agent": "Mozilla/5.0 (github-profile-meme-bot)"}
OUT = "dist/meme.svg"
os.makedirs("dist", exist_ok=True)


def get(url, timeout=20):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def try_reddit_meme():
    from PIL import Image
    for attempt in range(8):
        try:
            data = json.loads(get("https://meme-api.com/gimme/ProgrammerHumor"))
        except Exception as e:
            print(f"meme-api attempt {attempt + 1} failed: {e}")
            continue
        url = data.get("url", "")
        if data.get("nsfw") or data.get("spoiler") or not url.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        try:
            img = Image.open(io.BytesIO(get(url))).convert("RGB")
        except Exception as e:
            print(f"image download failed: {e}")
            continue
        img.thumbnail((600, 900))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        w, h = img.size
        print(f"Meme: {url} — {data.get('title')}")
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
                f'<image width="{w}" height="{h}" href="data:image/jpeg;base64,{b64}"/></svg>')
    return None


def joke_card():
    j = json.loads(get("https://v2.jokeapi.dev/joke/Programming?safe-mode"))
    parts = [j["joke"]] if j.get("type") == "single" else [j["setup"], "", j["delivery"]]
    lines = []  # (text, color) — the punchline is cyan
    for i, p in enumerate(parts):
        color = "#06b6d4" if len(parts) > 1 and i == len(parts) - 1 else "#e5e7eb"
        lines += [(t, color) for t in (textwrap.wrap(p, 46) or [""])]
    w, lh, top = 520, 26, 64
    h = top + len(lines) * lh + 36
    texts = "".join(
        f'<text x="32" y="{top + i * lh}" font-size="17" fill="{c}">{escape(t)}</text>'
        for i, (t, c) in enumerate(lines))
    print("Fallback joke:", " / ".join(parts))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="JetBrains Mono, Consolas, monospace">'
            f'<rect width="{w}" height="{h}" rx="14" fill="#0d1117" stroke="#a855f7" stroke-width="2"/>'
            f'<text x="32" y="36" font-size="14" fill="#a855f7" font-weight="bold">// joke.of_the_day()</text>'
            f'{texts}</svg>')


svg = None
try:
    svg = try_reddit_meme()
except Exception as e:
    print("Reddit meme failed:", e)
if not svg:
    try:
        svg = joke_card()
    except Exception as e:
        print("Joke fallback failed:", e)
if not svg:
    try:
        svg = get(f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/output/meme.svg").decode()
        print("Kept previous meme")
    except Exception as e:
        print("No meme available:", e)
        sys.exit(0)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
