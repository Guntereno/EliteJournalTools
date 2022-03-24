import argparse
import json
import os
import re
import time
import traceback
from datetime import datetime, timezone
from dateutil import parser as date_parser
from pytz import UTC

data_path = os.path.expanduser(
    "~/Saved Games/Frontier Developments/Elite Dangerous")
os.chdir(data_path)

cmdr_name = None


class JournalScanner:
    def __init__(self):
        self.event_handlers = {}

    def register_handler(self, event_name, handler):
        self.event_handlers[event_name] = handler

    def handle_event(self, event):
        event_id = event["event"]
        if event_id in self.event_handlers:
            self.event_handlers[event_id](event)


class BookMark:
    def __init__(self, filename, line_number, line_hash) -> None:
        self.filename = filename
        self.line_number = line_number
        self.line_hash = line_hash


def init_argparse():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] function",
        description="Perform a variety of analysis functions on the users journal files."
    )

    parser.add_argument("-s", "--start_date",
                        help="Date to start search from.")
    parser.add_argument("-e", "--end_date", help="Date to end search at.")

    return parser


def include_journal_file(filename):
    if not filename.startswith('Journal.'):
        return False
    if not filename.endswith('.log'):
        return False
    return True


filename_formats = [
    # New: 'Journal.2022-03-15T130425.01.log'
    (
        re.compile(
            u"""^Journal.(?P<date>\d{4}-\d{2}-\d{2}T\d{6}).(?P<part>\d+).log$"""),
        '%Y-%m-%dT%H%M%S'
    ),
    # Old: 'Journal.180828201628.01.log'
    (
        re.compile(u"""^Journal.(?P<date>\d{12}).(?P<part>\d+).log$"""),
        '%y%m%d%H%M%S'
    )
]


def match_filename_to_entry(filename, regex, time_format):
    match = re.search(regex, filename)
    if match is not None:
        struct = time.strptime(match.group('date'), time_format)
        date = datetime.fromtimestamp(
            time.mktime(struct), tz=timezone.utc)
        part = int(match.group('part'))
        return (filename, date, part)
    return None


def filename_to_entry(filename):
    for format in filename_formats:
        result = match_filename_to_entry(filename, format[0], format[1])
        if result is not None:
            return result
    return None


def get_journal_file_list():
    all_files = os.listdir(data_path)

    file_list = []
    for filename in all_files:
        entry = filename_to_entry(filename)
        if entry is None:
            continue
        file_list.append(entry)

    return sorted(file_list, key=lambda e: (e[1], e[2]))


def scan_file(file_entry, scanners, book_mark=None):
    filename = file_entry[0]

    if not isinstance(scanners, list):
        scanners = [scanners]
    for scanner in scanners:
        if not isinstance(scanner, JournalScanner):
            raise Exception(
                f"Object '{scanner}' parameter is not a JournalScanner!")

    try:
        with open(filename, encoding='utf-8') as file_ptr:
            lines = file_ptr.readlines()
            if(len(lines) == 0):
                return None

            start_line = 0
            if book_mark is not None:
                last_line = lines[book_mark.line_number]
                if (hash(last_line) != book_mark.line_hash) or (filename != book_mark.filename):
                    raise Exception(
                        "Attempting to resume from invalid book mark!")
                start_line = book_mark.line_number + 1

            for line_num in range(start_line, len(lines)):
                line = lines[line_num]
                event = json.loads(line)

                # HACK: Only read events for the first CMDR encountered
                global cmdr_name
                if (event['event'] == 'Commander'):
                    if (cmdr_name is None):
                        cmdr_name = event['Name']
                    else:
                        if event['Name'] != cmdr_name:
                            break

                try:
                    for scanner in scanners:
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


def scan_files(scanners, file_entries):
    book_mark = None
    for entry in file_entries:
        book_mark = scan_file(entry, scanners)
    return book_mark


def file_in_range(file_entry, start_date, end_date):
    if start_date is not None and file_entry[1] < start_date:
        return False
    if end_date is not None and file_entry[1] > end_date:
        return False
    return True


def scan_journal_files_in_date_range(scanners, start_date, end_date):
    files_in_range = filter(
        lambda f: file_in_range(f, start_date, end_date),
        get_journal_file_list())
    scan_files(scanners, files_in_range)


def resume_from_book_mark(scanners, book_mark):
    if book_mark is None:
        return

    file_entries = get_journal_file_list()
    last_file_index = next(
        i for i in file_entries if file_entries[i][0] == book_mark.filename)

    # Scan the first file
    book_mark = scan_file(file_entries[last_file_index], scanners, book_mark)

    # Scan remaining files
    remaining_files = file_entries[(last_file_index+1):len(file_entries)]
    if(len(remaining_files) > 0):
        return scan_files(scanners, remaining_files)
    else:
        return book_mark


def scan_journal(scanners):
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

    return scan_journal_files_in_date_range(scanners, start_date, end_date)


if __name__ == "__main__":
    # Simple scanner which prints all recieved text as a test
    scanner = JournalScanner()
    scanner.register_handler('ReceiveText', lambda e: print(
        e['Message_Localised']) if ('Message_Localised' in e) else print(e['Message']))
    scan_journal(scanner)
