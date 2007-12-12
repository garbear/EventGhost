import wx
import eg
from eg.Controls.SizeGrip import SizeGrip


class DefaultConfig:
    position = None
    size = (400, 300)
        
config = eg.GetConfig("HTMLDialog", DefaultConfig)


class HTMLDialog(eg.Dialog):
    
    def __init__(self, title, htmldata, icon=None, basePath=None):
        
        style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        wx.Dialog.__init__(self, None, -1, title, style=style)
        if icon:
            self.SetIcon(icon)
        htmlCtrl = eg.HtmlWindow(self, -1, style=wx.SUNKEN_BORDER)
        htmlCtrl.SetBorders(2)
        htmlCtrl.SetBasePath(basePath)
        htmlCtrl.SetPage(htmldata)
        okButton = wx.Button(self, wx.ID_OK, eg.text.General.ok)
        okButton.SetDefault()
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(htmlCtrl, 1, wx.EXPAND|wx.ALL, 5)
        
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((5, 5), 1, wx.EXPAND)
        btnSizer.Add(
            okButton, 
            0, 
            wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, 
            5
        )
        btnSizer.Add((5, 5), 1, wx.EXPAND)
        btnSizer.Add(SizeGrip(self), 0, wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT)
        
        mainSizer.Add(btnSizer, 0, wx.EXPAND)
        
        self.SetSizerAndFit(mainSizer)
        if config.position is not None:
            self.SetPosition(config.position)
        self.SetSize(config.size)


    def Destroy(self):
        config.size = self.GetSizeTuple()
        config.position = self.GetPositionTuple()
        eg.Dialog.Destroy(self)
        