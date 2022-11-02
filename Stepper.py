import time
from sys import argv
import WebPower
import Logger
import StepperControl
from HelpCommand import HelpCommand
#Gear ratio 14:1


if __name__ == "__main__":

    def Splash():
        print("===============================================================")
        print("==================== STEPPER CONTROl ==========================")
        print("===============================================================")
        print("Control software for stepper motor actuator control            ")
        print("Contact Tim Gray         graytj@ornl.gov                       ")
        print("Contact James Christie   jchris44@vols.utk.edu                 ")
        print("type \"help\" for commands                                     ")
        print("port is {}".format(port))
    
    def GetBooted():
        if booted:
            print ("Controller is booted")
        else:
            print("Controller is not booted")

    port = "/dev/ttyS4" 
    Splash()

    log     = Logger.Logger("stepper.log")
    power   = WebPower.WebPower(log, 24)
    power.CheckStatus()
    control = StepperControl.StepperControl(logger=log, port=port)
    # keep the log from knowing anything about the impl of control 
    if len(log.log_history) == 0:
        control.print_log_headers()
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

    def SetPort(in_port: str):
        global port
        port = in_port
        global control
        control.port = port
        control.motor_init()
    
    def GetPort():
        print(port)


    def helpme(command: str = ""):
        for i in cmd:
            if i.name == command and not i.is_advanced:
                i.print_long(False)
                return
        for i in cmd:
            if not i.is_advanced:
                i.print_short(False)
 
    def helpmeadvanced(command: str = ""):
        for i in cmd:
            if i.name == command and i.is_advanced:
                i.print_long(True)
                return
        for i in cmd:
            if i.is_advanced:
                i.print_short(True)
        
        
        

    cmd=[
        HelpCommand("boot", BootStepper, [], False, False, "Boots the controller with the supplied port", ["port: the port that the controller is attached to"],"boot /dev/ttyUSB0"),
        #HelpCommand("reboot", PowerCycle, [], False, False, "Reboots the controller, by power cycling the power switch", [], "reboot"),
        HelpCommand("motorenable",control.motor_enable,[int],False,False,"Enables or disables the motor attached to the controller",["Enable/disable (int), enter 1 for enable, 0 for disable"],"motorenable 1"),
        HelpCommand("alarmclear",control.clear_alarm,[],False,False,"Clears any alarms for the controller immediately",[],"alarmclear"),
        HelpCommand("shutdown",power.PowerOff,[],False,False,"Shutdown the controller by turning off power to the webpower switch and closing the connection to the serial port",[],"shutdown"),
        HelpCommand("moverel",control.move_relative,[float],False,False,"Moves the output shaft by an angle relative to it's current position, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",["Angle (float), the angle in degrees to move the output shaft"],"moverel 45.0"),
        HelpCommand("moveabs",control.move_absolute,[float],False,False,"Moves the output shaft to an absolute position as an angle, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",["Angle (float), the angle in degrees where the output shaft will be moved to"],"moveabs 45.0"),
        HelpCommand("setres",control.set_steps_per_rotation,[int],False,False,"Changes the resolution for stepping used by the controller. Maps the input resolution onto a table of resolution that the controller supports.",["Resolution (int) the resolution you want to target"],"setres 2000"),
        HelpCommand("getpos",control.get_position,[],False,False,"Prints the position of the output shaft as an angle.",[],"echopos"),
        HelpCommand("cmd",control.send,[str],False,True,"Sends the command supplied to the controller. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",["Command (str), the command you want to send to the controller"],"cmd FL200"),
        HelpCommand("cmdout",control.send_get_out,[str],False,True,"Sends the command supplied to the controller, and prints the response from the controller. For commands that do not send a reply, nothing may be printed. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",["Command (str), the command you want to send to the controller"],"cmdout SC"),
        HelpCommand("getout",control.get_output,[],False,True,"Gets the data from the output buffer and prints it",[],"out"),
        HelpCommand("calibrate",control.calibrate,[float],False,True,"Define the position to be the supplied angle. This respects software limits.",["Angle (float), the angle in degrees where the position will be defined to be"],"calibrate 0"),
        HelpCommand("getlim",control.print_limits,[],False,False,"Prints the software limits set for the angle of the output shaft",[],"getlim"),
        HelpCommand("setlim",control.set_limits,[float, float],False,True,"Changes the software limits of the position of the output shaft",["Low (float), the angle in degrees where lower limit of the position will be.","High (float), the angle in degrees where upper limit of the position will be."],"setlim 0.0 90.0"),
        HelpCommand("help",helpme,[str],True,False,"Prints the help text for the specified command. Defaults to all non advanced commands.",["Command (str), the command you want information about, defaults to all"],"help moverel"),
        HelpCommand("helpadv",helpmeadvanced,[str],True,False,"Prints the help text for the specified advanced commands. Defaults to all advanced commands. Caution: Advanced commands should only be used if you know what you're doing",["Command (str), the command you want information about, defaults to all"],"helpadv cmd"),
        HelpCommand("setport",SetPort,[str],False,True,"Sets the serial port used to connect to the motor controller", ["Port (str), the port being connected to"],"setport /dev/ttyUSB0"),
        HelpCommand("getport",GetPort,[],False,True,"Gets the serial port used to connect to the motor controller", [],"getport"),
        HelpCommand("booted",GetBooted,[],False,False,"Gets the boot status", [],"getbooted"),
        HelpCommand("getang",control.get_angle,[],False,False,"Gets the angle corresponding to the current position of the output shaft.", [],"getang"),

        HelpCommand("getstatus",control.get_status,[],False,False,"Gets the status of the controller and decodes to human readable output.", [],"getstatus"),       
        HelpCommand("getalarm",control.get_alarm,[],False,False,"Gets the alarm code if there is any and decodes to human readable output.", [],"getalarm"),       

        HelpCommand("savelog",control.make_log_entry,[],False,False,"Outputs the current state of the controller to the log.", [],"savelog"),       
        
        HelpCommand("getpower",power.PrintStatus,[],False,True,"Checks whether the webpower switch connection is on", [],"getpower"),
        #HelpCommand("setport",SetPort,[str],False,False,"Sets the port used to connect", )
        #"testfunc":   {"func": testfunc, "args":[str, float, int]}
        #"testloadfromlog":   {"func": control.load_from_log, "args":[]},
    ]

    
    
    def cmd_parse(in_cmd: str):
        spl = in_cmd.split(" ")
        spl = [i for i in spl if len(i) > 0]
        if len(spl) == 0:
            return
        if spl[0] == "bootoverride":
            global booted
            booted=True
            return
        if spl[0] != "boot" and not booted and spl[0] != "help":
            print("Please boot!")
            return
        j = -1
        for i in range(len(cmd)):
            if spl[0] == cmd[i].name:
                j = i
                break
        if j == -1:
            return
        t_cmd = cmd[j]
        t_args = spl[1:]
        if len(t_cmd.arg_types) != len(t_args) and not t_cmd.arg_opt:
            a = len(t_cmd.arg_types)
            print(f"Wrong number of arguments, expected {a}, got {len(t_args)}")
            return
        if len(t_args) > 0 and not t_cmd.arg_opt:
            for i in range(len(t_args)):
                try:
                    #if not type(t_args[i]) is 
                    t_args[i] = t_cmd.arg_types[i](t_args[i])
                except:
                    t = t_cmd.arg_types[i]
                    print(f"Failed to parse argument {i} as {t}")
                    return
        if len(t_cmd.arg_types) > 0:
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
            break
        cmd_parse(inval)

    if booted:
        control.ser.close()



