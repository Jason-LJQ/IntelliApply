# IntelliApply

> **Intelligent job application tracking powered by AI**

Track your job applications effortlessly with LLM-powered information extraction, smart search, and multi-status workflow management. Simply paste a job URL and let AI do the rest.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

See [DESIGN.md](DESIGN.md) for technical showcase, architecture deep-dive, performance analysis, and more.

Stars are welcomed! ^_^

---

## What is IntelliApply?

IntelliApply is a **command-line job application tracker** (with a local web UI) that eliminates the tedium of manual data entry. It combines:

- **AI-Powered Extraction**: Paste any job URL, and LLM automatically extracts company, location, job title, and more
- **Smart Search**: Find applications instantly by company name, initials, or job title
- **Multi-Status Tracking**: Track applications through Rejected/Processing/Offer stages with dates
- **Universal Input**: Supports URLs, markdown tables, JSON, and raw text
- **Duplicate Detection**: Prevents accidentally adding the same job twice
- **Session Management**: Remembers your login cookies for LinkedIn, Handshake, and other job boards

Perfect for anyone managing multiple job applications and tired of spreadsheet drudgery.

---

## Screenshots

![Add new jobs](images/Screenshot%201.png)
*Add jobs by simply pasting URLs - AI extracts all the details*

![Search jobs and mark results](images/Screenshot%202.png)
*Search and update application status with simple commands*

![Web UI](images/Screenshot%203.png)
*Built-in Web UI for searching, sorting, editing, and exporting*

---

## Key Features

### SQLite Storage & Web UI
Your data lives in a single local SQLite file (Python standard library, no extra dependencies):
- **Simple & robust**: Short-lived connection per operation, so the CLI and the web UI safely share the same data
- **Automatic backups**: The database is copied to your system temp directory before marking statuses or deleting records
- **Built-in Web UI**: Starts automatically with the CLI at `http://127.0.0.1:7779` (localhost only) - search, sort, edit cells inline, change status, add and delete records
- **Excel when you need it**: Import an existing Excel file automatically on first run, export any time with the `export` command

### AI-Powered Extraction
Paste any job posting URL and watch as AI automatically extracts:
- Company name
- Job title
- Location (including remote/hybrid)
- Job ID/code
- Job type (Onsite/Hybrid/Remote)
- Cleaned posting URL

Works with **any job board** - LinkedIn, Handshake, Greenhouse, Lever, company career pages, and more.

### Smart Search Engine
Find applications instantly with flexible search:
```bash
> Amazon          # Find by company name
> am              # Find by initials (Amazon, Amplitude, etc.)
> GSK             # Find by abbreviation (GlaxoSmithKline)
> engineer        # Find by job title keywords
```
**3-5x faster** than traditional search thanks to vectorized pandas operations.

### Multi-Status Workflow
Track your application lifecycle with three distinct stages:
- **Processing** (Yellow →): Application under review, tracks Processed Date
- **Rejected** (Red ⨉): Application rejected, tracks Result Date
- **Offer** (Green ✔): Offer received, tracks Result Date

Update status with simple commands:
```bash
1p    # Mark line 1 as Processing
2r    # Mark line 2 as Rejected
3o    # Mark line 3 as Offer
```

### Multiple Input Formats
IntelliApply is flexible about how you add jobs:
- **URLs**: Just paste the job posting link
- **Markdown Tables**: Copy-paste from spreadsheets
- **JSON**: Import from other systems
- **Raw Text**: Wrap content in `< >` or triple backticks

### Intelligent Web Scraping
- **Static pages**: Fast scraping with requests + BeautifulSoup
- **JavaScript-heavy pages**: Automatic fallback to Playwright for SPAs
- **Smart detection**: Analyzes content to choose the right method
- **Browser optimization**: Auto-detects best Chrome channel at startup (no runtime overhead)
- **Cookie persistence**: Stay logged into LinkedIn and Handshake

