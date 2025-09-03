# IntelliApply

An intelligent job application tracking system with LLM-powered information extraction and management capabilities.

## Overview

IntelliApply is a smart command-line tool designed to streamline the job application process. It uses LLM-powered
information extraction to process job postings from various sources, automatically extracting structured job
information, tracking application status, and providing powerful search capabilities through an interactive CLI. The
system supports multiple input formats including URLs, markdown tables, and raw content, with automatic duplicate
detection and Excel-based storage.

Stars are welcomed! ^_^

## Screenshots

![Add new jobs](images/Screenshot%201.png)
![Search jobs and mark results](images/Screenshot%202.png)

## Features

- **LLM-Powered Information Extraction**: Uses OpenAI-compatible API endpoints with sophisticated prompt engineering and
  Pydantic models for accurate job information extraction
- **Multi-Format Input Processing**: Process job information from:
    - **URLs**: Direct job posting links with intelligent web scraping (static and dynamic content support)
    - **Markdown tables**: Structured job data with automatic parsing
    - **Raw content**: Text wrapped with `< >` or triple backticks for LLM processing
- **Advanced Web Scraping**:
    - Static content using requests + BeautifulSoup
    - Dynamic content using Playwright for JavaScript-heavy pages
    - Session-based scraping with cookie persistence for authenticated portals (LinkedIn, Handshake)
- **Intelligent Data Management**:
    - Excel-based storage with automatic schema validation
    - Duplicate detection using company name matching algorithms
    - Application status tracking with color-coded results
- **Interactive CLI**: User-friendly command-line interface with signal handling (Ctrl+C) for graceful shutdown

## System Requirements

- Python 3.8+
- OpenAI-compatible API key (supports Google Gemini and other providers)
- Required Python packages (managed via pyproject.toml)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Jason-LJQ/IntelliApply.git
   cd IntelliApply
   ```

2. Install dependencies:
   ```bash
   # Using uv (recommended)
   uv install
   ```

3. Install Playwright browsers (required for dynamic content scraping):
   ```bash
   playwright install
   ```

4. Set up your credentials:
   ```bash
   # Copy credential template and configure
   cp config/credential-example.py config/credential.py
   # Edit config/credential.py with your API key and Excel file path
   ```

### Configuration Requirements

Before running, ensure:

1. OpenAI-compatible API key is set in `config/credential.py`
2. Base URL for the API endpoint is configured in `config/credential.py`
3. Excel file path is configured in `config/credential.py`
4. Excel file exists or allow the system to create it on first run

## Usage

Run the main script:

```bash
python main.py
```

### Core Commands

- **Search jobs**: Simply enter your search term to find existing applications
  ```
  > Amazon
  ```

- **Add a job posting (URL)**: Paste a job posting URL for automatic extraction
  ```
  > https://example.com/jobs/12345
  ```

- **Add job from web content**: Paste content wrapped with `< >` or triple backticks for LLM processing
  ```
  > < Job Title: Software Engineer
    Company: Example Inc.
    Location: Remote
    >
  ```

- **Add job from Markdown table**: Paste a properly-formatted Markdown table with structured data
  ```
  > | Company | Location | Job Title | Code | Type | Link |
    | ------- | -------- | --------- | ---- | ---- | ---- |
    | Example Inc | Remote | Software Engineer | ENG123 | Remote | https://example.com/jobs/123 |
  ```

- **View statistics**: See a summary of your job applications
  ```
  > summary
  ```

- **Mark application status**: Update the status of applications
  ```
  > result
  ```
  (Then select numeric options to mark rejection status)

- **Update session cookies**: Update cookies using browser automation for authenticated portals
  ```
  > cookie
  ```

- **Delete last entry**: Remove the most recently added job entry
  ```
  > delete
  ```

- **Exit the application**: Save cookies and exit gracefully
  ```
  > exit
  ```

### Additional Features

- **Signal handling**: Press Ctrl+C for graceful shutdown with automatic cookie saving
- **Duplicate detection**: Automatic identification of duplicate job postings using company name matching
- **Session management**: Persistent cookie storage for authenticated job portals (LinkedIn, Handshake)
- **Multi-threaded processing**: Efficient cookie loading and validation

## LLM Integration

IntelliApply uses OpenAI-compatible API endpoints for job information extraction with sophisticated prompt engineering.
The `JobInfo` Pydantic model defines the expected output structure with required fields (Company, Location, Job Title)
and optional fields (Code, Type, Link). The system includes strict validation rules to ensure accurate extraction
without paraphrasing, using the `SYSTEM_PROMPT` template for consistent results.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See the LICENSE file for details.

## Acknowledgements

- Google Gemini API and other OpenAI-compatible providers for powering information extraction
- OpenAI and Anthropic Claude for inspiration and alternative models
- All the job boards that unintentionally contributed to this project's development

---

*Built with ❤️ by [Jason Liao](https://github.com/Jason-LJQ)*
