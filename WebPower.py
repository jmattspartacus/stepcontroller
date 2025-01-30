import subprocess, os
import Logger

class WebPower:
    def __init__(self, logger: Logger.Logger, index: int):
        self.logger = logger
        self.index=index
    

    def PowerOn(self):
        home = os.environ["HOME"]
        if not os.path.exists("%s/stepper/lnrelay-eth.sh"%(home)):
            print("Failed to find the webpower script for toggling power!")
            return    
        retval=subprocess.check_output(["%s/stepper/lnrelay-eth.sh"%(home),str(self.index),"ON"]).decode()
        if (int(retval) != 0):
            print("Warning! Error in %s/stepper/lnrelay-eth.sh"%(home))
            return False
        return True

    def PowerOff(self):
        home = os.environ["HOME"]
        if not os.path.exists("%s/stepper/lnrelay-eth.sh"%(home)):
            print("Failed to find the webpower script for toggling power!")
            return    
        retval=subprocess.check_output(["%s/stepper/lnrelay-eth.sh"%(home),str(self.index),"OFF"]).decode()
        if (int(retval) != 0):
            print("Warning! Error in %s/stepper/lnrelay-eth.sh"%(home))
            return False
        return True
    
    def CheckStatus(self):
        home = os.environ["HOME"]
        if not os.path.exists("%s/stepper/lnrelay-check.sh"%(home)):
            print("Failed to find the webpower script for checking status!")
            return    
        retval=subprocess.check_output(["%s/stepper/lnrelay-check.sh"%(home),str(self.index)]).decode()
        retval=retval.split("\n")
        if (int(retval[1]) != 0):
            print("Warning! Error in %s/stepper/lnrelay-check.sh"%(home))
 
        if (retval[0] == "ON"):
            return True 
        elif (retval[0] == "OFF"):
            return False
        else:
            print("Warning! %s/stepper/lnrelay-check.sh gave unexpected output"%(home))
            return False

    def PrintStatus(self):
        home = os.environ["HOME"]
        print(f"Webpower switch is {'enabled' if self.CheckStatus() else 'disabled'}!")
        
