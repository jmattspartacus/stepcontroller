import serial, time
import Logger
import WebPower

class StepperControl:
    name = "" 
    logger = Logger.Logger 
    power = WebPower.WebPower 
    actuatorType = None
    booted = False
    enabled = True
    stepsPerRot=1
    connect_timeout=1
    gear_ratio=1
    port=""
    model_code=""
    accumulated_error = 0
    previous_move     = 0
    targetedPosition=0        

    def __init__(self,
        name: str,
        logger: Logger.Logger,
        power: WebPower.WebPower,
        stepsPerRot: int = 200, 
        connect_timeout: float = 2.0, 
        port: str = "/dev/ttyS4",
        gear_ratio: float = 14.0 / 1.0,
        model_code: str ="ff0716"): 
        self.name = name
        self.logger = logger
        self.power = power
        self.actuatorType = None
        self.booted = False
        self.enabled = True
        self.stepsPerRot=stepsPerRot
        self.connect_timeout=connect_timeout
        self.gear_ratio=gear_ratio
        self.port=port
        self.model_code=model_code
        self.accumulated_error = 0
        self.previous_move     = 0
        self.targetedPosition=0        
        self.motor_init()
        
        
    def first_boot(self, webpower):
        # power cycle to make sure the motor is ready to configure
        print("Powering off webpower switch")
        if not webpower.PowerOff():
            print("PowerOff failed!")
            return
        print("Sleeping for 1 second")
        time.sleep(1)
        if not webpower.PowerOn():
            print("PowerOff failed!")
            return
        print("Powering on switch")
        # command must be received at least 2 milliseconds after power is on
        # but not more than 2 seconds, so we wait just long enough
        time.sleep(0.5)
        # enable SCL mode
        self.send("00")
        response = self.get_output()
        try:
            self.send("PR1")
            ret=self.send_get_out("SSFOO", ret=True)
            if ("FOO" not in ret.strip()):
                print("Motor did not acknowledge being booted in scl mode!")
                print(ret)
                return
        except serial.SerialTimeoutException as e:
            print(f"Attempting to get FOO reply from motor threw exception:\n{e}")
            return
        except serial.SerialException as e:
            print(f"Threw an exception in PySerial:\n{e}")
            return
        except Exception as e:
            print(f"Unhandled exception!\n{e}")
            return

        # enable Power Mode 2 to ensure that the motor doesn't auto detect connections
        # as this causes an unclearable alarm state
        self.send("PM2")
        # removes the hardware drive motion limits, from the factory, the lower and
        # upper values are set to the same thing, and so it causes an alarm when trying to
        # move for the first time
        if (self.actuatorType=="ROT"):
            self.send("DL3")
        elif (self.actuatorType=="LIN"):
            self.send("DL2")
        else:
            print("Invalid actuator type for initial boot!")
        # Configure the protocol to make sure that we're not getting ack/nack, etc back
        # when trying to check for boot
        self.send("PR1")
        # set to point to point command mode
        self.send("CM21")
        # set acceleration rate to 10 rev/sec/sec
        self.send("AC10")
        # set deceleration rate to 10 rev/sec/sec
        self.send("DE10")
        # Save all parameters for the next time we turn on the motor
        self.send("SA")
        # set the position that the motor thinks it's at to zero because otherwise we 
        # will trigger errors in the script with movement
        self.send("SP0")

        if not self.check_connect():
            print("Failed to do first boot, please check that\n\tThe controller is powered\n\tThe serial port is correct\n\tThe webpower switch port is correct\n\tThe webpower switch is turned on\n\tThe webpower switch script is configured correctly!")
            return False

        self.is_motor_on()
        return True

    def boot(self):
        self.power.PowerOn()
        time.sleep(3)
        self.check_connect()
        self.load_from_log()
        if (self.booted):
            self.is_motor_on()
  
    def powerOff(self):
       self.power.PowerOff() 
       self.booted = False
        
    def check_connect(self):
        try:
            ret=self.send_get_out("SSFOO", ret=True)
            if (ret.strip()=="FOO"):
                self.booted = True
                return True
            else:
                self.booted = False
                return False
        except:
            self.booted = False
            print(f"Serial connection is not open, check that your port is valid!")

    # Initialization parameters. Note the serial port and baud rate of your project
    # may vary. Our default baud rate is 9600
    def motor_init(self) -> None:
        ser=serial.Serial()
        ser.port = self.port
        ser.baudrate = 9600
        ser.bytesize = serial.EIGHTBITS
        ser.parity = serial.PARITY_NONE
        ser.stopbits = serial.STOPBITS_ONE
        ser.timeout=1.0 
        ser.xonxoff = False
        ser.rtscts = False
        ser.dsrdtr = False
        ser.writeTimeout = 0
        self.ser = ser
        try:
            self.ser.open()
        except Exception as e:
            print(f"Failed to initialize serial connection, check that the port '{self.port}' exists and is valid")

        #self.make_log_entry()
            

    # When we send a serial command, the program will check and print
    # the response given by the drive.
    def send(self, command) -> None:
        if self.ser.isOpen():
            try:
                self.ser.write((command+'\r').encode())
            except Exception as e1:
                print ("Error Communicating...: " + str(e1))
            self.flush_input()

    def get_output(self, ret= False ):
        response = self.ser.read(15)
        #print(response)
        try:
            text = response.decode()
            if ret:
                self.flush()
                return text
            if len(text) > 0:
                print (text)
                self.flush()
            
        except:
            if ret:
                self.flush()
                return response.hex()
            else:
                self.flush()
                print(response.hex())

    def send_get_out(self, command, ret=False):
        self.send(command)
        return self.get_output(ret=ret)

    def motor_setup(self):
            """
            Setup initial motor parameters, also resets alarm
            """
            self.flush()
            self.send('IFD') # Sets the format of drive responses to decimal
            self.send('SP0') # Sets the starting position at 0

    def set_steps_per_rotation(self, steps: int) -> None:
        if type(steps) is not int:
            print(type(steps), steps)
            print("Steps must be an int!")
            return

        if steps < 200:
            print("Steps must be greater than 200")
            return

        sub = self.get_closest_value_in_steps_range(steps)
        self.send('MR{}'.format(sub[0]))
        self.stepsPerRot = sub[1] 
        #print("Set resolution to {} steps per rev, gear ratio {}, total steps per rev {}".format(self.stepsPerRot, self.gear_ratio, self.stepsPerRot * self.gear_ratio))

    def get_closest_value_in_steps_range(self, val: int) -> int:
        table=[
            200, 400, 1000, 2000, 5000, 10000, 12800, 18000, 20000,
            21600, 25000, 25400, 36000, 50000, 50800
        ]
        t_ret = 0
        diff = abs(val - 200)
        for i in range(len(table)):
            if abs(table[i] - val) < diff:
                t_ret = i
        t_ret = 3 if t_ret == 2 else t_ret
        return t_ret, table[t_ret]

    def flush(self):
        self.flush_input()
        self.flush_output()

    def flush_input(self):
        self.ser.flushInput()

    def flush_output(self):
        self.ser.flushOutput()

    def clear_alarm(self):
        self.send("AR")

    def motor_enable(self, enable=True):
        if enable == 1:
            print("Set motor enable true")
            self.send("ME")
            self.enabled = True 
        elif enable == 0:
            print("Set motor enable false")
            self.send("MD")
            self.enabled = False
    
    def get_status(self):
        ret=self.send_get_out("SC", ret=True)
        ret = int(ret[3:])
        ret = int(bin(ret).replace("0b", ""))
        ret = "%016i"%(ret)
        print(ret)
        true_strings = ["Motor Enabled and in position",
                        "Sampling",
                        "Drive Fault (check Alarm Code)",
                        "In Position, only valid on servo and StepSERVO drives",
                        "Moving",
                        "Jogging",
                        "Stopping",
                        "Waiting",
                        "Saving",
                        "Alarm present (check Alarm Code)",
                        "Homing",
                        "Waiting",
                        "Wizard running",
                        "Checking encoder",
                        "Q Program is running",
                        "Initializing"]
        for i in range(0,16):
            if ret[i]=="1":
                print(true_strings[15-i])

    def validate_position(self) -> bool: 
        actualPos = int(self.send_get_out("SP", True)[3:])
        if (self.targetedPosition != actualPos):
            print("Severe error! Actuator may be in different position than we think!")
            print(self.targetedPosition, actualPos) 
            return False
        return True

    def is_motor_on(self) -> bool:
        status = int(self.send_get_out("SC", ret=True)[3:])
        if status % 2 != 1:
            print("Motor is not enabled!")
        self.enabled = status % 2
        return status % 2 == 1
        
    def get_alarm(self):
        ret=self.send_get_out("AL", ret=True)
        ret = int(ret[3:])
        ret = int(bin(ret).replace("0b", ""))
        ret = "%016i"%(ret)
        print(ret)
        true_strings = ["Position Limit",
                        "CCW Limit",
                        "CW Limit",
                        "Over Temp",
                        "Internal Voltage",
                        "Over Voltage",
                        "Under Voltage",
                        "Over Current",
                        "Open Motor Winding",
                        "Bad Encoder",
                        "Comm Error",
                        "Bad Flash",
                        "No Move",
                        "",
                        "Blank Q Segment",
                        ""]

        if (int(ret) == 0):
            print("No alarm")
        else:
            for i in range(0,16):
                if ret[i]=="1":
                    print(true_strings[15-i])


    def move_relative(self):
        return

    def move_absolute(self):
        return

    def angle_to_steps(self):
        return

    def steps_to_angle(self):
        return

    def steps_to_time(self):
        return

    def get_angle(self):
        return

    def get_position(self):
        return

    def calibrate(self, calibrate_position: float, dummy: float) -> None:
        return

    def angle_in_valid_range(self, angle: float) -> bool: 
        return

    def get_diff_in_requested_position(self, steps: int, amt: float) -> float:
        return

    def make_log_entry(self):
        return

    def load_from_log(self):
        return

    def print_limits(self):
        return

    def set_limits(self, low: float, high: float) -> None:
        return
            
    def print_log_headers(self) -> None:
        return

    def sstat(self):
        return

    def stat(self):
        return

