# github_api.py
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitHubAPI:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
    
    def get_repo_info(self, repo_full_name: str) -> Optional[Dict]:
        """Get repository information from GitHub API"""
        try:
            url = f'{self.base_url}/repos/{repo_full_name}'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched repo info for: {repo_full_name}")
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Repository not found: {repo_full_name}")
            elif response.status_code == 403:
                logger.error(f"Forbidden access to: {repo_full_name}")
            elif response.status_code == 401:
                logger.error(f"Invalid authentication for: {repo_full_name}")
            elif response.status_code == 429:
                logger.error(f"Rate limit exceeded for: {repo_full_name}")
            else:
                logger.error(f"GitHub API error {response.status_code} for {repo_full_name}: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {repo_full_name}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {repo_full_name}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {repo_full_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for {repo_full_name}: {str(e)}")
            
        return None
    
    def get_latest_commits(self, repo_full_name: str, branch: str = 'main', since: datetime = None) -> List[Dict]:
        """Get latest commits from a repository"""
        try:
            url = f'{self.base_url}/repos/{repo_full_name}/commits'
            
            params = {'sha': branch, 'per_page': 20}
            if since:
                params['since'] = since.strftime('%Y-%m-%dT%H:%M:%SZ')
                
            logger.info(f"Fetching commits for {repo_full_name} (branch: {branch}) since {since if since else 'beginning'}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                commits = response.json()
                parsed_commits = []
                
                logger.info(f"Retrieved {len(commits)} commits from {repo_full_name}")
                
                for commit in commits:
                    try:
                        # Parse basic commit info
                        commit_info = {
                            'sha': commit['sha'],
                            'message': commit['commit']['message'].strip(),
                            'author_name': commit['commit']['author']['name'],
                            'author_email': commit['commit']['author']['email'],
                            'date': datetime.strptime(
                                commit['commit']['author']['date'],
                                '%Y-%m-%dT%H:%M:%SZ'
                            ),
                            'url': commit['html_url'],
                            'repo_full_name': repo_full_name,
                            'added': 0,
                            'removed': 0,
                            'modified': 0,
                            'files': []
                        }
                        
                        # Try to get detailed commit information
                        try:
                            detail_url = f'{self.base_url}/repos/{repo_full_name}/commits/{commit["sha"]}'
                            detail_resp = requests.get(detail_url, headers=self.headers, timeout=10)
                            
                            if detail_resp.status_code == 200:
                                detail = detail_resp.json()
                                if 'files' in detail:
                                    for f in detail['files']:
                                        status = f.get('status', '')
                                        if status == 'added':
                                            commit_info['added'] += 1
                                        elif status == 'removed':
                                            commit_info['removed'] += 1
                                        elif status == 'modified':
                                            commit_info['modified'] += 1
                                    
                                    commit_info['files'] = [f['filename'] for f in detail['files'][:5]]
                                    logger.debug(f"Got file details for commit {commit['sha'][:7]}: "
                                                f"+{commit_info['added']} -{commit_info['removed']} ~{commit_info['modified']}")
                        except Exception as e:
                            logger.warning(f"Failed to get commit details for {commit['sha'][:7]}: {str(e)}")
                        
                        parsed_commits.append(commit_info)
                        
                    except KeyError as e:
                        logger.warning(f"Missing field in commit data for {repo_full_name}: {str(e)}")
                        continue
                    except ValueError as e:
                        logger.warning(f"Date parsing error for commit in {repo_full_name}: {str(e)}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error parsing commit in {repo_full_name}: {str(e)}")
                        continue
                
                logger.info(f"Successfully parsed {len(parsed_commits)} commits for {repo_full_name}")
                return parsed_commits
                
            elif response.status_code == 404:
                logger.error(f"Repository {repo_full_name} not found")
            elif response.status_code == 409:
                logger.error(f"Repository {repo_full_name} is empty")
            elif response.status_code == 403:
                logger.error(f"Access forbidden to {repo_full_name}")
            else:
                logger.error(f"Error getting commits for {repo_full_name}: {response.status_code} - {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for commits in {repo_full_name}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for commits in {repo_full_name}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for commits in {repo_full_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for commits in {repo_full_name}: {str(e)}")
            
        return []
    
    def test_connection(self) -> bool:
        """Test GitHub API connection"""
        try:
            url = f'{self.base_url}/user'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Successfully connected to GitHub as: {user_data.get('login')}")
                return True
            elif response.status_code == 401:
                logger.error("Invalid GitHub token")
            elif response.status_code == 403:
                logger.error("Token access is restricted")
            else:
                logger.error(f"Connection error: {response.status_code}")
                
            return False
            
        except requests.exceptions.Timeout:
            logger.error("Connection to GitHub API timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Connection error to GitHub API")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing connection: {str(e)}")
            return False
    
    def get_rate_limit(self) -> Dict:
        """Get GitHub API rate limit status"""
        try:
            url = f'{self.base_url}/rate_limit'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error getting rate limit: {str(e)}")
            return {}
    
    def get_branches(self, repo_full_name: str) -> List[Dict]:
        """Get all branches of a repository"""
        try:
            url = f'{self.base_url}/repos/{repo_full_name}/branches'
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                branches = response.json()
                logger.info(f"Retrieved {len(branches)} branches for {repo_full_name}")
                return branches
            else:
                logger.error(f"Error getting branches for {repo_full_name}: {response.status_code}")
            return []
        except requests.exceptions.Timeout:
            logger.error(f"Timeout getting branches for {repo_full_name}")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error getting branches for {repo_full_name}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting branches for {repo_full_name}: {str(e)}")
            return []


if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) > 1:
        token = sys.argv[1]
        github = GitHubAPI(token)
        
        logger.info("Testing GitHub API connection...")
        
        if github.test_connection():
            logger.info("Connection successful")
            
            logger.info("Testing repository info retrieval...")
            repo_info = github.get_repo_info("octocat/Hello-World")
            if repo_info:
                logger.info(f"Repository: {repo_info['full_name']}")
                logger.info(f"Description: {repo_info.get('description', 'No description')}")
                logger.info(f"Default branch: {repo_info.get('default_branch', 'main')}")
            
            logger.info("Testing commits retrieval...")
            commits = github.get_latest_commits("octocat/Hello-World", "main")
            if commits:
                logger.info(f"{len(commits)} commits retrieved")
                logger.info(f"Latest commit: {commits[0]['message'][:50]}...")
            
            logger.info("Testing rate limit status...")
            rate_limit = github.get_rate_limit()
            if rate_limit:
                core = rate_limit.get('resources', {}).get('core', {})
                remaining = core.get('remaining', 0)
                limit = core.get('limit', 0)
                logger.info(f"Rate limit remaining: {remaining}/{limit}")
        else:
            logger.error("Connection failed")
    else:
        logger.warning("Please provide a GitHub Token as an argument:")
        logger.warning("   python github_api.py YOUR_GITHUB_TOKEN")