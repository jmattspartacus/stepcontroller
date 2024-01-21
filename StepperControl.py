import serial, time
import Logger

class StepperControl:
    def __init__(self, 
        logger: Logger.Logger,
        stepsPerRot: int = 200, 
        connect_timeout: float = 60, 
        port: str = "/dev/ttyS4",
        gear_ratio: float = 14.0 / 1.0,
        model_code: str ="ff0716"):
        self.logger = logger
        self.stepsPerRot=stepsPerRot
        self.connect_timeout=connect_timeout
        self.gear_ratio=gear_ratio
        self.targetedAngle=0
        self.targetedPosition=0
        self.lowerLimit = 0
        self.upperLimit = 90
        self.port=port
        self.model_code=model_code
        self.accumulated_error = 0
        self.previous_move     = 0
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
        time.sleep(0.05)
        # enable SCL mode
        self.send("00")
        try:
            ret=self.send_get_out("SSFOO", ret=True)
            if ("FOO" not in ret.strip()):
                print("Motor did not acknowledge being booted in scl mode!")
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
        self.send("DL3")
        # Configure the protocol to make sure that we're not getting ack/nack, etc back
        # when trying to check for boot
        self.send("PR1")
        # Save all parameters for the next time we turn on the motor
        self.send("SA")
        # set the position that the motor thinks it's at to zero because otherwise we 
        # will trigger errors in the script with movement
        self.send("SP0")
        if not self.check_connect():
            print("Failed to do first boot, please check that\n\tThe controller is powered\n\tThe serial port is correct\n\tThe webpower switch port is correct\n\tThe webpower switch is turned on\n\tThe webpower switch script is configured correctly!")
            return False
        return True

        
    def check_connect(self):
        try:
            ret=self.send_get_out("SSFOO", ret=True)
            if (ret.strip()=="FOO"):
                return True
            else:
                return False
        except:
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
        ser.timeout= 2.0
        ser.xonxoff = False
        ser.rtscts = False
        ser.dsrdtr = False
        ser.writeTimeout = 0
        self.ser = ser
        try:
            self.ser.open()
            self.make_log_entry()
        except Exception as e:
            print(f"Failed to initialize serial connection, check that the port '{self.port}' exists and is valid")
            

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
        print("Set resolution to {} steps per rev, gear ratio {}, total steps per rev {}".format(self.stepsPerRot, self.gear_ratio, self.stepsPerRot * self.gear_ratio))

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
        while True:
            ret=self.send_get_out("SC", True)
            try:
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                print("Moving...")
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break
 
        

        self.make_log_entry()
        print("Move Finished")
        
        self.validate_position()

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
        while True:
            ret=self.send_get_out("SC", True)
            try:
                ret = int(ret[3:])
                ret = int(bin(ret).replace("0b", ""))
                ret = "%016i"%(ret)
                print("Moving...")
                if ret[11] == "0":
                    break
            except:
                print("SC unexpected output, default to waiting")
                time.sleep(esttime)
                break

        self.make_log_entry()
        print("Move Finished")

        self.validate_position()

    def angle_to_steps(self, angle_deg: float) -> int:
        return int((angle_deg / 360) * self.stepsPerRot * self.gear_ratio)

    def steps_to_angle(self, steps: int) -> float:
        return steps * (360 / (self.stepsPerRot * self.gear_ratio))

    def steps_to_time(self, steps: int) -> float:
        # assumes VE1 has been called
        return abs(1.1 * float(steps) / float(self.stepsPerRot))


    def flush(self):
        self.flush_input()
        self.flush_output()

    def flush_input(self):
        self.ser.flushInput()

    def flush_output(self):
        self.ser.flushOutput()

    def get_angle(self):
        print(self.targetedAngle)

    def get_position(self):
        print(self.targetedPosition)
        self.send_get_out("SP")

    def clear_alarm(self):
        self.send("AR")

    def motor_enable(self, enable=True):
        if enable == 1:
            print("Set motor enable true")
            self.send("ME")
        elif enable == 0:
            print("Set motor enable false")
            self.send("MD")

    def calibrate(self, calibrate_position: float) -> None:
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
            date, ang, pos, res, err, prev, low, high, port = last.split(",")
            print(f"Loading position from log, date: {date}, position: {pos} steps, angle: {ang} degrees, resolution: {res} spr, Limits: [{low}, {high}] deg, port{port}")
            self.targetedAngle = float(ang)
            self.targetedPosition = int(pos)
            self.set_steps_per_rotation(int(res))
            self.accumulated_error = float(err)
            self.previous_move = int(prev)
            self.set_limits(float(low), float(high))
            self.send("SP"+str(int(pos)))
        else:
            self.send("SP0")
            self.set_steps_per_rotation(2000)

    def print_limits(self):
        print(f"Limits: [{self.lowerLimit}, {self.upperLimit}]")

    def set_limits(self, low: float, high: float) -> None:
        if abs(low - high) < 1e-6:
            print("Limits are equal, this removes limits on movement!")
        self.lowerLimit = min(low, high)
        self.upperLimit = max(low, high)
    
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
        if (self.targetedPosition != int(self.send_get_out("SP", True)[3:])):
            print("Severe error! Actuator may be in different position than we think!")
            return False
        return True

    def is_motor_on(self) -> bool:
        status = int(self.send_get_out("SC", ret=True)[3:])
        if status % 2 != 1:
            print("Motor is not enabled!")
        return status % 2 == 1
        
    def print_log_headers(self) -> None:
        self.logger.write_header("date, angle(deg), pos(steps), res(spr), err(deg), prev(step), low(deg), high(deg, port")

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

