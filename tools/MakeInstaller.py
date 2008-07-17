# $LastChangedDate$
# $LastChangedRevision$
# $LastChangedBy$

PROGRAM_NAME = "EventGhost"
ROOT_DLLS = ["MFC71.dll", "msvcr71.dll", "msvcp71.dll"]
PY2EXE_EXCLUDES = [
    "pywin",
    "pywin.dialogs",
    "pywin.dialogs.list",
    "_ssl",
    # no TCL
    "Tkconstants", 
    "Tkinter", 
    "tcl",
    # and no TCL through PIL
    "_imagingtk", 
    "PIL._imagingtk", 
    "ImageTk", 
    "PIL.ImageTk", 
    "FixTk",
]

INNO_SCRIPT_TEMPLATE = """
[Tasks]
Name: "desktopicon"; Description: {cm:CreateDesktopIcon}; GroupDescription: {cm:AdditionalIcons}

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: Deutsch; MessagesFile: "compiler:Languages\\German.isl"
Name: "fr"; MessagesFile: "compiler:Languages\\French.isl"

[Setup]
ShowLanguageDialog=auto
AppName=EventGhost
AppVerName=EventGhost %(VERSION)s
DefaultDirName={pf}\\EventGhost
DefaultGroupName=EventGhost
Compression=lzma/ultra
SolidCompression=yes
InternalCompressLevel=ultra
OutputDir=%(OUT_DIR)s
OutputBaseFilename=%(OUT_FILE_BASE)s
InfoBeforeFile=%(TOOLS_DIR)s\\LICENSE.RTF
DisableReadyPage=yes
AppMutex=EventGhost:7EB106DC-468D-4345-9CFE-B0021039114B

[InstallDelete]
Type: filesandordirs; Name: "{app}\\eg"
%(INSTALL_DELETE)s

[Files]
Source: "%(TRUNK_DIR)s\\*.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(TRUNK_DIR)s\\*.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(TRUNK_DIR)s\\lib\\*.*"; DestDir: "{app}\\lib"; Flags: ignoreversion recursesubdirs
%(INSTALL_FILES)s
Source: "%(TRUNK_DIR)s\\Example.xml"; DestDir: "{userappdata}\\EventGhost"; DestName: "MyConfig.xml"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "%(TRUNK_DIR)s\\tools\\WebSite.url"; DestName: "EventGhost Web Site.url"; DestDir: "{group}"
Source: "%(TRUNK_DIR)s\\tools\\WebForums.url"; DestName: "EventGhost Forums.url"; DestDir: "{group}"
Source: "%(TRUNK_DIR)s\\tools\\WebWiki.url"; DestName: "EventGhost Wiki.url"; DestDir: "{group}"

[Run]
Filename: "{app}\\EventGhost.exe"; Parameters: "-install"

[UninstallRun]
Filename: "{app}\\EventGhost.exe"; Parameters: "-uninstall"

[Run] 
Filename: "{app}\\EventGhost.exe"; Flags: postinstall nowait skipifsilent 

[Icons]
Name: "{group}\\EventGhost"; Filename: "{app}\\EventGhost.exe"
Name: "{group}\\Uninstall EventGhost"; Filename: "{uninstallexe}"
Name: "{userdesktop}\\EventGhost"; Filename: "{app}\\EventGhost.exe"; Tasks: desktopicon
"""

# The manifest will be inserted as resource into the exe.  This
# gives the controls the Windows XP appearance (if run on XP ;-)

MANIFEST_TEMPLATE = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="%(prog)s"
    type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''

OptionsList = (
    ("Create Source Archive", "createSourceArchive", False),
    ("Create Imports", "createImports", False),
    ("Create Lib", "createLib", False),
    ("SVN Commit", "commitSvn", True),
    ("Upload", "upload", True),
    ("Include 'noinclude' plugins", "includeNoIncludePlugins", False),
)



class Options:
    pass

for label, name, default in OptionsList:
    setattr(Options, name, default)

