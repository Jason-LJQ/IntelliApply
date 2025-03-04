from utils.string_utils import format_string

# Color constants
COLOR = {"RED": '\033[31m', "GREEN": '\033[32m', "YELLOW": '\033[33m', "RESET": '\033[0m'}


def print_results(results, mark_mode=False):
    """
    Prints the search results, including the 'Result' column with 'x' for colored cells.
    If mark_mode is True, adds a numbered index column for selection.
    """
    if not results:
        print_("Not found.", "RED")
        return

    print_(f"Found {len(results)} matching records:", "GREEN")

    # Calculate maximum widths for each column, including 'Result'
    company_width = max(len(format_string(r['Company'], limit=30)) for r in results)
    company_width = max(company_width, len("Company"))

    location_width = max(len(format_string(r['Location'])) for r in results)
    location_width = max(location_width, len("Location"))

    job_width = max(len(format_string(r['Job Title'], limit=65)) for r in results)
    job_width = max(job_width, len("Job Title"))

    result_width = max(len(str(r.get('result', ''))) for r in results)
    result_width = max(result_width, len("Result"))

    # Width for the index column in mark mode
    index_width = len(str(len(results))) + 1 if mark_mode else 0

    # Check if any Applied Date is valid
    has_valid_date = any(str(r.get('Applied Date', '')).strip() != '' for r in results)
    if has_valid_date:
        date_width = max(len(str(r.get('Applied Date', ''))) for r in results)
        date_width = max(date_width, len("Applied Date"))

    # Print header, including 'Result' and 'Applied Date' if valid
    if has_valid_date:
        if mark_mode:
            print("\n{:<{width0}}  {:<{width5}}  {:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                "No.", "Applied Date", "Result", "Company", "Location", "Job Title",
                width0=index_width,
                width5=date_width,
                width1=result_width,
                width2=company_width,
                width3=location_width,
                width4=job_width
            ))
            print("-" * (company_width + location_width + job_width + result_width + date_width + index_width + 10))
        else:
            print("\n{:<{width5}}  {:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                "Applied Date", "Result", "Company", "Location", "Job Title",
                width5=date_width,
                width1=result_width,
                width2=company_width,
                width3=location_width,
                width4=job_width
            ))
            print("-" * (company_width + location_width + job_width + result_width + date_width + 8))
    else:
        if mark_mode:
            print("\n{:<{width0}}  {:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                "No.", "Result", "Company", "Location", "Job Title",
                width0=index_width,
                width1=result_width,
                width2=company_width,
                width3=location_width,
                width4=job_width
            ))
            print("-" * (company_width + location_width + job_width + result_width + index_width + 8))
        else:
            print("\n{:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                "Result", "Company", "Location", "Job Title",
                width1=result_width,
                width2=company_width,
                width3=location_width,
                width4=job_width
            ))
            print("-" * (company_width + location_width + job_width + result_width + 6))

    # Print results
    for i, result in enumerate(results, 1):
        if has_valid_date:
            if mark_mode:
                print("{:<{width0}}  {:<{width5}}  {:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                    str(i),
                    str(result.get('Applied Date', '')),
                    str(result['result']),
                    format_string(result['Company'], limit=30),
                    format_string(result['Location']),
                    format_string(result['Job Title'], limit=65),
                    width0=index_width,
                    width5=date_width,
                    width1=result_width,
                    width2=company_width,
                    width3=location_width,
                    width4=job_width
                ))
            else:
                print("{:<{width5}}  {:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                    str(result.get('Applied Date', '')),
                    str(result['result']),
                    format_string(result['Company'], limit=30),
                    format_string(result['Location']),
                    format_string(result['Job Title'], limit=65),
                    width5=date_width,
                    width1=result_width,
                    width2=company_width,
                    width3=location_width,
                    width4=job_width
                ))
        else:
            if mark_mode:
                print("{:<{width0}}  {:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                    str(i),
                    str(result['result']),
                    format_string(result['Company'], limit=30),
                    format_string(result['Location']),
                    format_string(result['Job Title'], limit=65),
                    width0=index_width,
                    width1=result_width,
                    width2=company_width,
                    width3=location_width,
                    width4=job_width
                ))
            else:
                print("{:<{width1}}  {:<{width2}}  {:<{width3}}  {:<{width4}}".format(
                    str(result['result']),
                    format_string(result['Company'], limit=30),
                    format_string(result['Location']),
                    format_string(result['Job Title'], limit=65),
                    width1=result_width,
                    width2=company_width,
                    width3=location_width,
                    width4=job_width
                ))


def print_(text="", color=None, return_text=False):
    """
    Print text with optional color and [*] prefix.
    If text starts with \n, print newlines first.
    """
    # Check if text starts with newlines
    if isinstance(text, str):
        # Print newlines and remove them from text
        while text.startswith('\n'):
            print()  # Print empty line
            text = text[1:]  # Remove the leading newline
    
    formatted_text = ""

    if not color or color not in COLOR:
        formatted_text = f"[*] {text}"
    else:
        formatted_text = "{}[*] {}{}".format(COLOR[color.upper()], text, COLOR["RESET"])

    if return_text:
        return formatted_text
    else:
        print(formatted_text)
