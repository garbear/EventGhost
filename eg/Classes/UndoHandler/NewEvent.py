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


import eg


class NewEvent(eg.UndoHandler.NewItem):
    name = eg.text.MainFrame.Menu.AddEvent.replace("&", "").replace("...", "")

    def Do(self, document, label=None, parent=None, pos=-1):
        if parent is None:
            obj = document.selection
            if isinstance(obj, document.MacroItem):
                parent = obj
            else:
                parent = obj.parent
            pos = 0
            for child in parent.childs:
                if isinstance(child, document.ActionItem):
                    break
                pos += 1
            else:
                pos = 0
        if not isinstance(parent, eg.MacroItem):
            return
        if isinstance(parent, eg.AutostartItem):
            return
        needsConfigure = False
        if label is None:
            label = eg.event.string
            needsConfigure = True
        item = document.EventItem.Create(parent, pos, name=label)
        item.Select()

        if needsConfigure and not eg.UndoHandler.Configure().Do(item, True):
            item.Delete()
            return None
        self.StoreItem(item)
        return item