### Data Management
- **SQLite storage**: A single local `.db` file, editable through the CLI or the Web UI
- **Excel import/export**: Legacy Excel files are imported automatically; export to color-coded `.xlsx` with `export`
- **Duplicate detection**: Warns before adding the same job twice
- **Schema upgrade**: Missing columns are added to the database automatically
- **Local backups**: Saves HTML copies of job postings for offline reference

## Quick Start

### Prerequisites

- **Python 3.11+**
- **OpenAI-compatible API key** (Google Gemini, OpenAI, or any compatible provider)
- **Chrome browser** (Chrome, Chrome Dev, or Chrome Canary) - Required for JavaScript-heavy job sites

### Installation

#### Option 1: Install from GitHub (Recommended)

```bash
# Install globally with pipx (recommended for CLI tools)
pipx install git+https://github.com/Jason-LJQ/IntelliApply.git

# Or install with pip
pip install git+https://github.com/Jason-LJQ/IntelliApply.git

# Configure credentials
intelliapply  # Run the command
# Edit ~/intelliApply_config/config.yaml with your settings
```

#### Option 2: Install from Source

```bash
# 1. Clone the repository
git clone https://github.com/Jason-LJQ/IntelliApply.git
cd IntelliApply

# 2. Install with pip
pip install -e .

# Or using uv (faster)
uv pip install -e .

# 3. Run IntelliApply
intelliapply
# Or: python -m intelliapply
```

#### Updating IntelliApply

**If installed with pipx:**
```bash
# Update to latest version from GitHub
pipx upgrade intelliapply

# Or force reinstall if upgrade doesn't work
pipx reinstall intelliapply

```

**If installed with pip:**
```bash
# Update to latest version
pip install --upgrade git+https://github.com/Jason-LJQ/IntelliApply.git
```

**If installed from source:**
```bash
# Pull latest changes and reinstall
git pull
pip install -e .  # or: uv pip install -e .
```

**First-time setup**:
- On first run, IntelliApply creates `~/intelliApply_config/config.yaml`
- The config file will open in your default editor automatically
- Edit the file with your settings:
  - `api_services`: Your LLM API service(s) (`api_key`, `base_url`, `model`, optional `reasoning_effort`)
  - `paths.database_file_path`: Where to store your job data (SQLite file)
  - `paths.backup_folder_path`: Where to save job posting backups
- Save and press Enter to continue

**Note**: IntelliApply automatically detects the best available browser (Chrome variants or Playwright chromium) at startup. If no browser is found, it will auto-install Playwright's chromium.

### Configuration

Your configuration is stored at `~/intelliApply_config/config.yaml`. Edit it anytime:

```yaml
# LLM API Configuration
# List of API services, tried in order from top to bottom
api_services:
  - api_key: "your-api-key-here"
    base_url: "https://api.provider.com/v1"  # OpenAI-compatible endpoint
    model: "model-name"
    reasoning_effort: "none"  # Optional: none, low, medium, high

  # Add more services as fallback
  # - api_key: "sk-proj-xxxxx"
  #   base_url: "https://api.openai.com/v1/"
  #   model: "gpt-4o"

# Storage Configuration
paths:
  database_file_path: "/path/to/your/job_applications.db"
  # Optional: legacy Excel file, imported once when the database is first created
  # excel_file_path: "/path/to/your/job_applications.xlsx"
  backup_folder_path: "/path/to/job_backups"
```

IntelliApply will create the database file automatically on first run.

### Migrating from Excel

Earlier versions stored data in an Excel file. If your config still has `paths.excel_file_path` (and no `database_file_path`), nothing breaks:
- The database path is derived by replacing the `.xlsx` extension with `.db`
- On first run, when the database file does not exist yet, the Excel file is imported automatically (status is read from the Status cell fill color)
- The original Excel file is left untouched and is no longer updated afterwards

You can also set `database_file_path` explicitly and keep `excel_file_path` for the one-time import.

## Usage Guide

### Starting IntelliApply

