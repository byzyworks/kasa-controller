#!/usr/bin/env python3

import math
import os
import re
import sys
from   threading import Thread
from   yaml      import Loader

def getThings():
    file   = os.path.join(os.path.dirname(os.path.realpath(__file__)), "things.yml")
    things = None

    # Load the things.yml file from the same directory as this script
    with open(file, "r") as f:
        things = Loader(f).get_data()
    
    return things['things']

def getScopes(things):
    scopes = { }

    # Re-order the things into scopes
    for thing in things:
        tags = thing['tags'].split(' ')
        for tag in tags:
            if tag not in scopes:
                scopes[tag] = [ ]
            scopes[tag].append(thing['host'])
    
    # Alphabetically sort the dictionary
    scopes = dict(sorted(scopes.items()))

    return scopes

def getHosts(things, scope):
    scopes = getScopes(things)

    # Define a custom scope from the intersection of the tags
    hosts = None
    for tag in scope:
        if tag in scopes:
            if hosts is None:
                hosts = scopes[tag]
            else:
                hosts = list(set(hosts) & set(scopes[tag]))
        else:
            print("Unknown tag: " + tag)
            sys.exit(1)
    
    return hosts

def getTypes(things):
    types = { }

    # Load the types from the things.yml file
    for thing in things:
        host = thing['host']
        if "bulb" in thing['tags']:
            types[host] = "bulb"
        elif "plug" in thing['tags']:
            types[host] = "plug"

    return types

def getPresets(conf):
    presets = { }

    # Load the presets from the things.yml file
    for thing in conf:
        host = thing['host']
        if "pset" in thing:
            presets[host] = thing['pset']

    return presets

def getState(host, type=None):
    # Builds the command to get the state of the system
    cmd = "kasa "
    if type is not None:
        cmd += "--type " + type + " "
    cmd += "--host " + host + " state"

    # Gets the state of the system, and returns it as a string
    state = os.popen(cmd).read()

    # If the state is empty, then the host is unreachable
    if state == None or state == "":
        print("Host unreachable: " + host)

    return state

def isOn(host, type=None):
    # Checks the state of the system
    state = getState(host, type)

    # Works for bulbs
    if "power=0.0" in state:
        return False
    
    # Works for plugs
    if "On since: None" in state:
        return False

    # Default to thinking it's on (hence, default action should be to toggle off)
    return True

def getValue(input, presets, host, key):
    # If the input doesn't start with an '@', then it's just a literal
    input = str(input)
    if not input.startswith('@'):
        return int(input)

    # Means the host doesn't have any presets
    if host not in presets:
        return None

    # Narrows down the presets to the host, and checks if the index is valid
    idx     = int(input[1:])
    presets = presets[host]
    if idx >= len(presets):
        return None

    # Narrows down the preset to the index represented, and checks if the key is valid
    preset = presets[idx]
    if key not in preset:
        return None
    
    # Returns the value of the key
    return preset[key]

def doCommand(command, arg, scope, hosts, types, presets):
    threads = [ ]

    # Runs through all the IoT devices in the selected scope
    for host in hosts:
        match command:
            # Turns on
            case "on":
                exec = "kasa --type " + types[host] + " --host " + host + " on"

            # Turns off
            case "off":
                exec = "kasa --type " + types[host] + " --host " + host + " off"

            # If on, turns off, and vice versa
            case "toggle":
                if isOn(host, types[host]):
                    exec = "kasa --type " + types[host] + " --host " + host + " off"
                else:
                    exec = "kasa --type " + types[host] + " --host " + host + " on"

            # Other commands that require an argument (this requires the scope to purely include bulbs)
            case _:
                if "bulb" not in scope:
                    print("Command not supported for this scope")
                    sys.exit(1)
                
                if arg is None:
                    print("A value is required for this command")
                    sys.exit(1)

                # Gets the value to set the command to, in case the value is a preset pointer
                value = getValue(arg, presets, host, command)

                match command:
                    # Changes the brightness
                    case "brightness":
                        exec = "kasa --type bulb --host " + host + " brightness " + str(value)
                    
                    # Changes the temperature (in Kelvin), referring to natural light-based color scheme
                    case "temperature":
                        exec = "kasa --type bulb --host " + host + " temperature " + str(value)

                    # Changes the color to a user-provided hue, referring to the degree value on an HSV color wheel
                    # Saturation is calculated based on a custom-made formula to avoid some colors appearing garrish
                    # A sine wave is used to calculate the saturation for a bi-directionally smooth transition
                    # Overall, saturation is minimal at 330 (pink) at 70%, and maximal at 150 (sage) at 100%
                    # The "value" part (brightness) is calculated from preset 0, i.e. the default brightness
                    case "color":
                        h = value
                        s = round(15 * math.sin((h + 300) * math.pi / 180) + 85)
                        v = int(getValue("@0", presets, host, "brightness"))

                        exec = "kasa --type bulb --host " + host + " hsv " + str(h) + " " + str(s) + " " + str(v)

                    # Changes the hue based on an HSV color wheel while maintaining the current saturation and brightness
                    # This requires a state call to get the current saturation and brightness
                    case "hue":
                        r = re.search(r"HSV\(hue=\d+, saturation=(\d+), value=(\d+)\)", getState(host, "bulb"))

                        h = value
                        s = int(r.group(1))
                        v = int(r.group(2))

                        exec = "kasa --type bulb --host " + host + " hsv " + str(h) + " " + str(s) + " " + str(v)

                    # Changes the saturation based on an HSV color wheel while maintaining the current hue and brightness
                    # This requires a state call to get the current hue and brightness
                    case "saturation":
                        r = re.search(r"HSV\(hue=(\d+), saturation=\d+, value=(\d+)\)", getState(host, "bulb"))

                        h = int(r.group(1))
                        s = value
                        v = int(r.group(2))

                        exec = "kasa --type bulb --host " + host + " hsv " + str(h) + " " + str(s) + " " + str(v)
                    
                    case _:
                        print("Unknown command: " + command)
                        sys.exit(1)
        
        # Creates a thread to run the command
        thread = Thread(target=os.system, args=[exec])
        threads.append(thread)
    
    # Runs all the threads
    for thread in threads:
        thread.start()
    
    # Waits for all the threads to finish
    for thread in threads:
        thread.join()

def main(argv):
    # Check for the correct number of arguments
    if len(argv) < 2:
        print("Usage: things.py <scope> <command> [{value | @preset}]")
        print("  scope   - Comma-separated list of tags")
        print("  command - on, off, toggle, brightness, temperature, color, saturation")
        print("  value   - Value to set for the command")
        print("  preset  - Preset number index to load")

        if len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help"):
            sys.exit(0)
        sys.exit(1)

    # All the preliminary info-parsing before running the actual command is done here
    scope   = argv[0].split(',')
    command = argv[1]
    value   = argv[2] if len(argv) > 2 else None
    conf    = getThings()
    hosts   = getHosts(conf, scope)
    types   = getTypes(conf)
    presets = getPresets(conf)

    # The second argument should be the command to run
    doCommand(command, value, scope, hosts, types, presets)

if __name__ == "__main__":
    main(sys.argv[1:])