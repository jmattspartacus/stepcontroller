import time
from sys import argv
import WebPower
import Logger
import StepperControl
from HelpCommand import HelpCommand
import os
#Gear ratio 14:1


def load_config(config_file_name, default_profile_values):
    """
    Loads a config for the stepper motor controller from disk,
    creating a default nonfunctional one if it does not exist. 
    Returns profiles for each motor that exists in the config.
    """
    profiles = {}
    # verify config exists and create default if not found
    if not os.path.exists(config_file_name):
        print(f"No config file detected! Generating a default config at ./{config_file_name}! This must be edited for your environment before continuing!")
        with open(config_file_name, "w+") as fp:
            header = ", ".join([i[0] for i in default_profile_values]) + "\n"
            values = ", ".join([i[1] for i in default_profile_values]) + "\n"
            fp.writelines([
                header, values
            ])
        exit(1)
    config_header = []
    # load config into files
    with open(config_file_name, "r") as fp:
        l = fp.readlines()
        # get the name of the fields we want each profile to have
        config_header = [ i.strip() for i in l[0].replace(" ", "").split(",") ][1:]
        # get the names of the profiles
        for i in range(1, len(l)):
            pname = l[i].split(",")[0]
            profiles[pname] = {}
        # now we populate the fields of the profiles
        for i in range(1, len(l)):
            spl = [k.strip() for k in l[i].split(",")]
            for j in range(1, len(spl)):
                profiles[spl[0]][config_header[j - 1]] = default_profile_values[j][2](spl[j])
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

    def Splash():
        print("===============================================================")
        print("==================== STEPPER CONTROl ==========================")
        print("===============================================================")
        print("Control software for stepper motor actuator control            ")
        print("Contact Tim Gray         graytj@ornl.gov                       ")
        print("Contact James Christie   jmchristie321@gmail.com               ")
        print("Using profile:           {}".format(profile_name))
        print("Connecting on:           {}".format(port))
        print("Using WebPower port:     {}".format(webpower_port))
        print("type \"help\" for commands                                     ")
        print("===============================================================")


    def GetBooted():
        if booted:
            print ("Controller is booted")
        else:
            print("Controller is not booted")

    config_file_name = "stepper_config.csv"
    default_profile_values = [
        # property name, default value, type, validation lambda, failure message
        ("profile", "nobody", str, None, ""), 
        ("port", "/dev/null", str, lambda a: os.path.exists(a), "port not found"), 
        ("webpower_port", "-1", int, lambda a: a >= 0 and a < 40, "value out of range"),
        ("log_name", "nobody.log", str, None, "")
    ]
    profiles = load_config(config_file_name, default_profile_values)
    profile_name = "nobody"

    # use the specified profile!
    if len(argv) == 2 and argv[1] in profiles:
        profile_name = argv[1]
    # use the first profile found
    else:
        profile_name = list(profiles.keys())[0]
        print(f"Profile name not found or not provided, using profile {profile_name}!")

    # check for the default profile name, because this must not be used
    if profile_name == "nobody":
        print("Profile name cannot be 'nobody' name is reserved!")
        exit(1)
    
    profile = profiles[profile_name]
    validate_profile(profile, default_profile_values)

    # take the data out of the profile to make easier to work with
    port          = profile["port"]
    log_name      = profile["log_name"]
    webpower_port = profile["webpower_port"]
    
    Splash()
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
    control = StepperControl.StepperControl(logger=log, port=port)

    if first_boot:
        print("Attempting first boot!")
        control.first_boot(power)

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
        nobootallowed = ["boot", "help", "helpadv", "setport"]
        if spl[0] not in nobootallowed and not booted:
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


    endvals = ["quit", "exit", "stop", "end", ".q"]
    while True:
        inval = input("-> ")
        if inval in endvals:
            break
        cmd_parse(inval)

    if booted:
        control.ser.close()
        power.PowerOff()
