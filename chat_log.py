import journal_scan

class ChatLogScanner(journal_scan.JournalScanner):
    def __init__(self):
        super().__init__()
        self.register_handler("SendText", self.handle_send_text)
        self.register_handler("ReceiveText", self.handle_recieve_text)
        self.hearts_sold = 0

    def handle_send_text(self, event):
        print(f"To {event['To']}: {event['Message']}")

    def handle_recieve_text(self, event):
        print(f"From {event['From']}: {event['Message']}")

if __name__ == "__main__":
    scanner = ChatLogScanner()
    journal_scan.scan_journal(scanner)
