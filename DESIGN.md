# IntelliApply - Technical Design Document

## Table of Contents

- [Executive Summary](#executive-summary)
- [System Architecture](#system-architecture)
- [Core Technologies](#core-technologies)
- [Feature Specifications](#feature-specifications)
- [Storage & Web UI Design](#storage--web-ui-design)
- [Performance Optimizations](#performance-optimizations)
- [Data Models](#data-models)
- [API Integration](#api-integration)
- [Web Scraping Architecture](#web-scraping-architecture)
- [User Experience Design](#user-experience-design)
- [Security Considerations](#security-considerations)
- [Future Roadmap](#future-roadmap)

---

## Executive Summary

**IntelliApply** is a sophisticated job application tracking system that leverages large language models (LLMs) for intelligent information extraction. Built with Python, it combines advanced web scraping, natural language processing, and local SQLite-backed data management with a built-in web UI to automate the tedious aspects of job application tracking.

### Key Innovations

1. **LLM-Powered Extraction**: Uses OpenAI-compatible APIs with structured output via Pydantic models for reliable job information extraction
2. **Intelligent Web Scraping**: Hybrid approach using both static (requests + BeautifulSoup) and dynamic (Playwright) content fetching with automatic detection
3. **Multi-Status Workflow**: Sophisticated application lifecycle tracking (Rejected/Processing/Offer) with temporal tracking
4. **Vectorized Search**: High-performance search implementation using pandas vectorized operations
5. **Adaptive Terminal UI**: Dynamic terminal width adjustment for optimal content display

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Interface                         │
│                    (Interactive CLI - main.py)                  │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ├─── Input Processing Layer
                │    ├─ URL Detection & Web Scraping
                │    ├─ Markdown Table Parser
                │    ├─ JSON Content Handler
                │    └─ Raw Text Wrapper
                │
                ├─── Intelligence Layer
                │    ├─ LLM API Client (OpenAI-compatible)
                │    ├─ Content Analysis (Static vs Dynamic)
                │    ├─ Pydantic Validation Models
                │    └─ Multi-API Fallback System
                │
                ├─── Data Management Layer
                │    ├─ JobDatabase Class (SQLite, shared instance)
                │    │   ├─ Short-lived connection per operation
                │    │   ├─ Vectorized Search (pandas over SQLite rows)
                │    │   ├─ Status Management
                │    │   ├─ Duplicate Detection
                │    │   ├─ Automatic Schema Upgrade (ALTER TABLE)
                │    │   └─ Excel Import / Export (legacy format)
                │
                ├─── Web UI Layer (background thread)
                │    ├─ ThreadingHTTPServer (127.0.0.1:8765)
                │    ├─ JSON API over the same JobDatabase instance
                │    └─ Single-page UI (vanilla JS)
                │
                ├─── Session Management Layer
                │    ├─ Cookie Persistence (pickle)
                │    ├─ Multi-Domain Authentication
                │    └─ Browser Automation (Playwright)
                │
                └─── Utility Layer
                     ├─ String Processing & Normalization
                     ├─ Terminal UI Rendering
                     ├─ Color-Coded Output
                     └─ Local Backup (SingleFile)
```

### Module Organization

```
intelliapply/
├── __init__.py            # Package metadata
├── __main__.py            # Module execution entry point
├── main.py                # CLI orchestration
│
├── config/
│   ├── __init__.py
│   ├── config.py          # Domain keywords, cookie paths, HTTP headers, web UI host/port
│   ├── credential.py      # Config manager & loader (loads from user directory)
│   ├── credential-example.yaml  # Configuration template
│   └── prompt.py          # LLM prompts & Pydantic models
│
├── web/
│   ├── __init__.py
│   ├── server.py          # Local web UI server & JSON API (stdlib http.server)
│   └── index.html         # Single-page UI (vanilla JS)
│
└── utils/
    ├── __init__.py
    ├── db_utils.py        # SQLite storage (JobDatabase), search engine, Excel import/export
    ├── web_utils.py       # Web scraping & LLM integration
    ├── string_utils.py    # Text processing & normalization
    ├── print_utils.py     # Terminal rendering & UI
    └── singlefile.py      # Webpage backup functionality
```

### Installation Methods

The package can be installed via:
- **GitHub**: `pip install git+https://github.com/Jason-LJQ/IntelliApply.git` or `pipx install git+https://github.com/Jason-LJQ/IntelliApply.git`
- **Source**: `pip install -e .` or `uv pip install -e .`
- **Module execution**: `python -m intelliapply`

### Configuration System

IntelliApply uses a YAML-based configuration system with automatic setup:

1. **Location**: `~/intelliApply_config/config.yaml` (cross-platform user home directory)
2. **First-time setup**:
   - Automatically copies template from `credential-example.yaml`
   - Opens config file in default system editor
   - Validates configuration before proceeding
3. **Structure**: YAML format with an `api_services` list (`api_key`, `base_url`, `model`, optional `reasoning_effort`) and a `paths` section (`database_file_path`, `backup_folder_path`, optional legacy `excel_file_path`)
4. **Loading**: `credential.py` contains `ConfigManager` class that handles all config operations

This approach ensures credentials are never committed to version control while providing a smooth setup experience.

---

## Core Technologies

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.8+ | Core implementation language |
| **LLM API** | OpenAI-compatible API | Job information extraction |
| **Data Storage** | SQLite (stdlib `sqlite3`) | Structured data persistence |
| **Web UI** | stdlib `http.server` + vanilla JS | Local browser interface |
| **Excel I/O** | openpyxl | Legacy import / export |
| **Data Analysis** | pandas | Vectorized search operations |
| **Validation** | Pydantic | Schema validation & type safety |
| **Static Scraping** | requests + BeautifulSoup4 | HTML parsing for simple pages |
| **Dynamic Scraping** | Playwright | JavaScript-heavy pages & SPAs |
| **Session Management** | pickle | Cookie persistence |
| **UI Rendering** | ANSI escape codes | Terminal color & formatting |

### Dependency Rationale

- **sqlite3**: Standard library, zero extra dependencies, single-file storage with transactions
- **openpyxl**: Only used for Excel import/export (status is represented by cell fill color)
- **pandas**: Enables vectorized operations for 3-5x performance improvement in search
- **Playwright**: Handles JavaScript-rendered content that requests cannot fetch
- **Pydantic**: Ensures type safety and structured LLM output with automatic validation

---

## Feature Specifications

### 1. Multi-Format Input Processing

#### URL Processing
```python
Input: https://job-board.com/positions/123456
Pipeline:
  1. Detect URL pattern (http/https prefix)
  2. Attempt static fetch with requests
  3. Analyze content for JavaScript requirements
  4. Fallback to Playwright if needed
  5. Extract text content with BeautifulSoup
  6. Send to LLM for structured extraction
  7. Validate with Pydantic models
  8. Check for duplicates
  9. Store in the SQLite database with metadata
  10. Backup HTML to local storage (async)
```

**Intelligent Content Detection**:
- Checks for hydration markers (`__NEXT_DATA__`, `data-reactroot`)
- Detects JavaScript requirements (`<noscript>` tags, "enable javascript")
- Identifies Cloudflare challenges (403/429/503 status codes)
- Processes iframe content recursively

#### Markdown Table Processing
```python
Input:
| Company | Location | Job Title | Code | Type | Link |
| ------- | -------- | --------- | ---- | ---- | ---- |
| Acme Co | Remote   | Engineer  | E123 | Remote | https://... |

Pipeline:
  1. Detect pipe-delimited format
  2. Parse headers and data rows
  3. Map columns to internal schema
  4. Validate required fields
  5. Store directly in the database (no LLM needed)
```

#### JSON Input Processing
```python
Input: {"Company": "Acme", "Location": "NYC", "Job_Title": "Engineer"}
Pipeline:
  1. Detect JSON structure
  2. Parse with safe JSON parser
  3. Normalize field names (Job_Title → Job Title)
  4. Validate against Pydantic schema
  5. Store in the database
```

#### Raw Content Processing
```python
Input:
< Job Title: Software Engineer
  Company: Example Inc.
  Location: Remote
>

Pipeline:
  1. Detect wrapper characters (< > or ```)
  2. Extract wrapped content
  3. Send to LLM for extraction
  4. Validate and store
```

### 2. Multi-Status Application Tracking

#### Status System Design

The application lifecycle is tracked through three distinct states:

| Status | Color | Symbol | Date Column | Meaning |
|--------|-------|--------|-------------|---------|
| **REJECTED** | Red (FFFF0000) | ⨉ | Result Date | Application rejected by company |
| **PROCESSING** | Yellow (FFFFFF00) | → | Processed Date | Application under review |
| **OFFER** | Green (FF00FF00) | ✔ | Result Date | Offer received |

#### Date Column Architecture

```
Schema:
  - Applied Date: Auto-generated when entry is created
  - Processed Date: Updated when marked as PROCESSING
  - Result Date: Updated when marked as REJECTED or OFFER
```

**Design Philosophy**: No enforced state transitions. Users have full freedom to mark any status at any time, enabling flexible workflows (e.g., offer → processing for negotiation tracking).

#### Command Syntax

```bash
# Marking syntax: <line_number><action>
1r    # Mark line 1 as REJECTED (red)
2p    # Mark line 2 as PROCESSING (yellow)
3o    # Mark line 3 as OFFER (green)
1     # Mark line 1 as REJECTED (default action)
```

**Implementation**: Regex pattern `r'^(\d+)([a-z]?)$'` with fallback to 'r' for pure numbers.

### 3. Intelligent Search Engine

#### Search Capabilities

```python
# Direct company name match
> "Databricks"  # Matches "Databricks" exactly

# Prefix matching
> "Data"        # Matches "Databricks", "DataDog", etc.

# Abbreviation matching (target)
> "om"          # Matches "Old Mission Capital"

# Abbreviation matching (keyword)
> "GSK"         # Matches "GlaxoSmithKline"

# Job title word-level matching
> "engineer"    # Matches "Software Engineer", "ML Engineer"
```

#### Implementation Details

**Vectorized Search Algorithm** (`utils/db_utils.py::JobDatabase.search_applications`, operating on a DataFrame loaded from SQLite for each search):

```python
# 1. Pre-compute normalized columns
df['norm_company'] = df['Company'].apply(normalize_company_name)
df['abbr_company'] = df['Company'].apply(get_abbreviation_lower)
df['clean_job_title'] = df['Job Title'].apply(cleaned_string).str.lower()

# 2. Build boolean masks
m_base = (
    (df['norm_company'] == norm_keyword) |                          # Direct match
    (df['norm_company'].str.startswith(norm_keyword, na=False)) |   # Prefix match
    (df['clean_job_title'].str.contains(job_title_pattern, regex=True))  # Job title
)

m_abbr_target = (df['abbr_company'] == norm_keyword)  # "om" → "Old Mission"

m_abbr_keyword_vs_abbr_target = pd.Series([False] * len(df))
if len(abbr_keyword) > 1:  # Prevent single-letter false positives
    m_abbr_keyword_vs_abbr_target = (df['abbr_company'] == abbr_keyword)

# 3. Combine masks
final_mask = m_base | m_abbr_target | m_abbr_keyword_vs_abbr_target

# 4. Filter and return
matched_df = df[final_mask]
```

**Performance**:
- Before: O(n) row-by-row iteration with function calls
- After: O(n) vectorized operations
- Speedup: ~3-5x for datasets with 100+ entries
- Scales linearly with dataset size

### 4. Session Management & Cookie Handling

#### Multi-Domain Authentication

```python
DOMAIN_KEYWORDS = {
    "https://linkedin.com/jobs": ["sign out", "profile"],
    "https://app.joinhandshake.com": ["dashboard", "applications"]
}
```

**Cookie Persistence Flow**:

```
1. Browser-based cookie capture:
   - User runs `cookie` command
   - System opens browser tabs for each domain
   - User logs in manually
   - User pastes cookie in Netscape format
   - Cookie saved to pickle file

2. Cookie loading:
   - On startup, load cookies from pickle
   - Convert to requests.Session format
   - Validate against domain keywords
   - Multi-threaded validation checks

3. Playwright integration:
   - Convert pickle cookies to Playwright format
   - Handle expires, secure, httpOnly, sameSite attributes
   - Skip expired or invalid cookies
   - Inject into browser context
```

### 5. Duplicate Detection

#### Algorithm

```python
def check_duplicate_entry(self, new_data):
    """
    Checks if entry with same Company + Job Title exists.
    Returns matching record or None.
    """
    for row in self.get_all_jobs():
        if all(row[f].strip() == str(new_data[f]).strip()
               for f in ['Company', 'Job Title'] if f in new_data):
            return row
    return None
```

**User Flow**:
1. Duplicate detected → Display existing entry
2. Prompt: "Add it anyway? (y/yes to confirm)"
3. User confirms or cancels

---

## Storage & Web UI Design

### Motivation

Earlier versions stored data in an Excel file and needed an elaborate dual cache (DataFrame + workbook), mtime-based invalidation, sync/save decorators and write-conflict detection to stay fast and safe when the file was edited externally. Moving to SQLite removes all of that machinery: transactions give consistency, there is no external file editing to detect, and a browser UI replaces "open the spreadsheet and edit".

### JobDatabase

`utils/db_utils.py::JobDatabase` is the sole data access point. One instance is created at startup and shared by the CLI thread and the web server thread.

- **Schema**: table `jobs` with `id INTEGER PRIMARY KEY AUTOINCREMENT` plus TEXT columns named exactly like the former Excel headers: `Status` and all fields from `ALL_FIELDS`. `Status` holds `''`, `REJECTED`, `PROCESSING` or `OFFER`.
- **Connections**: every operation opens a short-lived connection inside a transaction and closes it afterwards, so the two threads never share a connection object.
- **Schema upgrade**: on startup, columns missing from the table are added with `ALTER TABLE ... ADD COLUMN`.
- **Search**: the algorithm is unchanged (vectorized pandas masks); the DataFrame is now loaded from SQLite on each search instead of being cached.
- **Status & safety**: marking a status also stamps the matching date column (`Processed Date` or `Result Date`). Before marking or deleting, the database is copied to the system temp directory using SQLite's backup API.
- **Other operations**: duplicate check (Company + Job Title), summary statistics, show/delete last record, update/delete by id.

### Excel Compatibility

- **Path resolution** (`config/credential.py`): `paths.database_file_path` is used if set; for legacy configs with only `paths.excel_file_path`, the database path is the same path with `.xlsx` replaced by `.db`.
- **Import**: if the database file does not exist on startup and a legacy Excel file exists, it is imported once (`import_excel`); the status is derived from the Status cell fill color and empty rows are skipped. If the import fails, the new empty database is removed so the import is retried next time.
- **Export** (`export_excel`): writes the legacy format - header row `Status` + fields, Status cell without value but filled red/yellow/green. Used by the CLI `export` command (timestamped file next to the database) and the web `/api/export` endpoint.

### Web UI

`web/server.py` runs a `ThreadingHTTPServer` bound to `127.0.0.1:8765` (`WEB_HOST`/`WEB_PORT` in `config/config.py`). It is started in a daemon thread when the CLI starts, or standalone via `python -m intelliapply.web.server`. If the port is taken, a warning is printed and the CLI continues without it. The CLI `open` command opens the UI in the default browser.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Single-page UI (`web/index.html`, vanilla JS) |
| GET | `/api/jobs[?q=]` | All records, or smart-search results when `q` is given |
| POST | `/api/jobs` | Add a record (required-field check, 409 on duplicate unless `force`) |
| PATCH | `/api/jobs/<id>` | Update fields of a record |
| DELETE | `/api/jobs/<id>` | Delete a record (with database backup) |
| POST | `/api/jobs/<id>/mark` | Set status and stamp its date column |
| GET | `/api/summary` | Statistics (same numbers as CLI `summary`) |
| GET | `/api/export` | Download Excel export |

**UI behavior**: smart search (same algorithm as the CLI) or plain "Contains" search over all fields; status filter; click column headers to sort; double-click a cell to edit (Enter saves, Shift+Enter newline, Esc cancels, blur saves); status dropdown (setting a status stamps the date column like the CLI, clearing it does not); per-row delete with confirmation; add form with duplicate warning; summary line.

**Security**: the server only binds to localhost, and every non-GET request must be `application/json`. Browsers therefore send a CORS preflight for cross-site requests, which the server does not allow, so other websites cannot modify data.

---

## Performance Optimizations

### 1. Storage Simplification (SQLite, replaces Excel caching)

The former `ExcelManager` dual cache (DataFrame + workbook with mtime invalidation) was removed together with Excel storage. SQLite reads of a personal-scale dataset are fast enough to load per search, and there is no cached state that can become stale. See [Storage & Web UI Design](#storage--web-ui-design).

### 2. Keyword Matching Optimization (Implemented 2024-12)

**Problem**: Row-by-row iteration with multiple function calls per row was slow for large datasets.

**Solution**: Vectorized pandas operations with pre-computed helper columns.

**Impact**:
- 3-5x speedup for 100+ entries
- Better scaling with dataset growth
- Single-pass processing

**Code Location**: `utils/db_utils.py::JobDatabase.search_applications()`

### 3. Terminal Display Optimization (Implemented 2025-01)

**Problem**: Multiple print() calls caused flickering and poor performance. Fixed-width terminal truncated long content.

**Solution**:
1. **Atomic Output**: Generate all lines as list, join with `\n`, single `print()` call
2. **Dynamic Width**: Calculate actual line length, auto-resize terminal
3. **Smart Detection**: Only increase width (never decrease) based on content

**Implementation** (utils/print_utils.py:46-201):

```python
# Build all lines with inline max length tracking
lines = [header, separator]
max_line_length = max(len(header), len(separator))

for result in results:
    line = generate_row(result)  # Format data
    max_line_length = max(max_line_length, len(line))
    lines.append(line)

# Adjust terminal once, print once
auto_adjust_terminal_width(max_line_length)
print('\n'.join(lines))
```

**Impact**:
- Reduced system calls from O(n) to O(1)
- Single-pass string generation
- No content truncation
- Flicker-free output

### 4. LLM API Fallback System

**Strategy**: Multiple API services (key + endpoint + model) with ordered fallback

```python
for service in API_SERVICES:       # Try each configured service in order
    try:
        response = client.chat.completions.create(...)
        return parse(response)
    except Exception:
        continue  # Next service
```

**Benefits**:
- Resilience against rate limits
- Cost optimization across providers
- Automatic failover

---

## Data Models

### Pydantic Schema (config/prompt.py)

```python
class JobInfo(BaseModel):
    isValid: bool           # Validation flag
    Company: str            # Required
    Location: str           # Required
    Job_Title: str          # Required (mapped to "Job Title" column)
    Code: str = ""          # Optional: Job ID
    Type: str = ""          # Optional: Onsite/Hybrid/Remote
    Link: str = ""          # Optional: URL (cleaned of params)
```

### Database Schema

```python
ALL_FIELDS = [
    'Company',       # Required
    'Location',      # Required
    'Job Title',     # Required
    'Code',          # Optional
    'Type',          # Optional
    'Applied Date',  # Auto-generated (YYYY-MM-DD)
    'Processed Date',# Auto-updated when marked as PROCESSING
    'Result Date',   # Auto-updated when marked as REJECTED/OFFER
    'Link'           # Optional
]

# Table `jobs`: id INTEGER PRIMARY KEY AUTOINCREMENT,
# "Status" + ALL_FIELDS as TEXT NOT NULL DEFAULT ''
# Status values: '', 'REJECTED', 'PROCESSING', 'OFFER'
```

### Schema Migration

- **New columns**: `JobDatabase._init_schema()` compares `PRAGMA table_info(jobs)` with the expected fields and runs `ALTER TABLE ... ADD COLUMN` for any that are missing.
- **Excel to SQLite**: one-time import on first run when the database file does not exist yet (see [Excel Compatibility](#excel-compatibility)).

---

## API Integration

### LLM Prompt Engineering

**System Prompt Design** (config/prompt.py:7-43):

```json
{
  "role": "system",
  "requirements": {
    "extraction_rule": "NO PARAPHRASING. Use exact text or leave blank.",
    "required_fields_validation": "Set isValid=false if Company/Location/Job_Title missing",
    "optional_fields_validation": "Empty string if not found"
  },
  "required_fields": {
    "Company": "Company name",
    "Location": "Job location (Remote if remote, comma-separated if multiple)",
    "Job_Title": "Job title"
  },
  "optional_fields": {
    "Code": "Job ID like SOFTW008765",
    "Type": "Onsite/Hybrid/Remote or blank",
    "Link": "URL without query parameters"
  },
  "output_format": {
    "structure": "JobInfo Pydantic model",
    "formatting": "Single-line JSON, no markdown, no linebreaks"
  }
}
```

**Key Design Decisions**:
1. **Strict Validation**: `isValid` flag prevents garbage data
2. **No Paraphrasing**: Preserves original text for accuracy
3. **Structured Output**: Pydantic `response_format` ensures schema compliance
4. **Optional Fields**: Empty strings prevent N.A./Unknown clutter

### API Configuration

```python
# ~/intelliApply_config/config.yaml
api_services:                             # Tried in order (fallback)
  - api_key: "key1"
    base_url: "https://api.provider.com/v1"  # OpenAI-compatible endpoint
    model: "model-1"
    reasoning_effort: "medium"            # Optional, for reasoning models
  - api_key: "key2"
    base_url: "https://api.other.com/v1"
    model: "model-2"
```

---

## Web Scraping Architecture

### Hybrid Scraping Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    URL Input Received                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Fetch with requests  │
            └───────────┬───────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Analyze Content for JS Needs │
        │  - Hydration markers          │
        │  - <noscript> tags            │
        │  - Cloudflare challenges      │
        │  - Blocked status codes       │
        └───────────┬───────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  ┌─────────┐           ┌──────────────┐
  │  Good   │           │  Needs JS    │
  │ Content │           │  Execution   │
  └────┬────┘           └──────┬───────┘
       │                       │
       │                       ▼
       │           ┌────────────────────┐
       │           │ Fetch with         │
       │           │ Playwright         │
       │           │ (headless browser) │
       │           └──────┬─────────────┘
       │                  │
       └──────────┬───────┘
                  │
                  ▼
      ┌──────────────────────┐
      │  Clean HTML          │
      │ - Remove noise tags  │
      │ - Remove layout tags │
      │ - Preserve attributes│
      │ - Process iframes    │
      └──────────┬───────────┘
                 │
                 ▼
      ┌──────────────────────┐
      │  Send to LLM         │
      │  Extract job info    │
      │  Validate & store    │
      └──────────────────────┘
```

### Content Analysis Heuristics

```python
HYDRATION_PATTERNS = [
    r'__NEXT_DATA__',              # Next.js server-side data
    r'data-reactroot',             # React hydration root
    r'id=["\'](?:root|app)["\']'   # SPA mount points
]

JS_REQUIRED_PATTERNS = [
    r'please enable javascript',
    r'enable javascript',
    r'<noscript',
    r'cloudflare', r'cf-ray'
]

BLOCK_STATUS = {403, 429, 503}  # Challenge/rate-limit codes

# Playwright browser channel configuration
_CHROME_CHANNELS = ['chrome', 'chrome-dev', 'chrome-canary']
```

### Playwright Browser Channel Auto-Detection

**Startup Optimization**: Automatically detects the best available browser channel at startup with intelligent fallback.

**Detection Strategy**:
```python
_CHROME_CHANNELS = ['chrome', 'chrome-dev', 'chrome-canary', '']  # '' = default chromium

def detect_playwright_channel():
    for channel in _CHROME_CHANNELS:
        try:
            browser = p.chromium.launch(channel=channel, headless=True)
            browser.close()
            return channel
        except:
            continue
    
    # No browser found - auto-install Playwright chromium
    ensure_playwright_browsers()
    return ''

_PLAYWRIGHT_CHANNEL = detect_playwright_channel()  # Runs once at module load
```

**Fallback Mechanism**:
1. Try Chrome variants in priority order
2. Try default Playwright chromium (`channel=''`)
3. If all fail, auto-install via `playwright install chromium`
4. Exit if installation fails (user must fix environment)

**Key Benefits**:
- **Zero configuration**: Works out-of-box with any Chrome or Playwright chromium
- **Fast**: Single detection at startup (~100-300ms), saves 50-100ms per request
- **Resilient**: Auto-installs missing browsers
- **Consistent**: Same browser for entire session

**Usage**: `browser = p.chromium.launch(channel=_PLAYWRIGHT_CHANNEL, headless=True)`

### Iframe Processing

```python
def process_requests_content(content, redirect=True):
    """
    Recursively process iframe content:
    1. Find all <iframe> tags
    2. Fetch iframe src URLs
    3. Append inline to main content with markers
    4. Prevents infinite recursion with redirect=False flag
    """
```

### HTML Content Cleaning

**Function**: `remove_script_content()` (utils/web_utils.py:317-358)

**Design Philosophy**: "Maximum Compatibility" approach - only removes universally safe-to-remove, high-token content while preserving all semantic information that could help LLM extraction.

**Removal Strategy**:

```python
def remove_script_content(html_content: str) -> str:
    """
    Cleans HTML for job extraction to achieve "maximum compatibility" while reducing tokens.
    Only removes content that can be safely removed on any website with high token 
    consumption and zero information value.
    
    It preserves all other tags, all attributes (class, id, itemprop, etc.) and all text 
    content to ensure the LLM has sufficient context for extraction.
    """
```

**Removed Content**:
1. **Noise tags**: `<script>`, `<style>`, `<svg>`, `<link>`, `<noscript>` - High token count, zero information value
2. **Layout tags**: `<header>`, `<footer>`, `<nav>`, `<aside>` - High token count, unlikely to contain core JD info
3. **HTML comments**: All comment nodes removed

**Preserved Content**:
- **All HTML attributes**: `class`, `id`, `itemprop`, `data-*`, etc. - Preserved for semantic context
- **All text content**: Complete text nodes retained
- **All structural tags**: `<div>`, `<span>`, `<p>`, `<h1-h6>`, etc. - Preserved for context

**Token Optimization**:
- Collapses multiple consecutive empty lines into single newline
- Strips leading/trailing whitespace from each line
- Removes empty lines entirely

**Key Design Decision**: Unlike previous versions that removed all attributes except `href` on `<a>` tags, the current implementation preserves **all attributes** to maximize LLM context. This ensures semantic information encoded in attributes (like `itemprop`, `class` names, `data-*` attributes) remains available for extraction.

**Usage**: Called automatically in `process_requests_content()` and `fetch_with_playwright()` before sending content to LLM.

### Local Backup System

**SingleFile Integration** (utils/singlefile.py):
- Runs asynchronously in daemon thread
- Captures complete webpage with embedded assets
- Filename format: `Company_JobTitle_YYYYMMDD_N.html`
- Stored in configured BACKUP_FOLDER_PATH
- Does not block main workflow

---

## User Experience Design

### Interactive CLI Design

**Prompt System**:

```python
DEFAULT_PROMPT = """
Search: Enter keywords or initials
Add new record: Enter one-line JSON data / URL / webpage content (wrapped with '< >' or '```')
Other commands: delete last record, update cookie, view statistics summary, open web UI, export Excel file, exit tool
"""

UPDATE_PROMPT = """
Update status: Enter number+action (e.g. 1r=line 1 as reject, 2p=line 2 as processing, 3o=line 3 as offer)
"""
```

**Context-Aware Prompting**: UPDATE_PROMPT only shown when search results are active.

### Signal Handling

```python
def signal_handler(sig, frame):
    global exit_flag
    if not exit_flag:
        print_("Previous line deleted. Press Ctrl+C again to exit.", "YELLOW")
        exit_flag = True
    else:
        save_cookie()
        sys.exit(0)
```

**Design**: First Ctrl+C cancels current operation, second Ctrl+C saves cookies and exits gracefully.

### Multi-Line Input Detection

```python
def detect_ending(min_threshold=0.05, max_threshold=0.5):
    """
    Detects double Enter press or ending markers (> or ```)
    within threshold seconds to signal end of multi-line input.
    """
```

**UX Flow**:
1. User starts typing multi-line content
2. System detects wrapper characters (< or ```)
3. Continues accepting input until:
   - Closing wrapper detected (> or ```)
   - Double Enter within 0.05-0.5 seconds
   - EOF or KeyboardInterrupt

### Color-Coded Output

```python
COLOR = {
    "RED": '\033[31m',        # Errors, cancellations
    "GREEN": '\033[32m',      # Success, confirmations
    "YELLOW": '\033[33m',     # Warnings, info
    "BLUE": '\033[34m',       # Prompts, questions
    "BOLD": '\033[1m',
    "ITALIC": '\033[3m',
    "BOLD_ITALIC": '\033[1;3m',
    "RESET": '\033[0m'
}
```

### Result Display

**Adaptive Column Widths**:
```python
company_width = max(len(format_string(r['Company'], limit=30)) for r in results)
job_width = max(len(format_string(r['Job Title'], limit=65)) for r in results)
```

**Dynamic Layout**:
- With Applied Date: `No. | Applied Date | Status | Company | Location | Job Title`
- Without Applied Date: `No. | Status | Company | Location | Job Title`
- Mark mode adds numbered index for selection

---

## Security Considerations

### Credential Management

```yaml
# ~/intelliApply_config/config.yaml (auto-created from template)
api_services:
  - api_key: "your-api-key-here"
    base_url: "https://..."
    model: "gemini-2.5-flash"

paths:
  database_file_path: "/path/to/job_applications.db"
  backup_folder_path: "/path/to/backups"
```

**Best Practices**:
- Config stored in user home directory (`~/intelliApply_config/`)
- Auto-created from `credential-example.yaml` on first run
- Opens default editor for user to configure
- Validates config before proceeding
- No credentials in version control

### Cookie Security

**Storage**:
- Cookies stored in pickle format
- File path configurable in config.py
- Not encrypted (relies on file system permissions)

**Validation**:
- Multi-threaded validation on startup
- Domain keyword matching prevents invalid sessions
- User prompted to update if validation fails

### LLM Data Privacy

**Concerns**:
- Job posting content sent to external LLM API
- May contain sensitive company information

**Mitigations**:
- Users can self-host OpenAI-compatible models
- BASE_URL configurable for private endpoints
- No user data stored by IntelliApply beyond the local SQLite database
- The web UI binds to `127.0.0.1` only and requires `application/json` for all write requests (forces a CORS preflight, blocking cross-site modification)

---

## Statistics & Analytics

### Summary Function

```python
def summary():
    """
    Displays:
    - Total Applications
    - Rejected count
    - Processing count
    - Offers count
    - Rejection Rate: rejections / total * 100
    - Processing Rate: processing / total * 100
    - Offer Rate: offers / processing * 100
    """
```

**Offer Rate Design**: Calculated as `offers / processing` rather than `offers / total` to show conversion rate from processing stage to offer stage.

---

## Testing & Quality Assurance

### Test Files

There is no automated test suite. `applied_job_checker.py` is only a compatibility alias that runs `intelliapply.main:main`.
The 2026-09-30 refactor was verified manually; see [refactor_20260930.md](refactor_20260930.md) for the procedure and results.

### Manual Testing Checklist

1. **Input Processing**
   - [ ] URL scraping (static content)
   - [ ] URL scraping (dynamic content / JavaScript)
   - [ ] Markdown table parsing
   - [ ] JSON input validation
   - [ ] Raw text with wrapper characters

2. **Search Functionality**
   - [ ] Direct company name match
   - [ ] Prefix matching
   - [ ] Abbreviation matching (both types)
   - [ ] Job title word-level matching

3. **Status Management**
   - [ ] Mark as rejected (Result Date)
   - [ ] Mark as processing (Processed Date)
   - [ ] Mark as offer (Result Date)

4. **Web UI & Export**
   - [ ] Smart / Contains search, status filter, column sort
   - [ ] Double-click edit (Enter / Shift+Enter / Esc / blur)
   - [ ] Status dropdown stamps date column; clearing keeps dates
   - [ ] Add record (required fields, duplicate confirm), delete with confirm
   - [ ] Export Excel (web download and CLI `export`) keeps legacy format

5. **Session Management**
   - [ ] Cookie save/load
   - [ ] Cookie validation
   - [ ] Browser-based cookie update

6. **Error Handling**
   - [ ] Legacy Excel import / missing column upgrade
   - [ ] Duplicate entry confirmation
   - [ ] LLM API failures
   - [ ] Network errors

---

## Future Roadmap

### Planned Features

#### 1. Database Migration (Implemented)
Excel storage was replaced by SQLite (`JobDatabase`), with automatic import of legacy Excel files and Excel export.

#### 2. Web Interface (Implemented, basic)
A local single-page web UI (search, sort, inline edit, status, add/delete, summary, Excel export) is served by the CLI. Still open: charts/dashboard, calendar view, PDF/CSV export, multi-user support.

#### 3. Email Integration
**Goal**: Automatic status updates from email monitoring
**Approach**:
- IMAP integration for email parsing
- Regex patterns for rejection/offer emails
- Auto-update status in database

#### 4. Browser Extension
**Goal**: One-click job posting capture
**Features**:
- Detect job posting pages
- Extract with content script
- Send to backend API
- Visual confirmation

#### 5. Resume/Cover Letter Matching
**Goal**: LLM-powered resume tailoring suggestions
**Features**:
- Extract key requirements from job posting
- Compare with resume
- Suggest modifications
- Generate cover letter draft

#### 6. Analytics Dashboard
**Goal**: Advanced insights into job search
**Metrics**:
- Application velocity over time
- Response rate by company/industry
- Time to offer
- Offer acceptance rate

#### 7. Notification System
**Goal**: Proactive reminders and alerts
**Features**:
- Email/Slack notifications
- Reminder for follow-ups
- Deadline tracking
- Interview scheduling

---

## Appendix

### Commit History Highlights

```
fb543fa - Update confirmation prompts and adjust color usage
b3a6188 - Improve user input handling for marking commands
c064c02 - Add multi-status tracking with date columns
7f92f0d - Add terminal width adjustment functions
879618a - Refactor Excel validation and search logic (later replaced by SQLite storage)
83de6e0 - Enhance job title and company matching
c1e39e6 - Implement local backup functionality
a24de30 - Add JSON input handling and validation
449a8eb - Implement content analysis to decide Playwright usage
```

### Performance Benchmarks

**Search Performance** (100 entries, vectorized):
- Before optimization: ~150ms
- After vectorization: ~30ms
- Speedup: **5x**

**Terminal Rendering** (10 results):
- Before optimization: 10 print() calls, ~50ms
- After optimization: 1 print() call, ~5ms
- Speedup: **10x**

---

## Package Distribution

### PyPI Package Structure

IntelliApply is distributed as a Python package with the following characteristics:

**Package Name**: `intelliapply`
**Entry Points**:
- CLI command: `intelliapply` → `intelliapply.main:main`
- Module execution: `python -m intelliapply` → `intelliapply.__main__:main`

**Installation Methods**:
```bash
# Global installation with pipx (recommended for CLI tools)
pipx install git+https://github.com/Jason-LJQ/IntelliApply.git

# Local installation with pip
pip install git+https://github.com/Jason-LJQ/IntelliApply.git

# Development installation from source
git clone https://github.com/Jason-LJQ/IntelliApply.git
cd IntelliApply
pip install -e .
# Or: uv pip install -e .
```

**Build System**: `setuptools` with `pyproject.toml` configuration

**Dependencies**: See `pyproject.toml` for full dependency list

---

**Last Updated**: 2025-10-18
**Author**: Jason Liao
**License**: See LICENSE file
