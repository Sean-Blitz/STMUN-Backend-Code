import csv
import os

class CSV:
    def __init__(self) -> None:
        pass

    def append_to_csv(self, filename, row_data):
        """
        Appends a single row of data to a specified CSV file.
        Automatically handles comma-escaping and structural formatting.
        
        Parameters:
        filename (str): The name or path of the CSV file (e.g., 'assignments_log.csv').
        row_data (list): A list of items representing the cells of the row (e.g., ['School A - #1', 'DISEC', 'Bolivia']).
        """
        # Opening with mode='a' enables appending without wiping existing data.
        # newline='' prevents standard Windows/Unix double-spacing bugs.
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(row_data)
    
    def find_non_overlap_string(self, Dataset, csv_filepath):
        #finds strings inside Dataset not in CSV.
        assigned = set()
        if os.path.exists(csv_filepath):
            with open(csv_filepath, mode='r', encoding='utf-8') as f:
                csvdata = csv.reader(f)
                for row in csvdata:
                    if row: 
                        assigned.add(row[0].strip())
        return [s for s in Dataset if s.strip() not in assigned]