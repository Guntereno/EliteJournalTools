import journal_scan

# List count of each scanned body type


class DiscoveryScanner(journal_scan.JournalScanner):
    def __init__(self):
        super().__init__()

        self.body_counts = {}
        self.handled_bodies = set()

        self.register_handler("Scan", self.handle_scan)

    def handle_scan(self, event):
        # We only care about detailed scans
        if (not "ScanType" in event) or (event["ScanType"] != "Detailed"):
            return

        # Looks like there are multiple scans for each body
        body_name = event["BodyName"]
        if (body_name in self.handled_bodies):
            return
        self.handled_bodies.add(body_name)

        if "PlanetClass" in event:
            key = event["PlanetClass"]
            if(("TerraformState" in event) and (event["TerraformState"] != "")):
                key += " (Terraformable)"
            if not key in self.body_counts:
                self.body_counts[key] = 1
            else:
                self.body_counts[key] += 1

    def output_report(self):
        for key, value in sorted(self.body_counts.items()):
            print(f"{key}:{value}")


if __name__ == "__main__":
    scanner = DiscoveryScanner()
    journal_scan.scan_journal(scanner)
    scanner.output_report()
