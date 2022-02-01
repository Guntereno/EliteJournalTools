import argparse
import os
import json
import traceback
from dateutil import parser as date_parser
from pytz import UTC

class JournalScanner:
    event_handlers = {}

    def register_handler(self, event_name, handler):
        self.event_handlers[event_name] = handler

    def handle_event(self, event):
        if event["event"] in self.event_handlers:
            self.event_handlers[event["event"]](event)

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

def parse_files(scanner, start_date, end_date):
    if not isinstance(scanner, JournalScanner):
        raise Exception("'scanner' parameter is not a JournalScanner!")

    data_path = os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous")
    os.chdir(data_path)

    for filename in os.listdir(data_path):
        if filename.endswith(".log"):
            try:
                with open(filename, encoding='utf-8') as file_ptr:
                    for cnt, line in enumerate(file_ptr):
                        event = json.loads(line)

                        if(start_date != None):
                            event_date = date_parser.isoparse(event["timestamp"])
                            if event_date < start_date:
                                continue
                        
                        if(end_date != None):
                            event_date = date_parser.isoparse(event["timestamp"])
                            if event_date > end_date:
                                continue

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
