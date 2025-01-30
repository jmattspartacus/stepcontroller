import os
from datetime import datetime

class Logger:
    def __init__(self, log_file: str):
        self.log_history = []
        self.name = log_file
        if os.path.exists(log_file):
            #print("Loading history from log %s"%(log_file))
            with open(log_file, "r") as rfp:
                self.log_history=rfp.readlines()
            self.log_fp = open(log_file, "a+")
            self.log_history = [i.replace("\n", "").replace(" ", "") for i in self.log_history]
            loglen = len(self.log_history)
            #for i in range(max(loglen - 3, 0), loglen):
            #    print(self.log_history[i])
        else:
            print("No history, opening new log")
            self.log_fp = open(log_file, "w+")

    def get_last(self):
        if len(self.log_history) > 1:
            return self.log_history[-1]
        else:
            return None

    def write(self, out: str) -> None:
        date_string = f'{datetime.now():%Y-%m-%d/%H:%M:%S%z}, '
        entry = date_string+out
        self.log_fp.write(entry+"\n")
        self.log_history.append(entry)
        self.log_fp.flush()
    
    def write_header(self, entry: str) -> None:
        # don't append history this is a new log
        self.log_fp.write(entry + "\n")
        self.log_fp.flush()

    def get(self, idx: int) -> str:
        if idx < len(self.log_history):
            return self.log_history[idx]

    
    
