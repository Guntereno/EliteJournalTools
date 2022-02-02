from posixpath import relpath
import journal_scan
import os
import pirate_massacre
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

host_name = "localhost"
server_port = 8080

public_path = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), "Public")

scanner = pirate_massacre.PirateMassacreScanner()

mutex = threading.Lock()

mime_types = {
    ".css": "text/css",
    ".js": "text/javascript",
    ".htm": "text/html",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml"
}

def get_mime_type(path):
    extension = os.path.splitext(path)[1]
    if extension in mime_types:
        return mime_types[extension]
    return "text/plain"

class PirateMassacreServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/mission_report":
            self.send_mission_report()
        if self.path == "/":
            self.send_file("/index.htm")
        else:
            self.send_file(self.path)

    def send_file(self, path):
        path = relpath(path, "/")
        path = os.path.join(public_path, path)
        path = os.path.realpath(path)

        if not os.path.exists(path):
            print(f"Failed to find file '{path}'")
            self.send_response(404)
            return

        if not path.startswith(public_path):
            print(f"Attempt to access file outside of public path!: '{path}'")
            self.send_response(404)
            return

        self.send_response(200)
        self.send_header("Content-type", get_mime_type(path))
        self.end_headers()

        file = open(path, "rb")
        self.wfile.write(file.read())
        file.close()

    def send_mission_report(self):
        global mutex
        mutex.acquire()
        report = scanner.build_report()
        mutex.release()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        content = ""

        content += f'<div class ="MissionCount">Currently tracking {report["MissionCount"]}/20 missions.</div>'
        for system in report['Systems']:
            content += (f'<div class="SystemHeader">{system["Name"]}</div>')
            for faction in system["Factions"]:
                content += f'<div class="FactionHeader">{faction["Name"]}</div>'
                missions = faction["Missions"]
                if len(missions) > 0:
                    for mission in missions:
                        kills = mission.total_kills - mission.remaining_kills
                        content += '<div class="Mission">'
                        message = '{} for {:,} credits:'.format(mission.description, mission.reward)
                        if mission.remaining_kills > 0:
                            message += f' {kills}/{mission.total_kills} ({mission.remaining_kills} remain)'
                        else:
                            message += ' DONE!'
                        content += message
                        content += '</div>'
                else:
                    content += '<div class="Mission">'
                    content += 'None'
                    if faction['HasMissionsInOtherSystem']:
                        content +=' (have mission in other system)'
                    content += '</div>'

        self.wfile.write(bytes(content, "utf-8"))

def start_web_server(host_name, server_port, PirateMassacreServer):
    web_server = ThreadingHTTPServer((host_name, server_port), PirateMassacreServer)
    web_server_thread = threading.Thread(target=web_server.serve_forever)
    web_server_thread.start()
    print("Started server at http://%s:%s" % (host_name, server_port))

def main_loop():
    book_mark = journal_scan.scan_journal(scanner)
    while True:
        global mutex
        mutex.acquire()
        book_mark = journal_scan.resume_from_book_mark(scanner, book_mark)
        mutex.release()
        time.sleep(0.5)

if __name__ == "__main__":
    start_web_server(host_name, server_port, PirateMassacreServer)
    main_loop()


