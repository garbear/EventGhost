# This file is part of EventGhost.
# Copyright (C) 2005 Lars-Peter Voss <bitmonster@eventghost.org>
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
from PluginTools import OpenPlugin
from time import clock

EVENT_ICON_INDEX = eg.EventItem.icon.index

CORE_PLUGINS = (
    "EventGhost",
    "System",
    "Window",
    "Mouse",
)


class ActionThread(eg.ThreadWorker):
    
    @eg.LogItWithReturn
    def StartSession(self, filename):
        eg.eventTable.clear()
        for pluginIdent in CORE_PLUGINS:
            try:
                plugin = OpenPlugin(pluginIdent, None, ())
                plugin.__start__()
                plugin.info.isStarted = True
            except:
                eg.PrintTraceback()
        start = clock()
        eg.document.Load(filename)
        eg.DebugNote("XML loaded in %f seconds." % (clock() - start))
        eg.programCounter = (eg.document.autostartMacro, None)
        eg.RunProgram()
        
            
    def ExecuteTreeItem(self, obj, event):
        eg.SetProcessingState(2, event)
        eg.event = event
        if isinstance(obj, eg.MacroItem):
            eg.programCounter = (obj, 0)
            eg.RunProgram()
        elif isinstance(obj, eg.ActionItem):
            obj.Execute()
        eg.SetProcessingState(1, event)
        
        
    @eg.LogIt
    def StopSession(self):
        eg.document.autostartMacro.UnloadPlugins()
        for pluginIdent in CORE_PLUGINS:
            try:
                plugin = getattr(eg.plugins, pluginIdent).plugin
                plugin.__stop__()
                eg.ClosePlugin(plugin)
            except:
                eg.PrintTraceback()
        
        
    def HandleAction(self, action):
        try:
            action()
        except eg.PluginClass.Exception, e:
            eg.log.PrintItem(e.message, eg.Icons.ERROR_ICON, e.obj.info.treeItem)
            e.obj.info.treeItem.SetErrorState(True)
            #print "ex:", type(e), e.obj
        except:
            eg.PrintTraceback()
            