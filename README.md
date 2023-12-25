# About

This is a simple, personal script that I use to manage a few of the TP-Link Kasa-based smart devices around my home, namely (just) smart bulbs and smart plugs. Notably, this uses [Python Kasa](https://github.com/python-kasa/python-kasa) as a backend (where installing it is required), but adds the ability to (concurrently) refer to multiple hosts in one command by associating tags with them, as well as associating custom configurations with them as presets. All of this is read from a file `things.yml` that is stored with the script.

Included is my personal configuration file, as an example of what `things.yml` should look like.

# Usage Examples

### Turn on (bulbs + plugs)
`python3.exe main.py tag1 on`

### Turn off (bulbs + plugs)
`python3.exe main.py tag1,tag2 off`

### Toggle (bulbs + plugs)
`python3.exe main.py tag1,plug toggle`

### Set brightness (bulbs only)
Literal 80%:        `python3.exe main.py tag1,tag2,bulb brightness 80`<br>
Preset 0 (default): `python3.exe main.py tag1,tag2,bulb brightness @0`<br>
Preset 1:           `python3.exe main.py tag1,tag2,bulb brightness @1`

### Set temperature-based color (in Kelvin) (bulbs only)
2700K: `python3.exe main.py tag1,tag2,bulb temperature 2700`

### Set HSV-based color with calculated saturation and default brightness (required as preset 0) (bulbs only)
Red:   `python3.exe main.py tag1,tag2,bulb color 0`<br>
Green: `python3.exe main.py tag1,tag2,bulb color 120`<br>
Blue:  `python3.exe main.py tag1,tag2,bulb color 240`

### Set hue without changing saturation or brightness (bulbs only)
Red: `python3.exe main.py tag1,tag2,bulb hue 0`

### Set saturation (bulbs only)
50%: `python3.exe main.py tag1,tag2,bulb saturation 50`