import pandas as pd
import re


def get_abbreviation(name):
    """Get the abbreviation of a string by taking first letters of each word"""
    if not isinstance(name, str):
        return ''
    cleaned = re.sub(r'[^a-zA-Z\s]', '', str(name))
    return ''.join(word[0].upper() for word in cleaned.split() if word)


def normalize_string(text):
    """Normalize string by converting to lowercase and removing extra spaces"""
    if not isinstance(text, str):
        return ''
    return re.sub(r'\s+', ' ', str(text).lower().strip())


def is_similar_company(company1, company2):
    """Compare if two company names are similar (case insensitive, considering abbreviations)"""
    if not isinstance(company1, str) or not isinstance(company2, str):
        return False

    norm_company1 = normalize_string(company1)
    norm_company2 = normalize_string(company2)

    if norm_company1 == norm_company2:
        return True

    if norm_company1 in norm_company2 or norm_company2 in norm_company1:
        return True

    abbr1 = get_abbreviation(company1)
    abbr2 = get_abbreviation(company2)

    if len(abbr1) > 1 and len(abbr2) > 1 and (abbr1 == abbr2):
        return True

    return False


def search_applications(excel_file, search_term):
    """
    Search for both company and job title matches

    Parameters:
    excel_file: Path to Excel file
    search_term: Search keyword

    Returns: List of matching records
    """
    try:
        df = pd.read_excel(excel_file)

        # Convert DataFrame columns to string type where necessary
        string_columns = ['Company', 'Job Title', 'Location']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).apply(lambda x: x.strip() if x != 'nan' else '')

        matches = []
        normalized_search_term = normalize_string(search_term)

        for index, row in df.iterrows():
            # Check both company and job title
            if (is_similar_company(row['Company'], normalized_search_term) or
                    normalized_search_term in normalize_string(row['Job Title'])):
                matches.append({
                    'Company': row['Company'],
                    'Location': row['Location'],
                    'Job Title': row['Job Title']
                })

        return matches

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return []


def main():
    excel_file = '/Users/jason/Library/CloudStorage/OneDrive-Personal/Graduate Study/17-677-I Internship for Software Engineers - Summer 2025/Book1.xlsx'

    while True:
        search_term = input("\nEnter search keyword (or 'exit' to quit): ").strip()

        if search_term.lower() == 'exit':
            break

        if not search_term:
            print("Search keyword cannot be empty!")
            continue

        results = search_applications(excel_file, search_term)

        if results:
            print(f"\nFound {len(results)} matching records:")
            # Print header
            print("\nCompany\tLocation\tJob Title")
            print("-" * 80)
            # Print results in tab-separated format
            for result in results:
                print(f"{result['Company']}\t{result['Location']}\t{result['Job Title']}")
        else:
            print("\nNo matching records found!")


if __name__ == "__main__":
    main()
