"""app.html（Artifact 用の本体）を GitHub Pages 用の index.html へ包む。"""
from pathlib import Path

here = Path(__file__).parent
body = (here / "app.html").read_text(encoding="utf-8")
head_end = body.index("</style>") + len("</style>")
html = (
    "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
    + body[:head_end]
    + "\n</head>\n<body>\n"
    + body[head_end:]
    + "\n</body>\n</html>\n"
)
(here / "index.html").write_text(html, encoding="utf-8")
print("index.html", len(html), "bytes")
