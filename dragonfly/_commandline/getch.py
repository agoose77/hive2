# Inspired by the Python cookbook
import sys,functools

termios = None
termios_old_settings = None
termios_changed = False

def change_termios():
    pass

def restore_termios():
    pass

try:
    _raw_input = raw_input
    raw_input = raw_input

except NameError:
    _raw_input = input    
    raw_input = input

termios_err = False

try:
    from msvcrt import getch, kbhit

except ImportError:
    """ we're not on Windows, so we try the Unix approach """
    import sys, tty, termios, select, threading
    
    termilock = threading.Lock()
    iolock = threading.Lock()
    
    fd = sys.stdin.fileno()
    try:
        termios_old_settings = termios.tcgetattr(fd)    
    except termios.error:
        termios_err = True
    
    def change_termios():
        global termios_old_settings, termios_changed
        try:
            termilock.acquire()
            fd = sys.stdin.fileno()
            try:
                termios_old_settings = termios.tcgetattr(fd)
                tty.setraw(fd, termios.TCSADRAIN)
                termios_err = False
            except termios.error:
                termios_err = True
            termios_changed = True
        finally:
            termilock.release()

    def restore_termios():
        global termios_changed
        try:
            termilock.acquire()
            fd = sys.stdin.fileno()
            if not termios_err:
                termios.tcsetattr(fd, termios.TCSADRAIN, termios_old_settings)        
            termios_changed = False
        finally:
            termilock.release()
        
    
    def call_io(func, *args, **kargs):
        try:
            #iolock.acquire()
            if termios_changed:
                restore_termios()
                func(*args, **kargs)
                change_termios()
            else:
                func(*args, **kargs)
        finally:
            #iolock.release()                
            pass

    class new_stdio():
        def __init__(self, target):
            self.target = target
            for at in ("write","flush"):
                setattr(self,at,functools.partial(call_io, getattr(self.target,at)))
            self.encoding = self.target.encoding
            if hasattr(target, "errors"): self.errors = target.errors
            
            
            
    sys.stdout = new_stdio(sys.__stdout__)
    sys.stderr = new_stdio(sys.__stderr__)
    
    def kbhit():
        try:
            s = sys.stdin
            sel = select.select
        except AttributeError:
            return False
        return sel([s], [], [], 0) == ([s], [], [])
 
    def getch():
        while not termios_changed:
            pass
        try:    
            iolock.acquire()
            termilock.acquire()    
            ret = sys.stdin.read(1)
        finally:
            termilock.release()
            iolock.release()
        return ret    
        
    def raw_input(*args, **kwargs):
        global termios_changed    
        ret = None
        try:
            iolock.acquire()
            if termios_changed:
                restore_termios()
                if termios_err: 
                    ret = _raw_input()
                else: 
                    ret = _raw_input(*args, **kwargs)
                change_termios()
            else:
                if termios_err: 
                    ret = _raw_input()
                else: 
                    ret = _raw_input(*args, **kwargs)
        except:
            raising = False
            try:
                import threading
                if len(threading.enumerate()) > 1: raising = True
            except:
                raising = False
            if raising: raise
        finally:
            try:
                iolock.release()    
            except: #if this gives an exception, we are being killed
                pass
        return ret
                
