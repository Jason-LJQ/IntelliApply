############################################
# Author: Jason Liao
# Date: 2024-12-22
# Description: A simple script to search for job applications in an Excel file
############################################

import os
import time
import signal
import sys

from utils.string_utils import is_markdown_table, parse_markdown_table, is_json
from utils.excel_utils import summary, open_excel_file, show_last_row, append_data_to_excel, search_applications, \
    mark_as_rejected, mark_as_processing, mark_as_offer, validate_excel_file
from utils.print_utils import print_, print_results
from utils.web_utils import save_cookie, validate_cookie, handle_webpage_content, start_browser, add_cookie, \
    handle_json_content, get_backup_directory

exit_flag = False


def signal_handler(sig, frame):
    global exit_flag
    if not exit_flag:
        # delete the last line
        print("\033[F", end="")
        print_("\n Prevous line deleted. Press Ctrl+C again to exit.", "YELLOW")
        exit_flag = True
    else:
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

    # Validate Excel file
    if not validate_excel_file():
        print_("Excel file is invalid. Please check the file.", "RED")
        return

    # Validate job snapshot folder
    if not get_backup_directory():
        print_("Job snapshot folder is invalid. The website will not be backed up to local storage.", "RED")

    print_("Validating cookie...")
    if not validate_cookie():
        print_("Cookie is invalid. It is recommended to update the cookie.", "RED")

    def main_loop():
        global exit_flag
        last_results = None

        while True:
            print("\n" + "-" * 100)
            prompt = ""
            prompt += ("Search with keywords or initials, Add new record by one-line JSON data / URL / webpage content "
                       "(wrapped with '< >' or '```'), \nEnter ")
            if last_results:
                prompt += "number+action (e.g. 1r=line 1 as reject, 2p=line 2 as processing, 3o=line 3 as offer), \n"
            prompt += "'delete' to delete last record, 'cookie' to update cookie, 'summary' to view statistics, "
            prompt += "'open' to open Excel file, (or 'exit' to quit):"

            print_(prompt)

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

            if user_input_lines:
                exit_flag = False

            if is_webpage_content:
                print("|" + "-" * 99)
                print_("Webpage content detected. Processing ...")
                content = '\n'.join(user_input_lines)
                handle_webpage_content(content)
                last_results = None
                continue

            user_input = '\n'.join(user_input_lines).strip()

            if user_input.strip().lower() == 'exit':
                print_("Exiting ...")
                exit_flag = True
                signal_handler(None, None)
                break

            if user_input.strip().lower() == 'summary':
                summary()
                last_results = None
                continue

            if user_input.strip().lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                last_results = None
                continue

            if user_input.strip().lower() == 'open':
                open_excel_file()
                last_results = None
                continue

            if user_input.strip().lower() == 'delete':
                try:
                    show_last_row(delete=True)
                except KeyboardInterrupt:
                    print_('\nDeletion cancelled. Send SIGINT again to exit.')
                last_results = None
                continue

            if user_input.strip().lower() == 'last':
                show_last_row(delete=False)
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
                last_results = None
                continue

            if not user_input:
                print_("Search keyword cannot be empty!", "RED")
                continue

            # Check for marking command: <number><action> (e.g., 1r, 2p, 3o) or pure number (e.g., 1 = 1r)
            import re
            mark_match = re.match(r'^(\d+)([a-z]?)$', user_input.strip().lower())

            if last_results and mark_match:
                selection = int(mark_match.group(1))
                action = mark_match.group(2) or 'r'  # Default to 'r' (rejected) if no action specified

                # Validate action letter
                if action not in ['r', 'p', 'o']:
                    print_(f"Invalid action '{action}'. Valid actions are:", "RED")
                    print("  r - mark as REJECTED (default if number only)")
                    print("  p - mark as PROCESSING")
                    print("  o - mark as OFFER")
                    print_(
                        f"Example: 1r (mark line 1 as rejected), 2p (mark line 2 as processing), 3o (mark line 3 as offer)",
                        "YELLOW")
                    continue

                # Validate selection number
                if selection < 1 or selection > len(last_results):
                    print_(f"Invalid line number {selection}. Please enter a number between 1 and {len(last_results)}.",
                           "RED")
                    print_(f"Tip: Use the line number shown in the search results (No. column)", "YELLOW")
                    continue

                # Process valid marking command
                row_data = last_results[selection - 1]
                company = row_data['Company']
                job_title = row_data['Job Title']

                # Determine action type and confirmation message
                if action == 'r':
                    action_text = "REJECTED"
                    action_color = "RED"
                    mark_func = mark_as_rejected
                elif action == 'p':
                    action_text = "PROCESSING"
                    action_color = "YELLOW"
                    mark_func = mark_as_processing
                elif action == 'o':
                    action_text = "OFFER"
                    action_color = "GREEN"
                    mark_func = mark_as_offer

                # Show confirmation prompt with color formatting
                from utils.print_utils import COLOR
                reset = COLOR["RESET"]
                yellow = COLOR["YELLOW"]
                action_text_colored = f"{COLOR[action_color]}{action_text}{yellow}"
                print_(f"\nDo you want to mark \"{reset}{job_title}{yellow}\" at \"{reset}{company}{yellow}\" as {action_text_colored}?", "YELLOW")
                print_results([row_data])
                confirm = input(print_("Confirm? (y/N): ", color="YELLOW", return_text=True)).strip().lower()

                if confirm == 'y':
                    row_index = row_data['row_index']
                    mark_func(row_index=row_index)
                    print_(f"Updated record:")
                    print_results(search_applications(index=row_index))
                    last_results = None
                    continue
                else:
                    print_("Operation cancelled.", "RED")
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
                last_results = None

            elif is_json(user_input):
                # Handle JSON input
                print_("JSON content detected. Processing ...")
                handle_json_content(user_input)
                last_results = None
                continue

            else:
                results = search_applications(search_term=user_input)
                if results:
                    last_results = results
                    print_results(results, mark_mode=True)
                else:
                    print_("No matching records found.", "RED")
                    last_results = None

    while True:
        try:
            main_loop()
        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
