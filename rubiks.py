"""
2x2 Rubiks cube model
"""

import queue
import numpy as np
import sys


def permutation_matrix(N, srcs, dsts):
    """Make an NxN permutation matrix that when multiplied by an Nx1
    column vector takes entries at indices srcs to dsts.
    """
    M = np.identity(N, dtype='int64')
    M[srcs,srcs] = 0
    M[dsts,srcs] = 1
    return M


def create_matrices():
    identity = permutation_matrix(24, [], [])
        
    # Clockwise rotations
    front = permutation_matrix(24, [0,1,2,3,19,18,4,7,21,20,14,13],
                               [1,2,3,0,4,7,21,20,14,13,19,18])
    right = permutation_matrix(24, [4,5,6,7,18,17,8,11,22,21,2,1],
                               [5,6,7,4,8,11,22,21,2,1,18,17])
    top   = permutation_matrix(24, [16,17,18,19,4,5,8,9,12,13,0,1],
                               [17,18,19,16,0,1,4,5,8,9,12,13])
        
    transformations = [front, right, top, top.T, right.T, front.T]
    #transformations = [identity, front, right, top, top.T, right.T, front.T]

    names = ['front', 'right', 'top', 'top inverse', 'right inverse', 'front inverse']
    
    return transformations, names


transformations, transform_names = create_matrices()
projection = 100000 * np.random.randn(1, 24)


class Rubiks2x2:
    def __init__(self, faces=None, parent=None, parent_move=None):
        """Immutable representation of a 2x2 rubiks cube configuration

        Each face has 2x2 array of squares, so there are 24 squares
        total. There are six colors, represented by numbers
        0-5. Arrange of faces is:
        
        0: front
        1: right
        2: back
        3: left
        4: top
        5: bottom

        (16,17)
        (19,18)
           |
        ( 0, 1) _ ( 4, 5) _ ( 8, 9) _ (12,13)
        ( 3, 2)   ( 7, 6)   (11,10)   (15,14)
           |
        (20,21)
        (23,22)

        Also includes parent configuration and move to get there for
        backtracking purposes.  These are not considered in hashing
        and equality testing, though.

        """
        if faces is None:
            #                 front    right    back     left     top      bottom
            #                 0 1 2 3  4 5 6 7  8 91011 12131415 16171819 20212223
            faces = np.array([0,0,0,0, 1,1,1,1, 2,2,2,2, 3,3,3,3, 4,4,4,4, 5,5,5,5])
            faces = faces[:,None]
        self.faces = faces
        self.parent = parent
        self.parent_move = parent_move

    def transform(self, num):
        return Rubiks2x2(transformations[num] @ self.faces, self, num)

    def dist(self, other):
        return (self.faces != other.faces).sum()
    
    def __repr__(self):
        strings = [str(n[0]) for n in self.faces]
        return ("(" + strings[16] + "," + strings[17] + ")\n" +
                "(" + strings[19] + "," + strings[18] + ")\n" +
                "  |\n" +
                "(" + strings[0] + "," + strings[1] + ") _ " +
                "(" + strings[4] + "," + strings[5] + ") _ " +
                "(" + strings[8] + "," + strings[9] + ") _ " +
                "(" + strings[12] + "," + strings[13] + ")\n" +
                "(" + strings[3] + "," + strings[2] + ")   " +
                "(" + strings[7] + "," + strings[6] + ")   " +
                "(" + strings[11] + "," + strings[10] + ")   " +
                "(" + strings[15] + "," + strings[14] + ")\n" +
                "  |\n" +
                "(" + strings[20] + "," + strings[21] + ")\n" +
                "(" + strings[23] + "," + strings[22] + ")\n")

    def __hash__(self):
        return int(projection @ self.faces)

    def __eq__(self, other):
        return np.all(self.faces == other.faces)
    

def randomize(cube, n_steps):
    """Take n_steps random moves from cube. Avoid already-visited configurations.
    """
    visited = set([cube])
    while n_steps > 0:
        t = np.random.randint(len(transformations))
        new_cube = cube.transform(t)
        if new_cube not in visited:
            cube = new_cube
            n_steps -= 1
            visited.add(cube)
    return cube


def solve(cube, goal=None):
    """Breadth-first search from start state to goal state.
    """
    if goal is None:
        goal = Rubiks2x2()

    s = Status()
    q = queue.Queue()
    start = Rubiks2x2(cube.faces)
    q.put(start)
    
    while not q.empty():
        s.tick()
        latest = q.get()
        for t in range(len(transformations)):
            new_cube = latest.transform(t)
            if new_cube == goal:
                print("Found it!")
                print_history(new_cube)
                return new_cube
            q.put(new_cube)


def solve_2way(cube, goal=None):
    """Breadth-first search from both start state and goal state
    simultaneously.  Works best.

    """
    if goal is None:
        goal = Rubiks2x2()

    s = Status()

    start = Rubiks2x2(cube.faces)
    srcq = queue.Queue()
    srcq.put(start)

    end = Rubiks2x2(goal.faces)
    dstq = queue.Queue()
    dstq.put(end)

    goal_set = {end:end}
    
    while not srcq.empty():
        N = len(transformations)
        s.tick()
        latest_dst = dstq.get()
        for t in range(N):
            new_dst = latest_dst.transform(t)
            goal_set[new_dst] = new_dst
            dstq.put(new_dst)

        latest_src = srcq.get()
        for t in range(N):
            new_src = latest_src.transform(t)
            if new_src in goal_set:
                print("Found it!")
                remainder = goal_set[new_src]
                while remainder.parent:
                    new_src = new_src.transform(N - remainder.parent_move - 1)
                    remainder = remainder.parent
                print_history(new_src)
                return new_src
            srcq.put(new_src)
    

def solve_pq(cube, goal=None):
    """Use a priority queue to find best path where priority is the number
    of squares two configurations have in common.  This turns out not
    to be a good metric, so this method doesn't work very well.

    """
    if goal is None:
        goal = Rubiks2x2()

    s = Status()
    q = queue.PriorityQueue()
    start = Rubiks2x2(cube.faces)
    q.put(PriorityItem(start, goal))
    visited = set([start])
    
    while not q.empty():
        s.tick()
        latest = q.get().item
        for t in range(len(transformations)):
            new_cube = latest.transform(t)
            if new_cube == goal:
                print("Found it!")
                print_history(new_cube)
                return new_cube
            if new_cube not in visited:
                q.put(PriorityItem(new_cube, goal))
                visited.add(new_cube)


class PriorityItem:
    """Lower is better.
    """
    def __init__(self, item, goal):
        self.item = item
        self.goal = goal
        self.priority = item.dist(goal)
    def __lt__(self, other):
        return self.priority < other.priority

            
def print_history(cube):
    print(cube)
    n_steps = 0
    while cube.parent_move is not None:
        print(f"Came from move: '{transform_names[cube.parent_move]}' on")
        cube = cube.parent
        n_steps += 1
        print(cube)
    print("Total", n_steps, "steps")

            
class Status:
    "Print out periods in columns of 80."
    def __init__(self):
        self.counter = 0
    def tick(self):
        self.counter += 1
        if self.counter % 80 == 0:
            print('.')
        else:
            print('.', end="")
            
            
def main():
    if len(sys.argv) > 1:
        print(sys.argv)
        N = int(sys.argv[1])
    else:
        N = 12
        
    start = randomize(Rubiks2x2(), N)
    print(start)
    solution = solve_2way(start)
    

if __name__ == '__main__':
    main()
    
