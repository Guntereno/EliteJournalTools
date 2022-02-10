import datetime
import json
import threading
import time
import os

status_file = os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous/Status.json")
last_accessed = datetime.datetime.min
mutex = threading.Lock()
status = None
thread = None

def init():
    global thread
    thread = threading.Thread(target = main_thread)
    thread.start()

def main_thread():
    while True:
        time.sleep(1)

        file_modified_since_epoch = os.path.getmtime(status_file)
        file_modified = datetime.datetime.fromtimestamp(file_modified_since_epoch)

        global last_accessed
        if file_modified <= last_accessed:
            continue
        last_accessed = file_modified

        with open(status_file, encoding='utf-8') as file_ptr:
            status_json = file_ptr.readline()
            parsed = json.loads(status_json)

        mutex.acquire()
        global status
        status = parsed
        mutex.release()

def get_status():
    result = None
    mutex.acquire()
    result = status
    mutex.release()
    return result

if __name__ == "__main__":
    # Simple scanner which prints all recvieved text as a test
    init()
    my_status = None
    while True:
        new_status = get_status()
        if(new_status is not my_status):
            my_status = new_status
            print(json.dumps(my_status))
        time.sleep(0.2)
