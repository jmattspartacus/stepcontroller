# stepcontroller
This script was written to control the stepper motors used at FRIB FDSi using UHV MASC stepper controllers. It may be compatible with other controllers that use Applied Motion Products SCL Commands over RS232 and RS485 connections as well. RS485 mode is untested.

## Requirements
* Python 3 must be installed
* The python package pySerial must be installed
* A web power switch, with the appropriate shell scripts must be present
* The UHV MASC controller must be plugged into the WebPower switch and must have the power button in the on position. The WebPower switch is used to turn on/off power to the controller.
* The UHV MASC controller must be connected with a Serial connector to the controlling computer. The USB to serial cable included with the controller does not allow for two way communication, as the replies from the motor are not forwarded correctly to the Serial bus.

## Using for the first time

Using your shell of choice from the root directory of the repo, do
```python3 Stepper.py```

This will generate a default config file with invalid presets for a profile. The actual values in your config will depend on your machine's configuration. For example, a configuration used for the FRIB FDSi is
```
profile, port,       webpower_port, log_file
FP2,     /dev/ttyS4, 3,             stepper_FP2.log
```

After configuring your profile, and starting the script, it will detect that the log file does not exist, and initialize the controller for use with the script. Any other configuration is done through the script and stored in the log.

## Usage
Using your shell of choice from the root directory of the repo, do
```python3 Stepper.py profilename```
this will launch a command line interface that allows you to control the stepper motor using a set of predefined commands. 

To get that list of commands, use ```help```, this will give a list of the commands, for more information about a specific command, you can do ```help commandname``` 

For example, when you first run the script, the controller will likely be off, so you'll do `boot` and then you can move the output shaft to a specific location using something like `moveabs 30`

## More Information

### The Log
The log is used to cache the location of the motor shaft, as well as software movement limits and a few other things. Do not edit this unless you know what you're doing, as it can cause error states that will be difficult to clear.

### Lock file
When the script is running, an empty file named profilename.lock is created and if the script exits in a manner other than using one of the exit commands, it will need to be deleted.

### Calibration
*Only do this if you're sure you need to*

When you are reasonably sure you know the angle that the output shaft of the motor is at, for instance +20 degrees, do
```calibrate 20```
