# README

This project is a SAT Solver based on CDCL (Conflict Driven Clause Learning) implemented in Python.



The files of this folder:

[main.py] the file to run CDCL solver

[cdcl.py] main function in CDCL solver.

[cdcl_restart.py] revised version for CDCL solver with restart scheme

[Bandit.py] MAB policy for restarting containing UCB, Epsilon-greedy and EXP3 



To run this solver, you can use the default command as follow:  ` python main.py ` 



There are also several args that can be added.

- "-i", "--input", type=str, default="examples/bmc-1.cnf"	-- choose the example to run
- "-r","--restart", type=str, default="None"    -- choose the MAB policy between UCB, epsilon-greedy and EXP3 or None 
- "-m","--method", type=str, default="CHB"    -- choose the branching heuristic between LRB and CHB
- "-s","--strategy", type=str, default="exp"    -- choose the restart strategy between None and exp