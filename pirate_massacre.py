import datetime
import dateutil
import journal_scan
from pytz import UTC

class MissionInfo:
    id = None
    giving_faction = None
    target_faction = None
    remaining_kills = None
    total_kills = None
    system_name = None
    description = None
    reward = None
    expiry = None

    def __init__(
            self,
            id=None,
            giving_faction=None,
            target_faction=None,
            kill_count=None,
            system_name=None,
            description=None,
            reward=None,
            expiry=None):
        self.id = id
        self.giving_faction = giving_faction
        self.target_faction = target_faction
        self.remaining_kills = self.total_kills = kill_count
        self.system_name = system_name
        self.description = description
        self.reward = reward
        self.expiry = expiry


class SystemInfo:
    name = None
    factions = None

    def __init__(
        self,
        name = None,
        factions = None):
        self.name = name
        self.factions = factions

class FactionInfo:
    name = None
    reputation = None
    government = None
    def __init__(
        self,
        name = None,
        reputation = None,
        government = None):
        self.name = name
        self.reputation = reputation,
        self.government = government

    def get_reputation_string(self):
        if self.reputation == None:
            return "Unknown"
        rep = self.reputation[0]
        if rep < -80.0:
            return "HOSTILE"
        elif rep < -25.0:
            return "UNFRIENDLY"
        elif rep <  25.0:
            return "NEUTRAL"
        elif rep < 80.0:
            return "FRIENDLY"
        else:
            return "ALLIED"


def is_wing_massacre(mission_name):
    return mission_name.startswith('Mission_MassacreWing')

