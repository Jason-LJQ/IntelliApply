import re
import os
import sqlite3
import tempfile
from contextlib import contextmanager, closing
from datetime import datetime, date

import pandas as pd
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill

from intelliapply.utils.print_utils import print_, print_results
from intelliapply.utils.string_utils import normalize_company_name, get_abbreviation_lower, cleaned_string
from intelliapply.config.credential import DB_FILE_PATH, EXCEL_FILE_PATH
from intelliapply.config.prompt import ALL_FIELDS

# Stored columns besides 'id'. 'Status' holds '', 'REJECTED', 'PROCESSING' or 'OFFER'.
FIELDS = ['Status'] + ALL_FIELDS


def _quote(name):
    """Quote a column name for SQL (field names contain spaces)."""
    return f'"{name}"'


def _cell_text(value):
    """Convert an Excel cell value to the text stored in the database."""
    if value is None:
        return ''
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d')
    return str(value)


class JobDatabase:
    """
    SQLite-backed job application storage.
    Every operation opens a short-lived connection, so the CLI and the web UI thread can share one instance.
    """

    # Status colors used for Excel import/export
    STATUS_COLORS = {
        'REJECTED': 'FFFF0000',  # Red
        'PROCESSING': 'FFFFFF00',  # Yellow
        'OFFER': 'FF00FF00'  # Green
    }

    STATUS_SYMBOLS = {
        'REJECTED': '  ⨉  ',
        'PROCESSING': '  →  ',
        'OFFER': '  ✔  ',
    }

    # Date column updated when a record is marked with the status
    STATUS_DATE_COLUMNS = {
        'REJECTED': 'Result Date',
        'PROCESSING': 'Processed Date',
        'OFFER': 'Result Date'
    }

    def __init__(self, db_path=None, legacy_excel_path=None):
        """
        Open (or create) the database. A new database imports the legacy Excel file once if it exists.

        Args:
            db_path: Path to the SQLite file (defaults to DB_FILE_PATH from config)
            legacy_excel_path: Excel file to migrate from (defaults to EXCEL_FILE_PATH from config)
        """
        self.db_path = db_path or DB_FILE_PATH
        is_new = not os.path.exists(self.db_path)
        if is_new:
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_schema()

        if is_new:
            print_(f"Created new database at {self.db_path}", "GREEN")
            excel_path = legacy_excel_path or EXCEL_FILE_PATH
            if excel_path and os.path.exists(excel_path):
                try:
                    count = self.import_excel(excel_path)
                except Exception:
                    # Remove the empty database so the import is retried next time
                    os.remove(self.db_path)
                    raise
                print_(f"Imported {count} records from Excel file {excel_path}", "GREEN")

    @contextmanager
    def _connect(self):
        """Yield a connection inside a transaction, and always close it afterwards."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self):
        columns = ', '.join(f"{_quote(field)} TEXT NOT NULL DEFAULT ''" for field in FIELDS)
        with self._connect() as conn:
            conn.execute(f"CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns})")
            # Add columns introduced by newer field definitions
            existing = {row['name'] for row in conn.execute("PRAGMA table_info(jobs)")}
            for field in FIELDS:
                if field not in existing:
                    conn.execute(f"ALTER TABLE jobs ADD COLUMN {_quote(field)} TEXT NOT NULL DEFAULT ''")

    def _backup(self):
        """Copy the database to the system temp directory and return the backup path."""
        backup_path = os.path.join(tempfile.gettempdir(),
                                   f"job_application_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        with closing(sqlite3.connect(self.db_path)) as src, closing(sqlite3.connect(backup_path)) as dst:
            src.backup(dst)
        return backup_path

    def _to_result(self, row):
        """Add the display 'status' symbol used by print_results."""
        return {**row, 'status': self.STATUS_SYMBOLS.get(row['Status'], '')}

    def _insert(self, conn, record):
        """Insert one record (missing fields become empty strings) and return its id."""
        values = [str(record.get(field) or '') for field in FIELDS]
        cursor = conn.execute(
            f"INSERT INTO jobs ({', '.join(_quote(f) for f in FIELDS)}) VALUES ({', '.join('?' * len(FIELDS))})",
            values)
        return cursor.lastrowid

    def get_all_jobs(self):
        """Return all records as dicts ordered by insertion."""
        with self._connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM jobs ORDER BY id")]

    def get_job(self, job_id):
        """Return a single record as dict, or None if not found."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return dict(row) if row else None

    def search_applications(self, search_term=""):
        """
        Search for both company and job title matches.

        Args:
            search_term: The search term to match against company and job title

        Returns:
            List of matching records
        """
        try:
            with self._connect() as conn:
                df = pd.read_sql_query("SELECT * FROM jobs ORDER BY id", conn)

            if df.empty:
                return []

            # 1. Prepare search term variations
            search_term_clean_lower = cleaned_string(search_term).lower()
            norm_keyword = normalize_company_name(search_term)
            abbr_keyword = get_abbreviation_lower(norm_keyword)

            # 2. Create helper columns using vectorized `apply`
            df['norm_company'] = df['Company'].apply(normalize_company_name)
            df['abbr_company'] = df['Company'].apply(get_abbreviation_lower)
            df['clean_job_title'] = df['Job Title'].apply(cleaned_string).str.lower()

            # Create a regex pattern for word-level matching
            job_title_pattern = r'\b' + re.escape(search_term_clean_lower) + r'\b'

            # 3. Build boolean masks

            # Mask 1: Direct, Prefix, and Job Title matches
            m_base = (
                    (df['norm_company'] == norm_keyword) |
                    (df['norm_company'].str.startswith(norm_keyword, na=False)) |
                    (df['clean_job_title'].str.contains(job_title_pattern, na=False, regex=True))
            )

            # Mask 2: Handles "om" matching "Old Mission"
            m_abbr_target = (df['abbr_company'] == norm_keyword)

            # Mask 3: Handles "GSK" matching "GlaxoSmithKline"
            m_abbr_keyword_vs_abbr_target = pd.Series([False] * len(df), index=df.index)
            if len(abbr_keyword) > 1:
                m_abbr_keyword_vs_abbr_target = (df['abbr_company'] == abbr_keyword)

            # 4. Combine all masks using logical OR
            final_mask = m_base | m_abbr_target | m_abbr_keyword_vs_abbr_target

            # 5. Filter the DataFrame and format results
            matched_df = df.loc[final_mask, ['id'] + FIELDS]
            return [self._to_result(row) for row in matched_df.to_dict('records')]

        except Exception as e:
            print_(f"Error during search: {str(e)}", "RED")
            return []

    def check_duplicate_entry(self, new_data=None):
        """
        Check if the exact same job entry (Company and Job Title) already exists.
        Returns matching record if duplicate found, None otherwise.
        """
        if new_data is None:
            return None
        try:
            for row in self.get_all_jobs():
                if all(row[field].strip() == str(new_data[field]).strip()
                       for field in ['Company', 'Job Title'] if field in new_data):
                    return row
            return None

        except Exception as e:
            print_(f"Error checking for duplicates: {str(e)}", "RED")
            return None

    def get_summary(self):
        """Return application counts and rates."""
        statuses = [row['Status'] for row in self.get_all_jobs()]
        total = len(statuses)
        rejections = statuses.count('REJECTED')
        processing = statuses.count('PROCESSING')
        offers = statuses.count('OFFER')
        return {
            'total': total,
            'rejected': rejections,
            'processing': processing,
            'offers': offers,
            'rejection_rate': (rejections / total * 100) if total > 0 else 0,
            'processing_rate': (processing / total * 100) if total > 0 else 0,
            'offer_rate': (offers / processing * 100) if processing > 0 else 0,
        }

    def summary(self):
        """
        Print a summary of job applications including:
        - Total number of applications
        - Number of rejections, processing, and offers
        - Rejection, processing, and offer rates
        """
        try:
            s = self.get_summary()

            if s['total'] == 0:
                print_("No applications to summarize.", "RED")
                return

            # Print summary with color formatting
            print_(f"\nApplication Summary:")
            print(f"Total Applications: {s['total']}")
            print(f"Rejected: {s['rejected']}")
            print(f"Processing: {s['processing']}")
            print(f"Offers: {s['offers']}")
            print(f"Rejection Rate: {s['rejection_rate']:.1f}%")
            print(f"Processing Rate: {s['processing_rate']:.1f}%")
            print(f"Offer Rate: {s['offer_rate']:.1f}% (offers/processing)")

        except Exception as e:
            print_(f"Error generating summary: {str(e)}", "RED")

    def show_last_row(self, delete=False):
        """
        Show last record's data. If delete is True, delete the last record after user confirmation.
        """
        try:
            with self._connect() as conn:
                row = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1").fetchone()

            if row is None:
                print_("No data to show.", "RED")
                return

            last = dict(row)
            print_results([self._to_result(last)])

            if delete:
                # Ask for user confirmation
                confirm = input(print_("Delete this row? (y/Y to confirm, any other key to cancel): ", color="BLUE",
                                       return_text=True)).lower()
                if confirm == 'y':
                    self.delete_job(last['id'])
                    print_(f"Last row deleted successfully.", "GREEN")
                else:
                    print_(f"Deletion cancelled.", "RED")

        except Exception as e:
            print_(f"Error processing last row: \n{str(e)}", "RED")

    def append_data(self, data=None):
        """
        Append a list of dictionaries as new records. Unknown keys are ignored.

        Returns:
            List of new record ids (empty on failure)
        """
        if data is None:
            return []

        try:
            with self._connect() as conn:
                return [self._insert(conn, {**row_data, 'Status': ''}) for row_data in data]
        except Exception as e:
            print_(f"Error appending data to database: {str(e)}", "RED")
            return []

    def update_job(self, job_id, changes):
        """
        Update arbitrary fields of a record.

        Returns:
            Updated record, or None if not found

        Raises:
            ValueError: If a field or status value is invalid
        """
        for field, value in changes.items():
            if field not in FIELDS:
                raise ValueError(f"Unknown field: {field}")
            if field == 'Status' and value and value not in self.STATUS_COLORS:
                raise ValueError(f"Invalid status: {value}")
        if changes:
            assignments = ', '.join(f"{_quote(field)} = ?" for field in changes)
            values = [str(value or '') for value in changes.values()]
            with self._connect() as conn:
                conn.execute(f"UPDATE jobs SET {assignments} WHERE id = ?", values + [job_id])
        return self.get_job(job_id)

    def delete_job(self, job_id):
        """Delete a record after backing up the database. Returns True if a record was deleted."""
        self._backup()
        with self._connect() as conn:
            return conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,)).rowcount > 0

    def set_status(self, job_id, status):
        """
        Set status and update the corresponding date column with current date.

        Returns:
            Updated record, or None if not found
        """
        if status not in self.STATUS_DATE_COLUMNS:
            raise ValueError(f"Invalid status: {status}")
        current_date = datetime.now().strftime('%Y-%m-%d')
        return self.update_job(job_id, {'Status': status, self.STATUS_DATE_COLUMNS[status]: current_date})

    def _mark_status(self, job_id, status):
        """
        Internal helper method to mark status with a backup and console output.

        Returns:
            True if successful, False otherwise
        """
        try:
            backup_path = self._backup()
            print_(f"\nBackup created at {backup_path}")

            if self.set_status(job_id, status) is None:
                print_(f"Record {job_id} not found.", "RED")
                return False

            print_(f"Record {job_id} marked as {status}.", "GREEN")
            return True

        except Exception as e:
            print_(f"Error marking as {status}: {str(e)}", "RED")
            return False

    def mark_as_rejected(self, job_id):
        """Mark the record as REJECTED and update 'Result Date'. Also backs up the database to temp directory."""
        return self._mark_status(job_id, 'REJECTED')

    def mark_as_processing(self, job_id):
        """Mark the record as PROCESSING and update 'Processed Date'. Also backs up the database to temp directory."""
        return self._mark_status(job_id, 'PROCESSING')

    def mark_as_offer(self, job_id):
        """Mark the record as OFFER and update 'Result Date'. Also backs up the database to temp directory."""
        return self._mark_status(job_id, 'OFFER')

    def import_excel(self, excel_path):
        """
        Import records from an Excel file in the legacy format (Status cell color + field columns).

        Returns:
            Number of imported records
        """
        color_to_status = {color: status for status, color in self.STATUS_COLORS.items()}
        wb = load_workbook(filename=excel_path)
        ws = wb.active
        headers = {cell.value: cell.column for cell in ws[1]}

        records = []
        for row_idx in range(2, ws.max_row + 1):  # Start from row 2 (skip header)
            record = {field: _cell_text(ws.cell(row=row_idx, column=headers[field]).value)
                      for field in ALL_FIELDS if field in headers}
            # Skip rows without any data (e.g. formatted but empty rows)
            if not any(value.strip() for value in record.values()):
                continue
            if 'Status' in headers:
                cell = ws.cell(row=row_idx, column=headers['Status'])
                record['Status'] = color_to_status.get(cell.fill.start_color.rgb if cell.fill else None, '')
            records.append(record)
        wb.close()

        with self._connect() as conn:
            for record in records:
                self._insert(conn, record)
        return len(records)

    def export_excel(self, target=None):
        """
        Export all records to an Excel file in the legacy format (Status cell color + field columns).

        Args:
            target: File path or binary file object. Defaults to a timestamped file next to the database.

        Returns:
            The target written to
        """
        if target is None:
            target = os.path.join(os.path.dirname(os.path.abspath(self.db_path)),
                                  f"job_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.append(FIELDS)
        for row in self.get_all_jobs():
            # Status is represented by cell color only, same as the legacy Excel file
            ws.append([None] + [row[field] or None for field in ALL_FIELDS])
            color = self.STATUS_COLORS.get(row['Status'])
            if color:
                ws.cell(row=ws.max_row, column=1).fill = PatternFill(start_color=color, end_color=color,
                                                                     fill_type="solid")
        wb.save(target)
        return target
