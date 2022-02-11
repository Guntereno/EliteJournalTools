from datetime import datetime
from datetime import timedelta  
import journal_scan

class BondScanner(journal_scan.JournalScanner):
    def __init__(self):
        super().__init__()

        self.totals = {}
        self.current_system = "Unknown"

        self.register_handler("RedeemVoucher", self.handle_redeem_voucher)
        self.register_handler("Location", self.handle_location)

    def handle_redeem_voucher(self, event):
        if event["Type"] == "CombatBond":
            timestamp = datetime.strptime(event["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            # BGS tick is at 1
            if(timestamp.hour >= 13):
                timestamp += timedelta(days=1)
            datestamp = timestamp.date()
            if(datestamp not in self.totals):
                self.totals[datestamp] = {}
            self.totals[datestamp][self.current_system] = self.totals[datestamp].get(self.current_system, 0) + int(event["Amount"])

    def handle_location(self, event):
        global current_system
        self.current_system = event["StarSystem"]

    def output_report(self):
        for date,entries in self.totals.items():
            print(str(date) + ":")
            for system,amount in entries.items():
                print("\t" + system + ": " + str(amount))
            print()

if __name__ == "__main__":
    scanner = BondScanner()
    journal_scan.scan_journal(scanner)
    scanner.output_report()
