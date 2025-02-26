############################################
# Author: Jason Liao
# Date: 2024-12-22
# Description: A simple script to search for job applications in an Excel file
############################################

import os
import time
import signal
import sys

from utils.string_utils import is_markdown_table, parse_markdown_table
from utils.excel_utils import summary, open_excel_file, show_last_row, append_data_to_excel, search_applications, \
    mark_result
from utils.print_utils import print_, print_results
from utils.web_utils import save_cookie, validate_cookie, handle_webpage_content, start_browser, add_cookie


def signal_handler(sig, frame):
    print_("\nSaving cookie ...")
    save_cookie()
    print_('\nExiting ...', "RED")
    sys.exit(0)


def detect_ending(min_threshold=0.05, max_threshold=0.5):
    """
    Detect double Enter press within threshold seconds
    Returns the entered line and a boolean indicating if double Enter was detected
    """

    def end_char_check(line):
        return line.strip().endswith('>') or line.strip().endswith('```')

    line = input("| ")
    if line:
        if end_char_check(line):
            return line, True
        return line, False

    # First empty line detected, start timing
    start_time = time.time()
    try:
        line = input("| ")
        # If second line is entered within threshold seconds
        if not line and min_threshold <= (time.time() - start_time) <= max_threshold:
            return '', True
        elif end_char_check(line):
            return line, True
        return line, False
    except (EOFError, KeyboardInterrupt):
        return '', True


def update_result():
    last_search_term = None
    results = None

    # Enter mark mode
    while True:
        print("-" * 100)
        search_term = ""

        if not results:
            print_("[*] Entering mark mode. Please enter search keyword. Enter 'exit' to exit mark mode.")
            search_term = input("> ").strip()
        else:
            # Ask user to select a row to mark
            print_(f"\n[*] Current Search: {last_search_term}.")
            # Display results with numbers
            print_results(results, mark_mode=True)
            print_(f"Enter the number of the row to mark or start a new search.",
                   "GREEN")
            selection = input("> ").strip()

            # If slesction is not a number, start a new search
            try:
                selection = int(selection)
                search_term = last_search_term
            except ValueError:
                search_term = selection
                last_search_term = None
                results = None

        if search_term.lower() == 'exit':
            print_("Search interrupted. Exiting mark mode.", "GREEN")
            break

        if not search_term:
            print_("Search keyword cannot be empty!", "RED")
            continue

        if last_search_term and results:
            if 1 <= selection <= len(results):
                # Get the actual Excel row index from the result
                row_index = results[selection - 1]['row_index']
                mark_result(row_index=row_index)
                print_(f"Updated record:", "GREEN")
                print_results(search_applications(index=row_index))
                last_search_term, results = None, None
                continue
            else:
                print_(f"Invalid selection. Please enter a number between 1 and {len(results)}.", "RED")
                continue

        results = search_applications(search_term=search_term)
        if not results:
            print_("No matching records found.", "RED")
            continue
        else:
            last_search_term = search_term
            results = results


def main():
    # Set up signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    print_("Validating cookie...")
    if not validate_cookie():
        print_("Cookie is invalid. It is recommended to update the cookie.", "RED")

    try:
        while True:
            print("\n" + "-" * 100)
            print_(
                "Enter search keyword, paste Markdown table, URL, webpage content (wrapped with '< >' or '```'), "
                "\n'delete' to delete last row, 'cookie' to update cookie, 'summary' to view statistics, 'result' to enter mark mode, "
                "(or 'exit' to quit):")
            user_input_lines = []
            line_count = 0
            is_webpage_content = False
            while line_count < 3:
                line = input("> ").lstrip()

                if line.startswith('http://') or line.startswith('https://') or line.startswith('view-source:'):
                    is_webpage_content = True
                    user_input_lines.append(line)
                    break

                if line.startswith('<') or line.startswith('>') or line.startswith('```'):
                    is_webpage_content = True
                    user_input_lines.append(line)
                    try:
                        while True:
                            line, finished = detect_ending()
                            if finished:
                                raise KeyboardInterrupt
                            user_input_lines.append(line)
                    except (EOFError, KeyboardInterrupt):
                        break

                if not line:
                    break
                if "|" not in line:  # Not a Markdown table
                    user_input_lines.append(line)
                    break
                user_input_lines.append(line)
                line_count += 1

            if is_webpage_content:
                print("|" + "-" * 99)
                print_("Webpage content detected. Processing ...")
                content = '\n'.join(user_input_lines)
                handle_webpage_content(content)
                continue

            user_input = '\n'.join(user_input_lines).strip()

            if user_input.strip().lower() == 'exit':
                print_("Exiting ...")
                break

            if user_input.strip().lower() == 'summary':
                summary()
                continue

            if user_input.strip().lower().startswith('open'):
                open_excel_file()
                continue

            if user_input.strip().lower() == 'delete':
                try:
                    show_last_row(delete=True)
                except KeyboardInterrupt:
                    print_('\nDeletion cancelled. Send SIGINT again to exit.')
                continue

            if user_input.strip().lower() == 'last':
                show_last_row(delete=False)
                continue

            if user_input.strip().lower() == 'cookie':
                if not validate_cookie():
                    print_("Cookie is invalid. Starting cookie update.", "RED")
                    start_browser()
                    add_cookie()
                    validate_cookie()
                else:
                    print_("Cookie is valid.", "GREEN")
                continue

            if user_input.strip().lower() == 'result' or user_input.strip().lower() == 'mark':
                update_result()
                continue

            if not user_input:
                print_("Search keyword cannot be empty!", "RED")
                continue

            if is_markdown_table(user_input):
                # Parse the Markdown table
                data = parse_markdown_table(user_input)

                if not data:
                    print_("Invalid Markdown table format.", "RED")
                    continue

                # Append the data to the Excel file
                append_data_to_excel(data=data)
                print_(f"New record successfully appended to Excel file.", "GREEN")

            else:
                results = search_applications(search_term=user_input)
                if results:
                    print_results(results)
                else:
                    print_("No matching records found.", "RED")

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
