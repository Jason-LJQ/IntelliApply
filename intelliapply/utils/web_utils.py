import re
import subprocess, shutil, sys
import pickle
import threading
import time
import os
from datetime import datetime
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from intelliapply.config.config import DOMAIN_KEYWORDS, COOKIE_PATH, HEADERS
from intelliapply.config.prompt import SYSTEM_PROMPT, JobInfo, REQUIRED_FIELDS
from intelliapply.config.credential import API_KEY_LIST, BASE_URL, MODEL_LIST, REASONING_EFFORT, BACKUP_FOLDER_PATH
from intelliapply.utils.print_utils import print_
from intelliapply.utils.string_utils import parse_json_safe

# Initialize session objects
session = requests.session()
session_default = requests.session()


def save_cookie(cookie_path=COOKIE_PATH):
    """Save current session cookies to a pickle file."""
    try:
        with open(cookie_path, 'wb') as f:
            pickle.dump(session.cookies, f)
        print_(f"Cookie successfully saved to {cookie_path}", "GREEN")
        return True
    except Exception as e:
        print_(f"Failed to save cookie: {e}", "RED")
        return False


def load_cookies_to_session(cookie_path=COOKIE_PATH):
    """Load cookies from pickle file into the session."""
    try:
        with open(cookie_path, 'rb') as f:
            session.cookies.update(pickle.load(f))
            print_("Loaded cookies from pickle file", "GREEN")
            return True
    except FileNotFoundError:
        print_(f"Cookie file not found at path: {cookie_path}", "RED")
        return False
    except Exception as e:
        print_(f"Failed to load cookies: {e}", "RED")
        return False


session.max_redirects = 5
session_default.max_redirects = 5
session.headers.update(HEADERS)
session_default.headers.update(HEADERS)
load_cookies_to_session()

# -------- Intelligent Detection Patterns --------
HYDRATION_PATTERNS = [
    r'__NEXT_DATA__',  # Next.js
    r'data-reactroot',  # React hydration
    r'id=["\'](?:root|app)["\']'  # <div id="root"> / <div id="app">
]
JS_REQUIRED_PATTERNS = [
    r'please enable javascript', r'enable javascript',
    r'<noscript',  # generic <noscript> block
    r'cloudflare', r'cf-ray',  # CF challenge hints
]
BLOCK_STATUS = {403, 429, 503}
_CHROME_CHANNELS = ['chrome', 'chrome-dev', 'chrome-canary', '']


def detect_playwright_channel():
    """
    Detect and select the best available Playwright browser channel.
    Tests channels in order of preference and caches the result.
    Runs quickly and silently on startup.
    
    Returns:
        str or None: Best available channel name, or None to use default
    """

    # Channels to test in order of preference
    print_("Detecting available Playwright browser channel...", "YELLOW")

    try:
        with sync_playwright() as p:
            for channel in _CHROME_CHANNELS:
                try:
                    # Quick launch test - no actual navigation
                    browser = p.chromium.launch(channel=channel, headless=True)
                    browser.close()
                    return channel
                except Exception:
                    # Channel not available, try next one
                    continue

    except Exception as e:
        print_(f"Error detecting Browser: {str(e)}", "RED")
        raise e

    # No specific channel worked, install browsers and use default (None)
    ensure_playwright_browsers()
    return ''


def ensure_playwright_browsers():
    # Cross-platform detection
    playwright_cmd = shutil.which("playwright")
    if playwright_cmd is None:
        print("[error] Playwright CLI not found in PATH.")
        print("Please install it via: pip install playwright")
        sys.exit(1)

    try:
        subprocess.run([playwright_cmd, "install", "chromium"], check=True)
        print_("Playwright browsers installed successfully.", "GREEN")
    except subprocess.CalledProcessError as e:
        print_(f"Failed to install Playwright browsers: {e}", "RED")
        sys.exit(1)


# Cache for Playwright browser channel
_PLAYWRIGHT_CHANNEL = detect_playwright_channel()


