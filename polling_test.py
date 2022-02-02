import journal_scan
import time
from pytz import UTC

if __name__ == "__main__":
    scanner = journal_scan.JournalScanner()
    scanner.register_handler(
        'ReceiveText',
        lambda e: print(e['Message_Localised']) if ('Message_Localised' in e) else print (f'{e["Message"]}'))

    book_mark = journal_scan.scan_journal(scanner)
    
    while True:
        book_mark = journal_scan.resume_from_book_mark(scanner, book_mark)
        time.sleep(0.3)