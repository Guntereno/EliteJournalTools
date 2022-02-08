import datetime
import journal_scan
import os
import pirate_massacre
import threading
import time
import web_server
from pytz import UTC


scanner = None
mutex = threading.Lock()

# There appears to be a bug in the bookmark system. Until that's fixed we'll rebuild
# the complete scanner every time a request is made
rebuild_scanner_on_request = False

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

class PirateMassacreHandler(web_server.Handler):
    def get_handler(self, request):
        if request == "/mission_report":
            return self.send_mission_report
        return None

    def send_mission_report(self):
        if scanner == None:
            return

        global mutex
        mutex.acquire()
        if rebuild_scanner_on_request:
            build_scanner()
        report = scanner.build_report()
        mutex.release()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        content = ""

        content += f'<div class ="MissionCount">Currently tracking {report["MissionCount"]}/20 missions for a potential {"{:,}".format(report["TotalReward"])} credit reward.</div>'
        for system in report['Systems']:
            content += (f'<div class="SystemHeader">{system["Name"]}</div>')
            for faction in system["Factions"]:
                content += f'<div class="FactionHeader">{faction["Name"]}</div>'
                missions = faction["Missions"]
                if len(missions) > 0:
                    for mission in missions:
                        kills = mission.total_kills - mission.remaining_kills
                        content += '<div class="Mission">'

                        message = '{} for {:,} credits'.format(mission.description, mission.reward)
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
                    content += '<div class="Mission">'
                    content += 'None'
                    if faction['HasMissionsInOtherSystem']:
                        content +=' (have mission in other system)'
                    content += '</div>'

        self.wfile.write(bytes(content, "utf-8"))

def main_loop(book_mark):
    if rebuild_scanner_on_request:
        return

    global mutex
    global scanner
    
    while True:
        time.sleep(0.5)

        mutex.acquire()
        book_mark = journal_scan.resume_from_book_mark(scanner, book_mark)
        mutex.release()

def build_scanner():
    global scanner

    # Wing missions last around 7 days, so we only need to scan that far back
    scanner = pirate_massacre.PirateMassacreScanner()
    start_date = datetime.datetime.now(UTC) - datetime.timedelta(8)
    book_mark = journal_scan.scan_journal_files_in_date_range(scanner, start_date, None)
    return book_mark

if __name__ == "__main__":
    args = web_server.parse_args("Run a web server showing a live stream of your pirate massacre missions grouped by system.")

    book_mark = build_scanner()

    public_path = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)
        ), "Public")

    web_server.start(args, PirateMassacreHandler, public_path)

    main_loop(book_mark)
