#!/usr/bin/env python3

"""
Jev Website Source Analyzer
===========================

Analyzes publicly accessible website source using TypeSafe Jev.

Analyzes:
    - HTML
    - External JavaScript
    - Inline JavaScript
    - CSS
    - Inline CSS
    - Same-origin pages
    - Forms
    - Links/endpoints
    - Meta information
    - JSON/config-like resources

IMPORTANT:
This analyzes only content publicly returned by the web server.
It cannot retrieve private backend source code.

Requirements:
    pip install typesafe-sdk beautifulsoup4 requests lxml

Usage:
    python bug.py https://example.com

Optional:
    python bug.py https://example.com --max-pages 10
    python bug.py https://example.com --max-files 50
    python bug.py https://example.com --no-crawl
"""

import os
import sys
import time
import argparse
from urllib.parse import (
    urljoin,
    urlparse,
    urldefrag,
)
from typing import List, Dict, Optional, Tuple, Set

import requests
from bs4 import BeautifulSoup


# ============================================================
# IMPORT JEV
# ============================================================

try:
    from typesafe_sdk import TypeSafeClient, Choice
except ImportError:
    print("❌ typesafe-sdk is not installed.")
    print("Run:")
    print("    python -m pip install typesafe-sdk")
    sys.exit(1)


# ============================================================
# CONFIG
# ============================================================

MAX_FILE_SIZE_KB = 15000
MAX_CONTENT_CHARS = 28000

REQUEST_TIMEOUT = 15

DELAY_BETWEEN_JEV_CALLS = 0.3

DEFAULT_MAX_PAGES = 1000
DEFAULT_MAX_FILES = 1000

USER_AGENT = "Mozilla/5.0 " "(compatible; JevWebsiteAnalyzer/1.0; +https://example.com)"


# ============================================================
# API KEY
# ============================================================


def get_api_key() -> str:

    key = os.environ.get("TYPESAFE_API_KEY") or os.environ.get("JEV_API_KEY")

    if not key:
        print("\n❌ TYPESAFE_API_KEY environment variable not set.")
        print()
        print("PowerShell:")
        print('    $env:TYPESAFE_API_KEY="YOUR_API_KEY"')
        print()
        print("Then run:")
        print("    python bug.py https://example.com")
        print()

        sys.exit(1)

    return key


# ============================================================
# URL HELPERS
# ============================================================


def normalize_url(url: str) -> str:

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    url, _ = urldefrag(url)

    return url


def same_origin(url1: str, url2: str) -> bool:

    a = urlparse(url1)
    b = urlparse(url2)

    return a.scheme == b.scheme and a.netloc == b.netloc


# ============================================================
# HTTP FETCH
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }
)


def fetch_url(url: str) -> Optional[requests.Response]:

    try:

        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        return response

    except requests.RequestException as e:

        print(f"  ⚠️ Failed: {url}")
        print(f"     {e}")

        return None


# ============================================================
# RESOURCE SIZE CHECK
# ============================================================


def is_small_enough(text: str) -> bool:

    size_kb = len(text.encode("utf-8", errors="ignore")) / 1024

    return size_kb <= MAX_FILE_SIZE_KB


# ============================================================
# EXTRACT HTML INFORMATION
# ============================================================


