from datetime import datetime
from datetime import timedelta  
import journal_scan

class BondScanner(journal_scan.JournalScanner):
    totals = {}
    current_system = "Unknown"

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

    def __init__(self):
        self.register_handler("RedeemVoucher", self.handle_redeem_voucher)
        self.register_handler("Location", self.handle_location)

    def finalise(self):
        for date,entries in self.totals.items():
            print(str(date) + ":")
            for system,amount in entries.items():
                print("\t" + system + ": " + str(amount))
            print()

if __name__ == "__main__":
    journal_scan.scan_journal(BondScanner())