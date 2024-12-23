############################################
# Author: Jason Liao
# Date: 2024-12-22
# Description: A simple script to search for job applications in an Excel file
############################################

import pandas as pd
import re
import shutil
import signal
import sys


def get_abbreviation(name):
    """Get the abbreviation of a string by taking first letters of each word"""
    if not isinstance(name, str):
        return ''
    # Remove special characters, keep only letters and spaces
    cleaned_name = re.sub(r'[^a-zA-Z\s]', '', str(name))
    words = cleaned_name.strip().split()
    abbr_parts = []
    for w in words:
        if w.isupper():
            abbr_parts.append(w)  # Preserve the entire uppercase word
        else:
            abbr_parts.append(w[0].upper() if w else '')
    return ''.join(abbr_parts)


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


def format_location(location):
    """Convert multi-line location to single line with semicolons"""
    formatted = '; '.join(str(location).strip().split('\n'))
    # Limit location length to 50 characters
    if len(formatted) > 70:
        return formatted[:70] + '...'
    return formatted


def print_results(results):
    if not results:
        print("\nNo matching records found!")
        return

    print(f"\nFound {len(results)} matching records:")

    # Calculate maximum widths for each column
    company_width = max(len(str(r['Company'])) for r in results)
    company_width = max(company_width, len("Company"))

    location_width = max(len(format_location(r['Location'])) for r in results)
    location_width = max(location_width, len("Location"))

    job_width = max(len(str(r['Job Title'])) for r in results)
    job_width = max(job_width, len("Job Title"))

    # Print header
    print("\n{:<{width1}}  {:<{width2}}  {:<{width3}}".format(
        "Company", "Location", "Job Title",
        width1=company_width,
        width2=location_width,
        width3=job_width
    ))
    print("-" * (company_width + location_width + job_width + 4))

    # Print results
    for result in results:
        formatted_location = format_location(result['Location'])
        print("{:<{width1}}  {:<{width2}}  {:<{width3}}".format(
            str(result['Company']),
            formatted_location,
            str(result['Job Title']),
            width1=company_width,
            width2=location_width,
            width3=job_width
        ))


def is_company_match(company1, company2):
    """
    Compare if two company names match, considering exact matches and abbreviations
    """
    if not isinstance(company1, str) or not isinstance(company2, str):
        return False

    # Normalize both company names
    norm_company1 = normalize_company_name(company1)
    norm_company2 = normalize_company_name(company2)

    # Direct comparison after normalization
    if norm_company1 == norm_company2:
        return True

    # Get abbreviations
    abbr1 = get_abbreviation(company1)
    abbr2 = get_abbreviation(company2)

    # Compare abbreviation with full name and vice versa
    if len(abbr1) > 1:
        if abbr1 == abbr2:
            return True
        # Check if abbr1 matches the first letters of norm_company2's words
        if abbr1 == get_abbreviation(norm_company2):
            return True

    if len(abbr2) > 1:
        # Check if abbr2 matches the first letters of norm_company1's words
        if abbr2 == get_abbreviation(norm_company1):
            return True

    # Additional comparison: check if abbreviation of one matches normalized other
    abbr1 = get_abbreviation(norm_company1)
    abbr2 = get_abbreviation(norm_company2)
    
    if abbr1 == norm_company2 or abbr2 == norm_company1:
        return True

    # Handle case where one is abbreviation and other is full name
    words1 = norm_company1.split()
    words2 = norm_company2.split()

    if len(words1) >= 2 and len(words2) >= 2:
        # Check if the initials of one match the other's abbreviation
        initials1 = ''.join(word[0].upper() for word in words1)
        initials2 = ''.join(word[0].upper() for word in words2)

        if initials1 == abbr2 or initials2 == abbr1:
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


def signal_handler(sig, frame):
    print('\nExiting ...')
    sys.exit(0)

def main():
    excel_file = '/Users/jason/Library/CloudStorage/OneDrive-Personal/Graduate Study/17-677-I Internship for Software Engineers - Summer 2025/Book1.xlsx'
    
    # Set up signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            search_term = input("\nEnter search keyword (or 'exit' to quit): ").strip()

            if search_term.lower() == 'exit':
                print("Exiting ...")
                break

            if not search_term:
                print("Search keyword cannot be empty!")
                continue

            results = search_applications(excel_file, search_term)

            if results:
                print_results(results)
            else:
                print("\nNo matching records found!")

            # columns, _ = shutil.get_terminal_size()
            # print("-" * columns)

    except KeyboardInterrupt:
        print('\nExiting ...')
        sys.exit(0)

if __name__ == "__main__":
    main()
