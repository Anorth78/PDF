import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("Missing dependency: pypdf")
    print("Run: python -m pip install -r requirements.txt")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "config.json"
PDF_OUTPUT = ROOT / "pdfs"
TEXT_OUTPUT = ROOT / "text"
LIBRARY_JSON = ROOT / "library.json"
AI_TXT = ROOT / "ai.txt"
INDEX_HTML = ROOT / "index.html"
LLMS_TXT = ROOT / "llms.txt"
ROBOTS_TXT = ROOT / "robots.txt"
SITEMAP_XML = ROOT / "sitemap.xml"
API_DIR = ROOT / "api"
API_LIBRARY_JSON = API_DIR / "documents.json"


def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def slugify(name):
    value = Path(name).stem.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "document"


def unique_slug(slug, used):
    if slug not in used:
        used.add(slug)
        return slug

    i = 2
    while f"{slug}-{i}" in used:
        i += 1

    result = f"{slug}-{i}"
    used.add(result)
    return result


def title_from_filename(path):
    return Path(path).stem.replace("_", " ").replace("-", " ").strip()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pdf_text(pdf_path):
    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                text = f"[Text extraction failed on page {page_number}: {exc}]"
            pages.append(f"\n--- PAGE {page_number} ---\n{text.strip()}")
        return "\n".join(pages).strip(), len(reader.pages), None
    except Exception as exc:
        return "", 0, str(exc)


def remove_generated_contents():
    PDF_OUTPUT.mkdir(exist_ok=True)
    TEXT_OUTPUT.mkdir(exist_ok=True)

    for folder in (PDF_OUTPUT, TEXT_OUTPUT):
        for item in folder.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)


