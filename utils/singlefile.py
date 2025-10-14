from subprocess import run, CalledProcessError
import os
import time
import datetime
import requests

# Use absolute path relative to the script file
SINGLEFILE_BINARY_PATH = os.path.join(os.path.dirname(__file__), "node_modules", "single-file", "cli", "single-file")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"
}
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    # Windows paths
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Google\\Chrome Canary\\Application\\chrome.exe",
    "C:\\Program Files\\Chromium\\Application\\chrome.exe",
    # Add other paths if needed
]


def install_singlefile():
    """Installs single-file in the same directory as the script."""
    print("node_modules not found. Installing single-file...")
    try:
        # Install single-file locally
        run("npm i", shell=True, check=True, cwd=os.path.dirname(__file__))
        print("single-file installed successfully.")
        # No need to update SINGLEFILE_BINARY_PATH, as it's already an absolute path
    except CalledProcessError as e:
        print(f"Error installing single-file: {e}")
        exit(1)


def set_chrome_path():
    # Check common paths for Chrome-based browsers
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    return ""


CHROME_PATH = set_chrome_path()


def addQuotes(str):
    return "\"" + str.strip("\"") + "\""


def download_page(url, cookies_path, output_path, output_name_template="", timestamp=None):
    # Check if the URL is a PDF
    is_pdf = False

    try:
        # Only send HEAD request, do not download actual content
        response = requests.head(url, allow_redirects=True, timeout=10)
        content_type = response.headers.get('Content-Type', '')
        if 'application/pdf' in content_type:
            # Download the PDF using requests
            response = requests.get(url, allow_redirects=True, timeout=30, headers=HEADERS)
            # Get the filename from the server response
            if not output_name_template:
                output_name_template = response.headers.get('Content-Disposition', '').split('filename=')[1].strip('"')
                if not output_name_template:
                    output_name_template = os.path.basename(url)

            with open(output_path + "/" + output_name_template, "wb") as f:
                f.write(response.content)
            is_pdf = True
    except requests.RequestException as e:
        print(f"Error checking URL or downloading PDF: \n{e}")
        return -1
    except Exception as e:
        print(f"An unexpected error occurred: \n{e}")
        return -1

    if not is_pdf:
        if not os.path.exists(SINGLEFILE_BINARY_PATH):
            install_singlefile()

        args = [
            addQuotes(SINGLEFILE_BINARY_PATH),
            "--browser-executable-path=" + addQuotes(CHROME_PATH.strip("\"")),
            "--output-directory=" + addQuotes(output_path),
            addQuotes(url)
        ]

        if cookies_path:
            args.append("--browser-cookies-file=" + addQuotes(cookies_path))

        if output_name_template:
            args.append("--filename-template=" + addQuotes(output_name_template))

        try:
            run("node " + " ".join(args), shell=True, check=True)
        except CalledProcessError as e:
            print(f"Was not able to save the URL {url} using singlefile. The reported error was: {e}")
            return -1
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return -1

    # Set file modification time after successful download
    if timestamp:
        # Convert timestamp to a float if it's a string
        if isinstance(timestamp, str):
            try:
                timestamp = float(timestamp)
            except ValueError:
                print(f"Invalid timestamp format: {timestamp}. ")
                return -1

        # Convert timestamp to a float if it's a datetime object
        elif isinstance(timestamp, datetime.datetime):
            timestamp = timestamp.timestamp()

        downloaded_file_path = os.path.join(output_path, output_name_template)

        if os.path.exists(downloaded_file_path):
            os.utime(downloaded_file_path, (timestamp, timestamp))
        else:
            print(f"Downloaded file not found at {downloaded_file_path}. Unable to set modification time.")
            return -1


if __name__ == "__main__":
    # Example usage
    download_page("https://google.com", "", "/Users/jason/Library/Caches", "", timestamp=1678886400)