def analyze_content_for_playwright(html, status_code, redirect=True) -> bool:
    """
    Analyze already fetched content to determine if Playwright is needed.
    
    Args:
        html: HTML content already fetched
        status_code: HTTP status code from the request
    
    Returns:
        True if Playwright is likely needed, False otherwise
    """

    if not html:
        return False

    # Check for blocked status codes
    if status_code in BLOCK_STATUS:
        return True

    # Check iframe content in the response and send it instead
    soup = BeautifulSoup(html, 'html.parser')
    iframes = soup.find_all('iframe')

    # If redirect is True, check for iframe content
    if redirect:
        for iframe in iframes:
            iframe_src = iframe.get('src')
            if iframe_src and "googletagmanager" not in iframe_src:
                iframe_content, _ = get_raw_requests(iframe_src)
                if analyze_content_for_playwright(iframe_content, status_code, redirect=False):
                    return True

    html_lc = html.lower()

    # Check for hydration markers (client-side rendering)
    for pattern in HYDRATION_PATTERNS:
        if re.search(pattern, html, re.I):
            return True

    # Check for JS-required / Cloudflare hints
    for pattern in JS_REQUIRED_PATTERNS:
        if re.search(pattern, html_lc):
            return True

    return False


def start_browser(app_path="/Applications/Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta",
                  url=list(DOMAIN_KEYWORDS.keys())):
    """
    Open a browser to access the specified URL.
    If app_path is provided, it tries to open the URL using the specified application.
    If app_path is not provided, it uses the default browser to open the URL.

    :param app_path: Path to the specific browser application (e.g., /Applications/Microsoft Edge Beta.app)
    :param url: The URL to be accessed (default is None, and no page will be opened if not provided)
    """
    if not url:
        print_("URL is not provided, unable to open the browser.", "RED")
        return

    if isinstance(url, list):
        success = True
        for u in url:
            success = start_browser(app_path, u)
            if not success:
                success = False
        return success

    if app_path:
        try:
            # Attempt to open the URL with the specified application
            subprocess.run(["open", "-a", app_path, url], check=True)
            print_(f"Successfully opened {url} using {app_path}", "GREEN")
            return True
        except subprocess.CalledProcessError as e:
            print_(f"Failed to open the specified application, error: {e}", "RED")
            return False
        except FileNotFoundError:
            print_(f"The specified application path was not found. Please check the path.", "RED")
            return False


def add_cookie(cookie_path=COOKIE_PATH):
    # Prompt the user to paste the cookie in Netscape format
    print("\n[*] Please paste the cookie in Netscape format (end with an empty line):")
    netscape_cookie = []
    while True:
        line = input()  # Accept multi-line input
        if not line.strip():  # End input on an empty line
            break
        netscape_cookie.append(line)

    try:
        # Parse Netscape format cookies
        cookies = {}
        for line in netscape_cookie:
            if not re.match(r'^\#', line):
                lineFields = line.strip().split('\t')
                cookies[lineFields[5]] = lineFields[6]

        # Update session cookies
        session.cookies.update(cookies)

        # Save to pickle file
        if save_cookie(cookie_path):
            return True
        return False
    except Exception as e:
        print_(f"Failed to process cookie: {e}", "RED")
        return False


def validate_cookie():
    """
    Validate the cookies in the pickle file with the provided domain.

    Returns:
    - bool: True if the cookies are valid, False otherwise.
    """

    success = True
    for url, keywords in DOMAIN_KEYWORDS.items():
        try:
            response = session.get(url, timeout=5)
            if response.status_code == 200 and all(keyword in response.text.lower() for keyword in keywords):
                print_(f"{url} LOGGED IN.", "GREEN")
            else:
                print_(f"{url} NOT LOGGED IN.", "RED")
                success = False

        except requests.RequestException as e:
            print_(f"{url} ERROR: {e}", "RED")
            success = False

    return success


def process_webpage_content(content):
    """
    Process webpage content through OpenAI API and return structured data.
    Supports multiple API keys with automatic retry logic.
    """

    # Try each model with all API keys
    for model in MODEL_LIST:
        for api_key in API_KEY_LIST:
            try:
                print_(f"Sending content to {model} with API key {api_key[:10]}...")
                client = OpenAI(api_key=api_key, base_url=BASE_URL)

                response = client.beta.chat.completions.parse(
                    model=model,
                    reasoning_effort=REASONING_EFFORT,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": content}
                    ],
                    temperature=0,
                    response_format=JobInfo
                )

                # Parse the response and convert Job_Title to Job Title
                result = response.choices[0].message.parsed
                return {
                    "isValid": result.isValid,
                    "Company": result.Company,
                    "Location": result.Location,
                    "Job Title": result.Job_Title,
                    "Code": result.Code,
                    "Type": result.Type,
                    "Link": result.Link
                }
            except Exception as e:
                print_(f"API key {api_key[:10]}... error: {str(e)}", "RED")
                continue

    print_(f"Error processing content through LLM", "RED")
    return {"isValid": False}


