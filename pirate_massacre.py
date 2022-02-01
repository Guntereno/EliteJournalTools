import journal_scan
import json

class MissionInfo:
    id = None
    giving_faction = None
    target_faction = None
    kill_count = -1

    def __init__(self, id, giving_faction, target_faction, kill_count):
        self.id = id
        self.giving_faction = giving_faction
        self.target_faction = target_faction
        self.kill_count = kill_count

    def dump(self):
        print(
            '{id="' + str(self.id) +
            '", giving_faction="' + str(self.giving_faction) +
            '", target_faction="' + str(self.target_faction) +
            '", kill_count="' + str(self.kill_count) + '"}')

class PirateMassacreScanner(journal_scan.JournalScanner):

    mission_queue = []
    mission_dict = {}

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
        if event['Active']:
            for mission in event['Active']:
                if(mission['Name'] == 'Mission_MassacreWing_name'):
                    id = mission['MissionID']
                    # We only want to add missions we're not already tracking
                    if not id in self.mission_dict:
                        self.add_mission(id, MissionInfo(id, None, -1))

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
        if event['Name'] == 'Mission_MassacreWing':
            id = event['MissionID']
            self.add_mission(id, MissionInfo(id, event['Faction'], event['TargetFaction'], event['KillCount']))

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

    #{
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
            if mission.kill_count > 0:
                mission.kill_count -= 1
                handled_factions.add(mission.giving_faction)

    def __init__(self):
        self.register_handler("Missions", self.handle_missions)
        self.register_handler("MissionAccepted", self.handle_mission_accepted)
        self.register_handler("MissionAbandoned", self.handle_mission_abandoned)
        self.register_handler("MissionFailed", self.handle_mission_failed)
        self.register_handler("MissionCompleted", self.handle_mission_completed)
        self.register_handler("Bounty", self.handle_bounty)

    def finalise(self):
        output_dict = {}
        for id in self.mission_dict:
            mission = self.mission_dict[id]
            faction = mission.giving_faction
            if not faction in output_dict:
                output_dict[faction] = []
            output_dict[faction].append(mission)

        for key in sorted(output_dict.keys()):
            for mission in output_dict[key]:
                print(f'{mission.giving_faction}: {mission.kill_count}')

if __name__ == "__main__":
    journal_scan.scan_journal(PirateMassacreScanner())
