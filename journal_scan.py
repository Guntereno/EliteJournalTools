import argparse
import json
import os
import traceback
from datetime import datetime
from dateutil import parser as date_parser
from pytz import UTC

data_path = os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous")
os.chdir(data_path)

class JournalScanner:
    event_handlers = {}

    def register_handler(self, event_name, handler):
        self.event_handlers[event_name] = handler

    def handle_event(self, event):
        event_id = event["event"]
        if event_id in self.event_handlers:
            self.event_handlers[event_id](event)

class BookMark:
    filename = None
    line_number = -1
    line_hash = None

    def __init__(self, filename, line_number, line_hash) -> None:
        self.filename = filename
        self.line_number = line_number
        self.line_hash = line_hash

def init_argparse():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] function",
        description="Perform a variety of analysis functions on the users journal files."
    )

    parser.add_argument("-s", "--start_date", help="Date to start search from.")
    parser.add_argument("-e", "--end_date", help="Date to end search at.")

    return parser

def include_journal_file(filename):
    if not filename.startswith('Journal.'):
        return False
    if not filename.endswith('.log'):
        return False
    return True

def get_journal_file_list():
    all_files = os.listdir(data_path)
    return list(filter(lambda f: include_journal_file(f), all_files))

def scan_file(filename, scanner, book_mark=None):
    if not isinstance(scanner, JournalScanner):
        raise Exception("'scanner' parameter is not a JournalScanner!")

    try:
        with open(filename, encoding='utf-8') as file_ptr:
            lines = file_ptr.readlines()
            if(len(lines) == 0):
                return None

            start_line = 0
            if book_mark is not None:
                last_line = lines[book_mark.line_number]
                if (hash(last_line) != book_mark.line_hash) or (filename != book_mark.filename):
                    raise Exception("Attempting to resume from invalid book mark!")
                start_line = book_mark.line_number + 1

            for line_num in range(start_line, len(lines)):
                line = lines[line_num]
                event = json.loads(line)
                try:
                    scanner.handle_event(event)
                except Exception as e:
                    print(f"Error parsing event:\nEvent={event}")
                    raise e

            last_line_num = len(lines)-1
            last_line = lines[last_line_num]
            return BookMark(filename, last_line_num, hash(last_line))

    except Exception as e:
        print("Error loading file '" + filename + "': ")
        traceback.print_exc()
        return None

def scan_files(scanner, filenames):
    book_mark = None
    for filename in filenames:
        book_mark = scan_file(filename, scanner)
    return book_mark

def file_in_file_range(file, start_file, end_file):
    if (start_file is not None) and (file < start_file):
        return False
    if (end_file is not None) and (file > end_file):
        return False
    return True

def scan_files_in_file_range(scanner, start_file, end_file):
    files_in_range = filter(lambda f: file_in_file_range(f, start_file, end_file), get_journal_file_list())
    return scan_files(scanner, files_in_range)

def scan_journal_files_in_date_range(scanner, start_date, end_date):
    date_format = 'Journal.%y%m%d%H%M%S.01.log'
    start_file = None if start_date is None else start_date.strftime(date_format)
    end_file = None if end_date is None else end_date.strftime(date_format)
    return scan_files_in_file_range(scanner, start_file, end_file)

def resume_from_book_mark(scanner, book_mark):
    if book_mark is None:
        return
    file_names = get_journal_file_list()
    last_file_index = file_names.index(book_mark.filename)
    # Scan the first file
    book_mark = scan_file(file_names[last_file_index], scanner, book_mark)
    # Scan remaining files
    remaining_files = file_names[(last_file_index+1):len(file_names)]
    if(len(remaining_files) > 0):
        return scan_files(scanner, remaining_files)
    else:
        return book_mark

def scan_journal(scanner):
    args_parser = init_argparse()
    args = args_parser.parse_args()

    start_date = None
    if args.start_date is not None:
        start_date = UTC.localize(date_parser.parse(args.start_date))
        print(f"Using start date: {start_date}")

    end_date = None
    if args.end_date is not None:
        end_date = UTC.localize(date_parser.parse(args.end_date))
        print(f"Using end date: {end_date}")

    return scan_journal_files_in_date_range(scanner, start_date, end_date)

if __name__ == "__main__":
    # Simple scanner which prints all recvieved text as a test
    scanner = JournalScanner()
    scanner.register_handler('ReceiveText', lambda e: print(e['Message_Localised']) if ('Message_Localised' in e) else print (e['Message']))
    scan_journal(scanner)