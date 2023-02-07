import numpy as np
from v2 import cdcl
from v1 import cdclprev
import math
import random

class Bandit:
    def __init__(self,sentence, num_vars):
        self.sentence = sentence
        self.num_vars = num_vars
        
        self.num_arms = 3 # 三个arm，分别是vsids, lrb, 和chb
        self.emp_means = np.zeros(self.num_arms)
        self.num_pulls = np.ones(self.num_arms)
        self.epsilon = 0.1
        self.conflict_limit = 16

        self.vsids_scores = self.init_scores()
        self.lrb_scores = self.init_scores()
        self.chb_scores = self.init_scores()
    def init_scores(self):
        scores = {}
        for lit in range(-self.num_vars,self.num_vars+1):
            scores[lit] = 0
        return scores

    def UCB(self):
        t = 0 # times of restarts 
        while 1:
            print(t)
            print("limit",self.conflict_limit)
            if t < self.num_arms*3:
                # print("fic")
                arm = t%3
                if arm == 0:
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.VSIDS_solver(10)
                    self.vsids_scores = scores
                if arm == 1:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.LRB_solver(10)
                    self.lrb_scores = scores
                if arm == 2:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)   
                    label, num_decisions, scores, assignment = solver.CHB_solver(10)
                    self.chb_scores = scores
                if label == 'SAT':
                    return assignment
                else:
                    # self.scores = scores
                    self.emp_means[arm] = np.log(num_decisions)/len(assignment)
                    # self.conflict_limit*=2
                t+=1
                continue
            # print(t)
            ucb = np.zeros(self.num_arms)
            for i in range(self.num_arms):
                ucb[i] = self.emp_means[i]+ np.sqrt(2*np.log(t)/self.num_pulls[i])
            arm = np.argmax(ucb)
            print("best")
            print(arm)
            if arm == 0:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions, scores, assignment = solver.VSIDS_solver(self.conflict_limit)
                self.vsids_scores = scores
            if arm == 1:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions,scores, assignment = solver.LRB_solver(self.conflict_limit)
                self.lrb_scores = scores
            if arm == 2:
                solver = cdcl(self.sentence, self.num_vars)   
                label, num_decisions,scores, assignment = solver.CHB_solver(self.conflict_limit)
                self.chb_scores = scores
            if label == 'SAT':
                return assignment
            else:
                # print(t)
                # self.scores = scores
                r = np.log(num_decisions)/len(assignment)
                self.num_pulls[arm]+=1
                self.emp_means[arm] = (self.emp_means[arm]*(self.num_pulls[arm]-1)+r)/self.num_pulls[arm]
                self.conflict_limit*=2

            t+=1
    def EXP3(self):
        t = 0
        weight = np.ones(self.num_arms)
        possible = np.ones(self.num_arms)
        gamma = 1
        while 1:
            print(t)
            print("limit",self.conflict_limit)
            for i in range(self.num_arms):
                possible[i] = (1-gamma)*weight[i]/np.sum(weight) + gamma/self.num_arms
                
            arm = 0
            rand = random.uniform(0,1)
            if rand<possible[0]:
                arm = 0
            if rand>=possible[0] and rand< possible[0]+possible[1]:
                arm = 1
            if rand>=possible[0]+possible[1]:
                arm = 2
            print("best")
            print(arm)
            if arm == 0:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions, scores, assignment = solver.VSIDS_solver(self.conflict_limit)
                self.vsids_scores = scores
            if arm == 1:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions,scores, assignment = solver.LRB_solver(self.conflict_limit)
                self.lrb_scores = scores
            if arm == 2:
                solver = cdcl(self.sentence, self.num_vars)   
                label, num_decisions,scores, assignment = solver.CHB_solver(self.conflict_limit)
                self.chb_scores = scores
            if label == 'SAT':
                return assignment
            else:
                # self.scores = scores
                r = np.log(num_decisions)/len(assignment)
                weight[arm]=weight[arm]*np.exp(gamma*r/self.num_arms)
                gamma = min(1,np.sqrt(self.num_arms*np.log(self.num_arms)*3/(np.e-1)*2*t))
                self.conflict_limit*=2

            t+=1
                
            
        
    def EPSILON_GREEDY(self):
        t = 0 # times of restarts 
        while 1:
            print(t)
            print("limit ",self.conflict_limit )
            if t < self.num_arms*3:
                # print("fic")
                arm = t%3
                if arm == 0:
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.VSIDS_solver(10)
                    self.vsids_scores = scores
                if arm == 1:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.LRB_solver(10)
                    self.lrb_scores = scores
                if arm == 2:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)   
                    label, num_decisions, scores, assignment = solver.CHB_solver(10)
                    self.chb_scores = scores
                if label == 'SAT':
                    return assignment
                else:
                    self.scores = scores
                    self.emp_means[arm] = np.log(num_decisions)/len(assignment)
                    # self.conflict_limit*=2
                t+=1
                continue
            # print(t)
            if random.random() < self.epsilon:
                arm = random.randint(0, self.num_arms - 1)
            else:
                arm = np.argmax(self.emp_means)
            print("best")
            print(arm)
            if arm == 0:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions, scores, assignment = solver.VSIDS_solver(self.conflict_limit)
                self.vsids_scores = scores
            if arm == 1:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions,scores, assignment = solver.LRB_solver(self.conflict_limit)
                self.lrb_scores = scores
            if arm == 2:
                solver = cdcl(self.sentence, self.num_vars)   
                label, num_decisions,scores, assignment = solver.CHB_solver(self.conflict_limit)
                self.chb_scores = scores
            if label == 'SAT':
                return assignment
            else:
                # print(t)
                self.scores = scores
                r = np.log(num_decisions)/len(assignment)
                self.num_pulls[arm]+=1
                self.emp_means[arm] = (self.emp_means[arm]*(self.num_pulls[arm]-1)+r)/self.num_pulls[arm]
                self.conflict_limit*=2
            t+=1
            
            
