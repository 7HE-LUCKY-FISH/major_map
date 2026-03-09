import csv
import os
import time
import dotenv
from datetime import datetime
import mysql.connector
from mysql.connector import Error

dotenv.load_dotenv()


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Build the path to data/csv_data/ relative to this script's location.
# This script lives at backend/database/, so we go up two levels to the repo
# root and then down into data/csv_data/.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FOLDER = os.path.join(SCRIPT_DIR, '..', '..', 'data', 'csv_data')


# ---------------------------------------------------------------------------
# Step 1 — Mode mapping
# ---------------------------------------------------------------------------

# The CSV "Mode" column uses different strings than the ENUM in schedule_flat.
# This dictionary translates each CSV value to the matching ENUM literal.
MODE_MAP = {
    'In Person':    'InPerson',
    'Fully Online': 'Online',
    'Hybrid':       'Hybrid',
}


# ---------------------------------------------------------------------------
# Step 2 — parse_course_number
# ---------------------------------------------------------------------------

def parse_course_number(raw):
    """
    Takes a full Section string like "BIOL 10 (Section 01)"
    and returns just the course code: "BIOL 10".
    Strips any trailing whitespace.
    """
    return raw.split(' (Section')[0].strip()


# ---------------------------------------------------------------------------
# Step 3 — parse_time
# ---------------------------------------------------------------------------

def parse_time(raw):
    """
    Takes a times string like "09:00AM-10:15AM" and returns a tuple of two
    datetime.time objects: (time_start, time_end).

    Returns (None, None) if the value is "TBA" or empty — which is the case
    for fully online sections that have no fixed meeting time.
    """
    raw = raw.strip()

    # Online sections and arranged courses have no set time
    if not raw or raw.upper() == 'TBA':
        return None, None

    # The format is "HH:MMAM-HH:MMPM" — split on "-" to get the two halves
    parts = raw.split('-')

    # Format the parts as time objects for conversion to MySQL's TIME type
    time_start = datetime.strptime(parts[0].strip(), '%I:%M%p').time()
    time_end   = datetime.strptime(parts[1].strip(), '%I:%M%p').time()

    return time_start, time_end


# ---------------------------------------------------------------------------
# Step 4 — parse_dates
# ---------------------------------------------------------------------------

def parse_dates(raw):
    """
    Takes a dates string like "08/21/24-12/09/24" and returns a tuple of two
    datetime.date objects: (date_start, date_end).

    Returns (None, None) if the value is empty.
    """
    raw = raw.strip()

    if not raw:
        return None, None

    # The format is "MM/DD/YY-MM/DD/YY"
    parts = raw.split('-')

    # Turn into date object for conversion to MySQL's DATE type. 
    date_start = datetime.strptime(parts[0].strip(), '%m/%d/%y').date()
    date_end   = datetime.strptime(parts[1].strip(), '%m/%d/%y').date()

    return date_start, date_end


# ---------------------------------------------------------------------------
# Step 5 — load_csv_file
# ---------------------------------------------------------------------------

def load_csv_file(cursor, filepath):
    """
    Reads one CSV file, transforms each row to match schedule_flat, and
    bulk-inserts all rows using INSERT IGNORE.

    INSERT IGNORE means: if a row with the same (year, semester, section_code)
    already exists, that row is silently skipped instead of raising an error.
    This makes the script safe to run more than once.

    Returns the number of rows that were attempted.
    """
    rows = []

    with open(filepath, newline='', encoding='utf-8') as f:
        #reads the CSV file we just opened
        reader = csv.DictReader(f)

        for row in reader:
            # Strip leading/trailing whitespace from every column name and value
            row = {key.strip(): value.strip() for key, value in row.items()}

            # -- section_code: the CRN from CSV "Number" (e.g. "40443") --
            section_code = row['Number']

            # -- course_number: course code parsed from CSV "Section" (e.g. "BIOL 10") --
            course_number = parse_course_number(row['Section'])

            # -- mode: map the CSV string to the ENUM literal --
            mode = MODE_MAP.get(row['Mode'], row['Mode'])

            # -- title --
            title = row['Title']

            # -- satisfies --
            satisfies = row.get('Satisfies') or None

            # -- units: convert to float, None if empty --
            units = float(row['Unit']) if row['Unit'] else None

            # -- component_type: LEC, LAB, SEM, etc. --
            component_type = row['Type'] if row['Type'] else None

            # -- days_text: store None for TBA (online sections) --
            days_raw  = row['Days']
            days_text = days_raw if days_raw and days_raw.upper() != 'TBA' else None

            # -- time_start, time_end: parsed from CSV "Times" --
            time_start, time_end = parse_time(row['Times'])

            # -- instructor_name --
            instructor_name = row['Instructor'] if row['Instructor'] else None

            # -- location_text --
            location_text = row['Location'] if row['Location'] else None

            # -- date_start, date_end: parsed from CSV "Dates" --
            date_start, date_end = parse_dates(row['Dates'])

            # -- seats_available --
            seats_available = int(row['Seats']) if row['Seats'] else None

            # -- year, semester --
            year     = int(row['Year'])
            semester = row['Semester']

            # Build a tuple in the same column order as the INSERT below
            rows.append((
                section_code,
                course_number,
                mode,
                title,
                satisfies,
                units,
                component_type,
                days_text,
                time_start,
                time_end,
                instructor_name,
                location_text,
                date_start,
                date_end,
                seats_available,
                year,
                semester,
            ))

    insert_sql = """
        INSERT IGNORE INTO schedule_flat (
            section_code,
            course_number,
            mode,
            title,
            satisfies,
            units,
            component_type,
            days_text,
            time_start,
            time_end,
            instructor_name,
            location_text,
            date_start,
            date_end,
            seats_available,
            year,
            semester
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    cursor.executemany(insert_sql, rows)
    return len(rows)


# ---------------------------------------------------------------------------
# Step 6 — main
# ---------------------------------------------------------------------------

def main():
    # Connect to MySQL — retry up to 10 times in case the DB container is
    # still starting up (e.g. in Docker Compose)
    connection = None
    for _ in range(10):
        try:
            connection = mysql.connector.connect(
                host     = os.getenv('DB_HOST',     'localhost'),
                user     = os.getenv('DB_USER',     'root'),
                password = os.getenv('DB_PASSWORD', 'adminpass'),
                auth_plugin='mysql_native_password'
            )
            break
        except Error:
            print('Waiting for database connection...')
            time.sleep(5)
    else:
        print('Could not connect to the database after 10 attempts.')
        return

    cursor = connection.cursor()
    cursor.execute('USE major_map_db')

    # Find all .csv files in the data folder and sort for predictable output
    csv_files = sorted([f for f in os.listdir(CSV_FOLDER) if f.endswith('.csv')])

    if not csv_files:
        print(f'No CSV files found in: {CSV_FOLDER}')
        return

    total_rows = 0
    for filename in csv_files:
        filepath = os.path.join(CSV_FOLDER, filename)
        try:
            count = load_csv_file(cursor, filepath)
            print(f'Loaded {filename}: {count} rows attempted')
            total_rows += count
        except Exception as e:
            print(f'ERROR loading {filename}: {e}')

    connection.commit()
    cursor.close()
    connection.close()

    print(f'\nDone. Total rows attempted across all files: {total_rows}')


if __name__ == '__main__':
    main()
