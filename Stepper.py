import serial, time, sys
from sys import argv
import WebPower
import Logger
import StepperControl
#Gear ratio 14:1

if __name__ == "__main__":

    port = sys.argv[1]
    log     = Logger.Logger("stepper.log")
    power   = WebPower.WebPower(log)
    control = StepperControl.StepperControl(logger=log) 
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
    cmd={
        "boot":        {"func": BootStepper, "args":[str]},
        "reboot":      {"func": PowerCycle, "args":[]},
        "motorenable": {"func": control.motor_enable, "args":[int]},
        "alarmclear":  {"func": control.clear_alarm, "args":[]},
        "shutdown":    {"func": (), "args":[]},
        "exit":        {"func": sys.exit, "args":[]},
        "moverel":     {"func": control.move_relative, "args":[float]},
        "moveabs":     {"func": control.move_absolute, "args":[float]},
        "setres":      {"func": control.set_steps_per_rotation, "args":[int]},
        "echopos":     {"func": control.output_targeted_position, "args":[]},
        "cmd":         {"func": control.send, "args":[str]},
        "cmdout":      {"func": control.send_get_out, "args":[str]},
        "out":         {"func": control.get_output, "args":[]},
        "bootoverride":{},
        "calibrate":   {"func": control.calibrate, "args":[float]},
        "getlim":      {"func": control.print_limits, "args":[]},
        "setlim":      {"func": control.set_limits, "args":[float, float]},
        #"testfunc":   {"func": testfunc, "args":[str, float, int]}
        #"testloadfromlog":   {"func": control.load_from_log, "args":[]},
    }

    
    def cmd_parse(in_cmd: str):
        spl = in_cmd.split(" ")
        if spl[0] == "bootoverride":
            global booted
            booted=True
            return
        if spl[0] != "boot" and not booted:
            print("Please boot!")
            return
        if spl[0] in cmd.keys():
            t_cmd = cmd[spl[0]]
            t_args = spl[1:]
            if len(t_cmd["args"]) != len(t_args):
                a = len(t_cmd["args"])
                print(f"Wrong number of arguments, expected {a}, got {len(t_args)}")
                return
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



