#!/usr/bin/python3

import time
from sys import argv
import WebPower
import Logger
import StepperControl
from HelpCommand import HelpCommand
import os
import signal
#Gear ratio 14:1

def signal_handler(sig, frame):
    global controllers
    print("Ctrl-C captured, exiting gracefully")
    for i in range(len(controllers)):
        control = controllers[i]
        if control.booted:
            control.ser.close()
            control.power.PowerOff()

    os.remove("%s/.stepperLock"%(home))
    exit()
    

def load_config(config_file_name, default_profile_values):
    """
    Loads a config for the stepper motor controller from disk,
    creating a default nonfunctional one if it does not exist. 
    Returns profiles for each motor that exists in the config.
    """
    profiles = []
    # verify config exists and create default if not found
    if not os.path.exists(config_file_name):
        print(f"No config file detected! Generating a default config at ./{config_file_name}! This must be edited for your environment before continuing!")
        with open(config_file_name, "w+") as fp:
            header = "   ".join([i[0] for i in default_profile_values]) + "\n"
            values = "   ".join([i[1] for i in default_profile_values]) + "\n"
            fp.writelines([
                header, values
            ])
        exit(1)
    config_header = []
    # load config into files
    with open(config_file_name, "r") as fp:
        l = fp.readlines()
        # get the name of the fields we want each profile to have
        config_header = [ i.strip() for i in l[0].split() ]
        # get the names of the profiles
        for i in range(1, len(l)):
            pname = l[i].split()[0]
            profiles.append({})
        # now we populate the fields of the profiles
        for i in range(1, len(l)):
            spl = [k.strip() for k in l[i].split()]
            if l[i][0] == "#": continue
            for j in range(0, len(spl)):
                profiles[i-1][config_header[j]] = default_profile_values[j][2](spl[j])
    return profiles


def validate_profile(profile, default_profile_values):
    for i in range(1, len(default_profile_values)):
        prop            = default_profile_values[i][0]
        val             = default_profile_values[i][1]
        # function/lambda that converts the value to it's correct 
        # type
        typefunc        = default_profile_values[i][2]
        validation_func = default_profile_values[i][3]
        fail_message    = default_profile_values[i][4]
        try:
            val  = typefunc(val)
        except:
            print(f"Failed to parse default value property {prop} to it's correct type!")
            exit(1)
        # check for default value
        if profile[prop] == val:
            print(f"Profile {profile_name} has property {prop} with value {val}, the same as default!")
            exit(1)

        # check that the input is in a correct range
        if validation_func and not validation_func(profile[prop]):
            print(f"Profile {profile_name} has an invalid value for {prop}! {fail_message}")
            exit(1)

