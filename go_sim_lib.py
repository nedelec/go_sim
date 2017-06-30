#!/usr/bin/env python
#
# mini python library to run Cytosim
#  it is used by go_sim.py
#
# Copyright F. Nedelec, May 19th, 2007-2012
# Revised Dec. 2007; March 2010; Oct 2011, Feb. 2012, Sept 2012, June 2014

"""
 Functions to start cytosim and handle directory creation / copy,
 as necessary to run a simulation on a cluster

F. Nedelec, March 2010, May 2012, June 2014, Nov 2014, July 2015
"""

try:
    import os, shutil, exceptions, subprocess
except ImportError:
    import sys
    host = os.getenv('HOSTNAME', 'unknown')
    sys.stderr.write("go_sim_lib.py could not load python modules on %s\n" % host)
    sys.exit()


class Error( exceptions.Exception ):
    """go_sim.py exception class"""
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        return repr(self.value)

# default name of the config file:
config_name = 'config.cym'
logfile_name = 'log.txt'


#==========================  DIR/FILES HANDLING ==============================

def make_temp_directory(str):
    #make a directory on the /scratch disc if possible:
    import tempfile
    try:
        return tempfile.mkdtemp('', str, '/scratch/ned')
    except:
        pass
    try:
        return tempfile.mkdtemp('', str, '/scratch')
    except:
        pass
    return tempfile.mkdtemp('', str, '.')


def make_directory(path, n=0):
    """
    Create a new directory name????,
    where ???? is a 4-digit number greater than n
    """
    res = path
    if path[-1].isdigit():
        path = path + '-'
    while n < 10000:
        try:
            os.mkdir(res)
            #print("made " + res)
            return res
        except OSError:
            res = path + '%04i' % n
        n += 1
    raise Error("failed to create new run directory on "+os.getenv('HOSTNAME', 'unknown'))


def copy_recursive(src, dst):
    """recursively copy everything from src to dst"""
    if os.path.isfile(src):
        shutil.copy2(src, dst)
    elif os.path.isdir(src):
        try:
            os.mkdir(dst)
        except OSError:
            pass
        files = os.listdir(src)
        for f in files:
            s = os.path.join(src, f)
            d = os.path.join(dst, f)
            copy_recursive(s, d)


def move_directory(path, park, name):
    """Copy directory 'path' to park, under a similar name"""
    src = os.path.abspath(path)
    if src == os.path.abspath(park):
        return src
    try:
        dst = make_directory(os.path.join(park,name))
    except:
        sys.stderr.write("go_sim_lib.py found no parking space for '%s'\n" % path)
        return src
    #print("moving directory( %s -> %s )" % (src, dst))
    copy_recursive(src, dst)
    from filecmp import dircmp
    dcmp = dircmp(src, dst)
    if dcmp.left_only or dcmp.diff_files:
        sys.stderr.write("go_sim_lib.py could not copy '%s' identically\n" % path)
        return src
    else:
        shutil.rmtree(src)
    return dst


def make_config(conf, preconf, repeat, dest):
    """
    Generate config files by running a preconf script,
    or simply repeat the name if ( repeat > 1 ) and preconf==''.
    """
    module = {}
    if preconf:
        try:
            module = __import__(preconf.rstrip('.py'))
        except:
            import imp
            module = imp.load_source('pre_config', preconf)
        if not module:
            raise Error("could not load python module `"+preconf+"'")
    if module:
        print("Using " + preconf)
        # use preconf to generate a new config file:
        return module.parse(conf, {}, repeat, dest)
    else:
        res = []
        for x in xrange(repeat):
            res.extend([conf]);
        return res


#=======================  RUNNING THE SIMULATION  ==============================

def run_sim(exe, args):
    """
    Start executable in current directory, and wait for completion.
    The executable should find its default configuration file.
    The standard output is redirected to file `out.txt',
        and the standard error to 'err.txt'.
    """
    outname = 'out.txt'
    errname = 'err.txt'
    outfile = open(outname, 'w')
    errfile = open(errname, 'w')
    # run simulation
    if not args:
        code = subprocess.call(exe, stdout=outfile, stderr=errfile)
    else:
        code = subprocess.call([exe]+args, stdout=outfile, stderr=errfile)
    outfile.close()
    errfile.close()
    # remove output files if empty:
    if os.path.isfile(outname) and not os.path.getsize(outname):
        os.remove(outname)
    if os.path.isfile(errname) and not os.path.getsize(errname):
        os.remove(errname)
    return code


def info_start(filename, exe, args, conf, pid):
    import time
    with open(filename, "w") as f:
        f.write("host      %s\n" % os.getenv('HOSTNAME', 'unknown'))
        f.write("user      %s\n" % os.getenv('USER', 'unknown'))
        f.write("wdir      %s\n" % os.getcwd())
        f.write("exec      %s\n" % exe)
        f.write("args      %s\n" % args)
        f.write("conf      %s\n" % conf)
        f.write("pid       %s\n" % pid)
        f.write("start     %s\n" % time.asctime())


def info_end(filename, val):
    import time
    with open(filename, "a") as f:
        f.write("status    %s\n" % val)
        f.write("stop      %s\n" % time.asctime())


def run(exe, conf, name, args=['-']):
    """
    Run one simulation in a new sub directory and wait for completion.
    The config file 'conf' is copied to the subdirectory.
    Returns sub-directory in which `exe` was called.
    """
    if not os.path.isfile(conf):
        raise Error("missing/unreadable config file")
    conf = os.path.abspath(conf);    
    cdir = os.getcwd()
    # use a temporary directory on the cluster:
    if os.environ.has_key('SLURM_JOB_ID') or os.environ.has_key('LSB_JOBID'):
        wdir = make_temp_directory(os.getenv('USER', 'run')+'-')
    else:
        wdir = make_directory(name)
    os.chmod(wdir, 504)
    os.chdir(wdir)
    shutil.copyfile(conf, config_name)
    info_start(logfile_name, exe, args, conf, os.getpid())
    val = run_sim(exe, args)
    info_end(logfile_name, val)
    os.chdir(cdir)
    return wdir


def start(exe, conf, name, args=['-']):
    """
    Start simulation in a new sub directory, and return immediately.
    The config file `conf` is copied to the sub-directory.
    """
    if not os.path.isfile(conf):
        raise Error("missing/unreadable config file")
    cdir = os.getcwd()
    wdir = make_directory(name)
    conf = os.path.abspath(conf);
    os.chdir(wdir)
    shutil.copyfile(conf, config_name)
    outfile = open('out.txt', 'w')
    errfile = open('err.txt', 'w')
    #start simulation, but do not wait for completion:
    pid = subprocess.Popen(['nohup', exe]+args, stdout=outfile, stderr=errfile).pid
    info_start(logfile_name, exe, args, conf, pid)
    os.chdir(cdir)
    return (pid, wdir)


