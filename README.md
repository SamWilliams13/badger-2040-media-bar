# badger-2040-media-bar
Collects Windows 10/11 media control information for Now Playing Title, Artist, Album and compresses the thumbnail, displays on a Badger 2040 over serial.

## Requirements
### ImageMagick: https://imagemagick.org/script/download.php
importantly, tick the option in installation that installs legacy components (e.g., convert)
### winsdk: pip install winsdk
### ampy: pip install adafruit-ampy
### serial: pip install serial

there is also an issue with calling ampy with some versions of python. installing the non windows store non-visual studio standard version and adding to path is a solution
