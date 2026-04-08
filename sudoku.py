"""
File: sudoku.py
Author: Jacob Hall-Burns

"""

import random
import math
import sys

class Star:
    def __init__(self, board_list, fixed_indices):
        self.board = board_list
        self.fixed_indices = set(fixed_indices)
        self.luminosity = 0.0
        self.conflict_count = 999
        self.stagnation_count = 0
        self.conflict_map = [0] * 81

    def evaluate(self):
        old_conflicts = self.conflict_count
        self.conflict_map = [0] * 81
        for i in range(9):
            self._mark_conflicts([i*9 + j for j in range(9)])
            self._mark_conflicts([j*9 + i for j in range(9)])
            
        self.conflict_count = sum(1 for x in self.conflict_map if x > 0)
        self.luminosity = 1 / (1 + self.conflict_count)
        
        if old_conflicts != 999 and self.conflict_count >= old_conflicts:
            self.stagnation_count += 1
        else:
            self.stagnation_count = 0
        return self.conflict_count

    def _mark_conflicts(self, indices):
        seen = {}
        for idx in indices:
            val = self.board[idx]
            if val in seen:
                self.conflict_map[idx] += 1
                self.conflict_map[seen[val]] += 1
            else:
                seen[val] = idx

    def _get_subgrid_indices_by_box(self, box_idx):
        start_row, start_col = (box_idx // 3) * 3, (box_idx % 3) * 3
        return [r * 9 + c for r in range(start_row, start_row + 3)
                          for c in range(start_col, start_col + 3)]

    def pulsate(self, intensity):
        if intensity == 0: return
        box_heats = []
        for i in range(9):
            indices = self._get_subgrid_indices_by_box(i)
            heat = sum(self.conflict_map[idx] for idx in indices)
            box_heats.append((i, heat))
        
        box_heats.sort(key=lambda x: x[1], reverse=True)
        for i in range(min(intensity, 9)):
            box_idx, heat = box_heats[i]
            if heat > 0:
                # chance for a Triple-Rotation when intensity is high
                if intensity > 7 and random.random() < 0.3:
                    self._triple_rotate_within_box(box_idx)
                else:
                    self._swap_within_box(box_idx)

    def contract_toward(self, X_best, intensity):
        if intensity == 0: return
        diff_indices = [i for i in range(81) if self.board[i] != X_best.board[i] 
                        and i not in self.fixed_indices]
        if not diff_indices: return
        random.shuffle(diff_indices)
        
        # the intensity is reduced if the star is already close in simularity to the best star
        limit = intensity if self.conflict_count > 10 else max(1, intensity // 3)
        
        for i in range(min(limit, len(diff_indices))):
            idx_to_fix = diff_indices[i]
            target_val = X_best.board[idx_to_fix]
            self._move_value_to_index(idx_to_fix, target_val)

    def targeted_pulsation(self):
        self.pulsate(intensity=3)

    def supernova_reset(self, global_best_star):
        self.board = list(global_best_star.board)
        self.stagnation_count = 0
        hot_boxes = [i for i in range(9) if sum(self.conflict_map[idx] 
                     for idx in self._get_subgrid_indices_by_box(i)) > 0]
        if not hot_boxes: hot_boxes = list(range(9))

        # A Mix of swaps and rotations on reset
        for _ in range(15): 
            box = random.choice(hot_boxes)
            if random.random() < 0.4:
                self._triple_rotate_within_box(box)
            else:
                self._swap_within_box(box)

    def _swap_within_box(self, box_idx):
        indices = self._get_subgrid_indices_by_box(box_idx)
        swappable = [i for i in indices if i not in self.fixed_indices]
        if len(swappable) >= 2:
            idx1, idx2 = random.sample(swappable, 2)
            self.board[idx1], self.board[idx2] = self.board[idx2], self.board[idx1]

    def _triple_rotate_within_box(self, box_idx):
        """Description: Breaks local cycles by rotating three values in a subgrid."""
        indices = self._get_subgrid_indices_by_box(box_idx)
        swappable = [i for i in indices if i not in self.fixed_indices]
        if len(swappable) >= 3:
            idx1, idx2, idx3 = random.sample(swappable, 3)
            self.board[idx1], self.board[idx2], self.board[idx3] = \
                self.board[idx2], self.board[idx3], self.board[idx1]

    def _move_value_to_index(self, target_idx, val):
        box_idx = (target_idx // 27) * 3 + (target_idx % 9 // 3)
        indices = self._get_subgrid_indices_by_box(box_idx)
        for i in indices:
            if self.board[i] == val:
                self.board[target_idx], self.board[i] = self.board[i], self.board[target_idx]
                break

def initial_validation(initial_board, max_solutions_explored):
    if len(initial_board) != 81 or set(initial_board) - set("123456789."):
        raise ValueError("Invalid board string.")
    if max_solutions_explored <= 0:
        raise ValueError("Budget must be positive.")

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
    try:
        initial_board = sys.stdin.readline().strip()
        max_solutions_explored = int(sys.stdin.readline().strip())
        initial_validation(initial_board, max_solutions_explored)
        fixed_cells = [k for k, val in enumerate(initial_board) if val != "."]
    except (ValueError, EOFError):
        sys.exit(1)

    population_size = 50
    constellation = [Star(population_initialization(initial_board), fixed_cells) 
                     for _ in range(population_size)]
    
    # 10% of budget, capped at 500k
    event_horizon_trigger = min(500000, max(5000, max_solutions_explored // 10))
    
    evaluations = 0
    for star in constellation:
        star.evaluate()
        evaluations += 1
        if star.conflict_count == 0:
            print(f"{''.join(star.board)}\nSolutions Explored: {evaluations}\nConflicts: 0")
            return

    global_best_star = Star(list(constellation[0].board), fixed_cells)
    global_best_star.conflict_count = 999
    global_stagnation = 0 
    phi = 0.0
    
    while evaluations < max_solutions_explored:
        X_best = max(constellation, key=lambda s: s.luminosity)
        T_pulsate = abs(math.sin(phi))
        T_contract = abs(math.cos(phi))
        
        if global_stagnation > event_horizon_trigger:
            for i in range(population_size):
                if constellation[i] != X_best:
                    # Crossover/Hybrid re-population
                    if random.random() < 0.3:
                         constellation[i] = Star(population_initialization(initial_board), fixed_cells)
                    else:
                        constellation[i] = Star(list(global_best_star.board), fixed_cells)
                        constellation[i].supernova_reset(global_best_star)
            global_stagnation, phi = 0, 0.0 

        for star in constellation:
            max_int = 9 if star.conflict_count > 20 else 3
            int_p, int_c = round(T_pulsate * max_int), round(T_contract * max_int)

            if star == X_best:
                if random.random() < T_pulsate: star.targeted_pulsation()
            elif star.conflict_count < 15:
                if random.random() < 0.05: star.pulsate(1)
                star.contract_toward(X_best, intensity=9)
            else:
                star.pulsate(int_p)
                star.contract_toward(X_best, int_c)
            
            star.evaluate()
            evaluations += 1
            
            if star.conflict_count == 0:
                print(f"{''.join(star.board)}\nSolutions Explored: {evaluations}\nConflicts: 0")
                return
            
            if star.luminosity > global_best_star.luminosity:
                global_best_star.board, global_best_star.conflict_count = list(star.board), star.conflict_count
                global_best_star.luminosity, global_stagnation = star.luminosity, 0
            else:
                global_stagnation += 1
            
            if star.stagnation_count > 64:
                star.supernova_reset(global_best_star)
        
        phi += max(0.01, 0.1 * (1 - (evaluations / max_solutions_explored)))

    print(f"{''.join(global_best_star.board)}\nSolutions Explored: {evaluations}\nConflicts: {global_best_star.conflict_count}")

if __name__ == "__main__":
    main()