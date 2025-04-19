from github import Github
import os
from collections import defaultdict

# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # Set your GitHub personal access token as an environment variable
if not GITHUB_TOKEN:
    print("Error: Please set the GITHUB_TOKEN environment variable.")
    exit()

g = Github(GITHUB_TOKEN)

def analyze_repository_conflict_risk(repo_name):
    """
    Analyzes a GitHub repository and predicts the potential for future conflicts.

    Args:
        repo_name (str): The full name of the repository (e.g., "owner/repo").

    Returns:
        dict: A dictionary containing the analysis results and a risk assessment.
    """
    try:
        repo = g.get_repo(repo_name)
    except Exception as e:
        return {"error": f"Could not access repository: {e}"}

    analysis = {
        "repository": repo_name,
        "num_contributors": repo.get_contributors().totalCount,
        "num_open_pulls": repo.get_pulls(state='open').totalCount,
        "frequently_modified_files": defaultdict(int),
        "recent_merge_conflicts": 0,
        "large_pull_requests": 0,
        "branching_strategy_notes": "Analysis of branching strategy is basic and may require manual review.",
        "risk_score": 0,
        "risk_level": "Low",
        "count_of_modified_files": 0,
        "commit_history_size": 0,
        "disparity_in_location": 0,
    }

    # Analyze commit history for frequently modified files (basic approach)
    commits = repo.get_commits(since=repo.created_at)  # Consider a more recent timeframe for better relevance
    for commit in commits:
        try:
            for file in commit.files:
                analysis["frequently_modified_files"][file.filename] += 1
        except Exception as e:
            print(f"Error processing commit {commit.sha}: {e}")

    # Analyze open pull requests for size (very basic)
    for pull in repo.get_pulls(state='open'):
        try:
            if pull.deletions + pull.additions > 500:  # Arbitrary threshold for a "large" PR
                analysis["large_pull_requests"] += 1
        except Exception as e:
            print(f"Error processing pull request {pull.number}: {e}")


    # Attempt to identify branching strategy (very basic)
    branches = [branch.name for branch in repo.get_branches()]
    if "main" in branches and "develop" in branches:
        analysis["branching_strategy_notes"] = "Detected 'main' and 'develop' branches, potentially indicating a Gitflow-like strategy."
    elif "main" in branches or "master" in branches:
        analysis["branching_strategy_notes"] = "Detected a primary branch ('main' or 'master')."
    else:
        analysis["branching_strategy_notes"] = "Could not easily identify a standard branching strategy."

    # Check for recent closed pull requests with merge conflicts (requires more detailed analysis)
    closed_pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')[:50] # Check the last 50 closed PRs
    for pull in closed_pulls:
        if pull.merge_commit_sha is None and pull.merged_at is None: # Likely a closed PR with conflicts
            analysis["recent_merge_conflicts"] += 1
    
    analysis["count_of_modified_files"] = len(analysis["frequently_modified_files"])
        # size of commit history
    # Output
    commit_history_size = len(list(repo.get_commits()))
    num_contributors = repo.get_contributors().totalCount
    num_open_pulls = repo.get_pulls(state='open').totalCount
    count_of_modified_files = len(analysis["frequently_modified_files"])
    disparity_in_location = repo.get_contents("src/").totalCount

    # find the number of locations of midified files
    for file in analysis["frequently_modified_files"]:  
        if file.startswith("src/"):
            analysis["disparity_in_location"] += 1


    # --- Risk Scoring (Simple Heuristic) ---
    analysis["risk_score"] += analysis["num_contributors"] * 0.5
    analysis["risk_score"] += analysis["num_open_pulls"] * 1
    analysis["risk_score"] += len(analysis["frequently_modified_files"]) * 0.2
    analysis["risk_score"] += analysis["recent_merge_conflicts"] * 3
    analysis["risk_score"] += analysis["large_pull_requests"] * 2
    analysis["risk_score"] += analysis["count_of_modified_files"] * 0.1

    analysis["risk_score"] += analysis["commit_history_size"] * 0.01

    if analysis["risk_score"] > 50:
        analysis["risk_level"] = "High"
    elif analysis["risk_score"] > 25:
        analysis["risk_level"] = "Medium"
    else:
        analysis["risk_level"] = "Low"

    return analysis

if __name__ == "__main__":
    repo_to_analyze = input("Enter the GitHub repository name (e.g., facebook/react): ")
    risk_assessment = analyze_repository_conflict_risk(repo_to_analyze)
    print("\n--- commit_history_size ---")
    print(commit_history_size)
    print("\n--- num_contributors ---")
    print(num_contributors)
    print("\n--- num_open_pulls ---")
    print(num_open_pulls)
    print("\n--- Conflict Risk Assessment ---")
    for key, value in risk_assessment.items():
          print(f"{key}: {value}")