class RotationControl(StepperControl):
    def __init__(self,
        name: str,
        logger: Logger.Logger,
        power: WebPower.WebPower,
        stepsPerRot: int = 200,
        connect_timeout: float = 60,
        port: str = "/dev/ttyS4",
        gear_ratio: float = 14.0 / 1.0,
        model_code: str ="ff0716"):
        self.actuatorType = "ROT"
        self.targetedAngle=0
        self.lowerLimit = 0
        self.upperLimit = 90
        super().__init__(name, logger, power, stepsPerRot, connect_timeout, port, gear_ratio, model_code)
    
    def move_relative(self, deg: float) -> None:
        if not self.angle_in_valid_range(deg + self.targetedAngle):
            print("Move would put it out of range!")
            return
    
        if (not self.validate_position() or not self.is_motor_on()):
            print("Move not executed!")
            return
    
        t_steps = self.angle_to_steps(deg)
        self.targetedAngle  += self.steps_to_angle(t_steps)
        self.targetedPosition += t_steps
    
        print("Diff in move {:.5f} deg".format(self.get_diff_in_requested_position(t_steps, deg)))
        # we want the timing predictable
        self.send("VE1")
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)
        self.previous_move = t_steps

        print("Moving by {:.5f} degrees".format(self.steps_to_angle(t_steps)))
        time.sleep(0.2)
        print("Moving...")
        while True:
            ret=self.send_get_out("SC", True)
            try:
                print(".", end="", flush=True)
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break

        self.make_log_entry()
        print(" Move Finished")
        
        self.validate_position()

    def move(self, target: str):
        try:
            ang = float(target)
        except:
            print("Please specify angle!")
            return
 
        self.move_absolute(ang)

    def move_absolute(self, target: float) -> None:
        if not self.angle_in_valid_range(target):
            print("Move would put it out of range! Limits: ({}, {}), Given:{}".format(self.lowerLimit, self.upperLimit, target))
            return

        if (not self.validate_position() or not self.is_motor_on()):
            print("Move not executed!")
            return

        diff = target - self.targetedAngle
        t_steps = self.angle_to_steps(diff)
        print("Diff in move {:.5f} deg".format(self.get_diff_in_requested_position(t_steps, diff)))

        self.targetedAngle += self.steps_to_angle(t_steps) 
        self.targetedPosition += t_steps

        self.send("VE1")
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)
        self.previous_move = t_steps

        print("Moving to {:.5f} deg".format(self.targetedAngle))
        time.sleep(0.2)
        print("Moving...", end="", flush=True)
        while True:
            ret=self.send_get_out("SC", True)
            try:
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                print(".", end="", flush=True)
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break

        self.make_log_entry()
        print(" Move Finished")

        self.validate_position()

    def angle_to_steps(self, angle_deg: float) -> int:
        return int((angle_deg / 360) * self.stepsPerRot * self.gear_ratio)

    def steps_to_angle(self, steps: int) -> float:
        return steps * (360 / (self.stepsPerRot * self.gear_ratio))

    def steps_to_time(self, steps: int) -> float:
        # assumes VE1 has been called
        return abs(1.1 * float(steps) / float(self.stepsPerRot))

    def get_angle(self):
        print(self.targetedAngle)
        return self.targetedAngle

    def get_mm(self):
        print("Only for linear actuators!")

    def get_position(self):
        print(self.targetedPosition)
        self.send_get_out("SP")

    def calibrate(self, calibrate_position: float, dummy: float) -> None:
        if not self.angle_in_valid_range(calibrate_position):
            print("Calibration must be inside the limits!")
            return
        print(f"Setting current position to {calibrate_position} degrees")
        self.targetedAngle = calibrate_position
        self.targetedPosition = 0
        self.send("SP0")

    def angle_in_valid_range(self, angle: float) -> bool: 
        return (
            (angle <= self.upperLimit and angle >= self.lowerLimit) or
            abs(self.upperLimit - self.lowerLimit) < 1e-6
        )

    def get_diff_in_requested_position(self, steps: int, amt: float) -> float:
        return self.steps_to_angle(steps) - amt

    def make_log_entry(self):
        self.logger.write("{:.5f}, {}, {}, {:.5f}, {}, {:.5f}, {:.5f}, {}".format(
            self.targetedAngle, 
            self.targetedPosition,
            self.stepsPerRot,
            self.accumulated_error,
            self.previous_move, 
            self.lowerLimit,
            self.upperLimit,
            self.port
        ))

    def load_from_log(self):
        last = self.logger.get_last()
        if last is not None:
            logname = self.logger.name
            date, ang, pos, res, err, prev, low, high, port = last.split(",")
            print(f"\033[2;39mLoading log \033[0m{logname}\033[2;39m --- date: \033[0m{date}\033[2;39m, angle: \033[0m{ang}\033[2;39m degrees, Limits: [\033[0m{low}\033[2;39m, \033[0m{high}\033[2;39m] deg\033[0m")
            self.targetedAngle = float(ang)
            self.targetedPosition = int(pos)
            self.set_steps_per_rotation(int(res))
            self.accumulated_error = float(err)
            self.previous_move = int(prev)
            self.set_limits(float(low), float(high))
            if (self.booted):
                self.send("SP"+str(int(pos)))
        else:
            if (self.booted):
                self.send("SP0")
            self.set_steps_per_rotation(2000)

    def print_limits(self):
        print(f"Limits: [{self.lowerLimit}, {self.upperLimit}]")

    def set_limits(self, low: float, high: float) -> None:
        if abs(low - high) < 1e-6:
            print("Limits are equal, this removes limits on movement!")
        self.lowerLimit = min(low, high)
        self.upperLimit = max(low, high)
            
    def print_log_headers(self) -> None:
        self.logger.write_header("date, angle(deg), pos(steps), res(spr), err(deg), prev(step), low(deg), high(deg, port")

    def stat_header(self):
        print("%10s %10s %10s %10s %10s     %10s"%("Name","Power","Serial","Booted","Motor","Position"))

    def sstat(self, emphasis=False):
        if (self.power.CheckStatus()):
            pStr = "\033[1;32mON\033[0m"
        else:
            pStr = "\033[1;31mOFF\033[0m"

        if (self.ser.isOpen()):
            serStr = "\033[1;32mOPEN\033[0m"
        else:
            serStr = "\033[1;31mCLOSED\033[0m"

        self.check_connect()
        if (self.booted):
            comStr = "\033[1;32mYES\033[0m"
        else:
            comStr = "\033[1;31mNO\033[0m"
            
        if (self.booted):
            enabled = self.is_motor_on()
            if (enabled):
                enStr = "\033[1;32mENABLED\033[0m"
            else:
                enStr = "\033[1;31mDISABLED\033[0m"
        else:
            enStr = "\033[2;39mUNKNOWN\033[0m"

        ang = self.targetedAngle
  
        if (emphasis):
            if (self.booted):
                nameStr = "> \033[1;32m%s\033[0m"%(self.name)
            else:
                nameStr = "> \033[1;36m%s\033[0m"%(self.name)
        else:
            nameStr = "\033[0;39m%s\033[0m"%(self.name)

        print("%21s %21s %21s %21s %21s      %5.2f deg"%(nameStr, pStr, serStr, comStr, enStr, ang))

    def stat(self, emphasis=False):
        if (self.power.CheckStatus()):
            pStr = "\033[1;32mON\033[0m"
        else:
            pStr = "\033[1;31mOFF\033[0m"

        if (self.ser.isOpen()):
            serStr = "\033[1;32mOPEN\033[0m"
        else:
            serStr = "\033[1;31mCLOSED\033[0m"

        if (self.booted):
            comStr = "\033[1;32mYES\033[0m"
        else:
            comStr = "\033[1;31mNO\033[0m"
            
        if (self.booted):
            enabled = self.enabled
            if (enabled):
                enStr = "\033[1;32mENABLED\033[0m"
            else:
                enStr = "\033[1;31mDISABLED\033[0m"
        else:
            enStr = "\033[2;39mUNKNOWN\033[0m"

        ang = self.targetedAngle

        if (emphasis):
            if (self.booted):
                nameStr = "> \033[1;32m%s\033[0m"%(self.name)
            else:
                nameStr = "> \033[1;36m%s\033[0m"%(self.name)
        else:
            nameStr = "\033[0;39m%s\033[0m"%(self.name)

        print("%21s %21s %21s %21s %21s      %5.2f deg"%(nameStr, pStr, serStr, comStr, enStr, ang))
        

