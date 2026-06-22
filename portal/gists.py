import json
import os
import re
from html import escape
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import markdown
from django.utils.safestring import mark_safe


GIST_ID_RE = re.compile(r"^[A-Fa-f0-9]{20,64}$")
IMG_TAG_RE = re.compile(r"<img\b(?P<attrs>[^>]*)>", re.IGNORECASE)
IMG_ATTR_RE = re.compile(r"(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)')")
GIST_FILE_LANGUAGES = {
    ".bash": "bash",
    ".css": "css",
    ".html": "html",
    ".js": "javascript",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".sh": "bash",
    ".sql": "sql",
    ".toml": "toml",
    ".ts": "typescript",
    ".yaml": "yaml",
    ".yml": "yaml",
}
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}


class GistError(Exception):
    pass


def parse_gist_id(gist_url):
    parsed = urlparse(gist_url.strip())
    path_parts = [part for part in parsed.path.split("/") if part]
    gist_id = path_parts[-1] if path_parts else gist_url.strip()

    if parsed.scheme and parsed.netloc.lower() != "gist.github.com":
        raise ValueError("Report gist URLs must use gist.github.com.")
    if not GIST_ID_RE.fullmatch(gist_id):
        raise ValueError("Report gist URL must end with a GitHub Gist ID.")

    return gist_id


def load_report_gist(gist_id):
    gist = _fetch_json(f"https://api.github.com/gists/{gist_id}")
    files = gist.get("files") or {}
    report_file = files.get("report.md")
    if not report_file:
        raise GistError("Report gist must contain report.md.")

    report_markdown = _normalize_report_images(_file_content(report_file))
    images = []
    snippets = []
    for filename in sorted(files):
        if filename == "report.md":
            continue
        file_info = files[filename]
        if _is_image_file(filename, file_info):
            images.append(
                {
                    "filename": filename,
                    "url": file_info.get("raw_url"),
                }
            )
            continue
        snippets.append(
            {
                "filename": filename,
                "language": _language_for(filename, file_info),
                "content": _file_content(file_info),
            }
        )

    return {
        "description": gist.get("description") or "",
        "report_html": mark_safe(
            markdown.markdown(
                escape(report_markdown),
                extensions=["fenced_code", "tables"],
            )
        ),
        "images": [image for image in images if image["url"]],
        "snippets": snippets,
    }


def _fetch_json(url):
    try:
        with urlopen(_request(url), timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GistError("Could not load report gist.") from exc


def _fetch_text(url):
    try:
        with urlopen(_request(url), timeout=10) as response:
            return response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
        raise GistError("Could not load report gist file.") from exc


def _request(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "greenpipe.partners",
    }
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return Request(url, headers=headers)


def _file_content(file_info):
    content = file_info.get("content")
    if content is not None and not file_info.get("truncated"):
        return content

    raw_url = file_info.get("raw_url")
    if not raw_url:
        raise GistError("Could not load report gist file.")
    return _fetch_text(raw_url)


def _normalize_report_images(markdown_text):
    def replace(match):
        attrs = _image_attrs(match.group("attrs"))
        src = attrs.get("src", "")
        if not _is_allowed_inline_image(src):
            return match.group(0)

        alt = attrs.get("alt") or "report image"
        return f"![{_markdown_label(alt)}]({src})"

    return IMG_TAG_RE.sub(replace, markdown_text)


def _image_attrs(attrs_text):
    attrs = {}
    for match in IMG_ATTR_RE.finditer(attrs_text):
        attrs[match.group("name").lower()] = match.group("double") or match.group("single") or ""
    return attrs


def _is_allowed_inline_image(src):
    parsed = urlparse(src)
    return parsed.scheme == "https" and parsed.netloc.lower() == "gist.github.com" and parsed.path.startswith(
        "/user-attachments/assets/"
    )


def _markdown_label(label):
    return label.replace("[", r"\[").replace("]", r"\]")


def _is_image_file(filename, file_info):
    file_type = file_info.get("type") or ""
    if file_type.startswith("image/"):
        return True
    lowered = filename.lower()
    return any(lowered.endswith(extension) for extension in IMAGE_EXTENSIONS)


def _language_for(filename, file_info):
    lowered = filename.lower()
    for suffix, language in GIST_FILE_LANGUAGES.items():
        if lowered.endswith(suffix):
            return language
    return (file_info.get("language") or "text").lower().replace(" ", "-")