```bash
# If installed with pip/pipx
intelliapply

# If installed from source with -e flag
python -m intelliapply
```

You'll see a welcome prompt with available commands. The interface adapts based on context (e.g., shows status marking commands after search).

---

### Common Workflows

#### 1. Adding a Job Application

**Easiest method - Just paste the URL:**
```bash
> https://jobs.lever.co/company/position-id
```

IntelliApply will:
1. Fetch the webpage (tries fast method first, fallback to browser if needed)
2. Send content to LLM for extraction
3. Validate required fields (Company, Location, Job Title)
4. Check for duplicates
5. Save to the database with current date
6. Backup HTML locally (async, doesn't block)

**Alternative methods:**

**From raw text:**
```bash
> <
Job Title: Senior Software Engineer
Company: Acme Corp
Location: San Francisco, CA
>
```

**From JSON:**
```bash
> {"Company": "Acme Corp", "Location": "Remote", "Job_Title": "Engineer"}
```

**From markdown table:**
```bash
> | Company | Location | Job Title | Code | Type | Link |
  | ------- | -------- | --------- | ---- | ---- | ---- |
  | Acme | Remote | Engineer | ENG123 | Remote | https://... |
```

---

#### 2. Searching Applications

Simply type a search term - no special commands needed:

```bash
# Search by company name
> Databricks

# Search by initials
> am          # Finds Amazon, Amplitude, etc.

# Search by abbreviation
> GSK         # Finds GlaxoSmithKline

# Search by job title
> engineer    # Finds all engineer positions
```

**Search results show:**
- Line number (for status marking)
- Applied date
- Current status (⨉/→/✔ or blank)
- Company name
- Location
- Job title

---

#### 3. Updating Application Status

After searching, mark status with `<number><action>`:

```bash
> Amazon         # Search first
Found 3 matching records:
No.  Applied Date  Status  Company  Location      Job Title
1    2025-10-10           Amazon    Seattle, WA   Software Engineer
2    2025-10-12           Amazon    Remote        SDE II
3    2025-10-14           Amazon    NYC           ML Engineer

> 1p             # Mark line 1 as Processing
> 2r             # Mark line 2 as Rejected
> 3o             # Mark line 3 as Offer (lucky you!)
```

**Actions:**
- `p` = Processing (yellow)
- `r` = Rejected (red) - default if you just type a number
- `o` = Offer (green)

**Confirmation prompt:**
System shows the job details and asks for confirmation before marking.

---

#### 4. Viewing Statistics

```bash
> summary
```

Displays:
- Total applications
- Rejected / Processing / Offer counts
- Rejection rate (% of total)
- Processing rate (% of total)
- Offer rate (% of processing stage)

---

#### 5. Managing Session Cookies

For LinkedIn, Handshake, and other authenticated job boards:

```bash
> cookie
```

System will:
1. Check if current cookies are valid
2. If invalid, open browser tabs for each configured domain
3. You log in manually
4. Paste cookie in Netscape format
5. Cookie saved for future sessions

---

#### 6. Using the Web UI

The Web UI starts automatically in the background when the CLI starts. Type `open` to launch it in your browser, or visit `http://127.0.0.1:8765`. To run it without the CLI:

```bash
python -m intelliapply.web.server
```

- **Search**: "Smart" mode uses the same algorithm as the CLI; "Contains" mode matches text in any field. Filter by status with the dropdown
- **Sort**: Click a column header (click again to reverse)
- **Edit**: Double-click any cell. `Enter` saves, `Shift+Enter` inserts a new line, `Esc` cancels, clicking away saves
- **Status**: Use the status dropdown in a row. Setting a status also stamps its date column, like the CLI; choosing no status just clears it
- **Add / delete**: "+ Add record" opens a form (with a duplicate warning); each row has a delete button with confirmation
- **Statistics**: Summary line shows totals and rates
- **Export**: "Export Excel" downloads an `.xlsx` file

The server only listens on localhost, and all write requests must be `application/json`, so other websites cannot modify your data. If the port is already in use (e.g. another IntelliApply instance), the CLI prints a warning and continues without the Web UI.

---

#### 7. Exporting to Excel

```bash
> export
```

Writes `job_applications_YYYYmmdd_HHMMSS.xlsx` next to the database file. The header row is `Status` + the data columns; the Status cell is empty but filled red/yellow/green.

---

### All Commands

| Command | Description |
|---------|-------------|
| `<search term>` | Search applications by company, initials, or job title |
| `<URL>` | Add job from URL (auto-detected) |
| `< content >` | Add job from wrapped text content |
| `<JSON>` | Add job from JSON object |
| `<markdown table>` | Add job from table format |
| `<number><action>` | Mark status: `1p` (processing), `2r` (rejected), `3o` (offer) |
| `summary` | View application statistics |
| `open` | Open the web UI in your default browser |
| `export` | Export all records to a timestamped Excel file next to the database |
| `cookie` | Update session cookies for authenticated sites |
| `delete` | Delete last added entry (with confirmation) |
| `last` | Show last added entry |
| `clear` | Clear terminal screen |
| `exit` | Save cookies and exit |
| `Ctrl+C` | First press cancels operation, second press exits |

---

### Tips & Tricks

1. **Multiple API services**: Add several entries under `api_services` in `config.yaml` for automatic fallback if one hits rate limits
2. **Batch adding**: You can quickly add multiple jobs by pasting URLs one after another
3. **Search shortcuts**: Use 2-3 letter abbreviations for quick company lookup (e.g., "gs" for Goldman Sachs)
4. **Status workflow**: Start with blank → mark as Processing when you hear back → mark as Rejected/Offer when finalized
5. **Web UI editing**: Use the `open` command to fix typos or change statuses in the browser - double-click any cell to edit
6. **Terminal width**: Terminal automatically adjusts width to fit content - no more new-line text!

---

## How It Works

### Architecture Overview

```
User Input → Input Detection → Processing Pipeline → LLM Extraction → Validation → Storage
```

1. **Input Detection**: System identifies input type (URL, JSON, markdown, or text)
2. **Web Scraping** (if URL):
   - Try fast static scraping (requests + BeautifulSoup)
   - Analyze content for JavaScript requirements
   - Fallback to Playwright if needed (JavaScript-rendered pages)
3. **LLM Extraction**: Send content to OpenAI-compatible API with structured prompt
4. **Validation**: Pydantic models ensure all required fields present
5. **Duplicate Check**: Compare with existing entries
6. **Storage**: Save to the SQLite database
7. **Backup**: Asynchronously save HTML copy to local storage

### LLM Prompt Engineering

IntelliApply uses carefully crafted prompts with Pydantic structured outputs:

```python
Required Fields (validation fails if missing):
  - Company name
  - Location (preserves format, comma-separated if multiple)
  - Job title

Optional Fields (empty string if not found):
  - Job ID/code
  - Type (Onsite/Hybrid/Remote)
  - URL (cleaned of tracking parameters)

Strict Rules:
  - NO paraphrasing - use exact text from posting
  - NO speculation - leave blank if not found
  - NO placeholders like "N/A" or "Unknown"
```

This design ensures high accuracy and prevents garbage data.

---

## Advanced Topics

### Supported LLM Providers

IntelliApply works with any **OpenAI-compatible API**:

- **Google Gemini** (via OpenAI compatibility layer)
- **OpenAI** (GPT-3.5, GPT-4, GPT-4o)
- **Anthropic Claude** (via compatibility proxies)
- **Self-hosted models** (Ollama, vLLM, LocalAI)
- **Other providers** (Groq, Together AI, Replicate)

Configure in `~/intelliApply_config/config.yaml`:
```yaml
api_services:
  - api_key: "your-api-key"
    base_url: "https://your-provider.com/v1"
    model: "your-model-name"
```

### Performance

**Search Performance** (100 entries):
- Vectorized pandas operations: ~30ms
- Traditional row-by-row: ~150ms
- **5x faster** with current implementation

**Web Scraping**:
- Static pages (requests): 200-500ms
- Dynamic pages (Playwright): 4-7 seconds
- Automatic detection minimizes slow scraping

### Data Format

**Database schema** (SQLite table `jobs`):
```
id (auto-increment) | Status | Company | Location | Job Title | Code | Type | Applied Date | Processed Date | Result Date | Link
```

- `id`: Auto-increment primary key, used by the Web UI and status marking
- `Status`: Empty, `REJECTED`, `PROCESSING` or `OFFER`
- `Applied Date`: Auto-generated on entry creation (YYYY-MM-DD)
- `Processed Date`: Updated when marked as Processing
- `Result Date`: Updated when marked as Rejected or Offer
- All columns except `id` are stored as text; missing columns are added automatically

**Excel import/export format**: Header row `Status` + the data columns. The Status cell has no value; its fill color (red/yellow/green) represents Rejected/Processing/Offer.

### Technical Details

Want to dive deeper? See **[DESIGN.md](DESIGN.md)** for:
- Detailed system architecture
- Algorithm explanations (search, deduplication, content analysis)
- Performance optimization techniques
- Future roadmap
- Development guidelines

---

## Troubleshooting

### Common Issues

**Q: LLM extraction fails with "Invalid content format"**
- Check that required fields (Company, Location, Job Title) are present in the job posting
- Try wrapping content manually with `< >` and cleaning up formatting

**Q: Playwright browser installation prompt**
- If no Chrome or Playwright chromium is found, automatic installation will run
- This is a one-time setup that installs Playwright's chromium browser
- Alternatively, install Chrome manually from [google.com/chrome](https://www.google.com/chrome/)

**Q: Search doesn't find jobs I know exist**
- Try searching by initials or abbreviation
- Check spelling of company name in the Web UI (double-click a cell to fix it)
- Use job title keywords instead of company name

**Q: Playwright times out on certain sites**
- Some sites have aggressive anti-bot measures
- Try manually copying content and wrapping with `< >`
- Increase timeout in `web_utils.py` if needed

**Q: Cookie validation fails**
- Run `cookie` command to update session cookies
- Log into sites manually through opened browser tabs
- Paste cookie in Netscape format when prompted

**Q: My old Excel data did not show up**
- The Excel file is only imported when the database file does not exist yet
- Make sure `paths.excel_file_path` still points to the old file, and remove/rename the `.db` file to trigger a fresh import (keep a copy if you have made changes since)

**Q: Web UI is not available**
- If port 8765 is in use, the CLI prints a warning and runs without its own Web UI server
- If the port is used by another IntelliApply instance (same config), `open` still works because that instance serves the same database
- Otherwise, free the port (or change `WEB_PORT` in `intelliapply/config/config.py`) and restart

---

## Contributing

Contributions are welcome! Areas for improvement:

- [x] Web interface (local single-page UI)
- [x] Database migration (SQLite)
- [ ] Email integration for auto-status updates
- [ ] Browser extension for one-click capture
- [ ] Resume/cover letter matching with LLM
- [ ] Advanced analytics dashboard

Please feel free to:
- Report bugs via [GitHub Issues](https://github.com/Jason-LJQ/IntelliApply/issues)
- Submit feature requests
- Open pull requests with improvements

See [DESIGN.md](DESIGN.md) for architecture details before contributing.

---

## License

See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- **Google Gemini API** and **OpenAI** for powering intelligent extraction
- **Playwright** team for enabling JavaScript-heavy scraping
- **pandas** and **openpyxl** for data management capabilities
- All the job boards that (unintentionally) contributed to this project's development

---

## Star History

If you find IntelliApply useful, please consider giving it a star! ⭐

---

**Built with ❤️ by [Jason Liao](https://github.com/Jason-LJQ)**

**Questions?** Open an issue or reach out on GitHub!
