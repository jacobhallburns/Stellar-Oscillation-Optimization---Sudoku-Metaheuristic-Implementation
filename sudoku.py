"""
File: sudoku.py
Author: Jacob Hall-Burns
Description: Stellar Oscillation Optimization (SOO) is an algorithm based on asteroseismology studying the oscillation frequencies of stars, stellar oscillations or pulsations.
             Starquakes are detected by small changes in brightness, or luminosity. My implement of SOO for sudoku makes changes to the base publication.
             SOO is continuous by nature of it's math being based in sin and cosine functions. We use probabilistic determination to convert the continous
             nature of SOO to discrete changes, fitting the nature of Sudoku. I also added a Supernova and Event Horizion trigger to address 
             the constrained nature of the project. Supernova's address when a specific "Star" or Sudoku board in the population has not made any meaningful
             changes over time, and is effectively stuck in a local optima. It will "destroy" the board state and make a mutation of the global best board state.
             The Event Horizion trigger, looks at the entire population in the same way, and determines that a sufficent set of the boardstate is stuck in
             a local optima and effictively collapses the population state and reforms them as mutations of the global best board state.
"""

import random
import math
import sys

class Star:
    # Initiates each Stars Object
    def __init__(self, board_list, fixed_indices):
        self.board = board_list
        self.fixed_indices = set(fixed_indices)
        self.luminosity = 0.0
        self.conflict_count = 999
        self.stagnation_count = 0
        self.conflict_map = [0] * 81

    # Evaluates the Sudoku boards
    def evaluate(self):
        # Stores the last amount of contflicts (at initialization it is 999)
        old_conflicts = self.conflict_count
        # Creates a new, empty conflict map
        self.conflict_map = [0] * 81
        # Checks for conflicts in each row and column
        for i in range(9):
            self._mark_conflicts([i*9 + j for j in range(9)])
            self._mark_conflicts([j*9 + i for j in range(9)])
        # Adds up the conflicts stored in the conflict map
        self.conflict_count = sum(1 for x in self.conflict_map if x > 0)
        # Luminosity is the inverse of the conflict_count
        self.luminosity = 1 / (1 + self.conflict_count)
        # If this is not the first time the board is being evaluated, and the number of conflicts is greater than or equal to the number of old conflicts you have stagnated.
        # If not, you have improved and you reset the stagnation counter
        if old_conflicts != 999 and self.conflict_count >= old_conflicts:
            self.stagnation_count += 1
        else:
            self.stagnation_count = 0
        return self.conflict_count

    # Marks the conflicts found in the conflict map
    def _mark_conflicts(self, indices):
        # Creates set of seen numbers for each given column and row
        seen = {}
        # For each index in the row, we look at the number seen at that index and check to see if it has been seen before.
        # If the number has already been seen in this column or row we increase the heat of the conflict_map at that index and increase the heat of that seen value
        # If it has not been seen yet, it is added to the set of seen values
        for idx in indices:
            val = self.board[idx]
            if val in seen:
                self.conflict_map[idx] += 1
                self.conflict_map[seen[val]] += 1
            else:
                seen[val] = idx

    # Gets the indexes for the rest of the cells in the subgrid that the given index is in
    def _get_subgrid_indices_by_box(self, box_idx):
        start_row, start_col = (box_idx // 3) * 3, (box_idx % 3) * 3
        return [r * 9 + c for r in range(start_row, start_row + 3)
                          for c in range(start_col, start_col + 3)]

    # Randomizes a stars board state based on the intensity of the pulsation
    def pulsate(self, intensity):
        if intensity == 0: return
        box_heats = []
        # Finds the sum of the heatmap for each subgrid 
        for i in range(9):
            indices = self._get_subgrid_indices_by_box(i)
            heat = sum(self.conflict_map[idx] for idx in indices)
            box_heats.append((i, heat))
        # Sorts the sums by overall heat
        box_heats.sort(key=lambda x: x[1], reverse=True)
        # Sorts the hotest boxes first
        for i in range(min(intensity, 9)):
            box_idx, heat = box_heats[i]
            if heat > 0:
                # chance for a Triple-Rotation when intensity is high
                if intensity > 7 and random.random() < 0.3:
                    self._triple_rotate_within_box(box_idx)
                else:
                    self._swap_within_box(box_idx)

    # Swaps cells, while trying to approach the current best star
    def contract_toward(self, X_best, intensity):
        if intensity == 0: return
        # Finds the differences between the best board and the current board
        diff_indices = [i for i in range(81) if self.board[i] != X_best.board[i] 
                        and i not in self.fixed_indices]
        if not diff_indices: return
        random.shuffle(diff_indices)
        
        # the intensity is reduced if the star is already close in similarity to the best star
        limit = intensity if self.conflict_count > 10 else max(1, intensity // 3)
        
        # Checks the randomized differences and does swaps to try and fix the board however many times the intensity allows
        for i in range(min(limit, len(diff_indices))):
            idx_to_fix = diff_indices[i]
            target_val = X_best.board[idx_to_fix]
            self._move_value_to_index(idx_to_fix, target_val)

    # Pulsation at a low intensity
    def targeted_pulsation(self):
        self.pulsate(intensity=3)

    # Resets a given board if it has stagnated for too long
    def supernova_reset(self, global_best_star):
        # Grabs the value for the global_best_star and replicates it
        # Resets the stagnation count
        self.board = list(global_best_star.board)
        self.stagnation_count = 0
        # Finds the sub grids with the most conflicts
        # Note: conflict_map here reflects the old board state, not the newly copied global best.
        # This is intentional — we perturb based on where this star was previously struggling,
        # on the assumption those regions are likely still tense in the global best board.
        hot_boxes = [i for i in range(9) if sum(self.conflict_map[idx] 
                     for idx in self._get_subgrid_indices_by_box(i)) > 0]
        if not hot_boxes: hot_boxes = list(range(9))

        # Randomily picks a box within the "hot boxes" and does changes 15 times
        # Each change, there is a 40% chance for a triple rotation to occur instead of a standard 2 value rotation
        for _ in range(15): 
            box = random.choice(hot_boxes)
            if random.random() < 0.4:
                self._triple_rotate_within_box(box)
            else:
                self._swap_within_box(box)

    # A swap between two cells within a subgrid is made randomly for the cells not in the list of given/ set indicies.
    def _swap_within_box(self, box_idx):
        indices = self._get_subgrid_indices_by_box(box_idx)
        swappable = [i for i in indices if i not in self.fixed_indices]
        if len(swappable) >= 2:
            idx1, idx2 = random.sample(swappable, 2)
            self.board[idx1], self.board[idx2] = self.board[idx2], self.board[idx1]

    # A swap between three cells within a given subgrid is made randomly for the cells not in the list of given/ set indicies.
    def _triple_rotate_within_box(self, box_idx):
        indices = self._get_subgrid_indices_by_box(box_idx)
        swappable = [i for i in indices if i not in self.fixed_indices]
        if len(swappable) >= 3:
            idx1, idx2, idx3 = random.sample(swappable, 3)
            self.board[idx1], self.board[idx2], self.board[idx3] = \
                self.board[idx2], self.board[idx3], self.board[idx1]

    # Used in Contraction, this swaps the value in the target cell towards the value of the best board it is being compared to
    def _move_value_to_index(self, target_idx, val):
        box_idx = (target_idx // 27) * 3 + (target_idx % 9 // 3)
        indices = self._get_subgrid_indices_by_box(box_idx)
        for i in indices:
            if self.board[i] == val:
                self.board[target_idx], self.board[i] = self.board[i], self.board[target_idx]
                break

# This validates the initial_board and max_solutions_explored value to make sure they are valid inputs for the program
def initial_validation(initial_board, max_solutions_explored):
    if len(initial_board) != 81 or set(initial_board) - set("123456789."):
        raise ValueError("Invalid board string.")
    if max_solutions_explored <= 0:
        raise ValueError("Budget must be positive.")

# Initiates a star/ Sudoku puzzle's baord state based on the initial string given (with "."'s in it for blank spots), in a subgrid valid way.
def population_initialization(initial_board):
    pop = list(initial_board)
    for box in range(9):
        indices = [r * 9 + c for r in range((box // 3) * 3, (box // 3) * 3 + 3)
                            for c in range((box % 3) * 3, (box % 3) * 3 + 3)]
        fixed = [pop[i] for i in indices if pop[i] != "."]
        missing = list(set("123456789") - set(fixed))
        random.shuffle(missing)
        for i in indices:
            if pop[i] == ".": pop[i] = missing.pop()
    return pop

def main():
    # Evaluates the input for being valid, and throws an error if it is not.
    # Creates a list of the fixed indices
    try:
        initial_board = sys.stdin.readline().strip()
        max_solutions_explored = int(sys.stdin.readline().strip())
        initial_validation(initial_board, max_solutions_explored)
        fixed_cells = [k for k, val in enumerate(initial_board) if val != "."]
    except (ValueError, EOFError):
        sys.exit(1)

    # Default population size is set to 50. This is arbitrary
    # The constellation of stars is initialized
    population_size = 50
    constellation = [Star(population_initialization(initial_board), fixed_cells) 
                     for _ in range(population_size)]
    
    # The Event Horizon Trigger is set at 10% of budget, capped at 500k
    event_horizon_trigger = min(500000, max(5000, max_solutions_explored // 10))
    
    # Evaluations are initialized 
    evaluations = 0

    # First check through the randomly subgrid valid Sudoku boards to see if a "perfect" star was found on initiation
    for star in constellation:
        star.evaluate()
        evaluations += 1
        if star.conflict_count == 0:
            print(f"{''.join(star.board)}\nConflicts: 0")
            return

    # The global best star is created based on the first star in the constellation index with the worst number of conflicts
    global_best_star = min(constellation, key=lambda s: s.conflict_count)


    # Global Stagnation is initiated
    global_stagnation = 0 

    # Phi is initialized
    phi = 0.0
    
    # While the number of evaluations is less than the budget, keep going
    while evaluations < max_solutions_explored:
        # The current best is set
        X_best = max(constellation, key=lambda s: s.luminosity)
        # The tick of the pulsation and contraction is based on the absolute value of the sin and cosine of phi
        T_pulsate = abs(math.sin(phi))
        T_contract = abs(math.cos(phi))
        
        # If the global stagnation is greater than 10% of the budget, trigger the event horizon
        if global_stagnation > event_horizon_trigger:
            for i in range(population_size):
                # Leave the current best alone
                if constellation[i] != X_best:
                    # Chance for the star to be reinitialized from scratch
                    if random.random() < 0.3:
                         constellation[i] = Star(population_initialization(initial_board), fixed_cells)
                    # Otherwise, a supernova is executed against the star, with reference to the global_best_star
                    else:
                        constellation[i] = Star(list(global_best_star.board), fixed_cells)
                        constellation[i].supernova_reset(global_best_star)
            # Global_stagnation and phi are reset
            global_stagnation, phi = 0, 0.0 

        # For each star we pulsated then contract before evaluating the star
        for star in constellation:
            # Initialized the values for each tick of the global clock
            max_int = 9 if star.conflict_count > 20 else 3
            # Phi changes every time an evaluation cycle finishes. This pushes us through the peaks and valleys of sin and cosine waves overtime
            int_p, int_c = round(T_pulsate * max_int), round(T_contract * max_int)

            # If the current star is the current best, there is a low chance to pulsate the star at a low intensity 
            if star == X_best:
                if random.random() < T_pulsate: star.targeted_pulsation()
            # If the star has less than 15 conflicts
            elif star.conflict_count < 15:
                # Chance for a really small pulsation
                if random.random() < 0.05: star.pulsate(1)
                # Contract towards X_best with high intensity
                star.contract_toward(X_best, intensity=9)
            # Otherwise, pulsate at the calculated intensity and contract towards X_best at the calculated intensity
            else:
                star.pulsate(int_p)
                star.contract_toward(X_best, int_c)
            # Each star is evaluated
            star.evaluate()
            evaluations += 1
            # If the star has no errors we can finish the program and escape
            if star.conflict_count == 0:
                print(f"{''.join(star.board)}\nConflicts: 0")
                return
            
            # If the star's luminosity is better than the current global best, we replace it
            if star.luminosity > global_best_star.luminosity:
                global_best_star.board, global_best_star.conflict_count = list(star.board), star.conflict_count
                global_best_star.luminosity, global_stagnation = star.luminosity, 0
            # If not, we increase the global stagnation (which is different than the stagnation_count)
            else:
                global_stagnation += 1
            # If the stagnation count for a given star is greater than 64, supernova_reset.
            # 64 is approximately one full oscillation cycle at the initial phase increment rate.
            if star.stagnation_count > 64:
                star.supernova_reset(global_best_star)
        # Phi is increased
        phi += max(0.01, 0.1 * (1 - (evaluations / max_solutions_explored)))
    # If we do not reach zero conflicts and the number of evaluations has reached the budget, print the current board and the number of conflicts
    print(f"{''.join(global_best_star.board)}\nConflicts: {global_best_star.conflict_count}")

if __name__ == "__main__":
    main()
