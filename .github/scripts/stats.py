#!/usr/bin/env python3
"""
Auto-update GitHub README stats
This script fetches latest GitHub stats and updates the README.md file
"""

import os
import re
import requests
from datetime import datetime
import json

class GitHubStatsUpdater:
    def __init__(self):
        self.username = "arpanchakraborty23"
        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
    def get_github_stats(self):
        """Fetch GitHub user statistics"""
        try:
            url = f"https://api.github.com/users/{self.username}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'public_repos': data.get('public_repos', 0),
                    'followers': data.get('followers', 0),
                    'following': data.get('following', 0),
                    'created_at': data.get('created_at', ''),
                    'updated_at': data.get('updated_at', '')
                }
        except Exception as e:
            print(f"Error fetching GitHub stats: {e}")
            return None
            
    def get_repo_stats(self):
        """Fetch repository statistics"""
        try:
            url = f"https://api.github.com/users/{self.username}/repos"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                repos = response.json()
                total_stars = sum(repo['stargazers_count'] for repo in repos)
                total_forks = sum(repo['forks_count'] for repo in repos)
                languages = {}
                
                for repo in repos:
                    if repo['language']:
                        languages[repo['language']] = languages.get(repo['language'], 0) + 1
                
                return {
                    'total_stars': total_stars,
                    'total_forks': total_forks,
                    'top_languages': sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
                }
        except Exception as e:
            print(f"Error fetching repo stats: {e}")
            return None
    
    def get_contribution_stats(self):
        """Fetch contribution statistics"""
        try:
            # GraphQL query for contribution data
            query = """
            query($username: String!) {
                user(login: $username) {
                    contributionsCollection {
                        totalCommitContributions
                        totalIssueContributions
                        totalPullRequestContributions
                        totalPullRequestReviewContributions
                    }
                    repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
                        totalCount
                        nodes {
                            stargazerCount
                            forkCount
                            primaryLanguage {
                                name
                            }
                        }
                    }
                }
            }
            """
            
            url = "https://api.github.com/graphql"
            response = requests.post(
                url, 
                json={'query': query, 'variables': {'username': self.username}},
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()['data']['user']
                contributions = data['contributionsCollection']
                
                return {
                    'total_commits': contributions['totalCommitContributions'],
                    'total_issues': contributions['totalIssueContributions'],
                    'total_prs': contributions['totalPullRequestContributions'],
                    'total_reviews': contributions['totalPullRequestReviewContributions']
                }
        except Exception as e:
            print(f"Error fetching contribution stats: {e}")
            return None
    
    def update_readme_section(self, readme_content, section_name, new_content):
        """Update a specific section in README"""
        pattern = f"(<!-- {section_name}_START -->)(.*?)(<!-- {section_name}_END -->)"
        replacement = f"\\1\n{new_content}\n\\3"
        return re.sub(pattern, replacement, readme_content, flags=re.DOTALL)
    
    def generate_stats_section(self, stats):
        """Generate updated stats section"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        stats_content = f"""
### 📊 **Live GitHub Statistics** (Last updated: {current_time})

<div align="center">

| 🏆 **Achievements** | 📈 **Activity** | 🌟 **Impact** |
|:-------------------:|:---------------:|:-------------:|
| 📂 {stats.get('public_repos', 'N/A')} Repositories | 💻 {stats.get('total_commits', 'N/A')} Total Commits | ⭐ {stats.get('total_stars', 'N/A')} Total Stars |
| 👥 {stats.get('followers', 'N/A')} Followers | 🔍 {stats.get('total_issues', 'N/A')} Issues Created | 🔀 {stats.get('total_forks', 'N/A')} Total Forks |
| 🤝 {stats.get('following', 'N/A')} Following | 📝 {stats.get('total_prs', 'N/A')} Pull Requests | 📊 Data Science Focus |

</div>
"""
        return stats_content
    
    def run(self):
        """Main execution function"""
        print("🚀 Starting README stats update...")
        
        # Fetch all stats
        github_stats = self.get_github_stats()
        repo_stats = self.get_repo_stats()
        contribution_stats = self.get_contribution_stats()
        
        # Combine stats
        all_stats = {}
        if github_stats:
            all_stats.update(github_stats)
        if repo_stats:
            all_stats.update(repo_stats)
        if contribution_stats:
            all_stats.update(contribution_stats)
        
        if not all_stats:
            print("❌ Failed to fetch GitHub stats")
            return
            
        # Read current README
        try:
            with open('README.md', 'r', encoding='utf-8') as file:
                readme_content = file.read()
        except FileNotFoundError:
            print("❌ README.md not found")
            return
        
        # Generate new stats section
        new_stats_section = self.generate_stats_section(all_stats)
        
        # Check if we have markers in README
        if "<!-- GITHUB_STATS_START -->" in readme_content and "<!-- GITHUB_STATS_END -->" in readme_content:
            # Update existing section
            updated_readme = self.update_readme_section(readme_content, "GITHUB_STATS", new_stats_section)
        else:
            # Add stats section before the last section
            stats_block = f"""
<!-- GITHUB_STATS_START -->
{new_stats_section}
<!-- GITHUB_STATS_END -->

---
"""
            # Insert before the final section
            insertion_point = readme_content.rfind("---\n\n<div align=\"center\">")
            if insertion_point != -1:
                updated_readme = readme_content[:insertion_point] + stats_block + readme_content[insertion_point:]
            else:
                updated_readme = readme_content + "\n" + stats_block
        
        # Write updated README
        try:
            with open('README.md', 'w', encoding='utf-8') as file:
                file.write(updated_readme)
            print("✅ README.md updated successfully!")
            print(f"📊 Stats: {all_stats.get('public_repos', 'N/A')} repos, {all_stats.get('followers', 'N/A')} followers, {all_stats.get('total_stars', 'N/A')} stars")
        except Exception as e:
            print(f"❌ Error writing README: {e}")

if __name__ == "__main__":
    updater = GitHubStatsUpdater()
    updater.run()