def find_pdfs(source, include_subfolders):
    if include_subfolders:
        return sorted(
            [p for p in source.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"],
            key=lambda p: str(p).lower()
        )
    return sorted(
        [p for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"],
        key=lambda p: p.name.lower()
    )


def build_library(source, config):
    remove_generated_contents()

    source_pdfs = find_pdfs(source, config.get("include_subfolders", True))
    used_slugs = set()
    documents = []

    for source_pdf in source_pdfs:
        relative = source_pdf.relative_to(source)
        base_slug = slugify(source_pdf.name)
        slug = unique_slug(base_slug, used_slugs)

        destination_pdf = PDF_OUTPUT / f"{slug}.pdf"
        destination_txt = TEXT_OUTPUT / f"{slug}.txt"

        shutil.copy2(source_pdf, destination_pdf)

        extracted, page_count, extraction_error = extract_pdf_text(source_pdf)
        destination_txt.write_text(extracted, encoding="utf-8")

        stat = source_pdf.stat()

        documents.append({
            "id": slug,
            "title": title_from_filename(source_pdf.name),
            "original_filename": source_pdf.name,
            "source_relative_path": str(relative).replace("\\", "/"),
            "pdf_url": f"pdfs/{slug}.pdf",
            "text_url": f"text/{slug}.txt",
            "type": "PDF",
            "pages": page_count,
            "bytes": stat.st_size,
            "sha256": sha256_file(source_pdf),
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
            "text_extraction": {
                "success": extraction_error is None,
                "error": extraction_error
            }
        })

        print(f"  Added: {relative}")

    generated = datetime.now(timezone.utc).isoformat()

    library = {
        "schema_version": "1.0",
        "name": config.get("site_name", "PDF Knowledge Library"),
        "description": config.get(
            "site_description",
            "A searchable collection of PDF knowledge resources."
        ),
        "owner": config.get("owner_name", ""),
        "site_url": config.get("site_url", "").rstrip("/"),
        "generated": generated,
        "document_count": len(documents),
        "documents": documents
    }

    LIBRARY_JSON.write_text(
        json.dumps(library, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    create_ai_txt(library)
    create_llms_txt(library)
    create_sitemap(library)
    create_html(library)

    return library


def create_ai_txt(library):
    lines = [
        f"# {library['name']}",
        "",
        library["description"],
        "",
        "This is a machine-readable document catalogue.",
        "Use library.json for structured metadata.",
        "Use the linked text_url for extracted document text.",
        "Use the linked pdf_url for the original PDF.",
        "",
        f"Document count: {library['document_count']}",
        f"Generated: {library['generated']}",
        "",
        "## Documents",
        ""
    ]

    for doc in library["documents"]:
        lines.extend([
            f"### {doc['title']}",
            f"- ID: {doc['id']}",
            f"- Original filename: {doc['original_filename']}",
            f"- PDF: {doc['pdf_url']}",
            f"- Extracted text: {doc['text_url']}",
            f"- Pages: {doc['pages']}",
            ""
        ])

    AI_TXT.write_text("\n".join(lines), encoding="utf-8")


def create_llms_txt(library):
    base = library.get("site_url", "").rstrip("/")
    def absolute(path):
        return f"{base}/{path}" if base else path

    lines = [
        f"# {library['name']}",
        "",
        library["description"],
        "",
        "This site is an AI-readable PDF knowledge base.",
        "START HERE: use library.json (or api/documents.json) to enumerate every document.",
        "Do not rely on search-engine indexing or directory browsing.",
        "For each document, fetch its extracted text_url for searchable text; use pdf_url for the original PDF.",
        "",
        f"Document count: {library['document_count']}",
        "",
        "## Machine-readable resources",
        f"- Catalogue: {absolute('library.json')}",
        f"- API catalogue: {absolute('api/documents.json')}",
        f"- AI guide: {absolute('ai.txt')}",
        "",
        "## Documents",
        ""
    ]
    for doc in library["documents"]:
        lines.extend([
            f"### {doc['title']}",
            f"- ID: {doc['id']}",
            f"- Text: {absolute(doc['text_url'])}",
            f"- PDF: {absolute(doc['pdf_url'])}",
            ""
        ])
    LLMS_TXT.write_text("\n".join(lines), encoding="utf-8")


def create_sitemap(library):
    base = library.get("site_url", "").rstrip("/")
    if not base:
        # A relative sitemap is not useful to crawlers, but keeping the file generated
        # makes the project ready once site_url is configured.
        base = "."
    urls = [f"{base}/", f"{base}/index.html", f"{base}/library.json", f"{base}/ai.txt", f"{base}/llms.txt", f"{base}/api/documents.json"]
    for doc in library["documents"]:
        urls.extend([f"{base}/{doc['pdf_url']}", f"{base}/{doc['text_url']}"])
    body = "\n".join(f"  <url><loc>{html.escape(u)}</loc></url>" for u in urls)
    SITEMAP_XML.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + body + '\n</urlset>\n', encoding="utf-8"
    )
    ROBOTS_TXT.write_text(
        "User-agent: *\nAllow: /\n\n" + f"Sitemap: {base}/sitemap.xml\n", encoding="utf-8"
    )
    API_DIR.mkdir(exist_ok=True)
    API_LIBRARY_JSON.write_text(json.dumps(library, indent=2, ensure_ascii=False), encoding="utf-8")


def create_html(library):
    cards = []

    for doc in library["documents"]:
        title = html.escape(doc["title"])
        filename = html.escape(doc["original_filename"])
        pdf_url = html.escape(doc["pdf_url"], quote=True)
        text_url = html.escape(doc["text_url"], quote=True)

        cards.append(f"""
        <article class="card"
                 data-search="{html.escape((doc['title'] + ' ' + doc['original_filename']).lower(), quote=True)}">
          <div class="pdf-badge">PDF</div>
          <div class="card-body">
            <h2>{title}</h2>
            <p>{filename}</p>
            <div class="actions">
              <a href="{pdf_url}" target="_blank" rel="noopener">Open PDF</a>
              <a href="{text_url}" target="_blank" rel="noopener">Text</a>
            </div>
          </div>
        </article>
        """)

    repo_url = html.escape(library.get("repository_url", ""), quote=True)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(library['name'])}</title>
<meta name="description" content="{html.escape(library['description'], quote=True)}">
<link rel="alternate" type="application/json" href="library.json">
<style>
:root {{
  --bg: #f4f6f8;
  --panel: #ffffff;
  --text: #172033;
  --muted: #667085;
  --border: #dfe4ea;
  --accent: #0b5cab;
  --accent-dark: #084b8a;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Arial, Helvetica, sans-serif;
}}
header {{
  background: #111827;
  color: white;
  padding: 48px 24px;
}}
.header-inner, main, footer {{
  max-width: 1120px;
  margin: auto;
}}
h1 {{ margin: 0 0 10px; font-size: 38px; }}
.subtitle {{ color: #d1d5db; font-size: 17px; }}
main {{ padding: 34px 24px 60px; }}
.search {{
  width: 100%;
  padding: 17px 18px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 17px;
  margin-bottom: 16px;
}}
.meta {{ color: var(--muted); margin-bottom: 24px; }}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
}}
.card {{
  display: flex;
  gap: 18px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px;
}}
.pdf-badge {{
  flex: 0 0 auto;
  width: 54px;
  height: 64px;
  border-radius: 8px;
  background: #eef2f7;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 12px;
}}
.card-body {{ min-width: 0; flex: 1; }}
.card h2 {{ margin: 0 0 8px; font-size: 19px; }}
.card p {{
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  overflow-wrap: anywhere;
}}
.actions {{ margin-top: 15px; display: flex; gap: 9px; flex-wrap: wrap; }}
.actions a {{
  text-decoration: none;
  background: var(--accent);
  color: white;
  padding: 8px 12px;
  border-radius: 7px;
  font-size: 13px;
}}
.actions a:hover {{ background: var(--accent-dark); }}
#empty {{
  display: none;
  padding: 50px;
  text-align: center;
  color: var(--muted);
}}
footer {{
  padding: 25px 24px 45px;
  color: var(--muted);
  font-size: 13px;
}}
footer a {{ color: var(--accent); }}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <h1>{html.escape(library['name'])}</h1>
    <div class="subtitle">{html.escape(library['description'])}</div>
  </div>