def extract_html_data(html: str, base_url: str) -> Dict:

    soup = BeautifulSoup(html, "lxml")

    result = {
        "js_urls": [],
        "css_urls": [],
        "inline_js": [],
        "inline_css": [],
        "links": [],
        "forms": [],
        "meta": [],
        "images": [],
        "iframes": [],
    }

    # --------------------------------------------------------
    # JavaScript
    # --------------------------------------------------------

    for script in soup.find_all("script"):

        src = script.get("src")

        if src:

            full_url = urljoin(base_url, src)

            if full_url.startswith(("http://", "https://")):

                result["js_urls"].append(full_url)

        else:

            content = script.get_text()

            if content and content.strip():

                if len(content.strip()) > 30:

                    result["inline_js"].append(content.strip())

    # --------------------------------------------------------
    # CSS
    # --------------------------------------------------------

    for link in soup.find_all("link"):

        rel = link.get("rel", [])

        if isinstance(rel, list):
            rel = [x.lower() for x in rel]

        if "stylesheet" in rel:

            href = link.get("href")

            if href:

                full_url = urljoin(base_url, href)

                if full_url.startswith(("http://", "https://")):

                    result["css_urls"].append(full_url)

    # --------------------------------------------------------
    # Inline CSS
    # --------------------------------------------------------

    for style in soup.find_all("style"):

        content = style.get_text()

        if content and content.strip():

            result["inline_css"].append(content.strip())

    # --------------------------------------------------------
    # Links
    # --------------------------------------------------------

    for tag in soup.find_all("a"):

        href = tag.get("href")

        if not href:
            continue

        full_url = urljoin(base_url, href)

        if full_url.startswith(("http://", "https://")):

            result["links"].append(full_url)

    # --------------------------------------------------------
    # Forms
    # --------------------------------------------------------

    for form in soup.find_all("form"):

        action = form.get("action", "")

        method = form.get("method", "GET").upper()

        action_url = urljoin(base_url, action)

        inputs = []

        for inp in form.find_all(["input", "textarea", "select"]):

            inputs.append(
                {
                    "name": inp.get("name"),
                    "type": inp.get("type", inp.name),
                }
            )

        result["forms"].append(
            {
                "action": action_url,
                "method": method,
                "inputs": inputs,
            }
        )

    # --------------------------------------------------------
    # Meta
    # --------------------------------------------------------

    for meta in soup.find_all("meta"):

        result["meta"].append(
            {
                "name": meta.get("name"),
                "property": meta.get("property"),
                "content": meta.get("content"),
            }
        )

    # --------------------------------------------------------
    # Images
    # --------------------------------------------------------

    for img in soup.find_all("img"):

        src = img.get("src")

        if src:

            result["images"].append(urljoin(base_url, src))

    # --------------------------------------------------------
    # Iframes
    # --------------------------------------------------------

    for iframe in soup.find_all("iframe"):

        src = iframe.get("src")

        if src:

            result["iframes"].append(urljoin(base_url, src))

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    for key in [
        "js_urls",
        "css_urls",
        "links",
        "images",
        "iframes",
    ]:

        result[key] = list(dict.fromkeys(result[key]))

    return result


# ============================================================
# DOWNLOAD TEXT RESOURCE
# ============================================================


def download_text_resource(url: str) -> Optional[str]:

    response = fetch_url(url)

    if not response:
        return None

    try:

        content = response.text

    except Exception:

        return None

    if not is_small_enough(content):

        size_kb = len(content.encode("utf-8", errors="ignore")) / 1024

        print(f"  ⚠️ Skipping large resource " f"({size_kb:.1f} KB): {url}")

        return None

    return content


# ============================================================
# RESOURCE TYPE
# ============================================================


def get_resource_type(url: str) -> str:

    path = urlparse(url).path.lower()

    if path.endswith(".js"):
        return "javascript"

    if path.endswith(".css"):
        return "css"

    if path.endswith(".json"):
        return "json"

    if path.endswith((".html", ".htm")):
        return "html"

    return "resource"


# ============================================================
# BUILD HTML SUMMARY
# ============================================================


def build_html_analysis(html: str, page_url: str, data: Dict) -> str:

    soup = BeautifulSoup(html, "lxml")

    title = ""

    if soup.title:
        title = soup.title.get_text(strip=True)

    text = soup.get_text(" ", strip=True)

    if len(text) > 6000:
        text = text[:6000]

    output = f"""
WEBSITE PAGE ANALYSIS

URL:
{page_url}

TITLE:
{title}

PAGE TEXT:
{text}

EXTERNAL JAVASCRIPT:
{chr(10).join(data["js_urls"])}

EXTERNAL CSS:
{chr(10).join(data["css_urls"])}

FORMS:
{data["forms"]}

LINKS:
{chr(10).join(data["links"][:100])}

IFRAMES:
{chr(10).join(data["iframes"][:50])}

META:
{data["meta"][:50]}
"""

    return output


# ============================================================
# JEV ANALYSIS
# ============================================================