def remove_script_content(content):
    """
    Remove all script tags and their content from HTML content.
    """
    try:
        soup = BeautifulSoup(content, 'html.parser')
        # Remove all script tags and their content
        for script in soup.find_all('script'):
            script.decompose()
        return str(soup)
    except Exception as e:
        print_(f"Error removing script content: {str(e)}", "RED")
        return content


def get_raw_requests(url):
    """
    Get raw content from a URL using requests.
    Returns tuple: (content, status_code)
    """
    try:
        if 'linkedin.com' in url or 'handshake' in url:
            response = session.get(url, timeout=8)
        else:
            response = session_default.get(url, timeout=8)
        response.raise_for_status()
        return response.text, response.status_code
    except Exception as e:
        print_(f"Error fetching webpage: {str(e)}", "RED")
        return "", 0


def process_requests_content(content, redirect=True):
    """
    Fetch content from a URL and extract the main text content.
    """
    try:
        # Remove script content from the final content
        content = remove_script_content(content)

        # Check iframe content in the response and send it instead
        soup = BeautifulSoup(content, 'html.parser')
        iframes = soup.find_all('iframe')

        # Combine all iframe content into a single string
        if redirect:
            for iframe in iframes:
                iframe_src = iframe.get('src')
                if iframe_src and "googletagmanager" not in iframe_src:
                    print_(f"Found iframe, fetching content from: {iframe_src}")
                    content += f"<INLINE IFRAME SRC='{iframe_src}'>\n"
                    iframe_content, _ = get_raw_requests(iframe_src)
                    content += iframe_content
                    content += f"</INLINE IFRAME>\n"

        return content

    except Exception as e:
        print_(f"Error fetching webpage: {str(e)}", "RED")
        return ""


def load_cookies_for_playwright(cookie_path=COOKIE_PATH):
    """
    Load cookies from pickle file and convert them to Playwright format.
    
    Args:
    - cookie_path: Path to the pickle file containing cookies
    
    Returns:
    - list: List of cookie dictionaries in Playwright format, or empty list if failed
    """
    try:
        with open(cookie_path, 'rb') as f:
            requests_cookies = pickle.load(f)

        # Convert requests cookies to Playwright format
        playwright_cookies = []
        for cookie in requests_cookies:
            # Skip cookies with missing essential fields
            if not cookie.name or not cookie.value or not cookie.domain:
                continue

            # Create base cookie structure
            playwright_cookie = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path or '/',
            }

            # Add optional fields if they exist
            if cookie.expires:
                if cookie.expires < time.time():
                    continue
                playwright_cookie['expires'] = int(cookie.expires)
            if hasattr(cookie, 'secure') and cookie.secure:
                playwright_cookie['secure'] = True
            if hasattr(cookie, 'httpOnly') and cookie.httpOnly:
                playwright_cookie['httpOnly'] = True
            if hasattr(cookie, '_rest'):
                if cookie._rest.get("HttpOnly"):
                    playwright_cookie['httpOnly'] = True
                if 'SameSite' in cookie._rest:
                    playwright_cookie['sameSite'] = cookie._rest['SameSite'].title()

            playwright_cookies.append(playwright_cookie)

        # print_(f"Loaded {len(playwright_cookies)} cookies for Playwright", "GREEN")
        return playwright_cookies

    except FileNotFoundError:
        print_(f"Cookie file not found at path: {cookie_path}", "YELLOW")
        return []
    except Exception as e:
        print_(f"Failed to load cookies for Playwright: {e}", "RED")
        return []


def fetch_with_playwright(url):
    """
    Fetch dynamic content using Playwright with cookie support.
    """

    print_("Attempting to fetch dynamic content with Playwright...", "YELLOW")

    try:
        print_("Using Playwright for dynamic content loading...")
        with sync_playwright() as p:
            browser = p.chromium.launch(channel=_PLAYWRIGHT_CHANNEL, headless=True)
            # Create browser context and add cookies
            context = browser.new_context()
            # if 'linkedin.com' in url or 'handshake.com' in url:
            #     cookies = load_cookies_for_playwright()
            #     if cookies:
            #         context.add_cookies(cookies)
            page = context.new_page()
            page.goto(url, timeout=7000, wait_until='domcontentloaded')
            page.wait_for_timeout(4000)  # 4 seconds should be enough for most job sites
            content = page.content()
            browser.close()
            # Remove script content from the final content
            content = remove_script_content(content)
            return content
    except Exception as e:
        print_(f"Playwright failed: {str(e)}", "RED")
        return ""


