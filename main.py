import argparse
from cdcl import cdclprev
from bandit import Bandit, Banditt
# from cdcl import cdcl
from utils import read_cnf
import time

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, default="examples/bmc-1.cnf")
    parser.add_argument("-r","--restart", type=str, default="None")
    parser.add_argument("-m","--method", type=str,default="VSIDS")
    parser.add_argument("-s","--strategy",type=str,default="exp")
    return parser.parse_args()

def main(args):
    # Create problem.
    rd_start = time.time()
    with open(args.input, "r") as f:
        sentence, num_vars = read_cnf(f)
    print('read time: ', time.time()-rd_start,'s')
    
    # Create CDCL solver and solve it!
    so_start = time.time()
    solver = Bandit(sentence, num_vars)
    solverr = Banditt(sentence, num_vars)
    scores = solver.init_scores()
    if args.restart == "None":
        solver_prev = cdclprev(sentence, num_vars,scores,scores,scores)
        if(args.method == "VSIDS"):
            res = solver_prev.VSIDS_solver()
        if(args.method == "LRB"):
            res = solver_prev.LRB_solver()
        if(args.method == "CHB"):
            res = solver_prev.CHB_solver()
    else:
        if args.strategy == "None":
            if args.restart == "UCB":
                res = solverr.UCB()
            if args.restart == "EXP3":
                res = solverr.EXP3()
            if args.restart == "epsilon_greedy":
                res = solverr.EPSILON_GREEDY()
        if args.strategy == "exp":
            if args.restart == "UCB":
                res = solver.UCB()
            if args.restart == "EXP3":
                res = solver.EXP3()
            if args.restart == "epsilon_greedy":
                res = solver.EPSILON_GREEDY()          

    print('solve time: ', time.time()-so_start,'s')
    if res is None:
        print("✘ No solution found")
    else:
        print(f"✔ Successfully found a solution: {res}")

if __name__ == "__main__":
    args = parse_args()
    main(args)
