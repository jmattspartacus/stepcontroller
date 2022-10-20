import serial, time, sys
from sys import argv
import WebPower
import Logger
import StepperControl
#Gear ratio 14:1


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Please supply a default port for connection!")
        sys.exit()
    port    = sys.argv[1]
    log     = Logger.Logger("stepper.log")
    power   = WebPower.WebPower(log)
    control = StepperControl.StepperControl(port=port, logger=log) 
    booted  = False
    control.load_from_log()

    def BootStepper(boot_port: str):
        global power
        power=WebPower.WebPower(log)
        power.PowerOn()
        global control
        control=StepperControl.StepperControl(logger=log, port=boot_port)
        control.try_connect()
        global booted
        booted = True


    def PowerCycle():
        power.PowerOff()
        power.PowerOn()
        control.reinit()


    def testfunc(a, b, c):
        print("{}, {:.2f}, {}".format(a, b, c))

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

    cmd={
        "boot":        { 
            "func": BootStepper, 
            "args":[str],
            "arg_opt":False, 
            "desc": "Boots the controller with the supplied port",
            "args_desc":["port: the port that the controller is attached to"],
            "example":"boot /dev/ttyUSB0"
        },
        "reboot":      {
            "func": PowerCycle, 
            "args":[], 
            "arg_opt":False,
            "desc": "Reboots the controller, by power cycling the power switch",
            "args_desc":[],
            "example":"reboot"
        },
        "motorenable": {
            "func": control.motor_enable, 
            "args":[int],
            "arg_opt":False,
            "desc": "Enables or disables the motor attached to the controller",
            "args_desc":["Enable/disable (int), enter 1 for enable, 0 for disable"],
            "example":"motorenable 1"
        },
        "alarmclear":  {
            "func": control.clear_alarm, 
            "args":[],
            "arg_opt":False,
            "desc": "Clears any alarms for the controller immediately",
            "args_desc":[],
            "example":"alarmclear"
        },
        "shutdown":    {
            "func": (), 
            "args":[],
            "arg_opt":False,
            "desc": "Shutdown the controller by turning off power to the webpower switch and closing the connection to the serial port",
            "args_desc":[],
            "example":"shutdown"
        },
        "moverel":     {
            "func": control.move_relative, 
            "args":[float],
            "arg_opt":False,
            "desc": "Moves the output shaft by an angle relative to it's current position, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",
            "args_desc":["Angle (float), the angle in degrees to move the output shaft"],
            "example":"moverel 45.0"
        },
        "moveabs":     {
            "func": control.move_absolute, 
            "args":[float],
            "arg_opt":False,
            "desc": "Moves the output shaft to an absolute position as an angle, takes gear ratio and controller resolution into account. Will not move outside the software limits defined for the motor",
            "args_desc":["Angle (float), the angle in degrees where the output shaft will be moved to"],
            "example":"moveabs 45.0"
        },
        "setres":      {
            "func": control.set_steps_per_rotation, 
            "args":[int],
            "arg_opt":False,
            "desc": "Changes the resolution for stepping used by the controller. Maps the input resolution onto a table of resolution that the controller supports.",
            "args_desc":["Resolution (int) the resolution you want to target"],
            "example":"setres 2000"
        },
        "echopos":     {
            "func": control.output_targeted_position, 
            "args":[],
            "arg_opt":False,
            "desc": "Prints the position of the output shaft as an angle.",
            "args_desc":[],
            "example":"echopos"
        },
        "cmd":         {
            "func": control.send, 
            "args":[str],
            "arg_opt":False,
            "desc": "Sends the command supplied to the controller. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",
            "args_desc":["Command (str), the command you want to send to the controller"],
            "example":"cmd FL200"
        },
        "cmdout":      {
            "func": control.send_get_out, 
            "args":[str],
            "arg_opt":False,
            "desc": "Sends the command supplied to the controller, and prints the response from the controller. For commands that do not send a reply, nothing may be printed. Caution: Movement commands supplied this way do not respect software limits set through this script, and might cause damage.",
            "args_desc":["Command (str), the command you want to send to the controller"],
            "example":"cmdout SC"
        },
        "out":         {
            "func": control.get_output, 
            "args":[],
            "arg_opt":False,
            "desc": "Gets the data from the output buffer and prints it",
            "args_desc":[],
            "example":"out"
        },
        "calibrate":   {
            "func": control.calibrate, 
            "args":[float],
            "arg_opt":False,
            "desc": "Define the position to be the supplied angle. This respects software limits.",
            "args_desc":["Angle (float), the angle in degrees where the position will be defined to be"],
            "example":"calibrate 0"
        },
        "getlim":      {
            "func": control.print_limits, 
            "args":[],
            "arg_opt":False,
            "desc": "Prints the software limits set for the angle of the output shaft",
            "args_desc":[],
            "example": "getlim"
        },
        "setlim":      {
            "func": control.set_limits, 
            "args":[float, float],
            "arg_opt":False,
            "desc": "Changes the software limits of the position of the output shaft",
            "args_desc":[
                "Low (float), the angle in degrees where lower limit of the position will be.",
                "High (float), the angle in degrees where upper limit of the position will be."
            ],
            "example":"setlim 0.0 90.0"    
        },
        "helpme":      {
            "func": helpme, 
            "args":[str],
            "arg_opt":True,
            "desc": "Prints the help text for the specified command. Defaults to all commands.",
            "args_desc":["Command (str), the command you want information about, defaults to all"],
            "example":"help cmd"
        },
        #"dummy":      {
        #    "func": dummy, 
        #    "args":[str],
        #    "arg_opt":False,
        #    "desc": "Dummy command",
        #    "args_desc":["dummy arg"],
        #    "example":"dummy"
        #},
        #"testfunc":   {"func": testfunc, "args":[str, float, int]}
        #"testloadfromlog":   {"func": control.load_from_log, "args":[]},
    }

    
    
    def cmd_parse(in_cmd: str):
        spl = in_cmd.split(" ")
        if spl[0] == "bootoverride":
            global booted
            booted=True
            return
        if spl[0] != "boot" and not booted and spl[0] == "help":
            print("Please boot!")
            return
        if spl[0] in cmd.keys():
            t_cmd = cmd[spl[0]]
            t_args = spl[1:]
            if len(t_cmd["args"]) != len(t_args) and not t_cmd["arg_opt"]:
                a = len(t_cmd["args"])
                print(f"Wrong number of arguments, expected {a}, got {len(t_args)}")
                return
            if len(t_args) > 0 and not t_cmd["arg_opt"]:
                for i in range(len(t_args)):
                    try:
                        #if not type(t_args[i]) is 
                        t_args[i] = t_cmd["args"][i](t_args[i])
                    except:
                        t = t_cmd["args"][i]
                        print(f"Failed to parse argument {i} as {t}")
                        return
            if len(t_cmd["args"]) > 0:
                if len(t_args) == 0:
                    t_cmd["func"]()
                else:
                    t_cmd["func"](*t_args)
            else:
                t_cmd["func"]()

    endvals = ["quit", "exit", "stop", "end"]
    while True:
        inval = input("-> ")
        if inval in endvals:
            print("exit")
            break
        cmd_parse(inval)

    if booted:
        control.ser.close()



