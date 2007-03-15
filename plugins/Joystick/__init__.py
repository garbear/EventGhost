# This file is part of EventGhost.
# Copyright (C) 2005 Lars-Peter Voss <lpv@eventghost.org>
# 
# EventGhost is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# EventGhost is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with EventGhost; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# $LastChangedDate$
# $LastChangedRevision$
# $LastChangedBy$

import eg

class PluginInfo(eg.PluginInfo):
    name = "Joystick"
    author = "Bitmonster"
    version = "0.0.1"
    kind = "remote"
    description = (
        "Use joysticks and gamepads as input devices for EventGhost."
    )   
    icon = (
        "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QArABNAAA01td7"
        "AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH1QQHDwonssmjmQAAAIx0RVh0Q29t"
        "bWVudABNZW51LXNpemVkIGljb24KPT09PT09PT09PQoKKGMpIDIwMDMgSmFrdWIgJ2pp"
        "bW1hYycgU3RlaW5lciwgCmh0dHA6Ly9qaW1tYWMubXVzaWNoYWxsLmN6CgpjcmVhdGVk"
        "IHdpdGggdGhlIEdJTVAsCmh0dHA6Ly93d3cuZ2ltcC5vcmdnisdHAAACIUlEQVQ4y5WS"
        "y2tTQRTGf5Pc5CbW0qSxNvXRh6C4SbAU/4KCexGKiIKoIFgIwYWtD7TdiC5ECgqCSBZd"
        "1boTRNCFuyJUsxNEFCoVNTW3afTmdW/muLhpmkKy6IEDw/DNN7/55ig61MezhP+q3TNh"
        "KV8CfOsqsmBQvzo+Xyi16lSnw3V83/oO7Y0b4RCiNY5dZu37urWhegZPzOftTa2vnYFG"
        "pWNDsbivK4zr92MVa9iuj4Ej/b3A/Vatr8MLUoFdYfymiREMEAwa/F61iA7GicjGmVah"
        "kUpPzgB3WjfLVganVMHK2XRHuyjm/+HWHNyqQ0WZ0VT6sjSksyqVnpS5h4+2Xf/r5T2q"
        "y3NYuSL5tRKiYN/wHqKxLuqHL3Dw1G1s2+bGrSkMAK01hUJhC+v4OXJvHtM/1MfIaA+G"
        "GaD48w+5VYcD5y9iWRZBM7iVgWjxWrxWgRAD15dY1Kf5uvSFz+8+8ao0zv6b71GBECIC"
        "jUd4BKLRIiDifawAhokb6mXkwSorKyvk376GgInWGsAzaRKIYL24xo/pYdYXpxpEGrfu"
        "tiQjSF0jutENA6OZ/PICUitRWl6g++RdAI4lR3n67ElzXRfdRG/mtRliaGyCyofnhMYm"
        "0FqjREgkkiQSSUQUSomH3zDYRmCaJkevZIBM26mybW9yy+UyAJVKZTtBNpvFdV12Ukqp"
        "LYNIJNJEAqhWqwDUarWOBo7jeEbtRnkHNfsfqMAAn2HmrMwAAAAASUVORK5CYII="
    )


import os

EVT_DIRECTION       = 0
EVT_BTN_RELEASED    = 1
EVT_BTN_PUSHED  	= 2
EVT_X_AXIS          = 3
EVT_Y_AXIS          = 4
EVT_Z_AXIS          = 5



class Joystick(eg.PluginClass):
    
    def __start__(self):
        self.x = 0
        self.y = 0
        import imp
        path = os.path.join(os.path.dirname(__file__), "_dxJoystick.pyd")
        self._dxJoystick = imp.load_dynamic("_dxJoystick", path)
        self._dxJoystick.RegisterEventFunc(self.EventFunc)
        
        
    def __stop__(self):
        self._dxJoystick.RegisterEventFunc(None)
        
        
    def EventFunc(self, joynum, eventtype, value):
        if eventtype == EVT_BTN_PUSHED:
            self.TriggerEnduringEvent("Button" + str(value + 1))
        elif eventtype == EVT_BTN_RELEASED:
            self.EndLastEvent()
        elif eventtype == EVT_X_AXIS:
            self.x = value
            if value == 0:
                if self.y == 0:
                    self.EndLastEvent()
                elif self.y == 1:
                    self.TriggerEnduringEvent("Down")
                else:
                    self.TriggerEnduringEvent("Up")
            elif value == 1:
                self.TriggerEnduringEvent("Right")
            elif value == -1:
                self.TriggerEnduringEvent("Left")
        elif eventtype == EVT_Y_AXIS:
            self.y = value
            if value == 0:
                if self.x == 0:
                    self.EndLastEvent()
                elif self.x == 1:
                    self.TriggerEnduringEvent("Right")
                else:
                    self.TriggerEnduringEvent("Left")
            elif value == 1:
                self.TriggerEnduringEvent("Down")
            elif value == -1:
                self.TriggerEnduringEvent("Up")
        
        