import py2exe
import wx
import sys
import tempfile
import os
import fnmatch
import time
import zipfile
import subprocess
import _winreg
import locale
import ConfigParser

from ftplib import FTP
from urlparse import urlparse
from shutil import copy2 as copy
from os.path import basename, dirname, abspath, join, exists
try:
    import pysvn
except:
    pass

TMP_DIR = tempfile.mkdtemp()
TOOLS_DIR = abspath(dirname(sys.argv[0]))
TRUNK_DIR = abspath(join(TOOLS_DIR, ".."))
OUT_DIR = abspath(join(TRUNK_DIR, ".."))

# the namespace for different templates
class NS:
    OUT_DIR = OUT_DIR
    TRUNK_DIR = TRUNK_DIR
    TOOLS_DIR = TOOLS_DIR


SourcePattern = [
    "*.py", 
    "*.pyw", 
    "*.pyd", 
    "*.txt", 
    "*.png", 
    "*.jpg", 
    "*.gif", 
    "*.xml", 
    "*.ico",
    "*.vbs",
]

def GetFiles(files, pattern):
    for directory in ("eg", "plugins", "languages", "images"):
        for path in locate(pattern, join(TRUNK_DIR, directory)):
            files.append(path[len(TRUNK_DIR)+1:])
    return files


def GetSetupFiles():
    files = [
        "Example.xml",
        "CHANGELOG.TXT",
    ]
    return GetFiles(files, SourcePattern + ["*.dll"])
    

def UpdateVersionFile():
    versionFilePath = join(TRUNK_DIR, "eg", "Classes", "Version.py")
    fd = file(versionFilePath, "rt")
    lines = fd.readlines()
    fd.close()
    fd = file(versionFilePath, "wt")
    # update buildNum and buildTime in eg/Classes/Version.py
    for line in lines:
        if line.strip().startswith("buildNum"):
            parts = line.split("=")
            value = int(parts[1].strip())
            fd.write(parts[0] + "= " + str(value+1) + "\n")
        elif line.strip().startswith("buildTime"):
            parts = line.split("=")
            fd.write(parts[0] + "= " + str(time.time()) + "\n")
        else:
            fd.write(line)
    fd.close()
    data = {}
    execfile(versionFilePath, data, data)
    versionCls = data["Version"]
    if Options.commitSvn:
        def ssl_server_trust_prompt(trust_dict):
            return True, 0, True
        svn = pysvn.Client()
        svn.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
        svn.checkin([TRUNK_DIR], "created installer for %s" % versionCls.string)    return versionCls
    
    
def UpdateChangeLog():    
    path = join(TRUNK_DIR, "CHANGELOG.TXT")
    s1 = "Version %s (%s)\n" % (
        NS.VERSION, 
        time.strftime("%m/%d/%Y"),
    )
    fd = open(path, "r")
    s2 = fd.read(100) # read some data from the beginning
    if s2.strip().startswith("Version "):
        # no new lines, so skip the addition of a new header
        return
    s2 += fd.read() # read the remaining contents
    fd.close()
    fd = open(path, "w+")
    fd.write(s1 + s2)
    fd.close()
    

def locate(patterns, root=os.curdir):
    '''
    Locate all files matching supplied filename patterns in and below
    supplied root directory.
    '''
    for path, dirs, files in os.walk(root):
        ignoreDirs = [
            dir for dir in dirs 
                if (
                    dir.startswith("_") 
                    or dir == ".svn"
                    or (not Options.includeNoIncludePlugins and exists(join(path, dir, "noinclude")))
                )
        ]
        for dir in ignoreDirs:
            dirs.remove(dir)
        for pattern in patterns:
            for filename in fnmatch.filter(files, pattern):
                yield join(path, filename)

    
def RemoveDirectory(path):
    """
    Remove a directory and all its contents.
    DANGEROUS!
    """
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            try:
                os.remove(join(root, name))
            except:
                pass
        for name in dirs:
            try:
                os.rmdir(join(root, name))
            except:
                pass
    try:
        os.rmdir(path)
    except:
        pass



