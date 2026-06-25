from __future__ import annotations

from .config import SECTIONS, SITE_DIR
from .dashboard import build_html
from .payload import build_section_payload
from .team_pages import write_team_pages


def main() -> None:
    payload = [build_section_payload(section) for section in SECTIONS]
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    index_path = SITE_DIR / "index.html"
    index_path.write_text(build_html(payload), encoding="utf-8")
    print(f"Saved: {index_path}")
    write_team_pages()
    print("Saved team pages")
