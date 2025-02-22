############################################
# Author: Jason Liao
# Date: 2024-12-22
# Description: A simple script to search for job applications in an Excel file
############################################
import os
import time
import signal
import sys

from prompt import *
from string_utils import *
from excel_util import *
from credential import *
from print_utils import print_, print_results
from web_utils import *


def signal_handler(sig, frame):
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


def main(excel_file=EXCEL_FILE_PATH):
    # Set up signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    # Get cookie from the same directory as the script
    cookie_path = COOKIE_PATH

    print_("Validating cookie...")
    if not validate_cookie(cookie_path):
        print_("Cookie is invalid. It is recommended to update the cookie.", "RED")

    try:
        while True:
            print("\n" + "-" * 100)
            print_(
                "Enter search keyword, paste Markdown table, URL, webpage content (starting with '<' or '```'), "
                "\n'delete' to delete last row, 'cookie' to update cookie, 'summary' to view statistics, "
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
                handle_webpage_content(content, excel_file)
                continue

            user_input = '\n'.join(user_input_lines).strip()

            if user_input.strip().lower() == 'exit':
                print_("Exiting ...")
                break

            if user_input.strip().lower() == 'summary':
                summary(excel_file)
                continue

            if user_input.strip().lower().startswith('open'):
                open_excel_file(excel_file)
                continue

            if user_input.strip().lower() == 'delete':
                try:
                    delete_last_row(excel_file)
                except KeyboardInterrupt:
                    print_('\nDeletion cancelled. Send SIGINT again to exit.')

                continue

            if user_input.strip().lower() == 'cookie':
                if not validate_cookie(cookie_path):
                    print_("Cookie is invalid. Starting cookie update.", "RED")
                    start_browser()
                    save_cookie(cookie_path)
                    validate_cookie(cookie_path)
                else:
                    print_("Cookie is valid.", "GREEN")
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
                append_data_to_excel(excel_file, data)
                print_(f"New record successfully appended to Excel file.", "GREEN")

            else:
                results = search_applications(excel_file, user_input)
                if results:
                    print_results(results, excel_file)
                else:
                    print_("No matching records found.", "RED")

    except KeyboardInterrupt:
        print_('\nExiting ...', "RED")
        sys.exit(0)


if __name__ == "__main__":
    main()
