import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def analyze():
    # Load the data
    try:
        df = pd.read_csv('experiment_results2.csv')
    except FileNotFoundError:
        print("Error: experiment_results.csv not found.")
        return

    # 1. Basic Metrics
    total_trials = len(df)
    successes = df[df['success'] == 1]
    failures = df[df['success'] == 0]
    
    success_rate = (len(successes) / total_trials) * 100
    avg_solve_time = successes['time_sec'].mean() if not successes.empty else 0
    avg_fail_conflicts = failures['conflicts'].mean() if not failures.empty else 0

    print(f"--- SOO Benchmarking Summary ---")
    print(f"Total Trials:      {total_trials}")
    print(f"Success Rate:      {success_rate:.2f}%")
    print(f"Avg Solve Time:    {avg_solve_time:.2f}s")
    print(f"Avg Hangup Score:  {avg_fail_conflicts:.2f} conflicts")

    # --- VISUALIZATION ---
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Graph 1: Conflict Distribution (The "Hangup" Map)
    sns.histplot(df['conflicts'], bins=range(0, int(df['conflicts'].max()) + 2), 
                 kde=False, ax=axes[0], color='skyblue')
    axes[0].set_title('Final Conflict Distribution\n(Identifying Local Optima)')
    axes[0].set_xlabel('Conflicts at Termination')
    axes[0].set_ylabel('Frequency (Trials)')

    # Graph 2: Time vs. Success
    sns.boxplot(x='success', y='time_sec', data=df, ax=axes[1], palette='Set2')
    axes[1].set_xticklabels(['Fail', 'Success'])
    axes[1].set_title('Execution Time by Outcome')
    axes[1].set_xlabel('Outcome')
    axes[1].set_ylabel('Time (Seconds)')

    # Graph 3: Efficiency Scatter
    # Trials that solve quickly are in the bottom left.
    sns.scatterplot(x='evaluations', y='time_sec', hue='success', style='success', 
                    data=df, ax=axes[2], s=100)
    axes[2].set_title('Search Efficiency\n(Evals vs. Wall Time)')
    
    plt.tight_layout()
    plt.savefig('soo_analysis_summary2.png')
    print("\nGraphs saved to: soo_analysis_summary2.png")

if __name__ == "__main__":
    analyze()
