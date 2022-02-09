import journal_scan

class Transaction:
    timestamp = None
    delta = None
    desc = None

    def __init__(self, timestamp, delta, desc):
        self.timestamp = timestamp
        self.delta = delta
        self.desc = desc


# List count of each scanned body type
class FinanceTracker(journal_scan.JournalScanner):
    current_balance = 0
    transactions = []
    discrepencies = 0

    def apply_delta(self, delta, event):
        self.transactions.append(Transaction(event['timestamp'], delta, event['event']))
        self.current_balance += delta

    def set_balance(self, new_balance, event):
        delta = new_balance - self.current_balance
        self.apply_delta(delta, event)
        return delta


    def handle_load_game(self, event):
        delta = self.set_balance(event['Credits'], event)
        if delta != 0:
            print(f'Starting session with delta of {delta} at time {event["timestamp"]}')
            self.discrepencies += 1

    def handle_buy_exporation_data(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_sell_exporation_data(self, event):
        value = event['BaseValue'] + event['Bonus']
        self.apply_delta(value, event)

    def handle_buy_trade_data(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_market_buy(self, event):
        self.apply_delta(-event['TotalCost'], event)

    def handle_market_sell(self, event):
        self.apply_delta(event['TotalSale'], event)

    def handle_buy_ammo(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_buy_drones(self, event):
        self.apply_delta(-event['TotalCost'], event)

    def handle_community_goal_reward(self, event):
        self.apply_delta(event['Reward'], event)

    def handle_crew_hire(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_fetch_remote_module(self, event):
        self.apply_delta(-event['TransferCost'], event)

    def handle_mission_completed(self, event):
        delta = 0
        if 'Reward' in event:
            delta += event['Reward']
        if 'Donated' in event:
            delta -= event['Donated']
        if delta != 0:
            self.apply_delta(delta, event)

    def handle_module_buy(self, event):
        delta = -event['BuyPrice']
        if 'SellPrice' in event:
            delta += event['SellPrice']
        self.apply_delta(delta, event)

    def handle_module_sell(self, event):
        self.apply_delta(event['SellPrice'], event)

    def handle_module_store(self, event):
        if 'Cost' in event:
            self.apply_delta(-event['Cost'], event)

    def handle_npc_crew_paid_wage(self, event):
        self.apply_delta(-event['Amount'], event)

    def handle_pay_fines(self, event):
        self.apply_delta(-event['Amount'], event)

    def handle_redeem_voucher(self, event):
        self.apply_delta(event['Amount'], event)

    def handle_refuel(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_repair(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_restock_vehicle(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_sell_drones(self, event):
        self.apply_delta(event['TotalSale'], event)

    def handle_shipyard_buy(self, event):
        self.apply_delta(-event['ShipPrice'], event)

    def handle_shipyard_sell(self, event):
        self.apply_delta(event['ShipPrice'], event)

    def handle_shipyard_transfer(self, event):
        self.apply_delta(-event['TransferPrice'], event)

    def handle_powerplay_fast_track(self, event):
        self.apply_delta(-event['Cost'], event)

    def handle_powerplay_salary(self, event):
        self.apply_delta(event['Amount'], event)


    def __init__(self):
        self.register_handler('LoadGame', self.handle_load_game)
        self.register_handler('BuyExplorationData', self.handle_buy_exporation_data)
        self.register_handler('SellExplorationData', self.handle_sell_exporation_data)
        self.register_handler('MultiSellExplorationData', self.handle_sell_exporation_data)
        self.register_handler('BuyTradeData', self.handle_buy_trade_data)
        self.register_handler('MarketBuy', self.handle_market_buy)
        self.register_handler('MarketSell', self.handle_market_sell)
        self.register_handler('BuyAmmo', self.handle_buy_ammo)
        self.register_handler('BuyDrones', self.handle_buy_drones)
        self.register_handler('CommunityGoalReward', self.handle_community_goal_reward)
        self.register_handler('CrewHire', self.handle_crew_hire)
        self.register_handler('FetchRemoteModule', self.handle_fetch_remote_module)
        self.register_handler('MissionCompleted', self.handle_mission_completed)
        self.register_handler('ModuleBuy', self.handle_module_buy)
        self.register_handler('ModuleSell', self.handle_module_sell)
        self.register_handler('ModuleSellRemote', self.handle_module_sell)
        self.register_handler('ModuleStore', self.handle_module_store)
        self.register_handler('NpcCrewPaidWage', self.handle_npc_crew_paid_wage)
        self.register_handler('PayBounties', self.handle_pay_fines) # Missing from API doc
        self.register_handler('PayFines', self.handle_pay_fines)
        self.register_handler('PayLegacyFines', self.handle_pay_fines)
        self.register_handler('RedeemVoucher', self.handle_redeem_voucher)
        self.register_handler('RefuelAll', self.handle_refuel)
        self.register_handler('RefuelPartial', self.handle_refuel)
        self.register_handler('Repair', self.handle_repair)
        self.register_handler('RepairAll', self.handle_repair)
        self.register_handler('RestockVehicle', self.handle_restock_vehicle)
        self.register_handler('SellDrones', self.handle_sell_drones)
        self.register_handler('ShipyardBuy', self.handle_shipyard_buy)
        self.register_handler('ShipyardBuy', self.handle_shipyard_sell)
        self.register_handler('ShipyardTransfer', self.handle_shipyard_transfer)
        self.register_handler('PowerplayFastTrack', self.handle_powerplay_fast_track)
        self.register_handler('PowerplaySalary', self.handle_powerplay_salary)

    def output_report(self):
        print(f'Discrepencies: {self.discrepencies}')
        for transaction in self.transactions:
            print(f'{transaction.delta}: {transaction.desc}')
        print(self.current_balance)

if __name__ == "__main__":
    scanner = FinanceTracker()
    journal_scan.scan_journal(scanner)
    scanner.output_report()
