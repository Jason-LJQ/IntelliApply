import pandas as pd
import re


def get_abbreviation(name):
    """Get the abbreviation of a string by taking first letters of each word"""
    if not isinstance(name, str):
        return ''
    # Remove common company terms and special characters
    common_terms = ['corporation', 'corp', 'inc', 'incorporated', 'limited', 'ltd', 'llc', 'cooperation']
    cleaned_name = str(name).lower()
    for term in common_terms:
        cleaned_name = cleaned_name.replace(term, '')
    # Remove special characters, keep only letters and spaces
    cleaned_name = re.sub(r'[^a-zA-Z\s]', '', cleaned_name)
    # Get first letter of each word
    return ''.join(word[0].upper() for word in cleaned_name.split() if word)


def normalize_company_name(name):
    """Normalize company name by removing common suffixes and extra spaces"""
    if not isinstance(name, str):
        return ''
    # Remove common company terms
    common_terms = ['corporation', 'corp', 'inc', 'incorporated', 'limited', 'ltd', 'llc', 'cooperation']
    name_lower = str(name).lower().strip()
    for term in common_terms:
        name_lower = re.sub(rf'\b{term}\b', '', name_lower)
    # Remove special characters and extra spaces
    name_lower = re.sub(r'[^a-zA-Z\s]', '', name_lower)
    return re.sub(r'\s+', ' ', name_lower).strip()


def is_company_match(company1, company2):
    """
    Compare if two company names match, considering only exact matches and abbreviations
    """
    if not isinstance(company1, str) or not isinstance(company2, str):
        return False

    # Normalize both company names
    norm_company1 = normalize_company_name(company1)
    norm_company2 = normalize_company_name(company2)

    # Direct comparison after normalization
    if norm_company1 == norm_company2:
        return True

    # Compare abbreviation with full name
    abbr1 = get_abbreviation(company1)
    abbr2 = get_abbreviation(company2)

    # Check if one name is an abbreviation of the other
    if len(abbr1) > 1 and len(abbr2) > 1:
        if abbr1 == abbr2:
            return True
        if abbr1 == norm_company2 or abbr2 == norm_company1:
            return True

    return False


def search_applications(excel_file, search_term):
    """
    Search for both company and job title matches
    """
    try:
        # Read Excel file fresh every time
        df = pd.read_excel(excel_file)

        # Convert DataFrame columns to string type
        string_columns = ['Company', 'Job Title', 'Location']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).apply(lambda x: x.strip() if x != 'nan' else '')

        matches = []
        search_term_lower = search_term.lower().strip()

        for index, row in df.iterrows():
            # Check company name match
            if is_company_match(row['Company'], search_term):
                matches.append({
                    'Company': row['Company'],
                    'Location': row['Location'],
                    'Job Title': row['Job Title']
                })
            # Check exact job title match
            elif search_term_lower in row['Job Title'].lower():
                matches.append({
                    'Company': row['Company'],
                    'Location': row['Location'],
                    'Job Title': row['Job Title']
                })

        return matches

    except Exception as e:
        print(f"Error reading file: {str(e)}")
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
