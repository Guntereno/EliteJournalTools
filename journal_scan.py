import argparse
import json
import os
import re
import traceback
from datetime import datetime
from dateutil import parser as date_parser
from pytz import UTC

class JournalScanner:
    event_handlers = {}

    def register_handler(self, event_name, handler):
        self.event_handlers[event_name] = handler

    def handle_event(self, event):
        event_id = event["event"]
        if event_id in self.event_handlers:
            self.event_handlers[event_id](event)

    def finalise(self):
        pass


def init_argparse():
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] function",
        description="Perform a variety of analysis functions on the users journal files."
    )

    parser.add_argument("-s", "--start_date", help="Date to start search from.")
    parser.add_argument("-e", "--end_date", help="Date to end search at.")

    return parser

def include_journal_file(file_name, start_file, end_file):
    if not file_name.startswith('Journal.'):
        return False
    if not file_name.endswith('.log'):
        return False
    if (start_file is not None) and (file_name < start_file):
        return False
    if (end_file is not None) and (file_name > end_file):
        return False
    return True


def parse_files(scanner, start_date, end_date):
    if not isinstance(scanner, JournalScanner):
        raise Exception("'scanner' parameter is not a JournalScanner!")

    data_path = os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous")
    os.chdir(data_path)

    # e.g., 'Journal.220201192604.01.log'
    date_re = re.compile('^Journal.(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)\.\d\d\.log$')

    date_format = 'Journal.%y%m%d%H%M%S.01.log'
    start_file = None if start_date is None else start_date.strftime(date_format)
    end_file = None if end_date is None else end_date.strftime(date_format)

    all_files = os.listdir(data_path)
    filtered_files = filter(lambda f: include_journal_file(f, start_file, end_file), all_files)
    for filename in filtered_files:
        date_match = date_re.match(filename)
        if date_match:
            try:
                with open(filename, encoding='utf-8') as file_ptr:

                    for cnt, line in enumerate(file_ptr):
                        event = json.loads(line)

                        try:
                            scanner.handle_event(event)
                        except Exception as e:
                            print(f"Error parsing event:\nEvent={event}")
                            raise e

            except Exception as e:
                print("Error loading file '" + filename + "': ")
                traceback.print_exc()
                return

    scanner.finalise()

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

    parse_files(scanner, start_date, end_date)

if __name__ == "__main__":
    # Simple scanner which prints all recvieved text as a test
    scanner = JournalScanner()
    scanner.register_handler('ReceiveText', lambda e: print(e['Message_Localised']) if ('Message_Localised' in e) else print (e['Message']))
    scan_journal(scanner)