import re
import subprocess
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

from config import DOMAIN_KEYWORDS, COOKIE_PATH
from excel_util import check_duplicate_entry, append_data_to_excel
from prompt import SYSTEM_PROMPT, JobInfo, REQUIRED_FIELDS
from credential import OPENAI_API_KEY, BASE_URL, MODEL
from print_utils import print_

client = OpenAI(api_key=OPENAI_API_KEY, base_url=BASE_URL)


def process_webpage_content(content):
    """
    Process webpage content through OpenAI API and return structured data.
    """

    try:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ],
            temperature=0,
            response_format=JobInfo
        )

        print(response)

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


def save_cookie(cookie_path=COOKIE_PATH):
    # Prompt the user to paste the cookie in Netscape format
    print("\n[*] Please paste the cookie in Netscape format (end with an empty line):")
    netscape_cookie = []
    while True:
        line = input()  # Accept multi-line input
        if not line.strip():  # End input on an empty line
            break
        netscape_cookie.append(line)

    # Write the pasted cookie to the file
    try:
        with open(cookie_path, 'w') as f:
            f.write('\n'.join(netscape_cookie))
        print_(f"Cookie successfully saved to {cookie_path}", "GREEN")
    except IOError as e:
        print_(f"Failed to save the cookie to {cookie_path}: {e}", "RED")


def validate_cookie(cookie_path=COOKIE_PATH):
    """
    Validate the cookies in the specified cookie file with the provided domain.

    Parameters:
    - domain (str): The base domain of the target server.
    - cookie_path (str): Path to the cookie file in Netscape format.

    Returns:
    - bool: True if the cookies are valid, False otherwise.
    """

    def parseCookieFile(cookiefile):
        """Parse a cookies.txt file and return a dictionary of key value pairs
        compatible with requests."""

        cookies = {}
        with open(cookiefile, 'r') as fp:
            for line in fp:
                if not re.match(r'^\#', line):
                    lineFields = line.strip().split('\t')
                    cookies[lineFields[5]] = lineFields[6]
        return cookies

    try:
        cookies = parseCookieFile(cookie_path)
    except FileNotFoundError:
        print_(f"Cookie file not found at path: {cookie_path}", "RED")
        return False
    except Exception as e:
        print_(f"Failed to load cookies: {e}", "RED")
        return False

    success = True
    for url, keywords in DOMAIN_KEYWORDS.items():
        try:
            response = requests.get(url, cookies=cookies, timeout=3)
            if response.status_code == 200 and all(keyword in response.text.lower() for keyword in keywords):
                print_(f"{url} LOGGED IN.", "GREEN")
            else:
                print_(f"{url} NOT LOGGED IN.", "RED")
                success = False

        except requests.RequestException as e:
            print_(f"{url} ERROR: {e}", "RED")
            success = False

    return success


def fetch_webpage_content(url, cookie_path=COOKIE_PATH):
    """
    Fetch content from a URL and extract the main text content.
    """
    try:
        # Add User-Agent header to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        }

        # Parse cookies from the cookie file
        cookies = {}
        with open(cookie_path, 'r') as fp:
            for line in fp:
                if not re.match(r'^\#', line):
                    lineFields = line.strip().split('\t')
                    cookies[lineFields[5]] = lineFields[6]

        response = requests.get(url, headers=headers, cookies=cookies, timeout=8)
        response.raise_for_status()

        return response.text

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text(separator='\n')

        # Clean up text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)

        return cleaned_text
    except Exception as e:
        print_(f"Error fetching webpage: {str(e)}", "RED")
        return None


def handle_webpage_content(content, excel_file):
    """
    Handle webpage content: process it and add to Excel if valid
    """
    # Remove view-source: prefix if present
    content = content.strip()
    if content.startswith('view-source:'):
        content = content[11:]  # Remove 'view-source:' prefix

    # Check if content is a URL
    if content.startswith(('http://', 'https://')):
        print_("\nFetching content from URL...")
        webpage_content = fetch_webpage_content(content)
        if not webpage_content:
            print_("Failed to fetch webpage content.", "RED")
            return
        content = "URL: " + content + "\n" + webpage_content

    # Remove extra blank lines
    cleaned_content = '\n'.join(line for line in content.split('\n') if line.strip())

    # Process through OpenAI
    result = process_webpage_content(cleaned_content)

    # Validate required fields one by one
    if not result.get('isValid', False):
        print_("Invalid content format.", "RED")
        return

    for field in REQUIRED_FIELDS:
        if field not in result or not str(result[field]).strip():
            print_("Could not extract valid information from the content.", "RED")
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
    duplicate_entry = check_duplicate_entry(excel_file, data)
    if duplicate_entry is not None:
        print_("Warning: This job entry already exists in the Excel file.", "RED")
        print(f"Duplicate Entry: {duplicate_entry}")
        confirm = input("[*] Add it anyway? (y/Y to confirm, any other key to cancel): ").lower()
        if confirm != 'y':
            print_("Addition cancelled.", "RED")
            return

    # Add to Excel
    append_data_to_excel(excel_file, [data])

    # Display result
    print_(f"Successfully extracted and added to Excel:", "GREEN")
    print(f"Company: {data['Company']}")
    print(f"Location: {data['Location']}")
    print(f"Job Title: {data['Job Title']}")
    print(f"Code: {data['Code']}")
    print(f"Type: {data['Type']}")
    print(f"Link: {data['Link']}")