</header>
<main>
  <input id="search" class="search" type="search"
         placeholder="Search documents..."
         aria-label="Search documents">
  <div class="meta">
    <span id="count">{library['document_count']}</span> documents
    &nbsp;·&nbsp;
    Machine-readable index:
    <a href="library.json">library.json</a>
    &nbsp;·&nbsp;
    AI guide:
    <a href="ai.txt">ai.txt</a>
  </div>
  <section id="grid" class="grid">
    {''.join(cards)}
  </section>
  <div id="empty">No documents match your search.</div>
</main>
<footer>
  Generated {html.escape(library['generated'])}.
  {" Repository: <a href='" + repo_url + "'>" + repo_url + "</a>." if repo_url else ""}
</footer>
<script>
const input = document.getElementById("search");
const cards = [...document.querySelectorAll(".card")];
const count = document.getElementById("count");
const empty = document.getElementById("empty");

input.addEventListener("input", () => {{
  const q = input.value.trim().toLowerCase();
  let visible = 0;

  cards.forEach(card => {{
    const match = !q || card.dataset.search.includes(q);
    card.style.display = match ? "flex" : "none";
    if (match) visible++;
  }});

  count.textContent = visible;
  empty.style.display = visible ? "none" : "block";
}});
</script>
</body>
</html>
"""

    INDEX_HTML.write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a GitHub Pages PDF knowledge library."
    )
    parser.add_argument(
        "--source",
        help="Override source folder from config.json."
    )
    args = parser.parse_args()

    config = load_config()

    source = Path(args.source) if args.source else Path(config["source_folder"])
    source = source.expanduser().resolve()

    if not source.exists():
        print(f"ERROR: Source folder does not exist:\n{source}")
        print("Edit config.json or use --source.")
        sys.exit(1)

    if not source.is_dir():
        print(f"ERROR: Source path is not a folder:\n{source}")
        sys.exit(1)

    print()
    print("==============================================")
    print(" PDF KNOWLEDGE LIBRARY GENERATOR")
    print("==============================================")
    print(f"Source: {source}")
    print()

    library = build_library(source, config)

    print()
    print("----------------------------------------------")
    print(f"Documents generated: {library['document_count']}")
    print(f"HTML: {INDEX_HTML}")
    print(f"JSON: {LIBRARY_JSON}")
    print(f"AI guide: {AI_TXT}")
    print(f"LLM index: {LLMS_TXT}")
    print(f"Sitemap: {SITEMAP_XML}")
    print("----------------------------------------------")
    print()


if __name__ == "__main__":
    main()
