#!/usr/bin/python

from subprocess import Popen, PIPE, STDOUT
import datetime
import pickle
import time
import os

import nmap

import known_hosts

FULL_SUBNET = "192.168.86.0/24"
NETWORK_INTERFACE="enp1s0"

DIR="/home/cmooney/code/wifi_presence_tracker"

def GetOwnInfo():
  try:
    with open('/sys/class/net/%s/address' % NETWORK_INTERFACE) as f:
      return ("127.0.0.1", f.readline()[:-1].upper())
  except:
    print "ERROR: Unable to determine own MAC address, using 00:11:00:11:00:11"
    return ("127.0.0.1", "00:11:00:11:00:11")


def WhichDevicesAreCurrentlyPresent():
  nm = nmap.PortScanner()
  nm.scan(FULL_SUBNET, arguments='-sP', sudo=True)

  present_hosts = set([GetOwnInfo()])
  for host in nm.all_hosts():
    if 'mac' in nm[host]['addresses']:
      mac  = nm[host]['addresses']['mac']
      ip  = nm[host]['addresses']['ipv4']
      present_hosts.add((ip, mac))

  return present_hosts


def main():
  # Open up the log file so we can append it with the next pickled set
  with open('%s/log.p' % DIR, 'ab') as log_file:
    # Determine which devices are present on the wifi
    present_devices = WhichDevicesAreCurrentlyPresent()
    present_macs = set([mac for ip, mac in present_devices])
    unknown_devices = set([(ip, mac) for ip, mac in present_devices if mac not in known_hosts.names])
    known_devices = present_devices.difference(unknown_devices)

    # Check what time this reading was collected at
    timestamp = datetime.datetime.now()

    # Print the data to stdout for debugging
    print "===================="
    print timestamp
    print

    print "Known Devices:"
    for ip, mac in sorted(list(known_devices), key=lambda x:known_hosts.names[x[1]]):
      print "\t%s%s%s   (ipv4: %s)" % (known_hosts.names[mac], " " * (35 - len(known_hosts.names[mac])),
                                      mac, ip)
    print

    # Store a pickled copy of that set in the log
    pickle.dump((timestamp, present_macs), log_file)

    # Collect and dump some debugging logs for any unknown hosts, to help figure out what they are
    if unknown_devices:
      print "Unknown Devices:"
      for ip, mac in unknown_devices:
        print "\t%s   (ipv4: %s)" % (mac, ip)
        # TODO: Add more debugging commands here to learn as much as possible about the device
        cmds = ['nmap %s' % ip]

        output = ""
        for i, cmd in enumerate(cmds):
          p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
          output += ("#" * 80) + "\n"
          output += "# %s\n" % cmd
          output += ("#" * 80) + "\n"
          output += p.stdout.read()

        filename = "%s/unknown_logs/%s" % (DIR, mac)
        mode = 'w'
        if os.path.exists(filename):
          mode = "a"
        with open(filename, mode) as f:
          if mode != "w":
            f.write("\n" + ("-" * 80) + "\n\n")
          f.write(output)
      print

main()
