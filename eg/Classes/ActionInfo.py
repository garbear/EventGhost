class ActionInfo(object):
    
    def __init__(self, treeItem, text):
        actionInstance = self.actionCls()
#        try:
#            actionInstance = action()
#        except:
#            treeItem.PrintError(text)
#            actionInstance = None
            
        self.instance = actionInstance
        self.args = None
        
        
    def SetArgs(self, args):
        self.args = args
        
        
    def GetArgs(self):
        return self.args
            
            
    def GetLabel(self):
        # often the GetLabel() method of the action can't handle
        # a call without arguments, because suitable default arguments
        # are missing. So we use a fallback in such cases.
        action = self.instance
        try:
            name = action.GetLabel(*self.args)
        except:
            name = action.name
        pluginInfo = action.plugin.info
        if pluginInfo.kind != "core":
            name = pluginInfo.label + ": " + name
        return name
    
    
    def GetBasePath(self):
        # return the folder of the plugin where this action is defined
        return self.actionCls.plugin.info.GetBasePath()
        
        
    
