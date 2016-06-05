import subprocess
import threading

def run_command(args, output_callback=None, exit_callback=None):
    runner = SubprocessWorker(args, output_callback, exit_callback)
    runner.start()
    return runner

class SubprocessWorker(threading.Thread):
    def __init__(self, command, output_callback=None, exit_callback=None):
        threading.Thread.__init__(self)
        self.command = command
        self.process = None
        
        def noop(*args):
            print(args)
        
        self.output_callback = output_callback or noop
        self.exit_callback = exit_callback or noop
    
    def run(self):
        self.process = subprocess.Popen(self.command, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        while (True):
            line = self.process.stdout.readline().decode("utf-8", errors='surrogateescape')
            if line == "":
                break
            self.output_callback(self, line)
            
        self.process.wait()
        self.exit_callback(self, self.process.returncode)

if __name__ == "__main__":
    import sys
    
    def output_callback(thread, line):
        print((thread, line))
    
    def exit_callback(thread, status):
        print((thread, status))
    
    command = sys.argv[1:] or "ls -l /".split()
    thread = run_command(command, output_callback, exit_callback)
    thread.join()
    
