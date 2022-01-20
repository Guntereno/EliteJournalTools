import journal_scan

class PlayerInterdictionScanner(journal_scan.JournalScanner):
    def handle_interdicted(self, event):
        if (event["IsPlayer"]):
            print(event["Interdictor"])

    def __init__(self):
        self.register_handler("Interdicted", self.handle_interdicted)

if __name__ == "__main__":
    journal_scan.scan_journal(PlayerInterdictionScanner())