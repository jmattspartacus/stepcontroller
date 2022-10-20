import os
from datetime import datetime

class Logger:
    def __init__(self, log_file: str):
        self.log_history = []
        if os.path.exists(log_file):
            print("Loading history from log")
            with open(log_file, "r") as rfp:
                self.log_history=rfp.readlines()
            self.log_fp = open(log_file, "a+")
            self.log_history = [i.replace("\n", "") for i in self.log_history]
        else:
            print("No history, opening new log")
            self.log_fp = open(log_file, "w+")

    def get_last(self):
        if len(self.log_history) > 0:
            return self.log_history[-1]
        else:
            return None

    def write(self, out: str) -> None:
        date_string = f'{datetime.now():%Y-%m-%d/%H:%M:%S%z}, '
        entry = date_string+out
        self.log_fp.write(entry+"\n")
        self.log_history.append(entry)
        self.log_fp.flush()
        
    def get(self, idx: int) -> str:
        if idx < len(self.log_history):
            return self.log_history[idx]

    
    