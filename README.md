# go_sim
# Automates execution of cytosim

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
