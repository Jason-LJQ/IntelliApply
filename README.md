# IntelliApply

> **Intelligent job application tracking powered by AI**

Track your job applications effortlessly with LLM-powered information extraction, smart search, and multi-status workflow management. Simply paste a job URL and let AI do the rest.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

See [DESIGN.md](DESIGN.md) for technical showcase, architecture deep-dive, performance analysis, and more.

Stars are welcomed! ^_^

---

## What is IntelliApply?

IntelliApply is a **command-line job application tracker** that eliminates the tedium of manual data entry. It combines:

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

---

## Key Features

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
- **Cookie persistence**: Stay logged into LinkedIn and Handshake

### Data Management
- **Excel storage**: Familiar format with color-coded status cells
- **Duplicate detection**: Warns before adding the same job twice
- **Schema validation**: Automatic migration for backward compatibility
- **Local backups**: Saves HTML copies of job postings for offline reference

## Quick Start

### Prerequisites

- **Python 3.8+**
- **OpenAI-compatible API key** (Google Gemini, OpenAI, or any compatible provider)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Jason-LJQ/IntelliApply.git
cd IntelliApply

# 2. Install dependencies (using uv, recommended)
uv install

# 3. Install Playwright browsers for JavaScript-heavy job sites
playwright install

# 4. Configure your credentials
cp config/credential-example.py config/credential.py
# Edit config/credential.py with your settings:
#   - API_KEY_LIST: Your LLM API key(s)
#   - BASE_URL: API endpoint URL
#   - EXCEL_FILE_PATH: Where to store your job data
#   - BACKUP_FOLDER_PATH: Where to save job posting backups

# 5. Run IntelliApply
python main.py
```

### Configuration

Open `config/credential.py` and set:

```python
# LLM API Configuration
API_KEY_LIST = ["your-api-key-here"]  # Add multiple keys for fallback
BASE_URL = "https://api.provider.com/v1"  # OpenAI-compatible endpoint
MODEL_LIST = ["model-name"]  # Model priority order

# Storage Configuration
EXCEL_FILE_PATH = "/path/to/your/job_applications.xlsx"
BACKUP_FOLDER_PATH = "/path/to/job_backups"
```

IntelliApply will create the Excel file automatically on first run.

## Usage Guide

### Starting IntelliApply

```bash
python main.py
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
5. Save to Excel with current date
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
| `open` | Open Excel file in default application |
| `cookie` | Update session cookies for authenticated sites |
| `delete` | Delete last added entry (with confirmation) |
| `last` | Show last added entry |
| `clear` | Clear terminal screen |
| `exit` | Save cookies and exit |
| `Ctrl+C` | First press cancels operation, second press exits |

---

### Tips & Tricks

1. **Multiple API keys**: Add multiple API keys to `API_KEY_LIST` for automatic fallback if one hits rate limits
2. **Batch adding**: You can quickly add multiple jobs by pasting URLs one after another
3. **Search shortcuts**: Use 2-3 letter abbreviations for quick company lookup (e.g., "gs" for Goldman Sachs)
4. **Status workflow**: Start with blank → mark as Processing when you hear back → mark as Rejected/Offer when finalized
5. **Excel editing**: You can open the Excel file directly (`open` command) and manually edit if needed
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
6. **Storage**: Save to Excel with color-coded status cell
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

Configure in `config/credential.py`:
```python
BASE_URL = "https://your-provider.com/v1"
MODEL_LIST = ["your-model-name"]
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

**Excel Schema:**
```
Status | Company | Location | Job Title | Code | Type | Applied Date | Processed Date | Result Date | Link
```

- `Status`: Hidden column with cell fill color (Red/Yellow/Green)
- `Applied Date`: Auto-generated on entry creation (YYYY-MM-DD)
- `Processed Date`: Updated when marked as Processing
- `Result Date`: Updated when marked as Rejected or Offer

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

**Q: Search doesn't find jobs I know exist**
- Try searching by initials or abbreviation
- Check spelling of company name in Excel file
- Use job title keywords instead of company name

**Q: Playwright times out on certain sites**
- Some sites have aggressive anti-bot measures
- Try manually copying content and wrapping with `< >`
- Increase timeout in `web_utils.py` if needed

**Q: Cookie validation fails**
- Run `cookie` command to update session cookies
- Log into sites manually through opened browser tabs
- Paste cookie in Netscape format when prompted

**Q: Excel file has missing columns**
- System will detect and prompt for backup + migration
- Confirm migration to create new file with correct schema
- Manually copy data from backup if needed

---

## Contributing

Contributions are welcome! Areas for improvement:

- [ ] Web interface (React/Vue frontend)
- [ ] Database migration (SQLite/PostgreSQL)
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
