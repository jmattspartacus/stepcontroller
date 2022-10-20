import serial, time, serial.rs485
import Logger

class StepperControl:
    def __init__(self, 
        logger: Logger.Logger,
        stepsPerRot: int = 200, 
        connect_timeout: float = 60, 
        port: str = "/dev/ttyUSB0",
        gear_ratio: float = 14.0 / 1.0,
        model_code: str ="ff0716"):
        self.logger = logger
        self.stepsPerRot=stepsPerRot
        self.connect_timeout=connect_timeout
        self.gear_ratio=gear_ratio
        self.targetedPosition=0
        self.lowerLimit = 0
        self.upperLimit = 90
        self.port=port
        self.model_code=model_code
        self.accumulated_error = 0
        self.previous_move     = 0
        try:
            self.motor_init()
            self.ser.open()
        except Exception as e:
            print(e)
            raise e
        
        

    def try_connect(self):
        print("connecting")
        i = 0
        repeat = self.connect_timeout / 0.1
        while True:
            self.send_key()
            reply = self.get_output(ret=True, delay=0)
            if reply == self.model_code:
                break
            i+=1
            if i == repeat:
                raise Exception("Failed to initialize")
        print("connected")
        self.motor_setup()
        self.load_from_log()
    
    #def check_alive(self):
    #    self.send("SSFOO")
    #    test = self.get_output(ret=True)
    #    return test == "FOO"

    def reinit(self):
        try:
            self.try_connect()
            self.motor_setup()
        except Exception as e:
            raise e

    # Initialization parameters. Note the serial port and baud rate of your project
    # may vary. Our default baud rate is 9600
    def motor_init(self):
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
        #ser.rs485_mode = serial.rs485.RS485Settings(delay_before_rx=0.1, delay_before_tx=1e-3)
        self.ser = ser

    # When we send a serial command, the program will check and print
    # the response given by the drive.
    def send(self, command):
        if self.ser.isOpen():
            try:
                self.ser.write((command+'\r').encode())
            except Exception as e1:
                print ("Error Communicating...: " + str(e1))
            self.flush_input()

    def send_key(self):
        if self.ser.isOpen():
            try:
                self.ser.write("00".encode())
            except Exception as e1:
                print ("Error Communicating...: " + str(e1))
            self.flush_input()

    def send_get_out(self, command):
        self.send(command)
        self.get_output(delay=0)

    def motor_setup(self):
            """
            Setup initial motor parameters, also resets alarm
            """
            self.flush()
            self.send('IFD') # Sets the format of drive responses to decimal
            self.send('SP0') # Sets the starting position at 0

    def set_steps_per_rotation(self, steps: int) -> None:
        if type(steps) is int and steps >= 200:
            sub = self.get_closest_value_in_steps_range(steps)
            self.send('MR{}'.format(sub[0]))
            self.stepsPerRot = sub[1] 
            print("Set resolution to {} steps per rev, gear ratio {}, total steps per rev {}".format(self.stepsPerRot, self.gear_ratio, self.stepsPerRot * self.gear_ratio))
        else:
            print(type(steps), steps)
            print("Steps must be an int!")

    def get_closest_value_in_steps_range(self, val: int) -> int:
        table=[
            200, 400, 2000, 5000, 10000, 12800, 18000, 20000,
            21600, 25000, 25400, 36000, 50000, 50800
        ]
        t_ret = 0
        diff = abs(val - 200)
        for i in range(len(table)):
            if abs(table[i] - val) < diff:
                t_ret = i
        return t_ret, table[t_ret]



    def move_relative(self, deg: float) -> None:
        if not self.angle_in_valid_range(deg + self.targetedPosition):
            print("Move would put it out of range!")
            return

        t_steps = self.angle_to_steps(deg)
        self.targetedPosition  += self.steps_to_angle(t_steps)
    
        print("Diff in move {:.5f} deg".format(self.get_diff_in_requested_position(t_steps, deg)))
        # we want the timing predictable
        self.send("VE1")
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)
        self.previous_move = t_steps

        print("Moving by {:.5f} degrees".format(self.steps_to_angle(t_steps)))
        time.sleep(esttime)
        print("Move Finished")
        self.make_log_entry()
        

    def move_absolute(self, target: float) -> None:
        if not self.angle_in_valid_range(target):
            print("Move would put it out of range! Limits: ({}, {}), Given:{}".format(self.lowerLimit, self.upperLimit, target))
            return
        diff = target - self.targetedPosition
        t_steps = self.angle_to_steps(diff)
        print("Diff in move {:.5f} deg".format(self.get_diff_in_requested_position(t_steps, diff)))

        self.targetedPosition += self.steps_to_angle(t_steps) 
        self.send("VE1")
        self.send('FL{}'.format(t_steps))
        esttime = self.steps_to_time(t_steps)
        self.previous_move = t_steps

        print("Moving to {:.5f} deg".format(self.targetedPosition))
        time.sleep(esttime)
        print("Move Finished")
        self.make_log_entry()


    def angle_to_steps(self, angle_deg: float) -> int:
        return int((angle_deg / 360) * self.stepsPerRot * self.gear_ratio)

    def steps_to_angle(self, steps: int) -> float:
        return steps * (360 / (self.stepsPerRot * self.gear_ratio))

    def steps_to_time(self, steps: int) -> float:
        # assumes VE1 has been called
        return abs(1.1 * float(steps) / float(self.stepsPerRot))

    def get_output(self, ret= False, delay : float = 0.1):
        time.sleep(delay)
        response = self.ser.read(15)
        print(response)
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

    def flush(self):
        self.flush_input()
        self.flush_output()

    def flush_input(self):
        self.ser.flushInput()

    def flush_output(self):
        self.ser.flushOutput()

    def output_targeted_position(self):
        print(self.targetedPosition)

    def clear_alarm(self):
        self.send("AR")

    def motor_enable(self, enable=True):
        if enable:
            print("Set motor enable true")
            self.send("ME")
        else:
            print("Set motor enable false")
            self.send("MD")

    def make_log_entry(self):
        self.logger.write("{:.5f}, {}, {:.5f}, {}, {:.5f}, {:.5f}".format(
            self.targetedPosition, 
            self.stepsPerRot,
            self.accumulated_error,
            self.previous_move, 
            self.lowerLimit,
            self.upperLimit
        ))

    def calibrate(self, calibrate_position: float) -> None:
        if not self.angle_in_valid_range(calibrate_position):
            print("Calibration must be inside the limits!")
            return
        print(f"Setting current position to {calibrate_position} degrees")
        self.targetedPosition = calibrate_position

    def angle_in_valid_range(self, angle: float) -> bool: 
        return (
            (angle <= self.upperLimit and angle >= self.lowerLimit) or
            abs(self.upperLimit - self.lowerLimit) < 1e-6
        )

    def get_diff_in_requested_position(self, steps: int, amt: float) -> float:
        return self.steps_to_angle(steps) - amt

    def load_from_log(self):
        last = self.logger.get_last()
        if last is not None:
            date, pos, res, err, prev, low, high = last.split(", ")
            print(f"Loading position from log, date: {date}, position: {pos} deg, resolution: {res} spr, Limits: [{low}, {high}] deg")
            self.targetedPosition = float(pos)
            self.set_steps_per_rotation(int(res))
            self.accumulated_error = float(err)
            self.previous_move = int(prev)
            self.set_limits(low, high)
        else:
            self.set_steps_per_rotation(2000)

    def print_limits(self):
        print(f"Limits: [{self.lowerLimit}, {self.upperLimit}]")

    def set_limits(self, low: float, high: float) -> None:
        self.lowerLimit = min(low, high)
        self.upperLimit = max(low, high)