FETCH_METHOD = ['requests', 'playwright']


def validate_job_data(result, source="LLM Backend"):
    """
    Validate job data result from any source (LLM or JSON input).
    
    Args:
        result: Dictionary containing job information
        source: String describing the data source for error messages
    
    Returns:
        dict or None: Validated result or None if validation fails
    """
    # Validate required fields one by one
    if not result.get('isValid', False):
        print_(f"{source}: Invalid content format.", "RED")
        return None

    for field in REQUIRED_FIELDS:
        if field not in result or not str(result[field]).strip():
            print_(f"{source}: Required field \"{field}\" not found.", "RED")
            return None

    return result


def prepare_excel_data(result):
    """
    Prepare validated job data for Excel insertion.
    
    Args:
        result: Validated job data dictionary
    
    Returns:
        dict: Data formatted for Excel
    """
    from datetime import datetime
    return {
        'Company': result['Company'],
        'Location': result['Location'],
        'Job Title': result['Job Title'],
        'Code': result.get('Code', ''),  # Optional field
        'Type': result.get('Type', ''),  # Optional field
        'Link': result.get('Link', ''),  # Optional field
        'Applied Date': datetime.now().strftime('%Y-%m-%d'),  # Add current date
    }


def handle_duplicate_check(data, excel_manager):
    """
    Handle duplicate entry checking with user confirmation.

    Args:
        data: Excel data dictionary
        excel_manager: ExcelManager instance

    Returns:
        bool: True if should proceed, False if cancelled
    """
    duplicate_entry = excel_manager.check_duplicate_entry(new_data=data)
    if duplicate_entry is not None:
        try:
            print_("Warning: This job entry already exists in the Excel file.", "RED")
            print(f"Duplicate Entry: {duplicate_entry}")
            confirm = input(print_("[*] Add it anyway? (y/yes to confirm, any other key to cancel): ", color="BLUE",
                                   return_text=True)).lower()
            if confirm.lower() != 'y' and confirm.lower() != 'yes':
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            print_("Addition cancelled.", "RED")
            return False
    return True


def display_job_result(data):
    """
    Display the successfully processed job data.
    
    Args:
        data: Excel data dictionary
    """
    print_(f"Successfully extracted and added to Excel:", "GREEN")
    print(f"Company: {data['Company']}")
    print(f"Location: {data['Location']}")
    print(f"Job Title: {data['Job Title']}")
    print(f"Code: {data['Code']}")
    print(f"Type: {data['Type']}")
    print(f"Link: {data['Link']}")


def process_validated_job_data(result, excel_manager, source="LLM Backend"):
    """
    Process validated job data: prepare for Excel, check duplicates, and save.

    Args:
        result: Validated job data dictionary
        excel_manager: ExcelManager instance
        source: String describing the data source

    Returns:
        bool: True if successfully processed, False otherwise
    """
    # Prepare data for Excel
    data = prepare_excel_data(result)

    # Check for duplicates
    if not handle_duplicate_check(data, excel_manager):
        return False

    # Add to Excel
    excel_manager.append_data_to_excel(data=[data])

    # Display result
    display_job_result(data)
    return True


def handle_webpage_content(content, excel_manager):
    """
    Handle webpage content: process it and add to Excel if valid

    Args:
        content: Webpage content or URL
        excel_manager: ExcelManager instance
    """
    # Remove view-source: prefix if present
    content = content.strip()
    if content.startswith('view-source:'):
        content = content[12:]  # Remove 'view-source:' prefix

    def process_helper(content):
        # Process through OpenAI
        result = process_webpage_content(content)
        return validate_job_data(result, "LLM Backend")

    # Check if content is a URL
    if content.startswith(('http://', 'https://')):
        url = content
        result = None

        # First try with requests
        print_(f"Fetching content from URL with requests...", "YELLOW")
        fetched_raw_content, status_code = get_raw_requests(url)

        if not fetched_raw_content:
            print_(f"Failed to fetch webpage content with requests.", "RED")
        else:
            # Analyze the fetched content to see if we need Playwright
            print_(f"Analyzing content validity...")
            needs_playwright = analyze_content_for_playwright(fetched_raw_content, status_code)

            if not needs_playwright:
                # Content looks good, try to process it
                print_(f"Processing content based on requests...")
                webpage_content = process_requests_content(fetched_raw_content)
                webpage_content = "URL: " + url + "\n" + webpage_content
                result = process_helper(webpage_content)

        # Playwright as fallback
        if not result:
            print_(f"Fetching content from URL with playwright...", "YELLOW")
            fetched_content_pw = fetch_with_playwright(url)
            if fetched_content_pw:
                webpage_content = "URL: " + url + "\n" + fetched_content_pw
                result = process_helper(webpage_content)
            else:
                print_(f"Failed to fetch webpage content with playwright.", "RED")

        if not result:
            print_(f"Failed to fetch webpage content with any method.", "RED")
            return

        # Backup URL to local storage using singlefile with job info
        company = result.get('Company', '')
        job_title = result.get('Job Title', '')
        backup_url_local_async(url, company, job_title)
        print_("Started local backup of URL using singlefile")
    else:
        result = process_helper(content)
        if not result:
            return

    # Process the validated result
    process_validated_job_data(result, excel_manager, "LLM Backend")