class Banditt:
    def __init__(self,sentence, num_vars):
        self.sentence = sentence
        self.num_vars = num_vars
        
        self.num_arms = 3 # 三个arm，分别是vsids, lrb, 和chb
        self.emp_means = np.zeros(self.num_arms)
        self.num_pulls = np.ones(self.num_arms)
        self.epsilon = 0.1
        self.conflict_limit = 10

        self.vsids_scores = self.init_scores()
        self.lrb_scores = self.init_scores()
        self.chb_scores = self.init_scores()
    def init_scores(self):
        scores = {}
        for lit in range(-self.num_vars,self.num_vars+1):
            scores[lit] = 0
        return scores

    def UCB(self):
        t = 0 # times of restarts 
        while t < 20 :
            print(t)
            print("limit",self.conflict_limit)
            if t < self.num_arms*3:
                # print("fic")
                arm = t%3
                if arm == 0:
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.VSIDS_solver(10)
                    self.vsids_scores = scores
                if arm == 1:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.LRB_solver(10)
                    self.lrb_scores = scores
                if arm == 2:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)   
                    label, num_decisions, scores, assignment = solver.CHB_solver(10)
                    self.chb_scores = scores
                if label == 'SAT':
                    return assignment
                else:
                    # self.scores = scores
                    self.emp_means[arm] = np.log(num_decisions)/len(assignment)
                    # self.conflict_limit*=2
                t+=1
                continue
            # print(t)
            ucb = np.zeros(self.num_arms)
            for i in range(self.num_arms):
                ucb[i] = self.emp_means[i]+ np.sqrt(2*np.log(t)/self.num_pulls[i])
            arm = np.argmax(ucb)
            print("best")
            print(arm)
            if arm == 0:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions, scores, assignment = solver.VSIDS_solver(self.conflict_limit)
                self.vsids_scores = scores
            if arm == 1:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions,scores, assignment = solver.LRB_solver(self.conflict_limit)
                self.lrb_scores = scores
            if arm == 2:
                solver = cdcl(self.sentence, self.num_vars)   
                label, num_decisions,scores, assignment = solver.CHB_solver(self.conflict_limit)
                self.chb_scores = scores
            if label == 'SAT':
                return assignment
            else:
                r = np.log(num_decisions)/len(assignment)
                self.num_pulls[arm]+=1
                self.emp_means[arm] = (self.emp_means[arm]*(self.num_pulls[arm]-1)+r)/self.num_pulls[arm]
                # self.conflict_limit*=2
            t+=1
        ucb = np.zeros(self.num_arms)
        for i in range(self.num_arms):
            ucb[i] = self.emp_means[i]+ np.sqrt(2*np.log(t)/self.num_pulls[i])
        arm = np.argmax(ucb)
        print("best")
        print(arm)
        if arm == 0:
            solver = cdclprev(self.sentence, self.num_vars)
            label, num_decisions, scores, assignment = solver.VSIDS_solver()
            return assignment
        if arm == 1:
            solver = cdclprev(self.sentence, self.num_vars)
            label, num_decisions,scores, assignment = solver.LRB_solver()
            return assignment
        if arm == 2:
            solver = cdclprev(self.sentence, self.num_vars)   
            label, num_decisions,scores, assignment = solver.CHB_solver()
            return assignment
        
        
            
    def EXP3(self):
        t = 0
        weight = np.ones(self.num_arms)
        possible = np.ones(self.num_arms)
        gamma = 1
        while t<10:
            print(t)
            print("limit",self.conflict_limit)
            for i in range(self.num_arms):
                possible[i] = (1-gamma)*weight[i]/np.sum(weight) + gamma/self.num_arms
                
            arm = 0
            rand = random.uniform(0,1)
            if rand<possible[0]:
                arm = 0
            if rand>=possible[0] and rand< possible[0]+possible[1]:
                arm = 1
            if rand>=possible[0]+possible[1]:
                arm = 2
            print("best")
            print(arm)
            if arm == 0:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions, scores, assignment = solver.VSIDS_solver(self.conflict_limit)
                self.vsids_scores = scores
            if arm == 1:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions,scores, assignment = solver.LRB_solver(self.conflict_limit)
                self.lrb_scores = scores
            if arm == 2:
                solver = cdcl(self.sentence, self.num_vars)   
                label, num_decisions,scores, assignment = solver.CHB_solver(self.conflict_limit)
                self.chb_scores = scores
            if label == 'SAT':
                return assignment
            else:
                # self.scores = scores
                r = np.log(num_decisions)/len(assignment)
                weight[arm]=weight[arm]*np.exp(gamma*r/self.num_arms)
                gamma = min(1,np.sqrt(self.num_arms*np.log(self.num_arms)*3/(np.e-1)*2*t))
                # self.conflict_limit*=2

            t+=1
        arm = 0
        rand = random.uniform(0,1)
        if rand<possible[0]:
            arm = 0
        if rand>=possible[0] and rand< possible[0]+possible[1]:
            arm = 1
        if rand>=possible[0]+possible[1]:
            arm = 2
        print("best")
        print(arm)
        if arm == 0:
            solver = cdclprev(self.sentence, self.num_vars)
            label, num_decisions, scores, assignment = solver.VSIDS_solver()
            return assignment
        if arm == 1:
            solver = cdclprev(self.sentence, self.num_vars)
            label, num_decisions,scores, assignment = solver.LRB_solver()
            return assignment
        if arm == 2:
            solver = cdclprev(self.sentence, self.num_vars)   
            label, num_decisions,scores, assignment = solver.CHB_solver()
            return assignment
        
                
            
        
    def EPSILON_GREEDY(self):
        t = 0 # times of restarts 
        while t<20:
            print(t)
            print("limit ",self.conflict_limit )
            if t < self.num_arms*3:
                # print("fic")
                arm = t%3
                if arm == 0:
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.VSIDS_solver(10)
                    self.vsids_scores = scores
                if arm == 1:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)
                    label, num_decisions, scores, assignment = solver.LRB_solver(10)
                    self.lrb_scores = scores
                if arm == 2:
                    # print(t)
                    solver = cdcl(self.sentence, self.num_vars)   
                    label, num_decisions, scores, assignment = solver.CHB_solver(10)
                    self.chb_scores = scores
                if label == 'SAT':
                    return assignment
                else:
                    self.scores = scores
                    self.emp_means[arm] = np.log(num_decisions)/len(assignment)
                    # self.conflict_limit*=2
                t+=1
                continue
            # print(t)
            if random.random() < self.epsilon:
                arm = random.randint(0, self.num_arms - 1)
            else:
                arm = np.argmax(self.emp_means)
            print("best")
            print(arm)
            if arm == 0:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions, scores, assignment = solver.VSIDS_solver(self.conflict_limit)
                self.vsids_scores = scores
            if arm == 1:
                solver = cdcl(self.sentence, self.num_vars)
                label, num_decisions,scores, assignment = solver.LRB_solver(self.conflict_limit)
                self.lrb_scores = scores
            if arm == 2:
                solver = cdcl(self.sentence, self.num_vars)   
                label, num_decisions,scores, assignment = solver.CHB_solver(self.conflict_limit)
                self.chb_scores = scores
            if label == 'SAT':
                return assignment
            else:
                # print(t)
                self.scores = scores
                r = np.log(num_decisions)/len(assignment)
                self.num_pulls[arm]+=1
                self.emp_means[arm] = (self.emp_means[arm]*(self.num_pulls[arm]-1)+r)/self.num_pulls[arm]
                # self.conflict_limit*=2
            t+=1
        arm = np.argmax(self.emp_means)
        print("best")
        print(arm)
        if arm == 0:
            solver = cdclprev(self.sentence, self.num_vars)
            label, num_decisions, scores, assignment = solver.VSIDS_solver()
            return assignment
        if arm == 1:
            solver = cdclprev(self.sentence, self.num_vars)
            label, num_decisions,scores, assignment = solver.LRB_solver()
            return assignment
        if arm == 2:
            solver = cdclprev(self.sentence, self.num_vars)   
            label, num_decisions,scores, assignment = solver.CHB_solver()
            return assignment