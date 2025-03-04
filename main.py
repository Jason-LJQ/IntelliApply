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


def main():
    # Set up signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    print_("Validating cookie...")
    if not validate_cookie():
        print_("Cookie is invalid. It is recommended to update the cookie.", "RED")

    last_search_term = None
    last_results = None

    try:
        while True:
            print("\n" + "-" * 100)
        
            if last_results:
                print_(f"[*] Current Search: {last_search_term}")
                print_results(last_results, mark_mode=True)
                print_("Enter a number to mark the record, or enter a new search term.")
            else:
                print_(
                    "Enter search keyword, paste Markdown table, URL, webpage content (wrapped with '< >' or '```'), "
                    "\n'delete' to delete last row, 'cookie' to update cookie, 'summary' to view statistics, "
                    "Enter number to mark rejection "
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
                last_search_term = None
                last_results = None
                continue

            user_input = '\n'.join(user_input_lines).strip()

            if user_input.strip().lower() == 'exit':
                print_("Exiting ...")
                break

            if user_input.strip().lower() == 'summary':
                summary()
                last_search_term = None
                last_results = None
                continue

            if user_input.strip().lower().startswith('open'):
                open_excel_file()
                last_search_term = None
                last_results = None
                continue

            if user_input.strip().lower() == 'delete':
                try:
                    show_last_row(delete=True)
                except KeyboardInterrupt:
                    print_('\nDeletion cancelled. Send SIGINT again to exit.')
                last_search_term = None
                last_results = None
                continue

            if user_input.strip().lower() == 'last':
                show_last_row(delete=False)
                last_search_term = None
                last_results = None
                continue

            if user_input.strip().lower() == 'cookie':
                if not validate_cookie():
                    print_("Cookie is invalid. Starting cookie update.", "RED")
                    start_browser()
                    add_cookie()
                    validate_cookie()
                else:
                    print_("Cookie is valid.", "GREEN")
                last_search_term = None
                last_results = None
                continue

            if not user_input:
                print_("Search keyword cannot be empty!", "RED")
                continue

            
            if last_results and user_input.strip().isdigit():
                selection = int(user_input.strip())
                if 1 <= selection <= len(last_results):
                    row_data = last_results[selection - 1]
                    print_(f"\nYou are about to mark the following record:", "YELLOW")
                    print_results([row_data])
                    confirm = input(print_("Confirm? (y/N): ", color="YELLOW", return_text=True)).strip().lower()
                    if confirm == 'y':
                        row_index = row_data['row_index']
                        mark_result(row_index=row_index)
                        print_(f"Updated record:")
                        print_results(search_applications(index=row_index))
                    else:
                        print_("Operation cancelled.", "RED")
                    last_search_term = None
                    last_results = None
                    continue
                else:
                    print_(f"Invalid selection. Please enter a number between 1 and {len(last_results)}.", "RED")
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
                last_search_term = None
                last_results = None

            else:
                results = search_applications(search_term=user_input)
                if results:
                    last_search_term = user_input
                    last_results = results
                    print_results(results, mark_mode=True)
                else:
                    print_("No matching records found.", "RED")
                    last_search_term = None
                    last_results = None

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