def handle_json_content(json_content, excel_manager):
    """
    Handle JSON input: parse and validate job data, then add to Excel if valid.

    Args:
        json_content: JSON string containing job information
        excel_manager: ExcelManager instance

    Returns:
        bool: True if successfully processed, False otherwise
    """
    # Parse JSON with normalization
    success, result, error = parse_json_safe(json_content)

    if not success:
        print_(f"JSON Input: {error}", "RED")
        return False

    # Ensure Job_Title is mapped to Job Title for validation
    if 'Job_Title' in result and 'Job Title' not in result:
        result['Job Title'] = result['Job_Title']

    # Validate the parsed JSON data
    validated_result = validate_job_data(result, "JSON Input")
    if not validated_result:
        return False

    # Process the validated result
    return process_validated_job_data(validated_result, excel_manager, "JSON Input")


def get_backup_directory():
    """
    Get the backup directory path from configuration.
    Creates the directory if it doesn't exist.
    """
    try:
        backup_dir = BACKUP_FOLDER_PATH

        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
            print_(f"Created backup directory: {backup_dir}", "GREEN")

        return backup_dir
    except Exception as e:
        print_(f"Error creating backup directory: {str(e)}", "RED")
        return None


def generate_backup_filename(company, job_title, backup_dir):
    """
    Generate backup filename in format: company_jobtitle_currentdate_no.html
    Increments 'no' if duplicate files exist.
    
    Args:
        company: Company name
        job_title: Job title
        backup_dir: Backup directory path
    
    Returns:
        str: Generated filename
    """
    try:
        # Clean company and job title for filename
        company_clean = re.sub(r'[^\w\-_.]', '_', company.strip()) if company else "unknown_company"
        job_title_clean = re.sub(r'[^\w\-_.]', '_', job_title.strip()) if job_title else "unknown_job"

        # Get current date
        current_date = datetime.now().strftime("%Y%m%d")

        # Generate base filename
        base_filename = f"{company_clean}_{job_title_clean}_{current_date}"
        filename = f"{base_filename}.html"

        # Check if file already exists
        if not os.path.exists(os.path.join(backup_dir, filename)):
            return filename

        # If duplicate exists, start adding numbers from 2
        no = 2
        while True:
            filename = f"{base_filename}_{no}.html"
            if not os.path.exists(os.path.join(backup_dir, filename)):
                return filename
            no += 1

    except Exception as e:
        print_(f"Error generating backup filename: {str(e)}", "YELLOW")
        # Fallback to timestamp-based naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}.html"


def backup_url_local_async(url, company="", job_title=""):
    """
    Asynchronously backup URL to local storage using singlefile.
    Does not wait for response. Handles errors gracefully without exiting.
    
    Args:
        url: URL to backup
        company: Company name for filename generation
        job_title: Job title for filename generation
    """

    def _backup_request():
        try:
            from intelliapply.utils.singlefile import download_page

            backup_dir = get_backup_directory()
            if not backup_dir:
                print_(f"Failed to get backup directory, skipping backup", "RED")
                return

            # Generate filename using company and job title
            filename_template = generate_backup_filename(company, job_title, backup_dir)

            # Use existing cookie path for singlefile
            try:
                result = download_page(url, COOKIE_PATH, backup_dir, filename_template)

                if result == -1:
                    print_(f"Failed to backup URL locally.", "RED")
            except Exception as save_error:
                print_(f"Error during backup save: {str(save_error)}", "RED")

        except Exception as e:
            print_(f"Local backup request failed: {str(e)}", "RED")

    thread = threading.Thread(target=_backup_request)
    thread.daemon = True  # Set as daemon thread so it won't prevent program exit
    thread.start()