RT_MANIFEST = 24
shortpgm = "EventGhost"

py2exeOptions = dict(
    options = dict(
        build = dict(
            build_base = join(TMP_DIR, "build")
        ),
        py2exe = dict(
            compressed = 0,
            includes = [
                "encodings",
                "encodings.*",
            ],
            excludes = PY2EXE_EXCLUDES,
            dll_excludes = [
                "DINPUT8.dll", 
                "w9xpopen.exe", 
                "gdiplus.dll", 
                "msvcr71.dll"
            ],
            dist_dir = TRUNK_DIR,
            custom_boot_script=join(TOOLS_DIR, "Py2ExeBootScript.py")
        )
    ),
    # The lib directory contains everything except the executables and the python dll.
    zipfile = "lib\\python25.zip",
    windows = [
        dict(
            script = join(TRUNK_DIR, "EventGhost.pyw"),
            icon_resources = [(1, join(TRUNK_DIR, "EventGhost.ico"))],
            other_resources = [
                (RT_MANIFEST, 1, MANIFEST_TEMPLATE % dict(prog=shortpgm))
            ],
            dest_base = shortpgm
        ),
    ],
    # use out build_installer class as extended py2exe build command
    #cmdclass = {"py2exe": py2exe.run},
    verbose = 0,
)

consoleOptions = dict(
    options = dict(
        build = dict(
            build_base = join(TMP_DIR, "build2")
        ),
        py2exe = dict(
            compressed = 0,
            dist_dir = TRUNK_DIR,
            excludes = PY2EXE_EXCLUDES,
            dll_excludes = ["w9xpopen.exe"],
        )
    ),
    zipfile = r"lib\python25.zip",
    windows = [
        dict(
            script = join(TOOLS_DIR, "py.py"),
            dest_base = "pyw"
        )
    ],
    console = [
        dict(
            script = join(TOOLS_DIR, "py.py"),
            dest_base = "py"
        )
    ],
    verbose = 0,
)


def CompileInnoScript(innoScriptPath):
    """
    Execute command line to compile the Inno Script File
    """
    print "*** running Inno Setup ***"
    key = _winreg.OpenKey(
        _winreg.HKEY_LOCAL_MACHINE, 
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1"
    )
    installPath, _ = _winreg.QueryValueEx(key, "InstallLocation")
    _winreg.CloseKey(key)
    res = Execute(join(installPath, "ISCC.exe"), innoScriptPath)
    return res
        

def Execute(*args):
    si = subprocess.STARTUPINFO()
    si.dwFlags = subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE 
    return subprocess.call(
        args, 
        stdout=sys.stdout.fileno(),
        startupinfo=si
    )


