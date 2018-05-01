#!/usr/bin/python

import datetime;
import commands
import pickle
import time

def WhichDevicesAreCurrentlyPresent():
  CMD = "nmap 192.168.86.0-255 -sn | grep \"Nmap scan report for\""
  return_code, stdout = commands.getstatusoutput(CMD)
  present_devices = set()
  for line in stdout.split("\n"):
    present_devices.add(line.split()[4])
  return present_devices


def main():
  while True:
    # Open up the log file so we can append it with the next pickled set
    with open('log.p', 'ab') as log_file:
      # Determine which devices are present on the wifi
      present_devices = WhichDevicesAreCurrentlyPresent()

      # Check what time this reading was collected at
      timestamp = datetime.datetime.now()

      # Print the data to stdout for debugging
      print timestamp
      print present_devices
      print

      # Store a pickled copy of that set in the log
      pickle.dump((timestamp, present_devices), log_file)

    # Pause before the next reading
    time.sleep(10)

main()
