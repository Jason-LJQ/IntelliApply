import os

COOKIE_PATH = os.path.join(os.path.dirname(__file__), "cookie.txt")
DOMAIN_KEYWORDS = {"https://www.linkedin.com/mypreferences/d/categories/account": ["preferred", "demographic"],
                   "https://app.joinhandshake.com": ["explore", "people"]}