class LinearControl(StepperControl):
    def __init__(self,
        name: str,
        logger: Logger.Logger,
        power: WebPower.WebPower,
        stepsPerRot: int = 200,
        connect_timeout: float = 60,
        port: str = "/dev/ttyS4",
        gear_ratio: float = 14.0 / 1.0,
        model_code: str ="ff0716"):
        self.actuatorType = "LIN"
        self.targeted_mm=0
        self.lowerLimit = 0 
        self.upperLimit = 150
        self.stepsPerMM = 2000
        super().__init__(name, logger, power, stepsPerRot, connect_timeout, port, gear_ratio, model_code)
    
    def steps_to_mm(self, steps: int):
        return steps / self.stepsPerMM

    def move_relative(self, pos: float) -> None:
        if not self.pos_in_valid_range(pos + self.targeted_mm):
            print("Move would put it out of range!")
            return
    
        if (not self.validate_position() or not self.is_motor_on()):
            print("Move not executed!")
            return
    
        t_steps = self.mm_to_steps(pos)
        self.targeted_mm  += self.steps_to_mm(t_steps)
        self.targetedPosition += t_steps
    
        print("Diff in move {:.5f} mm".format(self.get_diff_in_requested_position(t_steps, pos)))
        # we want the timing predictable
        self.send("VE10")
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)
        self.previous_move = t_steps

        print("Moving by {:.5f} mm".format(self.steps_to_mm(t_steps)))
        time.sleep(0.2)
        print("Moving...", end="", flush=True)
        while True:
            ret=self.send_get_out("SC", True)
            try:
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                print(".", end="", flush=True)
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break

        self.make_log_entry()
        print(" Move Finished")
        
        self.validate_position()

    def move_absolute(self, target: float) -> None:
        if not self.mm_in_valid_range(target):
            print("Move would put it out of range! Limits: ({}, {}), Given:{}".format(self.lowerLimit, self.upperLimit, target))
            return

        if (not self.validate_position() or not self.is_motor_on()):
            print("Move not executed!")
            return

        diff = target - self.targeted_mm
        t_steps = self.mm_to_steps(diff)
        print("Diff in move {:.5f} mm".format(self.get_diff_in_requested_position(t_steps, diff)))

        self.targeted_mm += self.steps_to_mm(t_steps) 
        self.targetedPosition += t_steps

        self.send("VE10")
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)
        self.previous_move = t_steps

        print("Moving to {:.5f} mm".format(self.targeted_mm))
        time.sleep(0.2)
        print("Moving...", end="", flush=True)
        while True:
            ret=self.send_get_out("SC", True)
            try:
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                print(".", end="", flush=True)
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break

        self.make_log_entry()
        print(" Move Finished")

        self.validate_position()

    def mm_to_steps(self, mm: float) -> int:
        return int( float(mm) * float(self.stepsPerMM) )

    def steps_to_angle(self, steps: int) -> float:
        return steps * (1./ (self.stepsPerMM ))

    def steps_to_time(self, steps: int) -> float:
        # assumes VE10 has been called
        return abs(10.0 * float(steps) / float(self.stepsPerMM))

    def get_mm(self):
        print(self.targeted_mm)
        return self.targeted_mm

    def get_angle(self):
        print("Only for rotational actuators!")

    def get_position(self):
        self.send_get_out("SP")

    def calibrate(self, mm_low: float, mm_high: float) -> None:
        #make sure limit switches are enabled
        self.send('DL2')
        t_steps = -100000000
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)

        time.sleep(0.2)
        print("Moving...", end="", flush=True)
        while True:
            ret=self.send_get_out("SC", True)
            try:
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                print(".", end="", flush=True)
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break
        print("")

        self.send("SP0")
        time.sleep(1)

        self.send("VE10")
        t_steps = 100000000
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)

        print("Moving...", end="", flush=True)
        time.sleep(0.2)
        while True:
            ret=self.send_get_out("SC", True)
            try:
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                print(".", end="", flush=True)
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break
        print("")

        final_pos=int(self.send_get_out("SP", True)[3:])
        self.stepsPerMM = final_pos/(mm_high-mm_low);
        self.targeted_mm = mm_high 
        self.targetedPosition = final_pos 
        self.lowerLimit = mm_low + 0.5 
        self.upperLimit = mm_high - 0.5 
        self.move_absolute(self.upperLimit)
        self.clear_alarm()
    
    def move(self, pos: str):
        if (pos == "IN"):
            self.move_absolute(self.upperLimit)
        elif (pos == "OUT"):
            self.move_absolute(self.lowerLimit)
        else:
            try:
                pos = float(pos)
            except:
                print("Invalid argument! IN/OUT or position (mm)")

            self.move_absolute(pos)

    def mm_in_valid_range(self, mm: float) -> bool: 
        return (
            (mm <= self.upperLimit and mm >= self.lowerLimit) or
            abs(self.upperLimit - self.lowerLimit) < 1e-6
        )

    def get_diff_in_requested_position(self, steps: int, amt: float) -> float:
        return self.steps_to_mm(steps) - amt

    def make_log_entry(self):
        self.logger.write("{:.5f}, {}, {}, {}, {:.5f}, {}, {:.5f}, {:.5f}, {}".format(
            self.targeted_mm, 
            self.targetedPosition,
            self.stepsPerRot,
            self.stepsPerMM,
            self.accumulated_error,
            self.previous_move, 
            self.lowerLimit,
            self.upperLimit,
            self.port
        ))

    def load_from_log(self):
        last = self.logger.get_last()
        if last is not None:
            logname = self.logger.name
            date, mm, pos, res, spmm, err, prev, low, high, port = last.split(",")
            print(f"\033[2;39mLoading log \033[0m{logname}\033[2;39m --- date: \033[0m{date}\033[2;39m, position: \033[0m{mm}\033[2;39m mm, Limits: [\033[0m{low}\033[2;39m, \033[0m{high}\033[2;39m] deg\033[0m")
            self.targeted_mm = float(mm)
            self.targetedPosition = int(pos)
            self.set_steps_per_rotation(int(res))
            self.accumulated_error = float(err)
            self.previous_move = int(prev)
            self.set_limits(float(low), float(high))
            self.stepsPerMM = float(spmm)
            if (self.booted):
                self.send("SP"+str(int(pos)))
        else:
            if (self.booted):
                self.send("SP0")
            self.set_steps_per_rotation(2000)

    def print_limits(self):
        print(f"Limits: [{self.lowerLimit}, {self.upperLimit}]")

    def set_limits(self, low: float, high: float) -> None:
        if abs(low - high) < 1e-6:
            print("Limits are equal, this removes limits on movement!")
        self.lowerLimit = min(low, high)
        self.upperLimit = max(low, high)
            
    def print_log_headers(self) -> None:
        self.logger.write_header("date, pos(mm), pos(steps), res(spmm), err(deg), prev(step), low(deg), high(deg, port")

    def stat_header(self):
        print("%10s %10s %10s %10s %10s     %10s"%("Name","Power","Serial","Booted","Motor","Position"))

    def sstat(self, emphasis=False):
        if (self.power.CheckStatus()):
            pStr = "\033[1;32mON\033[0m"
        else:
            pStr = "\033[1;31mOFF\033[0m"

        if (self.ser.isOpen()):
            serStr = "\033[1;32mOPEN\033[0m"
        else:
            serStr = "\033[1;31mCLOSED\033[0m"

        self.check_connect()
        if (self.booted):
            comStr = "\033[1;32mYES\033[0m"
        else:
            comStr = "\033[1;31mNO\033[0m"
            
        if (self.booted):
            enabled = self.is_motor_on()
            if (enabled):
                enStr = "\033[1;32mENABLED\033[0m"
            else:
                enStr = "\033[1;31mDISABLED\033[0m"
        else:
            enStr = "\033[2;39mUNKNOWN\033[0m"

        unitStr = ""
        if (abs(self.targeted_mm - self.upperLimit) < 1e-2):
            posStr = "\033[1;32mIN\033[0m"
        elif (abs(self.targeted_mm - self.lowerLimit) < 1e-2):
            posStr = "\033[1;31mOUT\033[0m"
        else:
            posStr = "\033[0;39m%5.2f\033[0m"%(self.targeted_mm)
            unitStr = "mm"

        if (emphasis):
            if (self.booted):
                nameStr = "> \033[1;32m%s\033[0m"%(self.name)
            else:
                nameStr = "> \033[1;36m%s\033[0m"%(self.name)
        else:
            nameStr = "\033[0;39m%s\033[0m"%(self.name)

        print("%21s %21s %21s %21s %21s %21s %s"%(nameStr, pStr, serStr, comStr, enStr, posStr, unitStr))

    def stat(self, emphasis=False):
        if (self.power.CheckStatus()):
            pStr = "\033[1;32mON\033[0m"
        else:
            pStr = "\033[1;31mOFF\033[0m"

        if (self.ser.isOpen()):
            serStr = "\033[1;32mOPEN\033[0m"
        else:
            serStr = "\033[1;31mCLOSED\033[0m"

        if (self.booted):
            comStr = "\033[1;32mYES\033[0m"
        else:
            comStr = "\033[1;31mNO\033[0m"
            
        if (self.booted):
            enabled = self.enabled
            if (enabled):
                enStr = "\033[1;32mENABLED\033[0m"
            else:
                enStr = "\033[1;31mDISABLED\033[0m"
        else:
            enStr = "\033[2;39mUNKNOWN\033[0m"

        unitStr = ""
        if (abs(self.targeted_mm - self.upperLimit) < 1e-2):
            posStr = "\033[1;32mIN\033[0m"
        elif (abs(self.targeted_mm - self.lowerLimit) < 1e-2):
            posStr = "\033[1;31mOUT\033[0m"
        else:
            unitStr = "mm"
            posStr = "\033[0;39m%5.2f\033[0m"%(self.targeted_mm)

        if (emphasis):
            if (self.booted):
                nameStr = "> \033[1;32m%s\033[0m"%(self.name)
            else:
                nameStr = "> \033[1;36m%s\033[0m"%(self.name)
        else:
            nameStr = "\033[0;39m%s\033[0m"%(self.name)

        print("%21s %21s %21s %21s %21s %21s %s"%(nameStr, pStr, serStr, comStr, enStr, posStr, unitStr))
        
