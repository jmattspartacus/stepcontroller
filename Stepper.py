from sys import argv
import WebPower
import Logger
import StepperControl
from HelpCommand import HelpCommand
#Gear ratio 14:1


if __name__ == "__main__":

    def GetBooted():
        if booted:
            print ("Booted")
        else:
            print("Not booted")

    port = "/dev/ttyS4" 
    log     = Logger.Logger("stepper.log")
    power   = WebPower.WebPower(log, 24)
    power.CheckStatus()
    control = StepperControl.StepperControl(logger=log, port=port) 
    booted  = control.check_connect() 
    GetBooted()
    if booted:
        control.load_from_log()

    def BootStepper():
        power.PowerOn()
        time.sleep(5)
        global booted
        booted = control.check_connect()
        GetBooted()
        if booted:
            control.load_from_log()


    def PowerCycle():
        power.PowerOff()
        power.PowerOn()
        control.reinit()

    def SetPort(in_port: str):
        global port
        port = in_port
        global control
        control = StepperControl.StepperControl(logger=log, port=port) 
    
    def GetPort():
        print(port)

    commands = [
       
    ]

    def helpme(command: str = ""):
        def print_command(i):
            print("Command:", i)
            print(cmd[i]["desc"])
            if len(cmd[i]["args_desc"]) > 0:
                print("Arguments:")
                for j in cmd[i]["args_desc"]:
                    print("    ", j)
            print("Example:", cmd[i]["example"])
        if command in cmd.keys():
            print_command(command)
            return
        for i in cmd.keys():
            print("{:<20}:{}".format(i, cmd[i]["desc"]))
    
    def helpmeadvanced(command: str = ""):

        for i in cmd:
            if i.name == command and i.is_advanced:
                i.printshort(True)
                return
        for i in cmd:
            if i.is_advanced:
                i.printlong(True)
        
        
        

    cmd=[
        HelpCommand("boot", BootStepper, [str], False, False, "Boots the controller with the supplied port", ["port: the port that the controller is attached to"],"boot /dev/ttyUSB0"),
        HelpCommand("reboot", PowerCycle, [], False, False, "Reboots the controller, by power cycling the power switch", [], "reboot"),
        HelpCommand("motorenable",control.motor_enable,[int],False,False,"Enables or disables the motor attached to the controller",["Enable/disable (int), enter 1 for enable, 0 for disable"],"motorenable 1"),
        HelpCommand("alarmclear",control.clear_alarm,[],False,False,"Clears any alarms for the controller immediately",[],"alarmclear"),
        HelpCommand("shutdown",power.PowerOff(),[],False,False,"Shutdown the controller by turning off power to the webpower switch and closing the connection to the serial port",[],"shutdown"),
        HelpCommand("moverel",control.move_relative,[float],False,False,"Moves the output shaft by an angle relative to it's current position, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",["Angle (float), the angle in degrees to move the output shaft"],"moverel 45.0"),
        HelpCommand("moveabs",control.move_absolute,[float],False,False,"Moves the output shaft to an absolute position as an angle, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",["Angle (float), the angle in degrees where the output shaft will be moved to"],"moveabs 45.0"),
        HelpCommand("setres",control.set_steps_per_rotation,[int],False,False,"Changes the resolution for stepping used by the controller. Maps the input resolution onto a table of resolution that the controller supports.",["Resolution (int) the resolution you want to target"],"setres 2000"),
        HelpCommand("echopos",control.output_targeted_position,[],False,False,"Prints the position of the output shaft as an angle.",[],"echopos"),
        HelpCommand("cmd",control.send,[str],False,True,"Sends the command supplied to the controller. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",["Command (str), the command you want to send to the controller"],"cmd FL200"),
        HelpCommand("cmdout",control.send_get_out,[str],False,True,"Sends the command supplied to the controller, and prints the response from the controller. For commands that do not send a reply, nothing may be printed. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",["Command (str), the command you want to send to the controller"],"cmdout SC"),
        HelpCommand("out",control.get_output,[],False,False,"Gets the data from the output buffer and prints it",[],"out"),
        HelpCommand("calibrate",control.calibrate,[float],False,True,"Define the position to be the supplied angle. This respects software limits.",["Angle (float), the angle in degrees where the position will be defined to be"],"calibrate 0"),
        HelpCommand("getlim",control.print_limits,[],False,False,"Prints the software limits set for the angle of the output shaft",[],"getlim"),
        HelpCommand("setlim",control.set_limits,[float, float],False,True,"Changes the software limits of the position of the output shaft",["Low (float), the angle in degrees where lower limit of the position will be.","High (float), the angle in degrees where upper limit of the position will be."],"setlim 0.0 90.0"),
        HelpCommand("helpme",helpme,[str],False,True,"Prints the help text for the specified command. Defaults to all commands.",["Command (str), the command you want information about, defaults to all"],"helpme cmd"),
        HelpCommand("helpme",helpmeadvanced,[str],False,True,"Prints the help text for the specified advanced commands. Defaults to all commands.",["Command (str), the command you want information about, defaults to all"],"helpme cmd")


        #HelpCommand("setport",SetPort,[str],False,False,"Sets the port used to connect", )
        #"testfunc":   {"func": testfunc, "args":[str, float, int]}
        #"testloadfromlog":   {"func": control.load_from_log, "args":[]},
    ]

    
    
    def cmd_parse(in_cmd: str):
        spl = in_cmd.split(" ")
        if spl[0] == "bootoverride":
            global booted
            booted=True
            return
        if spl[0] != "boot" and not booted and spl[0] == "help":
            print("Please boot!")
            return
        j = 0
        for i in range(len(cmd)):
            if spl[0] == cmd.name:
                j = i
                break
        t_cmd = cmd[j]
        t_args = spl[1:]
        if len(t_cmd.args) != len(t_args) and not t_cmd.arg_opt:
            a = len(t_cmd.args)
            print(f"Wrong number of arguments, expected {a}, got {len(t_args)}")
            return
        if len(t_args) > 0 and not t_cmd.arg_opt:
            for i in range(len(t_args)):
                try:
                    #if not type(t_args[i]) is 
                    t_args[i] = t_cmd.args[i](t_args[i])
                except:
                    t = t_cmd.args[i]
                    print(f"Failed to parse argument {i} as {t}")
                    return
        if len(t_cmd["args"]) > 0:
            if len(t_args) == 0:
                t_cmd.func()
            else:
                t_cmd.func(*t_args)
        else:
            t_cmd.func()

    endvals = ["quit", "exit", "stop", "end"]
    while True:
        inval = input("-> ")
        if inval in endvals:
            print("exit")
            break
        cmd_parse(inval)

    if booted:
        control.ser.close()



