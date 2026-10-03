# 🔍 JEV Website Source Analyzer

**JEV Website Source Analyzer** is an AI-powered tool for analyzing publicly accessible website source code and identifying **genuine software bugs and security vulnerabilities**.

It crawls a website, collects relevant client-side resources, and uses **JEV** to analyze the extracted content.

> ⚠️ This tool analyzes content publicly returned by the web server. It does **not** retrieve private backend source code.

---

## ✨ Features

* 🌐 Same-origin website crawling
* 📄 HTML analysis
* 🟨 External JavaScript analysis
* 🟨 Inline JavaScript analysis
* 🎨 External CSS analysis
* 🎨 Inline CSS analysis
* 🔗 Link and endpoint collection
* 📝 Form analysis
* 🖼️ Image and iframe discovery
* ⚙️ JSON/config-like resource support
* 🤖 JEV-powered bug analysis
* 🎯 Focus on evidence-based findings
* 📊 Bug probability and confidence scores
* 🔥 Top suspicious resources
* 🚫 Attempts to avoid false positives from style issues, metadata, generated code, etc.

---

## 🧠 How It Works

```text
              Website
                 │
                 ▼
        ┌─────────────────┐
        │   Web Crawler   │
        └────────┬────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │ Resource Collection │
      └──────────┬──────────┘
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
      HTML       JS        CSS
       │         │         │
       └─────────┼─────────┘
                 ▼
        ┌─────────────────┐
        │   JEV Analysis  │
        └────────┬────────┘
                 ▼
       ┌─────────────────────┐
       │ Genuine Bug Check   │
       └──────────┬──────────┘
                  ▼
       Bug / No Bug + Evidence
```

---

## 🔎 What JEV Looks For

The analyzer asks JEV to look for concrete evidence of issues such as:

* Cross-Site Scripting (XSS)
* Injection vulnerabilities
* Authentication flaws
* Authorization issues
* CSRF-related issues
* Unsafe handling of sensitive data
* Exposed secrets
* Unsafe DOM manipulation
* Logic errors
* Incorrect conditions
* Null/undefined access
* Runtime failures
* Incorrect data processing

The model is instructed **not** to treat code style, comments, minification, public URLs, public IDs, normal metadata, or theoretical concerns as bugs by themselves.

---

## 📦 Requirements

* Python 3
* JEV / TypeSafe SDK
* BeautifulSoup4
* Requests
* lxml

Install dependencies:

```bash
pip install typesafe-sdk beautifulsoup4 requests lxml
```

---

## 🔑 API Key

Set your JEV API key as an environment variable.

### PowerShell

```powershell
$env:TYPESAFE_API_KEY="YOUR_API_KEY"
```

The program also supports:

```text
JEV_API_KEY
```

as an alternative environment variable.

---

## 🚀 Usage

Basic scan:

```bash
python bug.py https://example.com
```

Limit the number of pages:

```bash
python bug.py https://example.com --max-pages 10
```

Limit the number of resources:

```bash
python bug.py https://example.com --max-files 50
```

Analyze only the initial page:

```bash
python bug.py https://example.com --no-crawl
```

---

## 📊 Example Output

```text
================================================================================
🚨 FINAL RESULTS — HIGHEST BUG PROBABILITY FIRST
================================================================================

#01 | 🟠 MEDIUM | BUG PROBABILITY: 62.41%

   Resource   : https://example.com/app.js
   Type       : javascript
   Choice     : bug_hoga
   Bug        : 62.41%
   Clean      : 37.59%
   Confidence : 81.20%
   Score      : ██████████████████░░░░░░░░░░░░

================================================================================
🔥 TOP 10 RESOURCES TO REVIEW
================================================================================
```

The tool sorts analyzed resources by the model's `bug_hoga` probability and displays the highest-scoring resources first.

---

## ⚙️ Configuration

Important configuration values include:

```python
MAX_FILE_SIZE_KB = 15000
MAX_CONTENT_CHARS = 28000

REQUEST_TIMEOUT = 15
DELAY_BETWEEN_JEV_CALLS = 0.3

DEFAULT_MAX_PAGES = 1000
DEFAULT_MAX_FILES = 1000
```

These control resource size, JEV context size, request timeout, API call delay, and crawl/resource limits.

---

## 🛡️ Responsible Use

Use this tool only on websites and applications that you **own or have explicit permission to test**.

This project is intended for:

* Security research
* Authorized bug bounty testing
* Development security reviews
* Educational purposes
* Code auditing

Do not use it to access, disrupt, or test systems without authorization.

---

## ⚠️ Important Limitations

This tool is **not a replacement for manual security testing**.

A high `bug_hoga` probability is **not proof that a vulnerability exists**. Findings should be manually reviewed and verified before being reported. The program itself explicitly notes that probability is not proof of an actual vulnerability.

The analyzer only sees content that is publicly returned by the web server and cannot access private backend source code.

---

## 🧩 Project Structure

```text
.
├── bug.py
└── README.md
```

---

## 🚧 Future Improvements

Possible future improvements:

* Better vulnerability evidence extraction
* Exact code-location reporting
* More detailed bug classification
* Improved JavaScript analysis
* Parallel resource analysis
* JSON report generation
* HTML security reports
* Reduced false positives
* Browser-based analysis

---

## ⭐ Credits

Built with **JEV** for AI-assisted website source analysis.

If you find the project useful, consider giving it a ⭐ on GitHub.
