import datetime
import journal_scan
import os
import finance_tracker
import pirate_massacre
import threading
import time
import web_server
from pytz import UTC


pirate_scanner = None
finance_scanner = None
book_mark = None

def all_scanners():
    return [pirate_scanner, finance_scanner]

mutex = threading.Lock()

# There appears to be a bug in the bookmark system. Until that's fixed we'll rebuild
# the complete scanner every time a request is made
rebuild_scanner_on_request = False

def build_scanners():
    global pirate_scanner
    global finance_scanner
    global book_mark
    global mutex

    mutex.acquire()
    pirate_scanner = pirate_massacre.PirateMassacreScanner()
    finance_scanner = finance_tracker.FinanceTracker()
    mutex.release()

    # Wing missions last around 7 days, so we only need to scan that far back
    start_date = datetime.datetime.now(UTC) - datetime.timedelta(8)
    book_mark = journal_scan.scan_journal_files_in_date_range(all_scanners(), start_date, None)

    print("Scanners rebuilt.")

def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

def build_remaining_time_str(expiry):
    now = UTC.localize(datetime.datetime.utcnow())
    if(expiry < now):
        return '<em class="expiry">EXPIRED!</em>'
    else:
        message = "Expires in "
        remaining = expiry - now
        if remaining.days > 0:
            message += strfdelta(remaining, '{days}D {hours}H {minutes}MIN')
        else:
            message += strfdelta(remaining, '{hours}H {minutes}MIN')
        return message

rep_classes = {
    "HOSTILE": "FactionRepBad",
    "UNFRIENDLY": "FactionRepBad",
    "NEUTRAL": "FactionRepNeutral",
    "FRIENDLY": "FactionRepGood",
    "ALLIED": "FactionRepGood"
}

def get_reputation_class(rep_string):
    if rep_string not in rep_classes:
        return "FactionRepNeutral"
    return rep_classes[rep_string]

class PirateMassacreHandler(web_server.Handler):
    def get_handler(self, request):
        if request == "/mission_report":
            return self.get_mission_report
        elif request == "/finance_report":
            return self.get_finance_report
        elif request == "/rebuild":
            return self.get_rebuild
        return None

    def get_mission_report(self):
        if pirate_scanner == None:
            return

        if rebuild_scanner_on_request:
            build_scanners()

        global mutex
        mutex.acquire()
        report = pirate_scanner.build_report()
        mutex.release()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        content = ""

        content += f'<div class ="MissionCount">Tracking {report["MissionCount"]}/20 missions for a potential <em class="Credits">{"{:,}".format(report["TotalReward"])} credit</em> reward. (<em class="Credits">{"{:,}".format(report["TotalWingReward"])} credits</em> in <em class="Wing">wing missions</em>.)</div>'
        for system_entry in report['MissionsBySystem']:
            system_name = system_entry['Name']
            system = report['Systems'][system_name]
            content += (f'<div class="SystemHeader">{system.name}</div>')
            for faction_entry in system_entry["Factions"]:
                faction_name = faction_entry['Name']
                faction = report['Factions'][faction_name]

                rep_string = faction.get_reputation_string()
                rep_class = get_reputation_class(rep_string)

                icons = ""
                if faction.government == 'Anarchy':
                    icons += '&#x1F3F4;&#x200D;&#x2620;&#xFE0F;' # pirate flag
                if faction.state in ["War", "CivilWar"]:
                    icons += '&#x2694;&#xFE0F;' # crossed swords

                content += f'<div class="FactionHeader">{faction.name}{icons}<div class="{rep_class}">{rep_string}</div></div>'
                missions = faction_entry["Missions"]
                if len(missions) > 0:
                    for mission in missions:
                        kills = mission.total_kills - mission.remaining_kills
                        content += '<div class="Mission">'

                        message = 'Kill {} for <em class="Credits">{:,} credits</em>'.format(mission.target_faction, mission.reward)
                        if mission.wing:
                            message += ' <em class="Wing">WING</em> '
                        message += ' &mdash; '

                        if mission.remaining_kills > 0:
                            message += f' {kills}/{mission.total_kills} ({mission.remaining_kills} remain)'
                            message += ' &mdash; '
                            message += build_remaining_time_str(mission.expiry)
                        else:
                            message += ' <em class="Done">DONE!</em>'

                        content += message
                        content += '</div>'
                else:
                    content += '<div class="Mission"><em class="Greyed">'
                    content += 'None'
                    if faction_entry['HasMissionsInOtherSystem']:
                        content +=' (have mission in other system)'
                    content += '</em></div>'

        self.wfile.write(bytes(content, "utf-8"))

    def get_finance_report(self):
        if finance_scanner == None:
            return

        global mutex
        mutex.acquire()
        report = finance_scanner.build_report_json()
        mutex.release()

        self.send_response(200)
        self.send_header("Content-type", "text/json")
        self.end_headers()

        content = report
        self.wfile.write(bytes(content, "utf-8"))

    def get_rebuild(self):
        build_scanners()

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

        content = "Scanners Rebuilt"
        self.wfile.write(bytes(content, "utf-8"))

def main_loop():
    if rebuild_scanner_on_request:
        return

    global mutex
    global pirate_scanner
    global book_mark

    while True:
        time.sleep(0.5)

        mutex.acquire()
        book_mark = journal_scan.resume_from_book_mark(
            all_scanners(),
            book_mark)
        mutex.release()


if __name__ == "__main__":
    args = web_server.parse_args("Run a web server showing a live stream of your pirate massacre missions grouped by system.")

    build_scanners()

    public_path = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)
        ), "Public")

    web_server.start(args, PirateMassacreHandler, public_path)

    main_loop()