def ask_jev(
    client: TypeSafeClient, content: str, label: str, resource_type: str
) -> Dict:

    # --------------------------------------------------------
    # Limit context
    # --------------------------------------------------------

    if len(content) > MAX_CONTENT_CHARS:

        content = content[:MAX_CONTENT_CHARS] + "\n\n" "// ... CONTENT TRUNCATED ..."

    # --------------------------------------------------------
    # Choice definition
    # --------------------------------------------------------
    
    questions = { 
    "has_bug": Choice( 
        instructions=( 
            f"Analyze this publicly accessible website {resource_type} " 
            "strictly for actual software bugs and security vulnerabilities. " 
 
            "Only identify an issue when there is concrete evidence in the " 
            "provided code or content. Do not flag something merely because " 
            "it is unusual, old, minified, generated, or considered bad style. " 
 
            "For security issues, look for concrete vulnerabilities such as " 
            "XSS, injection, authentication or authorization flaws, CSRF, " 
            "insecure handling of sensitive data, exposed secrets, unsafe " 
            "DOM manipulation, or other directly evidenced security flaws. " 
 
            "For software bugs, look for concrete logic errors, incorrect " 
            "conditions, crashes, undefined/null access, broken state " 
            "handling, incorrect data processing, or behavior that can " 
            "clearly fail at runtime. " 
 
            "Do NOT classify the following as bugs by themselves: " 
            "code style issues, lack of comments, deprecated APIs, " 
            "third-party analytics, public URLs, public IDs, normal HTML " 
            "metadata, minified/generated code, or theoretical concerns " 
            "without an evidence-based attack or failure path. " 
 
            "If the provided source is insufficient to prove that an issue " 
            "is exploitable or actually causes incorrect behavior, choose " 
            "bug_nahi_hoga." 
        ), 
 
        criteria={ 
            "bug_hoga": ( 
                "There is concrete evidence of an actual software bug or " 
                "security vulnerability in the provided content. " 
                "The issue has a clear failure, exploit, or incorrect " 
                "behavior path supported by the analyzed code." 
            ), 
 
            "bug_nahi_hoga": ( 
                "There is no concrete evidence of an actual software bug " 
                "or security vulnerability in the provided content, or " 
                "the suspected issue cannot be established from the " 
                "available evidence." 
            ), 
        }, 
    ) 
}
    # --------------------------------------------------------
    # API call
    # --------------------------------------------------------

    try:

        response = client.system_one(
            state=content,
            questions=questions,
            model="jev-latest",
        )

        answer = response.answers["has_bug"]

        return {
            "choice": answer.choice,
            "probabilities": dict(answer.probabilities),
            "confidence": answer.confidence,
            "label": label,
            "resource_type": resource_type,
        }

    except Exception as e:

        print(f"  ❌ Jev API error: {label}")

        print(f"     {e}")

        return {
            "choice": None,
            "probabilities": {
                "bug_hoga": 0.0,
                "bug_nahi_hoga": 0.0,
            },
            "confidence": 0.0,
            "label": label,
            "resource_type": resource_type,
            "error": str(e),
        }


# ============================================================
# CRAWLER
# ============================================================


def crawl_site(
    start_url: str,
    max_pages: int,
) -> List[Tuple[str, str]]:

    queue = [start_url]

    visited: Set[str] = set()

    pages = []

    print("\n🌐 Crawling website...\n")

    while queue and len(pages) < max_pages:

        url = queue.pop(0)

        url, _ = urldefrag(url)

        if url in visited:
            continue

        visited.add(url)

        print(f"  [{len(pages)+1}/{max_pages}] " f"{url}")

        response = fetch_url(url)

        if not response:
            continue

        content_type = response.headers.get("Content-Type", "").lower()

        if "text/html" not in content_type and not urlparse(url).path.endswith(
            (".html", ".htm", "/")
        ):
            continue

        html = response.text

        pages.append((url, html))

        # Extract links for next pages

        try:

            soup = BeautifulSoup(html, "lxml")

            for a in soup.find_all("a"):

                href = a.get("href")

                if not href:
                    continue

                next_url = urljoin(url, href)

                next_url, _ = urldefrag(next_url)

                if not same_origin(start_url, next_url):
                    continue

                parsed = urlparse(next_url)

                if parsed.scheme not in ("http", "https"):
                    continue

                if next_url not in visited:
                    queue.append(next_url)

        except Exception:
            pass

    return pages