class PirateMassacreScanner(journal_scan.JournalScanner):
    mission_queue = []
    mission_dict = {}
    system_dict = {}
    faction_dict = {}
    current_system = None

    def add_mission(self, id, mission):
        self.mission_queue.append(mission)
        self.mission_dict[id] = mission

    def remove_mission(self, id):
        if id in self.mission_dict:
            mission = self.mission_dict[id]
            self.mission_queue.remove(mission)
            self.mission_dict.pop(id)

    # {
    #     "timestamp":"2022-01-31T19:52:04Z",
    #     "event":"Missions",
    #     "Active":
    #     [
    #         { "MissionID":842001573, "Name":"Mission_MassacreWing_name", "PassengerMission":false, "Expires":0 },
    #         ...
    #     ]
    # }
    def handle_missions(self, event):
        # Remove any tracked missions which aren't reported in this event.
        # (Clears up any which Elite didn't fire a MissionCompleted event for.)
        if event['Active']:
            current_missions = set(map(lambda x: x['MissionID'], event['Active']))
            tracked_missions = list(self.mission_dict.keys())
            for mission_id in tracked_missions:
                if mission_id not in current_missions:
                    self.remove_mission(mission_id)

    # {
    #     "timestamp": "2022-01-31T20:29:33Z",
    #     "event": "MissionAccepted",
    #     "Faction": "HR 1782 Republic Party",
    #     "Name": "Mission_MassacreWing",
    #     "LocalisedName": "Kill Drug Empire of HR 1613 faction Pirates",
    #     "TargetType": "$MissionUtil_FactionTag_Pirate;",
    #     "TargetType_Localised": "Pirates",
    #     "TargetFaction": "Drug Empire of HR 1613",
    #     "KillCount": 54,
    #     "DestinationSystem": "HR 1613",
    #     "DestinationStation": "von Bellingshausen Mines",
    #     "Expiry": "2022-02-07T20:17:31Z",
    #     "Wing": true,
    #     "Influence": "++",
    #     "Reputation": "++",
    #     "Reward": 12995513,
    #     "MissionID": 842359897
    # }
    def handle_mission_accepted(self, event):
        if is_wing_massacre(event['Name']):
            id = event['MissionID']

            expiry = dateutil.parser.isoparse(event['Expiry'])

            mission = MissionInfo(
                id=id,
                giving_faction=event['Faction'],
                target_faction=event['TargetFaction'],
                kill_count=event['KillCount'],
                system_name=self.current_system,
                description=event['LocalisedName'],
                reward=event['Reward'],
                expiry=expiry)

            self.add_mission(id, mission)

    # {
    #     "timestamp":"2022-01-31T21:07:45Z",
    #     "event":"MissionAbandoned",
    #     "Name":"Mission_Assassinate_Planetary_name",
    #     "MissionID":842363613
    # }
    def handle_mission_abandoned(self, event):
        self.remove_mission(event['MissionID'])

    # {
    #     "timestamp":"2022-01-31T21:07:45Z",
    #     "event":"MissionFailed",
    #     "Name":"Mission_Assassinate_Planetary_name",
    #     "MissionID":842363613
    # }
    def handle_mission_failed(self, event):
        self.remove_mission(event['MissionID'])

    # {
    # "timestamp": "2022-01-31T22:16:31Z",
    # "event": "MissionCompleted",
    # "Faction": "Independent Woyeru Alliance",
    # "Name": "Mission_MassacreWing_name",
    # "MissionID": 842009999,
    # "TargetType": "$MissionUtil_FactionTag_Pirate;",
    # "TargetType_Localised": "Pirates",
    # "TargetFaction": "Drug Empire of HR 1613",
    # "KillCount": 81,
    # "NewDestinationSystem": "Bhisma",
    # "DestinationSystem": "HR 1613",
    # "NewDestinationStation": "Dupuy de Lome Dock",
    # "DestinationStation": "Thornycroft Platform",
    # "Reward": 10202064,
    # "FactionEffects": [
    #     {
    #     "Faction": "Independent Woyeru Alliance",
    #     "Effects": [
    #         {
    #         "Effect": "$MISSIONUTIL_Interaction_Summary_EP_up;",
    #         "Effect_Localised": "The economic status of $#MinorFaction; has improved in the $#System; system.",
    #         "Trend": "UpGood"
    #         }
    #     ],
    #     "Influence": [
    #         {
    #         "SystemAddress": 2870514361713,
    #         "Trend": "UpGood",
    #         "Influence": "++"
    #         }
    #     ],
    #     "ReputationTrend": "UpGood",
    #     "Reputation": "++"
    #     },
    #     ...
    # ]
    # }
    def handle_mission_completed(self, event):
        self.remove_mission(event['MissionID'])

    # {
    #     "timestamp":"2022-01-31T21:14:38Z",
    #     "event":"Bounty",
    #     "Rewards":[ { "Faction":"Brazilian League of Pilots", "Reward":212922 } ],
    #     "Target":"typex_3",
    #     "Target_Localised":"Alliance Challenger",
    #     "TotalReward":212922,
    #     "VictimFaction":"Drug Empire of HR 1613",
    #     "SharedWithOthers":2
    # }
    def handle_bounty(self, event):
        handled_factions = set()
        for mission in self.mission_queue:
            faction = event['VictimFaction']
            if mission.target_faction != faction:
                continue
            if mission.giving_faction in handled_factions:
                continue
            if mission.remaining_kills > 0:
                mission.remaining_kills -= 1
                handled_factions.add(mission.giving_faction)

    # {
    #   "timestamp": "2022-01-31T19:52:04Z",
    #   "event": "Location",
    #   "Docked": false,
    #   "Taxi": false,
    #   "Multicrew": false,
    #   "StarSystem": "HR 1613",
    #   "SystemAddress": 697688901979,
    #   "StarPos": [
    #     54.3125,
    #     -68.0625,
    #     -136.375
    #   ],
    #   "SystemAllegiance": "Independent",
    #   "SystemEconomy": "$economy_Extraction;",
    #   "SystemEconomy_Localised": "Extraction",
    #   "SystemSecondEconomy": "$economy_Colony;",
    #   "SystemSecondEconomy_Localised": "Colony",
    #   "SystemGovernment": "$government_Confederacy;",
    #   "SystemGovernment_Localised": "Confederacy",
    #   "SystemSecurity": "$SYSTEM_SECURITY_low;",
    #   "SystemSecurity_Localised": "Low Security",
    #   "Population": 115439,
    #   "Body": "HR 1613",
    #   "BodyID": 0,
    #   "BodyType": "Star",
    #   "Factions": [
    #     {
    #       "Name": "HR 1613 Prison Colony",
    #       "FactionState": "None",
    #       "Government": "PrisonColony",
    #       "Influence": 0.115462,
    #       "Allegiance": "Independent",
    #       "Happiness": "$Faction_HappinessBand2;",
    #       "Happiness_Localised": "Happy",
    #       "MyReputation": 15
    #     },
    #     ...
    #   ],
    #   "SystemFaction": {
    #     "Name": "Brazilian League of Pilots"
    #   }
    # }
    def handle_location(self, event):
        system_name = event['StarSystem']
        self.current_system = system_name
        self.store_system_info(event, system_name)
        if 'Factions' in event:
            for faction in event['Factions']:
                faction_name = faction['Name']
                faction = FactionInfo(
                    name = faction_name,
                    reputation = faction['MyReputation'],
                    government = faction['Government'])
                self.faction_dict[faction_name] = faction

    # {
    #   "timestamp": "2022-01-31T20:41:04Z",
    #   "event": "FSDJump",
    #   "Taxi": false,
    #   "Multicrew": false,
    #   "StarSystem": "HIP 23575",
    #   "SystemAddress": 800768117083,
    #   "StarPos": [
    #     54.21875,
    #     -66.0625,
    #     -142.5
    #   ],
    #   "SystemAllegiance": "Independent",
    #   "SystemEconomy": "$economy_Industrial;",
    #   "SystemEconomy_Localised": "Industrial",
    #   "SystemSecondEconomy": "$economy_Colony;",
    #   "SystemSecondEconomy_Localised": "Colony",
    #   "SystemGovernment": "$government_PrisonColony;",
    #   "SystemGovernment_Localised": "Prison colony",
    #   "SystemSecurity": "$SYSTEM_SECURITY_low;",
    #   "SystemSecurity_Localised": "Low Security",
    #   "Population": 3481542,
    #   "Body": "HIP 23575 A",
    #   "BodyID": 1,
    #   "BodyType": "Star",
    #   "JumpDist": 10.207,
    #   "FuelUsed": 0.547034,
    #   "FuelLevel": 15.452966,
    #   "Factions": [
    #     {
    #       "Name": "HR 1613 Prison Colony",
    #       "FactionState": "None",
    #       "Government": "PrisonColony",
    #       "Influence": 0.289157,
    #       "Allegiance": "Independent",
    #       "Happiness": "$Faction_HappinessBand2;",
    #       "Happiness_Localised": "Happy",
    #       "MyReputation": 15,
    #       "RecoveringStates": [
    #         {
    #           "State": "Election",
    #           "Trend": 0
    #         }
    #       ]
    #     },
    #     ...
    #   ],
    #   "SystemFaction": {
    #     "Name": "HR 1613 Prison Colony"
    #   },
    #   "Conflicts": [
    #     {
    #       "WarType": "election",
    #       "Status": "",
    #       "Faction1": {
    #         "Name": "HR 1613 Prison Colony",
    #         "Stake": "Plucker Orbital",
    #         "WonDays": 1
    #       },
    #       "Faction2": {
    #         "Name": "Noblemen of Tacare",
    #         "Stake": "Salgari Colony",
    #         "WonDays": 0
    #       }
    #     }
    #   ]
    # }
    def handle_fsd_jump(self, event):
        self.handle_location(event)

    def store_system_info(self, event, system_name):
        if system_name in self.system_dict:
            return
        if 'Factions' in event:
            faction_names = list(map(lambda x: x['Name'], event['Factions']))
            self.system_dict[system_name] = SystemInfo(
                self.current_system, faction_names)

    def __init__(self):
        self.register_handler("Missions", self.handle_missions)
        self.register_handler("MissionAccepted", self.handle_mission_accepted)
        self.register_handler("MissionAbandoned",
                              self.handle_mission_abandoned)
        self.register_handler("MissionFailed", self.handle_mission_failed)
        self.register_handler("MissionCompleted",
                              self.handle_mission_completed)
        self.register_handler("Bounty", self.handle_bounty)
        self.register_handler("FSDJump", self.handle_fsd_jump)
        self.register_handler("Location", self.handle_location)

    def build_report(self):
        system_set = filter(lambda x: (x is not None) and (
            x.system_name is not None), self.mission_queue)
        system_set = map(lambda x: x.system_name, system_set)
        system_set = sorted(set(system_set))

        # Create dictionary of system & faction tuple to array of missions
        mission_dict = {}
        total_reward = 0
        for mission in self.mission_queue:
            system_faction = (mission.system_name, mission.giving_faction)
            if not system_faction in mission_dict:
                mission_dict[system_faction] = []
            mission_dict[system_faction].append(mission)
            if mission.reward is not None:
                total_reward += mission.reward

        systems = []
        for system_name in sorted(system_set):
            system_entry = {}
            system_info = self.system_dict[system_name]
            system_entry['System'] = system_info
            system_entry['Factions'] = []
            for faction_name in sorted(system_info.factions):
                system_faction = (system_name, faction_name)
                faction_entry = {}
                faction_info = self.faction_dict[faction_name]
                faction_entry['Faction'] = faction_info
                faction_entry['Missions'] = []
                if system_faction in mission_dict:
                    for mission in mission_dict[system_faction]:
                        faction_entry['Missions'].append(mission)
                has_missions_in_other_system = False
                for other_system_name in system_set:
                    if other_system_name == system_name:
                        continue
                    other_system_faction = (other_system_name, faction_name)
                    if other_system_faction in mission_dict:
                        has_missions_in_other_system = True
                        break
                faction_entry['HasMissionsInOtherSystem'] = has_missions_in_other_system
                system_entry['Factions'].append(faction_entry)
            systems.append(system_entry)

        report = {}
        report['Systems'] = systems
        report['MissionCount'] = len(self.mission_queue)
        report['TotalReward'] = total_reward

        return report

    def output_report(self):
        report = self.build_report()
        print(
            f'Currently tracking {report["MissionCount"]}/20 missions for a total reward of {report["TotalReward"]}.')
        print()

        for system_entry in report['Systems']:
            print(f'# {system_entry["System"].name}')
            for faction_entry in system_entry["Factions"]:
                faction = faction_entry["Faction"]
                print(f'## {faction.name} - {faction.reputation[0]}')
                missions = faction_entry["Missions"]
                if len(missions) > 0:
                    for mission in missions:
                        kills = mission.total_kills - mission.remaining_kills
                        message = '  - {} for {:,} credits:'.format(
                            mission.description, mission.reward)
                        if mission.remaining_kills > 0:
                            message += f' {kills}/{mission.total_kills} ({mission.remaining_kills} remain)'
                        else:
                            message += ' DONE!'
                        print(message)
                else:
                    if faction_entry['HasMissionsInOtherSystem']:
                        print('  - None (have mission in other system)')
                    else:
                        print('  - None')
            print()


if __name__ == "__main__":
    # Wing missions last around 7 days, so we only need to scan that far back
    start_date = datetime.datetime.now(UTC) - datetime.timedelta(8)
    scanner = PirateMassacreScanner()
    journal_scan.scan_journal_files_in_date_range(scanner, start_date, None)
    scanner.output_report()
