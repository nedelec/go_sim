#!/usr/bin/env python
# A script to run simulations sequentially.
# Copyright F. Nedelec, 2010--2014
#

"""
Synopsis:
    
    Run simulations sequentially.
    For each config file, a simulation is started in a separate 'run' directory.
    Completed runs are moved to the 'park' directory if specified.

Syntax:

    go_sim.py [executable] [repeat] [script.py] [park=directory] config_file [config_file]
    
    Bracketted arguments are optional.
    If working_directory is not specified, the current directory is used.
    [repeat] is an integer specifying the number of run for each config file.
    Completed simulations will be store in the 'park' directory if specified.
    
    script.py if specified should provide a function parse(input)
       You may use: pre_config.py
    
    Any number of config file can be provided (at least one).

F. Nedelec, 03.2010, 10.2011, 05.2012, 04.2013
"""

# we ignore interupting SIGNALS, to make sure that the cleaning-up operations
# are done once the executable is completed.
# This way 'CTRL-C' will kill the executable, but not this controlling script.

def handle_signal(sig, frame):
    sys.stderr.write("go_sim.py escaped signal %i\n" % sig)


try:
    import signal
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
except ImportError:
    pass

# Loading modules on the compute-cluster may fail for unexpected reasons.
# The long time.sleep() prevents zoombie nodes from accepting further LSF jobs

try:
    import os, sys, time
except ImportError:
    host = os.getenv('HOSTNAME', 'unknown')
    sys.stderr.write("go_sim.py could not load necessary python modules on %s\n" % host)
    time.sleep(10000)
    sys.exit()


#define output for error messages:
err = sys.stderr

try:
    import go_sim_lib
except ImportError:
    err.write("go_sim.py could not load go_sim_lib.py\n")
    sys.exit()


#------------------------------------------------------------------------

def executable(arg):
    return os.path.isfile(arg) and os.access(arg, os.X_OK)


def run(exe, base, park, conf, name, preconf, repeat):
    """run simulation in own directory"""
    
    if not os.path.isdir(base):
        err.write("go_sim.py: directory '%s' does not exist\n" % base)
        sys.exit()
    
    if not executable(exe):
        err.write("go_sim.py: executable '%s' not found\n" % exe)
        sys.exit()

    if not os.path.isfile(conf):
        err.write("go_sim.py: file '%s' does not exist\n" % conf)
        sys.exit()
    
    # generate config file(s):
    if preconf:
        import tempfile
        tmp = tempfile.mkdtemp('', 'go-', '.')
    else:
        tmp = ''
    files = go_sim_lib.make_config(conf, preconf, repeat, tmp)

    if not files:
        err.write("go_sim.py could not generate config files\n")
        sys.exit()
 
    # run the simulations sequentially:
    for conf in files:
        try:
            s = go_sim_lib.run(exe, conf, name)
            sys.stdout.write("Completed run `%s` in %s\n" % (conf,s))
        except Exception as e:
            err.write("go_sim.py run failed: %s\n" % repr(e))
        # move run to park directory:
        if os.path.isdir(park):
            try:
                s = go_sim_lib.move_directory(s, park, name)
                with open(s+"/log.txt", "a") as f:
                    f.write("parked    %s\n" % time.asctime())
                sys.stdout.write("            ---> parked in %s\n" % s)
            except Exception as e:
                err.write("go_sim.py cannot move directory: %s\n" % repr(e))


#------------------------------------------------------------------------

def main(args):
    preconf = ''
    name    = 'run0000'
    repeat  = 1
    base    = os.getcwd()
    park    = ''
    exe     = os.path.abspath('sim')
    files   = []
    
    # parse arguments list:
    for arg in args:
        if arg.isdigit():
            repeat = int(arg)
        elif os.path.isfile(arg) and arg.endswith('.py'):
            preconf = arg
        elif executable(arg):
            exe = os.path.abspath(arg)
        elif os.path.isfile(arg):
            files.append(arg)
        elif arg.startswith('name='):
            name = arg[5:]
        elif arg.startswith('park='):
            park = arg[5:]
            if not os.path.isdir(park):
                err.write("go_sim.py: `%s' is not a directory\n"%park)
                sys.exit()
        else:
            err.write("go_sim.py: unexpected argument `%s'\n"%arg)
            sys.exit()
        
    if not files:
        err.write("You should specify a config file on the command line\n")
        sys.exit()
    
    #run the simulations
    cnt = 0
    for conf in files:
        run(exe, base, park, conf, name, preconf, repeat)
        cnt += 1
        name = 'run%04i' % cnt


#------------------------------------------------------------------------


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1]=='help':
        print(__doc__)
    else:
        main(sys.argv[1:])


