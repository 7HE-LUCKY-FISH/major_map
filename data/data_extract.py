import re
import csv

def extract_courses_to_csv(file_path, csv_path, year="2025", semester="Fall", skip_lines=0, skip_end_lines=0):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if skip_end_lines > 0:
        lines = lines[skip_lines:-skip_end_lines]
    else:
        lines = lines[skip_lines:]

    # Get column headers from the first line
    headers = lines[0].strip().split('\t')
    headers += ["Year", "Semester"]
    class_code_pattern = re.compile(r'^([A-Z]{2,4})\s')

    rows = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if line.startswith(('RA ', 'RC ', 'RE ', 'RO ', 'PV ', 'RS', 'RL', 'PC', 'RQ ','RK', 'CA', 'CB', 'FB ', 'II','RH', 'IG ', 'PE', 'PP','PN', 'IN','IM', 'IL', 'FULLY', 'ONLINE', 'HYBRID')):
            continue
        match = class_code_pattern.match(line)
        if match:

            values = line.split('\t')
            # Pad values if missing columns
            values += ["" for _ in range(len(headers) - 2 - len(values))]
            values += [year, semester]
            rows.append(values)

    # Write to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(rows)

# Example usage:
default = [f"web_page_text ({i}).txt" for i in range(12)]  # Change range as needed


#change skip lines to 70 as there are 70 header lines in the new files
#we need to fix indendation on all files
for i, file_path in enumerate(default):
    extract_courses_to_csv(file_path, f"output_{i}.csv", year="2023", semester="Fall", skip_lines=41, skip_end_lines=0)
