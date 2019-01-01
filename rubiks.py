"""
2x2 Rubiks cube model
"""

import queue
import numpy as np


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
    return transformations


transformations = create_matrices()
projection = 100000 * np.random.randn(1, 24)


class Rubiks2x2:
    def __init__(self, faces=None, parent=None, parent_move=None):
        """Each face has 2x2 array of squares, so there are 24 squares
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
    for n in range(n_steps):
        t = np.random.randint(len(transformations))
        cube = cube.transform(t)
    return cube


def solve(cube, goal=None):
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


def print_history(cube):
    print(cube)
    while cube.parent_move is not None:
        print("Move:", cube.parent_move)
        cube = cube.parent
        print(cube)

            
class Status:
    def __init__(self):
        self.counter = 0
    def tick(self):
        self.counter += 1
        if self.counter % 80 == 0:
            print('.')
        else:
            print('.', end="")
            
            
def main():
    start = Rubiks2x2()
    print(start)
    

if __name__ == '__main__':
    main()
    
