import journal_scan

class PlayerInterdictionScanner(journal_scan.JournalScanner):
    def __init__(self):
        super().__init__()
        self.register_handler("Interdicted", self.handle_interdicted)

    def handle_interdicted(self, event):
        if (event["IsPlayer"]):
            print(event["Interdictor"])

if __name__ == "__main__":
    journal_scan.scan_journal(PlayerInterdictionScanner())