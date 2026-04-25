"""
File: research_suite.py
Author: Jacob Hall-Burns

Description:
    A multi-threaded benchmarking suite for the Sudoku SOO. This script 
    utilizes concurrent process pools to execute independent trials in 
    parallel across all available CPU cores. It provides real-time 
    telemetry via a progress bar and exports results to CSV for 
    statistical analysis.

Arguments:
    - PUZZLE: The 81-character Sudoku string to test.
    - BUDGET: The evaluation limit per trial.
    - TOTAL_TRIALS: Number of independent runs to perform.

Outputs:
    - experiment_results.csv: Raw data for every trial.
    - Terminal: Summary statistics (Success rate, Avg evals).
"""

import subprocess
import concurrent.futures
import time
import csv
import os
import sys
from tqdm import tqdm

# --- BENCHMARK CONFIGURATION ---
PUZZLE = ".9.2.1.....4..8.7..7..69..814...58...6.....2...86...472..34..6..3.1..7.....8.2.1."
BUDGET = 5000000
TOTAL_TRIALS = 32  
MAX_WORKERS = os.cpu_count()  # Detects your 16 cores on Fedora

def run_single_trial(trial_id):
    """
    Description: Spawns a sudoku.py subprocess and captures its output.
    Returns: Dictionary containing performance metrics for the trial.
    """
    start_time = time.time()
    
    try:
        # Spawning the worker script
        process = subprocess.Popen(
            ['python3', 'sudoku.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Passing input via stdin to match the main() try/except block
        input_data = f"{PUZZLE}\n{BUDGET}\n"
        stdout, stderr = process.communicate(input=input_data)
        
        duration = time.time() - start_time
        lines = stdout.strip().split('\n')
        
        # Expected output format:
        # [81-char board]
        # Solutions Explored: X
        # Conflicts: Y
        conflicts = int(lines[-1].split(': ')[1])
        evals = int(lines[-2].split(': ')[1])
        
        return {
            "id": trial_id,
            "success": 1 if conflicts == 0 else 0,
            "evaluations": evals,
            "conflicts": conflicts,
            "time_sec": round(duration, 2)
        }
    except Exception as e:
        # Catch errors (e.g., if sudoku.py crashes or output isn't as expected)
        return {
            "id": trial_id, 
            "success": 0, 
            "evaluations": BUDGET, 
            "conflicts": 99, 
            "time_sec": round(time.time() - start_time, 2),
            "error": str(e)
        }

def main():
    print(f"--- Starting SOO Research Suite ---")
    print(f"Target Puzzle: {PUZZLE}")
    print(f"Cores Active:  {MAX_WORKERS}")
    print(f"Total Trials:  {TOTAL_TRIALS}")
    print(f"----------------------------------")

    results = []

    # Parallel Execution via ProcessPool (CPU-bound tasks)
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Map trial IDs to futures
        future_to_trial = {executor.submit(run_single_trial, i): i for i in range(1, TOTAL_TRIALS + 1)}
        
        # Initialize tqdm progress bar
        with tqdm(total=TOTAL_TRIALS, desc="Stellar Search Progress", unit="trial", file=sys.stdout) as pbar:
            for future in concurrent.futures.as_completed(future_to_trial):
                res = future.result()
                results.append(res)
                
                # Update bar with live feedback of the most recent result
                status = "✔" if res['success'] else "✘"
                pbar.set_postfix_str(f"Trial {res['id']} {status} ({res['conflicts']} conf)")
                pbar.update(1)

    # Exporting data for research visualization
    csv_file = 'experiment_results2.csv'
    with open(csv_file, 'w', newline='') as f:
        fieldnames = ["id", "success", "evaluations", "conflicts", "time_sec"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Filter results to match fieldnames only (removes potential error keys)
        writer.writerows([{k: v for k, v in r.items() if k in fieldnames} for r in results])

    # Final Statistics for the Senior Design Report
    success_count = sum(r['success'] for r in results)
    avg_evals = sum(r['evaluations'] for r in results if r['success']) / success_count if success_count else 0
    
    print(f"\n--- Statistical Summary ---")
    print(f"Success Rate: {success_count}/{TOTAL_TRIALS} ({round(success_count/TOTAL_TRIALS * 100, 2)}%)")
    if success_count > 0:
        print(f"Avg Evaluations to Solve: {int(avg_evals)}")
    print(f"Detailed data exported to {csv_file}")

if __name__ == "__main__":
    main()
