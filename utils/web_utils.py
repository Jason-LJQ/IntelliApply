import re
import subprocess
import pickle
import threading
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from config.config import DOMAIN_KEYWORDS, COOKIE_PATH, HEADERS
from config.prompt import SYSTEM_PROMPT, JobInfo, REQUIRED_FIELDS
from utils.excel_utils import check_duplicate_entry, append_data_to_excel
from config.credential import OPENAI_API_KEY, BASE_URL, MODEL, REASONING_EFFORT
from utils.print_utils import print_

client = OpenAI(api_key=OPENAI_API_KEY, base_url=BASE_URL)
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
    """

    try:
        print_(f"Sending content to {MODEL}...")

        response = client.beta.chat.completions.parse(
            model=MODEL,
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
        print_(f"Error processing content through OpenAI: {str(e)}", "RED")
        return {"isValid": False}


def fetch_with_requests(url, redirect=True):
    """
    Fetch content from a URL and extract the main text content.
    """
    try:
        if 'linkedin.com' in url or 'handshake' in url:
            response = session.get(url, timeout=8)
        else:
            response = session_default.get(url, timeout=8)
        response.raise_for_status()

        # Check iframe content in the response and send it instead
        soup = BeautifulSoup(response.text, 'html.parser')
        iframes = soup.find_all('iframe')

        # Combine all iframe content into a single string
        content = response.text
        if redirect:
            for iframe in iframes:
                iframe_src = iframe.get('src')
                if iframe_src:
                    print_(f"Found iframe, fetching content from: {iframe_src}")
                    content += f"<INLINE IFRAME SRC='{iframe_src}'>\n"
                    content += fetch_with_requests(iframe_src, redirect=False)
                    content += f"</INLINE IFRAME>\n"

        return content

    except Exception as e:
        print_(f"Error fetching webpage: {str(e)}", "RED")
        return ""


def fetch_with_playwright(url):
    """
    Fetch dynamic content using Playwright.
    """

    print_("Attempting to fetch dynamic content with Playwright...", "YELLOW")

    try:
        print_("Using Playwright for dynamic content loading...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=12000, wait_until='networkidle')
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        print_(f"Playwright failed: {str(e)}", "RED")
        return ""


FETCH_METHOD = ['requests', 'playwright']


def handle_webpage_content(content):
    """
    Handle webpage content: process it and add to Excel if valid
    """
    # Remove view-source: prefix if present
    content = content.strip()
    if content.startswith('view-source:'):
        content = content[11:]  # Remove 'view-source:' prefix

    def fetch_webpage_helper(url, method):
        print_(f"Fetching content from URL with {method}...", "YELLOW")
        if method == 'requests':
            webpage_content = fetch_with_requests(url)
        elif method == 'playwright':
            webpage_content = fetch_with_playwright(url)

        if not webpage_content:
            print_(f"Failed to fetch webpage content with {method}.", "RED")
            return None

        content = "URL: " + url + "\n" + webpage_content
        return content

    def process_helper(content):
        # Process through OpenAI
        result = process_webpage_content(content)

        # Validate required fields one by one
        if not result.get('isValid', False):
            print_(f"LLM Backend: Invalid content format.", "RED")
            return None

        for field in REQUIRED_FIELDS:
            if field not in result or not str(result[field]).strip():
                print_(f"LLM Backend: Required field \"{field}\" not found.", "RED")
                return None

        return result

    # Check if content is a URL
    if content.startswith(('http://', 'https://')):
        url = content
        result = None

        for method in FETCH_METHOD:
            fetched_content = fetch_webpage_helper(url, method)
            if not fetched_content:
                continue

            result = process_helper(fetched_content)
            if result:
                break
        if not result:
            print_(f"Failed to fetch webpage content with any method.", "RED")
            return

        # Send URL to web.archive.org for archiving
        archive_url_async(url)
        print_("Sent URL to web.archive.org for archiving")
    else:
        result = process_helper(content)
        if not result:
            return

    # All validations passed, prepare data for Excel
    from datetime import datetime
    data = {
        'Company': result['Company'],
        'Location': result['Location'],
        'Job Title': result['Job Title'],
        'Code': result.get('Code', ''),  # Optional field
        'Type': result.get('Type', ''),  # Optional field
        'Link': result.get('Link', ''),  # Optional field
        'Applied Date': datetime.now().strftime('%Y-%m-%d'),  # Add current date
    }

    # Check for duplicates
    duplicate_entry = check_duplicate_entry(new_data=data)
    if duplicate_entry is not None:
        try:
            print_("Warning: This job entry already exists in the Excel file.", "RED")
            print(f"Duplicate Entry: {duplicate_entry}")
            confirm = input(print_("[*] Add it anyway? (y/yes to confirm, any other key to cancel): ", color="YELLOW",
                                   return_text=True)).lower()
            if confirm.lower() != 'y' and confirm.lower() != 'yes':
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            print_("Addition cancelled.", "RED")
            return

    # Add to Excel
    append_data_to_excel(data=[data])

    # Display result
    print_(f"Successfully extracted and added to Excel:", "GREEN")
    print(f"Company: {data['Company']}")
    print(f"Location: {data['Location']}")
    print(f"Job Title: {data['Job Title']}")
    print(f"Code: {data['Code']}")
    print(f"Type: {data['Type']}")
    print(f"Link: {data['Link']}")


def archive_url_async(url):
    """
    Asynchronously send URL to web.archive.org for archiving.
    Does not wait for response.
    """

    def _archive_request():
        try:
            archive_url = f"https://web.archive.org/save/{url}"
            requests.get(archive_url, timeout=120)
            # print_(f"Archived URL: {url}", "GREEN")
        except Exception as e:
            print_(f"Archive request failed: {str(e)}", "RED")

    thread = threading.Thread(target=_archive_request)
    thread.daemon = True  # Set as daemon thread so it won't prevent program exit
    thread.start()
