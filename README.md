# **SecureLoc**

UWB  platform for indoor secure localization platform based on DecaWino nodes.

## **Hardware**

DecaWino chips are based on Decawave DWM1000 module driven by a Teensyduino 3.2.
More information on DecaWino here: https://wino.cc/decawino/

A pdf documentation is provided with detailed instruction on the hardware required, the setup and how to use this project.

## **Project Description**

DecaWino nodes can perform Time-of-Flight UWB ranging, with distance estimations reaching an accuracy around 20 cm.
The ranging protocols can be controlled though the DecaDuino library, which provides a powerful interface for fast and easy protoyping on DecaWino nodes (https://github.com/Hedwyn/DecaDuino)
The SecureLoc platform is based on anchors and mobile tags. The anchors are fixed nodes with known location that estimate their distance to the mobile tags; with at least three distances, the position of the mobile tags can be computed. The positions are displayed in real-time with Panda 3D. The data measured (distances, RSSI..) and calculated (positions) are logged into json files.
DecaWino nodes can be programmed indifferently as anchors or nodes. However, anchors should be plugged to a Raspberry Pi, that will send the data to the station running this program through MQTT protocol. The MQTT broker (mosquitto) can be run of the same station as this program.


Three modes are available for the localization engine:
* Normal: the positions are calculated and displayed in real-time. The user can quit at anytime by pressing 'q'.
* Measurements: the user should specify a set of reference points with their coordinates in rp.tab prior to using this mode. Once started, the localization engine with perform a fixed number of  position estimation for each reference point. After each serie of measurements, an audio signal is played and the user can move the tag to the next reference. Once all the reference points have been evaluated, the global accuracy of the localization engine can be evaluated (as the average euclidean distance to the real coordinates).
* Playback: allows replaying ranging logs previously recorded. Playback can be used for example to compare different localization algorithm on the same set of data. Playback is supported on both measurements and normal logs, however, using logs from normal mode is more recommanded given that in measurements mode the localization is turned off when the tag is moved from one reference point to another.

## **Running this project**
Follow first all the setup instructions provided in Documentation.pdf. Then simply run "python main.py" in SecureLoc repository.

## **Firmware**
The DecaWino nodes can be programmed with the Arduino IDE; the Arduino codes for different projects can be found in DecaWino > Arduino.
The platform has been switched to a custom compilation tool, so these programs, although functional, are deprecated.
The more recent projects for the localization platform are written in cpp and can be found in DecaWino > Deployment > Projects.
A compilation menu (DecaWino /Deployment/Compilation.py), provides features for fast and easy firmware deployment:
* Multiple compilations with unique ID generation
* Anchors deployment in a single command. This will generate the binary with a unique ID for every anchor from a single cpp file, send them by ftp to the RPI and trigger remote flashing of the DecaWino.If more than one DecaWino are plugged to a RPI, pressing manually the flashing button of the DecaWino node will be required as the bootloader does unfortunately not handle multiple USB devices.




*Keyboard controls*:
* q to quit
* Directional arrows for navigation


## **Contact**
baptiste.pestourie@lcis.grenoble-inp.fr
