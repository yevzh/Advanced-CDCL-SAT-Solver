import time
class cdcl():
    def __init__(self, sentence, num_vars):
        self.sentence = sentence
        self.num_vars = num_vars

        # VSIDS的相关初始变量
        self.vsids_scores = self.init_vsids_scores()
        
        # LRB相关的初始变量
        self.learntCounter = 0
        self.lrb_scores, self.lrb_assigned, self.lrb_participated, self.lrb_reasoned = self.init_lrb_scores()
        self.reason_LCV = []
        
        # CHB相关的初始变量
        self.num_conflicts = 0
        self.chb_scores, self.chb_lastConflict= self.init_chb_scores()
        self.chb_plays = set()
        self.chb_multiplier = None
        self.chb_tmp = None
        
        # 初始变量
        self.assignment = []
        self.decided_idxs = []
        self.c2l_watch, self.l2c_watch = self.init_watch()
        self.alpha = 0.4 # for 指数平滑
        
    # 不同机制的初始函数
    def init_vsids_scores(self):
        """Initialize variable scores for VSIDS."""
        scores = {}
        for lit in range(-self.num_vars, self.num_vars + 1):
            scores[lit] = 0
        for clause in self.sentence:
            for lit in clause:
                scores[lit] += 1
        return scores
    
    def init_lrb_scores(self):
        scores = {}
        for lit in range(-self.num_vars, self.num_vars + 1):
            scores[lit] = 0
        return scores, scores, scores, scores
    
    def init_chb_scores(self):
        scores = {}
        for lit in range(-self.num_vars,self.num_vars+1):
            scores[lit] = 0
        return scores, scores
        
        
        
    # 不同机制的更新函数
    def update_vsids_scores(self, learned_clause, decay=0.95):
        """Update VSIDS scores."""
        for lit in learned_clause:
            self.vsids_scores[lit] += 1
        for lit in self.vsids_scores:
            self.vsids_scores[lit] = self.vsids_scores[lit] * decay
        # self.vsids_scores = dict(sorted(self.vsids_scores.items(),key=lambda kv: kv[1], reverse=True))

    def update_lrb_scores(self, decay = 0.95):
        """Update LRB scores"""
        for lit in self.lrb_scores:
            if lit not in self.assignment:
                self.lrb_scores[lit] = self.lrb_scores[lit]*decay
                
    def update_chb_scores(self):
        for v in self.chb_plays:
            # print("up")
            # print(self.chb_plays)
            reward = self.chb_multiplier / (self.num_conflicts - self.chb_lastConflict[v]+1)
            self.chb_scores[v] = (1-self.alpha)*self.chb_scores[v] +self.alpha*reward
    
    
    def decide_vsids(self):  # NOTE: `assignment` is for filtering assigned literals
        """Decide which variable to assign and whether to assign True or False."""
        assigned_lit = None

        # For fast checking if a literal is assigned.
        assigned_lits = [a[0] for a in self.assignment]
        unassigned_vsids_scores = self.vsids_scores.copy()
        for lit in assigned_lits:
            unassigned_vsids_scores[lit] = float("-inf")
            unassigned_vsids_scores[-lit] = float("-inf")
        assigned_lit = max(unassigned_vsids_scores, key=unassigned_vsids_scores.get)

        return assigned_lit
    
    def decide_lrb(self):  # NOTE: `assignment` is for filtering assigned literals
        """Decide which variable to assign and whether to assign True or False."""
        assigned_lit = None

        # For fast checking if a literal is assigned.
        assigned_lits = [a[0] for a in self.assignment]
        unassigned_lrb_scores = self.lrb_scores.copy()
        for lit in assigned_lits:
            unassigned_lrb_scores[lit] = float("-inf")
            unassigned_lrb_scores[-lit] = float("-inf")
        assigned_lit = max(unassigned_lrb_scores, key=unassigned_lrb_scores.get)

        return assigned_lit
    
    def decide_chb(self):  # NOTE: `assignment` is for filtering assigned literals
        """Decide which variable to assign and whether to assign True or False."""
        assigned_lit = None

        # For fast checking if a literal is assigned.
        assigned_lits = [a[0] for a in self.assignment]
        unassigned_chb_scores = self.chb_scores.copy()
        for lit in assigned_lits:
            unassigned_chb_scores[lit] = float("-inf")
            unassigned_chb_scores[-lit] = float("-inf")
        assigned_lit = max(unassigned_chb_scores, key=unassigned_chb_scores.get)

        return assigned_lit
    
    def bcp(self, up_idx=0):  # NOTE: `up_idx` is for recording which assignment triggers the BCP
        """Propagate unit clauses with watched literals."""

        # For fast checking if a literal is assigned.
        assigned_lits = [a[0] for a in self.assignment]

        # If the assignment is empty, try BCP.
        if len(self.assignment) == 0:
            assert up_idx == 0

            for clause_idx, watched_lits in self.c2l_watch.items():
                if len(watched_lits) == 1:
                    assigned_lits.append(watched_lits[0])
                    self.assignment.append((watched_lits[0], clause_idx))

        # If it is after conflict analysis, directly assign the literal.
        elif up_idx == len(self.assignment):  # we use `up_idx = len(assignment)` to indicate after-conflict BCP
            neg_first_uip = self.sentence[-1][-1]
            self.assignment.append((neg_first_uip, len(self.sentence) - 1))

        # Propagate until no more unit clauses.
        while up_idx < len(self.assignment):
            lit, _ = self.assignment[up_idx]
            watching_clause_idxs = self.l2c_watch[-lit].copy()

            for clause_idx in watching_clause_idxs:
                if len(self.sentence[clause_idx]) == 1: return self.sentence[clause_idx]

                another_lit = self.c2l_watch[clause_idx][0] if self.c2l_watch[clause_idx][1] == -lit else self.c2l_watch[clause_idx][1]
                if another_lit in assigned_lits:
                    continue

                is_new_lit_found = False
                for tmp_lit in self.sentence[clause_idx]:
                    if tmp_lit != -lit and tmp_lit != another_lit and -tmp_lit not in assigned_lits:
                        self.c2l_watch[clause_idx].remove(-lit)
                        self.c2l_watch[clause_idx].append(tmp_lit)
                        self.l2c_watch[-lit].remove(clause_idx)
                        self.l2c_watch[tmp_lit].append(clause_idx)
                        is_new_lit_found = True
                        break

                if not is_new_lit_found:
                    if -another_lit in assigned_lits:
                        return self.sentence[clause_idx]  # NOTE: return a clause, not the index of a clause
                    else:
                        assigned_lits.append(another_lit)
                        self.assignment.append((another_lit, clause_idx))

            up_idx += 1

        return None  # indicate no conflict; other return the antecedent of the conflict
    
    def init_watch(self):
        """Initialize the watched literal data structure."""
        c2l_watch = {}  # clause -> literal
        l2c_watch = {}  # literal -> watch

        for lit in range(-self.num_vars, self.num_vars + 1):
            l2c_watch[lit] = []

        for clause_idx, clause in enumerate(self.sentence):  # for each clause watch first two literals
            c2l_watch[clause_idx] = []

            for lit in clause:
                if len(c2l_watch[clause_idx]) < 2:
                    c2l_watch[clause_idx].append(lit)
                    l2c_watch[lit].append(clause_idx)
                else:
                    break

        return c2l_watch, l2c_watch
        
    def analyze_conflict(self, conflict_ante):  # NOTE: `sentence` is for resolution
        """Analyze the conflict with first-UIP clause learning."""
        backtrack_level, learned_clause = None, []

        # Check whether the conflict happens without making any decision.
        if len(self.decided_idxs) == 0:
            return -1, []
    
        # For fast checking if a literal is assigned.
        assigned_lits = [a[0] for a in self.assignment]
        # Find the first-UIP by repeatedly applying resolution.
        learned_clause = conflict_ante.copy()
        

        while True:
            lits_at_conflict_level = assigned_lits[self.decided_idxs[-1]:]
            clause_lits_at_conflict_level = [-lit for lit in learned_clause if -lit in lits_at_conflict_level]
            
            if len(clause_lits_at_conflict_level) <= 1:
                break
            # **************************************************************************
            # A method to get reason list
            
            # last_lit = self.last_lit_assigned(learned_clause, len(self.decided_idxs))
            # self.reason_LCV.append(last_lit)
            level = len(self.decided_idxs)
            self.decided_idxs.append(len(self.assignment))
            head = self.decided_idxs[level - 1]
            tail = self.decided_idxs[level]
            del self.decided_idxs[-1]
            for i in range(tail - 1, head - 1, -1):
                a = self.assignment[i][0]
                if -a in learned_clause:
                    self.reason_LCV.append(self.assignment[i])
            # ***************************************************************************
            # Apply the binary resolution rule.
            is_resolved = False
            while not is_resolved:
                lit, clause_idx = self.assignment.pop()
                if -lit in learned_clause:
                    learned_clause = list(set(learned_clause + self.sentence[clause_idx]))
                    learned_clause.remove(lit)
                    learned_clause.remove(-lit)
                    is_resolved = True

        # Order the literals of the learned clause. This is for:
        # 1) determining the backtrack level;
        # 2) watching the negation of the first-UIP and the literal at the backtrack level.
        lit_to_assigned_idx = {lit: assigned_lits.index(-lit) for lit in learned_clause}
        learned_clause = sorted(learned_clause, key=lambda lit: lit_to_assigned_idx[lit])

        # Decide the level to backtrack to as the second highest decision level of `learned_clause`.
        if len(learned_clause) == 1:
            backtrack_level = 0
        else:
            second_highest_assigned_idx = lit_to_assigned_idx[learned_clause[-2]]
            backtrack_level = next((level for level, assigned_idx in enumerate(self.decided_idxs) if assigned_idx > second_highest_assigned_idx), 0)

        return backtrack_level, learned_clause

    def backtrack(self, level):
        """Backtrack by deleting assigned variables."""
        # *****************************
        # On unassigned for LRB
        self.OnUnassign(level)
        # ******************************
        del self.assignment[self.decided_idxs[level]:]
        del self.decided_idxs[level:]
        
    def add_learned_clause(self, learned_clause):
        """Add learned clause to the sentence and update watch."""

        # Add the learned clause to the sentence.
        self.sentence.append(learned_clause)

        # Update watch.
        clause_idx = len(self.sentence) - 1
        self.c2l_watch[clause_idx] = []

        # Watch the negation of the first-UIP and the literal at the backtrack level.
        # Be careful that the watched literals may be assigned.
        for lit in learned_clause[::-1]:
            if len(self.c2l_watch[clause_idx]) < 2:
                self.c2l_watch[clause_idx].append(lit)
                self.l2c_watch[lit].append(clause_idx)
            else:
                break
            
    # LRB 函数       
    def AfterConflictAnalysis(self, learned_clause, conflict_ante):
        self.learntCounter += 1
        for v in set(learned_clause).union(set(conflict_ante)):
            self.lrb_participated[v]+=1
        for v,_ in set(self.reason_LCV).difference(set(learned_clause)):
            self.lrb_reasoned[v]+=1      
        if self.alpha > 0.06:
            self.alpha -= 1e-6        
    def OnAssign(self):
        for v,_ in self.assignment[self.decided_idxs[-1]:]:
            self.lrb_assigned[v] = self.learntCounter
            self.lrb_participated[v] = 0
            self.lrb_reasoned[v] = 0
    def OnUnassign(self, level):
        
        # *****************************
        # On unassigned for LRB
        for v,_ in self.assignment[self.decided_idxs[level]:len(self.assignment)]:
            interval = self.learntCounter - self.lrb_assigned[v]
            if interval>0:
                r = self.lrb_participated[v]/interval
                rsr = self.lrb_reasoned[v]/interval
                self.lrb_scores[v] = (1-self.alpha)*self.lrb_scores[v]+self.alpha*(r+rsr)
        # ******************************
        
    def ChbAssign(self,assigned_lit,conflict_ante):
        self.chb_tmp = set(self.assignment)
        self.chb_plays = {assigned_lit}
        self.chb_multiplier = 1.0 if conflict_ante is not None else 0.9

    def ChbAfterConflict(self, level):
        if self.alpha > 0.06:
            self.alpha -= 1e-6
        tail = self.assignment[self.decided_idxs[level]:len(self.assignment)]
        for var,_ in tail:
            self.chb_lastConflict[var] = self.num_conflicts
        self.chb_plays = set(a[0] for a in self.reason_LCV)
        
        
    def VSIDS_solver(self, conflicts_limit):
        """Run a CDCL solver for the SAT problem.

        To simplify the use of data structures, `sentence` is a list of lists where each list
        is a clause. Each clause is a list of literals, where a literal is a signed integer.
        `assignment` is also a list of literals in the order of their assignment.
        """
        # Run BCP.
        num_decisions = 0
        if self.bcp() is not None:
            return 'SAT',num_decisions,self.vsids_scores, self.assignment  # indicate UNSAT

        # Main loop.
        while len(self.assignment) < self.num_vars:
            # Make a decision.
            assigned_lit = self.decide_vsids()
            
            # restart
            num_decisions+=1
            
            
            self.decided_idxs.append(len(self.assignment))
            self.assignment.append((assigned_lit, None))
            # Run BCP.

            conflict_ante = self.bcp(len(self.assignment) - 1)

            # ****************************************
            
            while conflict_ante is not None:
                self.num_conflicts += 1
                if self.num_conflicts > conflicts_limit:
                    # print(self.num_conflicts)
                    return 'Restart', num_decisions,self.vsids_scores, self.assignment
                # Learn conflict.
                
                backtrack_level, learned_clause = self.analyze_conflict(conflict_ante)
                
                self.add_learned_clause(learned_clause)


                self.update_vsids_scores(learned_clause)
                # Backtrack.
                if backtrack_level < 0:
                    return None

                self.backtrack(backtrack_level)

                # Propagate watch.

                conflict_ante = self.bcp(len(self.assignment))

        self.assignment = [assigned_lit for assigned_lit, _ in self.assignment]

        return 'SAT',num_decisions,self.vsids_scores, self.assignment  # indicate SAT

    
    def LRB_solver(self, conflicts_limit):
        """Run a CDCL solver for the SAT problem.

        To simplify the use of data structures, `sentence` is a list of lists where each list
        is a clause. Each clause is a list of literals, where a literal is a signed integer.
        `assignment` is also a list of literals in the order of their assignment.
        """
        # Run BCP.
        num_decisions = 0
        if self.bcp() is not None:
            return 'SAT',num_decisions,self.vsids_scores, self.assignment  # indicate UNSAT

        # Main loop.
        while len(self.assignment) < self.num_vars:
            # Make a decision.
            assigned_lit = self.decide_lrb()
            num_decisions+=1
            self.decided_idxs.append(len(self.assignment))
            self.assignment.append((assigned_lit, None))   
            # ****************************************
            # LRB algorithm
            self.OnAssign()
            # ****************************************
            # Run BCP.
            conflict_ante = self.bcp(len(self.assignment) - 1)
            # ****************************************
            
            while conflict_ante is not None:
                self.num_conflicts += 1
                if self.num_conflicts > conflicts_limit:
                    return 'Restart', num_decisions,self.vsids_scores, self.assignment
                # Learn conflict.
                backtrack_level, learned_clause = self.analyze_conflict(conflict_ante)
                # **************************
                # LRB
                self.AfterConflictAnalysis(learned_clause, conflict_ante)
                # **************************
                self.add_learned_clause(learned_clause)


                self.update_lrb_scores()
                # Backtrack.
                if backtrack_level < 0:
                    return None

                self.backtrack(backtrack_level)

                # Propagate watch.
                conflict_ante = self.bcp(len(self.assignment))
        self.assignment = [assigned_lit for assigned_lit, _ in self.assignment]

        return 'SAT',num_decisions,self.vsids_scores, self.assignment  # indicate SAT

    
    def CHB_solver(self, conflicts_limit):
        """Run a CDCL solver for the SAT problem.

        To simplify the use of data structures, `sentence` is a list of lists where each list
        is a clause. Each clause is a list of literals, where a literal is a signed integer.
        `assignment` is also a list of literals in the order of their assignment.
        """
        # Run BCP.
        num_decisions = 0
        if self.bcp() is not None:
            return 'SAT', num_decisions,self.vsids_scores, self.assignment  # indicate UNSAT

        # Main loop.
        while len(self.assignment) < self.num_vars:
            assigned_lit = self.decide_chb()
            num_decisions+=1
            self.decided_idxs.append(len(self.assignment))
            self.assignment.append((assigned_lit, None))

            # Run BCP.
            
            
            conflict_ante = self.bcp(len(self.assignment) - 1)
            # ****************************************
            self.ChbAssign(assigned_lit, conflict_ante)
            self.update_chb_scores()
            
            while conflict_ante is not None:
                self.num_conflicts += 1
                if self.num_conflicts > conflicts_limit:
                    return 'Restart', num_decisions,self.vsids_scores, self.assignment
                # Learn conflict.
                
                backtrack_level, learned_clause = self.analyze_conflict(conflict_ante)
                
                # CHB
                self.ChbAfterConflict(backtrack_level)
                # *****************************
                self.add_learned_clause(learned_clause)
                if backtrack_level < 0:
                    return None

                self.backtrack(backtrack_level)

                # Propagate watch.
                conflict_ante = self.bcp(len(self.assignment))

        self.assignment = [assigned_lit for assigned_lit, _ in self.assignment]
        print("analyze conflict time: ", self.time_analysis)
        return 'SAT', num_decisions,self.vsids_scores, self.assignment # indicate SAT
