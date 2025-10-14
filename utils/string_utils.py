import re
import json


def cleaned_string(text):
    """Clean the string by removing special characters and extra spaces"""
    if not isinstance(text, str):
        return ''

    # Step 1: Remove newlines, tabs, carriage returns
    text = re.sub(r'[\n\t\r]', ' ', text)

    # Step 2: Remove common punctuation and symbols
    text = re.sub(r'[!@#$%^&*()_+=\[\]{}|;\':"<>?,./-]', '', text)

    # Step 3: Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Step 4: Strip leading/trailing whitespace
    text = text.strip()

    return text


def get_abbreviation_lower(name):
    """Get the abbreviation of a string by taking first letters of each word"""
    if not isinstance(name, str):
        return ''
    # Remove special characters, keep only letters and spaces
    cleaned_name = cleaned_string(name)
    words = cleaned_name.strip().split()
    abbr_parts = []
    for w in words:
        if w.isupper():
            abbr_parts.append(w)  # Preserve the entire uppercase word
        else:
            abbr_parts.append(w[0].upper() if w else '')
    return ''.join(abbr_parts).lower()


def normalize_company_name(name):
    """Normalize company name by removing common suffixes and extra spaces"""
    if not isinstance(name, str):
        return ''
    # Remove common company terms
    common_terms = ['corporation', 'corp', 'inc', 'incorporated', 'limited', 'ltd', 'llc', 'cooperation', 'logo']
    name_lower = str(name).lower().strip()
    for term in common_terms:
        name_lower = re.sub(rf'\b{term}\b', '', name_lower)
    # Remove special characters and extra spaces
    return cleaned_string(name_lower)


def format_string(name, limit=55):
    """Convert multi-line location to single line with semicolons"""
    formatted = '; '.join(str(name).strip().split('\n'))
    # Limit location length
    if len(formatted) > limit:
        return formatted[:limit] + '...'
    return formatted


def parse_json_safe(text):
    """
    Safely parse JSON with normalization of non-standard characters.
    Handles Chinese quotes, Chinese colons, and other Unicode characters.
    
    Args:
        text: JSON string to parse
    
    Returns:
        tuple: (success: bool, result: dict or None, error: str or None)
    """
    if not text:
        return False, None, "Empty input"

    try:
        text = text.strip()

        # Basic JSON structure check - must start with { or [
        if not re.match(r'^\s*[\[{]', text):
            return False, None, "Not a JSON structure"

        # Map of non-standard characters to standard JSON characters
        translation_table = str.maketrans({
            '“': '"',
            '”': '"',
            '‘': "'",
            '’': "'",
            '：': ':',
            '„': '"',
            '‚': "'",
            '‹': "'",
            '›': "'",
            '«': '"',
            '»': '"',
        })

        # Replace all non-standard characters with standard ones
        normalized_text = text.translate(translation_table)

        # Try to parse as JSON
        result = json.loads(normalized_text)
        return True, result, None

    except json.JSONDecodeError as e:
        return False, None, f"JSON decode error: {str(e)}"
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


def is_json(text):
    """Check if the text is valid JSON"""
    success, _, _ = parse_json_safe(text)
    return success


def is_markdown_table(input_string):
    """
    Checks if the input string is likely a Markdown table.
    This is a heuristic check and may not be 100% accurate.
    """
    lines = input_string.strip().split('\n')
    if len(lines) < 3:
        return False  # Not enough lines for a table

    # Check for at least one | in the header and data lines
    if '|' not in lines[0]:
        return False

    for line in lines[2:]:
        if '|' not in line:
            return False

    return True


def parse_markdown_table(markdown_table_string):
    """
    Parses a Markdown table string and returns a list of dictionaries,
    where each dictionary represents a row in the table.
    """
    lines = markdown_table_string.strip().split('\n')
    if len(lines) < 3:
        return []  # Not a valid Markdown table

    # Extract headers
    headers = [header.strip() for header in lines[0].split('|') if header.strip()]

    # Extract rows
    data = []
    for line in lines[2:]:
        values = [value.strip() for value in line.split('|') if value.strip()]
        if len(values) == len(headers):
            data.append(dict(zip(headers, values)))
    return data
