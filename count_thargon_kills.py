import journal_scan

class ThargonKillScanner(journal_scan.JournalScanner):
    in_wing = False
    solo_counts = {}
    wing_counts = {}

    def handle_wing_join(self, event):
        self.in_wing = True

    def handle_wing_leave(self, event):
        self.in_wing = False

    def handle_faction_kill_bond(self, event):
        if event["VictimFaction"] == "$faction_Thargoid;":
            reward = int(event["Reward"])
        else:
            return

        records = self.wing_counts if self.in_wing else self.solo_counts

        if not reward in records:
            records[reward] = 1
        else:
            records[reward] = records[reward] + 1

    def __init__(self):
        self.register_handler("WingJoin", self.handle_wing_join)
        self.register_handler("WingLeave", self.handle_wing_leave)
        self.register_handler("FactionKillBond", self.handle_faction_kill_bond)

    def finalise(self):
        key_set = set(list(self.solo_counts.keys()) + list(self.wing_counts.keys()))

        thargoid_name_by_reward = {
            10000: "Scout",
            2000000: "Cyclops",
            6000000: "Basilisk",
            10000000: "Medusa",
            15000000: "Hydra"
        }

        for reward in key_set:
            wing_count = 0
            if reward in self.wing_counts:
                wing_count = self.wing_counts[reward]
            
            solo_count = 0
            if reward in self.solo_counts:
                solo_count = self.solo_counts[reward]

            if reward in thargoid_name_by_reward:
                name = thargoid_name_by_reward[reward]
            else:
                name = str(reward)

            print(f"{name}: {solo_count} solo, {wing_count} in wing.")

if __name__ == "__main__":
    journal_scan.scan_journal(ThargonKillScanner())