# ============================================================
# SITE LEVEL SUMMARY
# ============================================================


def build_site_summary(pages: List[Tuple[str, str]], resources: List[Dict]) -> str:

    output = []

    output.append("WEBSITE SECURITY / BUG ANALYSIS")

    output.append(f"\nPages analyzed: {len(pages)}")

    output.append(f"\nResources analyzed: {len(resources)}")

    output.append("\n\nRESOURCE SUMMARY:\n")

    for r in resources:

        probs = r.get("probabilities", {})

        output.append(
            f"""
Resource: {r.get("label")}
Type: {r.get("resource_type")}
Choice: {r.get("choice")}
bug_hoga: {probs.get("bug_hoga", 0)}
bug_nahi_hoga: {probs.get("bug_nahi_hoga", 0)}
confidence: {r.get("confidence", 0)}
"""
        )

    return "\n".join(output)


# ============================================================
# MAIN
# ============================================================


def main():

    parser = argparse.ArgumentParser(
        description=("Analyze publicly accessible website " "source using Jev")
    )

    parser.add_argument("url", help="Website URL")

    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=("Maximum same-origin HTML pages " "to crawl"),
    )

    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=("Maximum resources to send to Jev"),
    )

    parser.add_argument(
        "--no-crawl",
        action="store_true",
        help="Analyze only the initial page",
    )

    args = parser.parse_args()

    start_url = normalize_url(args.url)

    print()
    print("=" * 80)
    print("🔍 JEV WEBSITE ANALYZER")
    print("=" * 80)
    print()
    print(f"Target: {start_url}")

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    api_key = get_api_key()

    # --------------------------------------------------------
    # Crawl
    # --------------------------------------------------------

    if args.no_crawl:

        response = fetch_url(start_url)

        if not response:
            sys.exit(1)

        pages = [(start_url, response.text)]

    else:

        pages = crawl_site(start_url, args.max_pages)

    if not pages:

        print("\n❌ No HTML pages found.")

        sys.exit(1)

    # --------------------------------------------------------
    # Collect resources
    # --------------------------------------------------------

    resources = []

    seen_resources = set()

    print("\n📦 Collecting website resources...\n")

    for page_url, html in pages:

        print(f"Analyzing page: {page_url}")

        data = extract_html_data(html, page_url)

        # ----------------------------------------------------
        # HTML itself
        # ----------------------------------------------------

        html_analysis = build_html_analysis(html, page_url, data)

        resources.append(
            {
                "label": f"HTML: {page_url}",
                "content": html_analysis,
                "resource_type": "html",
                "source": page_url,
            }
        )

        # ----------------------------------------------------
        # Inline JS
        # ----------------------------------------------------

        for index, code in enumerate(data["inline_js"], 1):

            resources.append(
                {
                    "label": (f"Inline JS #{index} " f"({page_url})"),
                    "content": code,
                    "resource_type": "javascript",
                    "source": page_url,
                }
            )

        # ----------------------------------------------------
        # Inline CSS
        # ----------------------------------------------------

        for index, code in enumerate(data["inline_css"], 1):

            resources.append(
                {
                    "label": (f"Inline CSS #{index} " f"({page_url})"),
                    "content": code,
                    "resource_type": "css",
                    "source": page_url,
                }
            )

        # ----------------------------------------------------
        # External JS
        # ----------------------------------------------------

        for js_url in data["js_urls"]:

            if js_url in seen_resources:
                continue

            seen_resources.add(js_url)

            resources.append(
                {
                    "label": js_url,
                    "url": js_url,
                    "resource_type": "javascript",
                }
            )

        # ----------------------------------------------------
        # External CSS
        # ----------------------------------------------------

        for css_url in data["css_urls"]:

            if css_url in seen_resources:
                continue

            seen_resources.add(css_url)

            resources.append(
                {
                    "label": css_url,
                    "url": css_url,
                    "resource_type": "css",
                }
            )

    # --------------------------------------------------------
    # Download external resources
    # --------------------------------------------------------

    prepared_resources = []

    for resource in resources:

        if "content" in resource:

            prepared_resources.append(resource)

            continue

        url = resource.get("url")

        if not url:
            continue

        print(f"  Downloading: {url}")

        content = download_text_resource(url)

        if content is None:
            continue

        resource["content"] = content

        prepared_resources.append(resource)

    resources = prepared_resources

    # --------------------------------------------------------
    # Limit
    # --------------------------------------------------------

    resources = resources[: args.max_files]

    print()
    print(f"📦 Total resources to analyze: " f"{len(resources)}")

    # --------------------------------------------------------
    # Jev
    # --------------------------------------------------------

    results = []

    with TypeSafeClient(api_key=api_key) as client:

        for index, resource in enumerate(resources, 1):

            label = resource["label"]

            resource_type = resource["resource_type"]

            content = resource["content"]

            print()
            print(f"[{index}/{len(resources)}] " f"🤖 Jev analyzing:")

            print(f"    {label}")

            result = ask_jev(
                client,
                content,
                label,
                resource_type,
            )

            result["source"] = resource.get("source", resource.get("url", ""))

            results.append(result)

            time.sleep(DELAY_BETWEEN_JEV_CALLS)

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    results.sort(
        key=lambda r: r.get("probabilities", {}).get("bug_hoga", 0.0),
        reverse=True,
    )

    # --------------------------------------------------------

    # SORT + PRINT FINAL RESULTS
    # --------------------------------------------------------

    results.sort(
        key=lambda r: float(r.get("probabilities", {}).get("bug_hoga", 0.0)), reverse=True
    )

    print()
    print("=" * 100)
    print("🚨 FINAL RESULTS — HIGHEST BUG PROBABILITY FIRST")
    print("=" * 100)

    for rank, result in enumerate(results, 1):

        probabilities = result.get("probabilities", {})

        bug_probability = float(probabilities.get("bug_hoga", 0.0))

        clean_probability = float(probabilities.get("bug_nahi_hoga", 0.0))

        confidence = float(result.get("confidence", 0.0))

        choice = result.get("choice", "error")

        label = result.get("label", "unknown")

        resource_type = result.get("resource_type", "unknown")

        # Percentage
        bug_percent = bug_probability * 100
        clean_percent = clean_probability * 100
        confidence_percent = confidence * 100

        # Visual bar
        bar_length = min(30, max(0, int(bug_probability * 30)))

        bar = "█" * bar_length + "░" * (30 - bar_length)

        # Risk label
        if bug_probability >= 0.80:
            risk = "🔴 HIGH"
        elif bug_probability >= 0.50:
            risk = "🟠 MEDIUM"
        elif bug_probability >= 0.25:
            risk = "🟡 LOW"
        else:
            risk = "🟢 VERY LOW"

        print()
        print(f"#{rank:02d} | {risk} | " f"BUG PROBABILITY: {bug_percent:6.2f}%")

        print(f"   Resource   : {label}")

        print(f"   Type       : {resource_type}")

        print(f"   Choice     : {choice}")

        print(f"   Bug        : {bug_percent:6.2f}%")

        print(f"   Clean      : {clean_percent:6.2f}%")

        print(f"   Confidence : {confidence_percent:6.2f}%")

        print(f"   Score      : {bar}")


    print()
    print("=" * 100)

    # --------------------------------------------------------
    # TOP SUSPICIOUS RESOURCES
    # --------------------------------------------------------

    print("🔥 TOP 10 RESOURCES TO REVIEW")
    print("=" * 100)

    top_results = results[:10]

    for rank, result in enumerate(top_results, 1):

        probabilities = result.get("probabilities", {})

        bug_probability = float(probabilities.get("bug_hoga", 0.0))

        print(
            f"{rank:02d}. "
            f"{bug_probability * 100:6.2f}% "
            f"| "
            f"{result.get('resource_type', 'unknown'):12} "
            f"| "
            f"{result.get('label', 'unknown')}"
        )


    print()
    print("=" * 100)

    print("ℹ️ Higher bug_hoga probability = " "higher likelihood according to Jev.")

    print("⚠️ Probability is not proof of an actual vulnerability.")

    print("=" * 100)

# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    main()
