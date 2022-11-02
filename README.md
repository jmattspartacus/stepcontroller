# stepcontroller
This script is intended to control the stepper motors used at FRIB FDSi using UHV MASC stepper controllers. 

## Requirements
* Python 3 must be installed
* The python package pySerial must be installed
* A web power switch, with the appropriate shell scripts must be present
* The UHV MASC controller must be plugged into the WebPower switch and must have the power button in the on position. The WebPower switch is used to turn on/off power to the controller.

## Usage
Using your shell of choice from the root directory of the repo, do
```python3 Stepper.py```
this will launch a command line interface that allows you to control the stepper motor using a set of predefined commands. 

To get that list of commands, use ```help```, this will give a list of the commands, for more information about a specific command, you can do ```help commandname``` 

For example, when you first run the script, the controller will likely be off, so you'll do `boot` and then you can move the output shaft to a specific location using something like `moveabs 30`

