from qarbon import config
from qarbon.qt.gui.application import Application
from qarbon.qt.gui.exceptionwidget import ErrorDialog
from qarbon.qt.gui.exceptionwidget import protect

class Beamer:
    def turnOn(self):
        return False

def buggy():
    l = [1, 2, 3]
    try:
        print(l[3])
    except IndexError:
        msgbox = ErrorDialog()
        msgbox.exec_()

@protect
def turnBeamOn(ctrl_obj):
    result = ctrl_obj.turnOn()
    if not result:
        raise Exception("Could not turn on beam!")

def main():
    config.APPLICATION_NAME = "Qarbon demo"
    app = Application()
    
    buggy()
    beamer = Beamer()
    turnBeamOn(beamer)

if __name__ == "__main__":
    main()