if __name__ == "__main__":
    global controllers
    home = os.environ["HOME"]
    if os.path.exists("%s/.stepperLock"%(home)):
        print("%s/.stepperLock exists, another instance of Stepper.py may be running!"%(home))
        exit()
    else:
        open("%s/.stepperLock"%(home), 'a').close()
    
    signal.signal(signal.SIGINT, signal_handler)

    def Splash():
        print("===============================================================")
        print("==================== STEPPER CONTROl ==========================")
        print("===============================================================")
        print("Control software for stepper motor actuator control            ")
        print("Contact Tim Gray         tgray30@utk.edu, graytj1@ornl.gov     ")
        print("Contact James Christie   jmchristie321@gmail.com               ")
        print("Using config:            {}".format(config_file_name))
        print("type \"help\" for commands                                     ")
        print("===============================================================")


    def GetBooted():
        global control
        if control.booted:
            print ("Controller is booted")
        else:
            print("Controller is not booted")

    config_file_name = "%s/stepper/stepper.cfg"%(home)
    default_profile_values = [
        # property name, default value, type, validation lambda, failure message
        ("type", "R", str, lambda a: a=="R" or a=="L", "only rotational (R) or linear (L) types supported"),
        ("name", "nobody", str, None, ""), 
        ("port", "/dev/null", str, lambda a: os.path.exists(a), "port not found"), 
        ("power", "-1", int, lambda a: a >= 0 and a < 40, "value out of range"),
        ("log", "nobody.log", str, None, "")
    ]
    
    Splash()
    
    profiles = load_config(config_file_name, default_profile_values)
    controllers = []

    #initialize all profiles in config file
    for i in range(len(profiles)):
        profile = profiles[i]
        if (not("name" in profile.keys())): continue
        name = profile["name"]
        validate_profile(profile, default_profile_values)

        # take the data out of the profile to make easier to work with
        port          = profile["port"]
        log_name      = "%s/stepper/%s"%(home, profile["log"])
        webpower_port = profile["power"]
    
        first_boot = False
        # Assume that this is the first boot if the log is empty
        try:
            with open(log_name) as fptr:
                # this is a new log
                if "".join(fptr.readlines()) == "":
                    first_boot = True
        except FileNotFoundError:
            first_boot = True

        log     = Logger.Logger(log_name)
        power   = WebPower.WebPower(log, webpower_port)
        power.CheckStatus()
        if (profile["type"] == "R"):
            lcontrol = StepperControl.RotationControl(name, logger=log, power=power, port=port)
        elif (profile["type"] == "L"):
            lcontrol = StepperControl.LinearControl(name, logger=log, power=power, port=port)
        else:
            print("Invalid config file! Types other than linear (L) or rotational (R) not valid!")
            exit(1)
            

        if first_boot:
            print("Attempting first boot!")
            lcontrol.first_boot(power)

        # keep the log from knowing anything about the impl of control 
        if len(log.log_history) == 0:
            lcontrol.print_log_headers()

        lcontrol.check_connect()
        booted = lcontrol.booted
        lcontrol.load_from_log()
        if booted:
            lcontrol.is_motor_on()

        controllers.append(lcontrol)


    control = controllers[0]
    
    def SetPort(in_port: str):
        port = in_port
        global control
        control.port = port
        control.motor_init()
    
    def GetPort():
        global control
        print(control.port)

    def Switch(name: str = "nobody"):
        global control
        for i in range(len(controllers)):
            if (name == controllers[i].name):
                control = controllers[i]
    def Clear():
        global control
        print("\033[2J\033[H")

    def Boot():
        global control
        control.boot()

    def Stat():
        global control
        control.stat_header()
        for i in range(len(controllers)):
            con = controllers[i]
            if (con.name == control.name):
                con.stat(emphasis=True)
            else:
                con.stat()

    def SStat():
        global control
        control.stat_header()
        for i in range(len(controllers)):
            con = controllers[i]
            if (con.name == control.name):
                con.sstat(emphasis=True)
            else:
                con.sstat()
    
    def MotorEnable(enable: int):
        global control
        control.motor_enable(enable)
  
    def AlarmClear():
        global control
        control.clear_alarm()

    def ShutDown():
        global control
        control.powerOff()

    def MoveRel(ang: float):
        global control
        control.move_relative(ang)

    def MoveAbs(ang: float):
        global control
        control.move_absolute(ang)
    
    def Move(target: str):
        global control
        control.move(target)

    def GetPosition():
        global control
        control.get_position()

    def SetStepsPerRotation(spr: int):
        global control
        control.set_steps_per_rotation(spr)

    def Cmd(command: str):
        global control
        control.send(command)

    def CmdOut(command: str):
        global control
        control.send_get_out(command)

    def GetOutput():
        global control
        control.get_output()

    def Calibrate(pos: float, pos2: float):
        global control
        control.calibrate(pos, pos2)

    def GetLim():
        global control
        control.print_limits()

    def SetLim(lowlim: float, highlim: float):
        global control  
        control.set_limits(lowlim, highlim)

    def GetAng():
        global control
        control.get_angle()

    def GetMM():
        global control
        control.get_mm()
    
    def GetStatus():
        global control
        control.get_status()

    def GetAlarm():
        global control
        control.get_alarm()

    def SaveLog():
        global control
        control.make_log_entry()

    def GetPower():
        global control
        control.power.PrintStatus()

    def MakeLogEntry():
        global control
        control.make_log_entry()
     

    def helpme(command: str = ""):
        for i in cmd:
            for n in i.name:
                if n == command and not i.is_advanced:
                    i.print_long(False)
                    return
        for i in cmd:
            if not i.is_advanced:
                i.print_short(False)
 
    def helpmeadvanced(command: str = ""):
        for i in cmd:
            for n in i.name:
                if n == command and i.is_advanced:
                    i.print_long(True)
                    return
        for i in cmd:
            if i.is_advanced:
                i.print_short(True)
        
        
        

    cmd=[
        HelpCommand(["sw","cd"], Switch, [str], False, False, "Switches to control a different motor", ["name: the name of motor to control"],"sw FP1_R1"),
        HelpCommand(["stat"], Stat, [], False, False, "Prints status (fast)", [],"Prints status overview"),
        HelpCommand(["sstat"], SStat, [], False, False, "Prints status (slow)", [],"Prints status overview"),
        HelpCommand(["clear", "clr"], Clear, [], False, False, "Clears screen", [],"Clears screen"),
        HelpCommand(["boot"], Boot, [], False, False, "Boots the controller with the supplied port", [],"boot /dev/ttyUSB0"),
        #HelpCommand("reboot", PowerCycle, [], False, False, "Reboots the controller, by power cycling the power switch", [], "reboot"),
        HelpCommand(["me", "motorenable"],MotorEnable,[int],False,False,"Enables or disables the motor attached to the controller",["Enable/disable (int), enter 1 for enable, 0 for disable"],"motorenable 1"),
        HelpCommand(["ac", "alarmclear"],AlarmClear,[],False,False,"Clears any alarms for the controller immediately",[],"alarmclear"),
        HelpCommand(["shutdown"],ShutDown,[],False,False,"Shutdown the controller by turning off power to the webpower switch and closing the connection to the serial port",[],"shutdown"),
        HelpCommand(["move"], Move, [str], False, False, "Moves to either IN/OUT (linear only), or to absolute position (mm/deg)", [], "move IN; move OUT; move 45.0"),
        HelpCommand(["moveabs"],MoveAbs,[float],False,False,"Moves the output shaft to an absolute position as an angle, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",["Angle (float), the angle in degrees where the output shaft will be moved to"],"moveabs 45.0"),
        HelpCommand(["moverel"],MoveRel,[float],False,False,"Moves the output shaft by an angle relative to it's current position, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",["Angle (float), the angle in degrees to move the output shaft"],"moverel 45.0"),
        HelpCommand(["setres"],SetStepsPerRotation,[int],False,False,"Changes the resolution for stepping used by the controller. Maps the input resolution onto a table of resolution that the controller supports.",["Resolution (int) the resolution you want to target"],"setres 2000"),
        HelpCommand(["getpos"],GetMM,[],False,False,"Gets the position in mm (linear only).", [],"getpos"),
        HelpCommand(["getang"],GetAng,[],False,False,"Gets the angle corresponding to the current position of the output shaft (rotational only).", [],"getang"),
        HelpCommand(["getstep"],GetPosition,[],False,False,"Prints the position of the output shaft in steps.",[],"getpos"),
        HelpCommand(["cmd"],Cmd,[str],False,True,"Sends the command supplied to the controller. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",["Command (str), the command you want to send to the controller"],"cmd FL200"),
        HelpCommand(["cmdout"],CmdOut,[str],False,True,"Sends the command supplied to the controller, and prints the response from the controller. For commands that do not send a reply, nothing may be printed. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",["Command (str), the command you want to send to the controller"],"cmdout SC"),
        HelpCommand(["getout"],GetOutput,[],False,True,"Gets the data from the output buffer and prints it",[],"out"),
        HelpCommand(["calibrate"],Calibrate,[float, float],False,True,"Define the position to be the supplied angle. This respects software limits.",["Angle (float), the angle in degrees where the position will be defined to be"],"calibrate 0"),
        HelpCommand(["getlim"],GetLim,[],False,False,"Prints the software limits set for the angle of the output shaft",[],"getlim"),
        HelpCommand(["setlim"],SetLim,[float, float],False,True,"Changes the software limits of the position of the output shaft",["Low (float), the angle in degrees where lower limit of the position will be.","High (float), the angle in degrees where upper limit of the position will be."],"setlim 0.0 90.0"),
        HelpCommand(["help"],helpme,[str],True,False,"Prints the help text for the specified command. Defaults to all non advanced commands.",["Command (str), the command you want information about, defaults to all"],"help moverel"),
        HelpCommand(["helpadv"],helpmeadvanced,[str],True,False,"Prints the help text for the specified advanced commands. Defaults to all advanced commands. Caution: Advanced commands should only be used if you know what you're doing",["Command (str), the command you want information about, defaults to all"],"helpadv cmd"),
        HelpCommand(["setport"],SetPort,[str],False,True,"Sets the serial port used to connect to the motor controller", ["Port (str), the port being connected to"],"setport /dev/ttyUSB0"),
        HelpCommand(["getport"],GetPort,[],False,True,"Gets the serial port used to connect to the motor controller", [],"getport"),
        HelpCommand(["booted"],GetBooted,[],False,False,"Gets the boot status", [],"getbooted"),

        HelpCommand(["getstatus"],GetStatus,[],False,False,"Gets the status of the controller and decodes to human readable output.", [],"getstatus"),       
        HelpCommand(["getalarm"],GetAlarm,[],False,False,"Gets the alarm code if there is any and decodes to human readable output.", [],"getalarm"),       

        HelpCommand(["savelog"],MakeLogEntry,[],False,False,"Outputs the current state of the controller to the log.", [],"savelog"),       
        
        HelpCommand(["getpower"],GetPower,[],False,True,"Checks whether the webpower switch connection is on", [],"getpower"),
        #HelpCommand("setport",SetPort,[str],False,False,"Sets the port used to connect", )
        #"testfunc":   {"func": testfunc, "args":[str, float, int]}
        #"testloadfromlog":   {"func": control.load_from_log, "args":[]},
    ]

    
    
    def cmd_parse(in_cmd: str):
        global control
        spl = in_cmd.split(" ")
        spl = [i for i in spl if len(i) > 0]
        all_names = []
        for x in cmd:
            for y in x.name:
                all_names.append(y)
        if len(spl) == 0:
            return
        if (spl[0] not in all_names):
            print("Unknown command!")
            return
        if spl[0] == "bootoverride":
            control.booted=True
            return
        nobootallowed = ["getpos", "getang", "getlim",
                         "clr", 
                         "clear", 
                         "stat", 
                         "sstat", 
                         "sw", 
                         "cd", "boot", "help", "helpadv", "setport", "booted"]
        if spl[0] not in nobootallowed and not control.booted:
            print("Please boot!")
            return
        j = -1
        for i in range(len(cmd)):
            for k in range(len(cmd[i].name)):
                if spl[0] == cmd[i].name[k]:
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

    print("")
    Stat()
    print("")

    endvals = ["quit", "exit", "stop", "end", ".q", "st"]
    while True:
        if (control.booted):
            prompt = "\033[1;38;5;28m %s\033[2;39m >> \033[0m"%(control.name)
        else:
            prompt = "\033[1;36m %s\033[2;39m >> \033[0m"%(control.name)
        
        inval = input(prompt)
        if inval in endvals:
            break
        cmd_parse(inval)

    for i in range(len(controllers)):
        control = controllers[i]
        if control.booted:
            control.ser.close()
            control.power.PowerOff()

    os.remove("%s/.stepperLock"%(home))