def MakeSourceArchive(outFile):
    svn = pysvn.Client()
    
    def ssl_server_trust_prompt(trust_dict):
        return True, 0, True
    svn.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
    
    def callback_notify(event_dict):
        print event_dict["path"][len(TMP_DIR)+1:]
    svn.callback_notify = callback_notify
    
    svn.checkout(TRUNK_DIR, TMP_DIR)
    zipFile = zipfile.ZipFile(outFile, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(TMP_DIR):
        if '.svn' in dirs:
            dirs.remove('.svn')
        if "noinclude" in files:
            continue
        for file in files:
            filename = os.path.join(root, file)
            arcname = filename[len(TMP_DIR)+1:]
            zipFile.write(filename, arcname)
            print "compressing", arcname
    zipFile.close()
    svn.cleanup(TMP_DIR)
    RemoveDirectory(TMP_DIR)


def InstallPy2exePatch():
    # ModuleFinder can't handle runtime changes to __path__, but win32com 
    # uses them, particularly for people who build from sources.  Hook this in.
    try:
        import modulefinder
        import win32com
        for p in win32com.__path__[1:]:
            modulefinder.AddPackagePath("win32com", p)
        for extra in ["win32com.shell"]:#,"win32com.shellcon","win32com.mapi"]:
            __import__(extra)
            m = sys.modules[extra]
            for p in m.__path__[1:]:
                modulefinder.AddPackagePath(extra, p)
    except ImportError:
        # no build path setup, no worries.
        pass


def CreateLibraryFiles():
    from distutils.core import setup
    InstallPy2exePatch()
    RemoveDirectory(join(TRUNK_DIR, "lib"))
    print "creating console exe"
    setup(**consoleOptions)
    print "creating main exe"
    setup(**py2exeOptions)
    print "copying DLLs"
    pythonDir = dirname(sys.executable)
    for dll in ROOT_DLLS:
        if not os.path.exists(join(TRUNK_DIR, dll)):
            copy(join(pythonDir, dll), TRUNK_DIR)
    print "done!"
    
    
def MakeInstaller():
    version = UpdateVersionFile()
    NS.VERSION = version.string
    NS.OUT_FILE_BASE = "EventGhost_%s_Setup" % version.string
    UpdateChangeLog()
    
    if Options.createSourceArchive:
        MakeSourceArchive(join(OUT_DIR, "EventGhost_%s_Source.zip" % NS.VERSION))
        
    if Options.createLib:
        CreateLibraryFiles()
                    
    installDeleteDirs = []
    for item in os.listdir(join(TRUNK_DIR, "plugins")):
        if item.startswith("."):
            continue
        if os.path.isdir(join(TRUNK_DIR, "plugins", item)):
            installDeleteDirs.append(
                'Type: filesandordirs; Name: "{app}\\plugins\\%s"' % item
            )
    installDelete = "\n".join(installDeleteDirs)
    NS.INSTALL_DELETE = installDelete
    
    installFiles = []
    for file in GetSetupFiles():
        installFiles.append(
            'Source: "%s"; DestDir: "{app}\\%s";' % (join(TRUNK_DIR, file), dirname(file))
        )
    NS.INSTALL_FILES = "\n".join(installFiles)  
    
    innoScriptPath = abspath(join(TMP_DIR, "Setup.iss"))
    fd = open(innoScriptPath, "w")
    fd.write(INNO_SCRIPT_TEMPLATE % NS.__dict__)
    fd.close()
    
    CompileInnoScript(innoScriptPath)
    RemoveDirectory(TMP_DIR)
    return join(OUT_DIR, NS.OUT_FILE_BASE + ".exe")



class Speedometer:
    
    def __init__(self):
        self.period = 15
        self.Reset()
        
    def Reset(self):
        now = time.clock()
        self.start = now
        self.lastSecond = now
        self.rate = 0
        self.lastBytes = 0
        
    def Add(self, b):
        now = time.clock()
        if b == 0 and (now - self.lastSecond) < 0.1:
            return
        
        if self.rate == 0:
            self.Reset()
            
        div = self.period * 1.0
        if self.start > now:
            self.start = now
        if now < self.lastSecond:
            self.lastSecond = now
            
        timePassedSinceStart = now - self.start
        timePassed = now - self.lastSecond
        if timePassedSinceStart < div:
            div = timePassedSinceStart
        if div < 1:
            div = 1.0
            
        self.rate *= 1 - timePassed / div
        self.rate += b / div
        
        self.lastSecond = now
        if b > 0:
            self.lastBytes = now
        if self.rate < 0:
            self.rate = 0
        
        
class FileProgressReader:
    
    def __init__(self, filepath):
        self.size = os.path.getsize(filepath)
        self.fd = open(filepath, "rb")
        self.pos = 0
        self.startTime = time.clock()
        self.speedo = Speedometer()
        
    def read(self, size):
        if size + self.pos > self.size:
            size = self.size - self.pos
        self.speedo.Add(size)
        remaining = (self.size - self.pos + size) / self.speedo.rate
        percent = 100.0 * self.pos / self.size
        print "%d%%" % percent, "%0.2f KiB/s" % (self.speedo.rate / 1024), "%0.2fs" % remaining
        self.pos += size
        return self.fd.read(size)
    
    def close(self):
        self.fd.close()
        elapsed = (time.clock() - self.startTime)
        print "File uploaded in %0.2f seconds" % elapsed
        print "Average speed: %0.2f KiB/s" % (self.size / (elapsed * 1024))
            

def UploadFile(filename, url):
    aborted = False
    urlComponents = urlparse(url)
    fd = FileProgressReader(filename)
    print "Connecting: %s" % urlComponents.hostname
    ftp = FTP(
        urlComponents.hostname, 
        urlComponents.username, 
        urlComponents.password
    )
    print "Changing path to: %s" % urlComponents.path
    ftp.cwd(urlComponents.path)
    print "Getting filelist."
    try:
        fileList = ftp.nlst()
    except:
        fileList = []
    for i in range(0, 999999):
        tempFileName = "tmp%06d" % i
        if tempFileName not in fileList:
            break
    print "Starting upload."
    ftp.storbinary("STOR " + tempFileName, fd, 64 * 1024)
    fd.close()
    if aborted:
        ftp.delete(tempFileName)
    else:
        ftp.rename(tempFileName, basename(filename))
    ftp.quit()
    print "Upload done!"
    
    
    
class MainDialog(wx.Dialog):
    class Ctrls:
        pass
    
    def __init__(self):
        wx.Dialog.__init__(self, None, title="Make EventGhost Installer")
        self.LoadSettings()
        
        # create controls
        ctrls = []
        for label, name, default in OptionsList:
            ctrl = wx.CheckBox(self, -1, label)
            ctrl.SetValue(default)
            ctrls.append(ctrl)
            setattr(self.Ctrls, name, ctrl)
        self.Ctrls.upload.Enable(self.url != "")
        
        okButton = wx.Button(self, wx.ID_OK)
        okButton.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelButton = wx.Button(self, wx.ID_CANCEL)
        cancelButton.Bind(wx.EVT_BUTTON, self.OnCancel)
        
        # add controls to sizers
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        for ctrl in ctrls:
            sizer.Add(ctrl, 0, wx.ALL, 10)
        sizer.Add(btnSizer, 0, wx.ALL, 10)
        self.SetSizerAndFit(sizer)
        
        
    def SaveSettings(self):
        config = ConfigParser.ConfigParser()
        # make ConfigParser case-sensitive
        config.optionxform = str
        config.read(join(TOOLS_DIR, "MakeInstaller.ini"))
        if not config.has_section("Settings"):
            config.add_section("Settings")
        for label, ident, value in OptionsList:
            value = getattr(Options, ident)
            config.set("Settings", ident, value)
        fd = open(join(TOOLS_DIR, "MakeInstaller.ini"), "w")
        config.write(fd)
        fd.close()
        
    
    def LoadSettings(self):
        global OptionsList
        config = ConfigParser.ConfigParser()
        config.read(join(TOOLS_DIR, "MakeInstaller.ini"))
        if config.has_option("Settings", "ftpUrl"):
            self.url = config.get("Settings", "ftpUrl")
        else:
            self.url = ""
        newOptionsList = []
        for label, ident, value in OptionsList:
            if config.has_option("Settings", ident):
                value = config.getboolean("Settings", ident)
            newOptionsList.append((label, ident, value))
        OptionsList = newOptionsList
        

    def OnOk(self, event):
        self.Show(False)
        for label, name, default in OptionsList:
            setattr(Options, name, getattr(self.Ctrls, name).GetValue())
        self.SaveSettings()
        if Options.createImports:
            import MakeImports
            MakeImports.Main()
        filename = MakeInstaller()
        if Options.upload and self.url:
            UploadFile(filename, self.url)
        print filename
        app.ExitMainLoop()
        
        
    def OnCancel(self, event):
        app.ExitMainLoop()
     
     
sys.argv.append("py2exe")
app = wx.App(0)
app.SetExitOnFrameDelete(False)
mainDialog = MainDialog()
mainDialog.Show()
app.MainLoop()

