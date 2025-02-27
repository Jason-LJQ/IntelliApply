# IntelliApply

An intelligent job application tracking system with LLM-powered information extraction and management capabilities.

## Overview

IntelliApply is a smart command-line tool designed to streamline the job application process. It automatically extracts key information from job postings, tracks application status, and provides powerful search capabilities—all enhanced by Large Language Models.

## Features

- **LLM-Powered Information Extraction**: Automatically extract structured job information from various sources using Google Gemini's AI capabilities
- **Multi-Format Input Processing**: Process job information from:
  - Markdown tables
  - URLs and web content
  - Raw text and HTML
- **Intelligent Job Matching**: Advanced search and matching algorithms to identify duplicate postings and related positions
- **Application Tracking**: Mark application status and track key dates
- **Web Scraping**: Session-based web scraping with cookie persistence for authenticated portals
- **Interactive CLI**: User-friendly command-line interface with intuitive commands

## System Requirements

- Python 3.8+
- Required Python packages (see requirements.txt)
- Google API key for Gemini access

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/intelliapply.git](https://github.com/Jason-LJQ/IntelliApply.git)
   cd intelliapply
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your credentials:
   - Copy `config/credential-example.py` to `config/credential.py`
   - Add your Google Gemini API key and other credentials
   - Update the Excel file path in `config/config.py`

## Usage

Run the main script:
```bash
python main.py
```

### Core Commands

- **Search jobs**: Simply enter your search term
  ```
  > Amazon
  ```

- **Add a job posting (URL)**: Paste a job posting URL
  ```
  > https://example.com/jobs/12345
  ```

- **Add job from web content**: Paste content wrapped with `< >` or triple backticks
  ```
  > ```
    Job Title: Software Engineer
    Company: Example Inc.
    Location: Remote
    ...
    ```
  ```

- **Add job from Markdown table**: Paste a properly-formatted Markdown table
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

- **Update cookie**: Update session cookies for web scraping
  ```
  > cookie
  ```

- **Exit the application**:
  ```
  > exit
  ```

## LLM Integration

IntelliApply uses a custom prompt template to extract structured information from job postings. The system is designed to validate required fields and handle optional information intelligently.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See the LICENSE file for details.

## Acknowledgements

- Google Gemini API for powering information extraction
- OpenAI and Anthropic Claude for inspiration and alternative models
- All the job boards that unintentionally contributed to this project's development

---

*Built with ❤️ by Jason Liao*
