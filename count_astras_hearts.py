import journal_scan

class AstrasHeartsScanner(journal_scan.JournalScanner):
    hearts_sold = 0

    def handle_market_sell(self, event):
        if (event["MarketID"] == 3701603328) and (event["Type"] == "thargoidheart"):
            self.hearts_sold = self.hearts_sold + 1

    def __init__(self):
        self.register_handler("MarketSell", self.handle_market_sell)

    def output_report(self):
        print(self.hearts_sold)

if __name__ == "__main__":
    scanner = AstrasHeartsScanner()
    journal_scan.scan_journal(scanner)
    scanner.output_report()