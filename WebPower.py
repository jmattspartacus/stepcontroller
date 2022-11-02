import subprocess, os
import Logger

class WebPower:
    def __init__(self, logger: Logger.Logger, index: int):
        self.logger = logger
        self.index=index
    

    def PowerOn(self):
        if not os.path.exists("./lnrelay-eth.sh"):
            print("Failed to find the webpower script for toggling power!")
            return    
        retval=subprocess.check_output(["./lnrelay-eth.sh",str(self.index),"ON"]).decode()
        if (int(retval) != 0):
            print("Warning! Error in ./lnrelay-eth.sh")
            return False
        return True

    def PowerOff(self):
        if not os.path.exists("./lnrelay-eth.sh"):
            print("Failed to find the webpower script for toggling power!")
            return    
        retval=subprocess.check_output(["./lnrelay-eth.sh",str(self.index),"OFF"]).decode()
        if (int(retval) != 0):
            print("Warning! Error in ./lnrelay-eth.sh")
            return False
        return True
    
    def CheckStatus(self):
        if not os.path.exists("./lnrelay-check.sh"):
            print("Failed to find the webpower script for checking status!")
            return    
        retval=subprocess.check_output(["./lnrelay-check.sh",str(self.index)]).decode()
        retval=retval.split("\n")
        if (int(retval[1]) != 0):
            print("Warning! Error in ./lnrelay-check.sh")
 
        if (retval[0] == "ON"):
            return True 
        elif (retval[0] == "OFF"):
            return False
        else:
            print("Warning! ./lnrelay-check.sh gave unexpected output")
            return False

    def PrintStatus(self):
        print(f"Webpower switch is {'enabled' if self.CheckStatus() else 'disabled'}!")
        
