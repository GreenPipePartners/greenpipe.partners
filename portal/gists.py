import csv
import json
import os
import re
from html import escape
from io import StringIO
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

import markdown
from django.utils.safestring import mark_safe


GIST_ID_RE = re.compile(r"^[A-Fa-f0-9]{20,64}$")
IMG_TAG_RE = re.compile(r"<img\b(?P<attrs>[^>]*)>", re.IGNORECASE)
IMG_ATTR_RE = re.compile(r"(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)')")
CALLOUT_RE = re.compile(
    r"^\s{0,3}>\s*\[!(?P<type>success|recommendation|quote)\](?:[+-])?(?:\s+(?P<title>.+?))?\s*$",
    re.IGNORECASE,
)
CALLOUT_LINE_RE = re.compile(r"^\s{0,3}>\s?(?P<body>.*)$")
YOUTUBE_LINK_RE = re.compile(r"^\s*\[(?P<label>[^\n\]]+)\]\((?P<url>https://[^\s)]+)\)\s*$", re.IGNORECASE)
YOUTUBE_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"m.youtube.com", "music.youtube.com", "www.youtube.com", "youtube.com"}
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
CSV_FILE_TYPES = {"application/csv", "application/vnd.ms-excel", "text/csv"}
CSV_PREVIEW_ROW_LIMIT = 25
REPORT_FILENAME = "report.md"


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
    report_filename = _report_filename(files)
    if not report_filename:
        raise GistError("Report gist must contain report.md.")

    report_file = files[report_filename]
    report_markdown = _normalize_report_images(_file_content(report_file))
    csvs = []
    images = []
    snippets = []
    for filename in sorted(files):
        if filename == report_filename:
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
        if _is_csv_file(filename, file_info):
            csv_content = _file_content(file_info)
            csvs.append(
                {
                    "filename": filename,
                    "preview_rows": _csv_preview_rows(csv_content),
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
        "report_markdown": report_markdown,
        "report_html": mark_safe(_render_report_markdown(report_markdown)),
        "csvs": csvs,
        "images": [image for image in images if image["url"]],
        "snippets": snippets,
    }


def load_report_csv(gist_id, filename):
    gist = _fetch_json(f"https://api.github.com/gists/{gist_id}")
    file_info = (gist.get("files") or {}).get(filename)
    if not file_info or not _is_csv_file(filename, file_info):
        raise GistError("CSV attachment not found.")
    return _file_content(file_info)


def _report_filename(files):
    if REPORT_FILENAME in files:
        return REPORT_FILENAME
    for filename in sorted(files):
        if filename.lower() == REPORT_FILENAME:
            return filename
    return ""


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


def _render_report_markdown(markdown_text):
    normalized_markdown, replacements = _extract_report_blocks(markdown_text)
    report_html = _render_safe_markdown(normalized_markdown)
    for token, block_html in replacements.items():
        report_html = report_html.replace(f"<p>{token}</p>", block_html)
    return report_html


def _extract_report_blocks(markdown_text):
    lines = markdown_text.splitlines()
    normalized_lines = []
    replacements = {}
    index = 0

    while index < len(lines):
        callout_match = CALLOUT_RE.match(lines[index])
        if callout_match:
            body_lines = []
            index += 1
            while index < len(lines):
                body_match = CALLOUT_LINE_RE.match(lines[index])
                if not body_match:
                    break
                body_lines.append(body_match.group("body"))
                index += 1

            callout_type = callout_match.group("type").lower()
            callout_kind = "recommendation" if callout_type in {"success", "recommendation"} else "quote"
            default_title = "Recommendation" if callout_kind == "recommendation" else "Quote"
            title = callout_match.group("title") or default_title
            token = _report_block_token()
            replacements[token] = _callout_html(callout_kind, title, body_lines)
            normalized_lines.extend(("", token, ""))
            continue

        youtube_match = YOUTUBE_LINK_RE.match(lines[index])
        if youtube_match:
            video_id = _youtube_video_id(youtube_match.group("url"))
            if video_id:
                token = _report_block_token()
                replacements[token] = _youtube_html(
                    video_id,
                    youtube_match.group("label"),
                    youtube_match.group("url"),
                )
                normalized_lines.extend(("", token, ""))
                index += 1
                continue

        normalized_lines.append(lines[index])
        index += 1

    return "\n".join(normalized_lines), replacements


def _report_block_token():
    return f"GPPREPORTBLOCK{uuid4().hex.upper()}"


def _render_safe_markdown(markdown_text):
    return markdown.markdown(
        escape(markdown_text),
        extensions=["fenced_code", "tables"],
    )


def _callout_html(callout_kind, title, body_lines):
    body_html = _render_safe_markdown("\n".join(body_lines))
    return (
        f'<aside class="report-callout report-callout-{callout_kind}">'
        '<span class="report-callout-icon" aria-hidden="true"></span>'
        f'<div class="report-callout-title">{escape(title)}</div>'
        f'<div class="report-callout-body">{body_html}</div>'
        "</aside>"
    )


def _youtube_video_id(url):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return ""

    hostname = (parsed.hostname or "").lower()
    video_id = ""
    if hostname in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/", 1)[0]
    elif hostname in YOUTUBE_HOSTS:
        path_parts = [part for part in parsed.path.split("/") if part]
        if parsed.path.rstrip("/") == "/watch":
            video_id = (parse_qs(parsed.query).get("v") or [""])[0]
        elif len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts"}:
            video_id = path_parts[1]

    return video_id if YOUTUBE_VIDEO_ID_RE.fullmatch(video_id) else ""


def _youtube_html(video_id, label, source_url):
    safe_label = escape(label)
    return (
        '<figure class="report-video">'
        '<div class="report-video-frame">'
        f'<iframe src="https://www.youtube-nocookie.com/embed/{video_id}" '
        f'title="{safe_label}" loading="lazy" '
        'referrerpolicy="strict-origin-when-cross-origin" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        "allowfullscreen></iframe>"
        "</div>"
        f'<figcaption><a href="{escape(source_url)}">{safe_label}</a></figcaption>'
        "</figure>"
    )


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


def _is_csv_file(filename, file_info):
    file_type = (file_info.get("type") or "").lower()
    return filename.lower().endswith(".csv") or file_type in CSV_FILE_TYPES


def _csv_preview_rows(csv_content):
    rows = []
    reader = csv.reader(StringIO(csv_content))
    for row in reader:
        if len(rows) >= CSV_PREVIEW_ROW_LIMIT:
            break
        rows.append(row)
    return rows


def _language_for(filename, file_info):
    lowered = filename.lower()
    for suffix, language in GIST_FILE_LANGUAGES.items():
        if lowered.endswith(suffix):
            return language
    return (file_info.get("language") or "text").lower().replace(" ", "-")
