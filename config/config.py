import os

COOKIE_PATH = os.path.join(os.path.dirname(__file__), "cookie.pkl")
DOMAIN_KEYWORDS = {"https://www.linkedin.com/mypreferences/d/categories/account": ["preferred", "demographic"],
                   "https://app.joinhandshake.com": ["explore", "people"]}
# Add User-Agent header to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
}

