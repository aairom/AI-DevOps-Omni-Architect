"""
Git integration utilities
Provides version control operations
"""
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import git
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)

class GitManager:
    """Manages Git operations"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo: Optional[Repo] = None
        self._initialize_repo()
    
    def _initialize_repo(self):
        """Initialize or open existing repository"""
        try:
            self.repo = Repo(self.repo_path)
            logger.info(f"Opened existing repository at {self.repo_path}")
        except git.InvalidGitRepositoryError:
            logger.info(f"No repository found at {self.repo_path}")
            self.repo = None
    
    def init_repo(self) -> Tuple[bool, str]:
        """Initialize a new Git repository"""
        try:
            if self.repo:
                return False, "Repository already exists"
            
            self.repo = Repo.init(self.repo_path)
            logger.info(f"Initialized new repository at {self.repo_path}")
            return True, "Repository initialized successfully"
        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            return False, str(e)
    
    def get_status(self) -> Tuple[bool, str]:
        """Get repository status"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            status = {
                'branch': self.repo.active_branch.name,
                'untracked': self.repo.untracked_files,
                'modified': [item.a_path for item in self.repo.index.diff(None)],
                'staged': [item.a_path for item in self.repo.index.diff('HEAD')]
            }
            
            status_text = f"Branch: {status['branch']}\n"
            status_text += f"Untracked: {len(status['untracked'])} files\n"
            status_text += f"Modified: {len(status['modified'])} files\n"
            status_text += f"Staged: {len(status['staged'])} files"
            
            return True, status_text
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return False, str(e)
    
    def add_files(self, files: List[str]) -> Tuple[bool, str]:
        """Stage files for commit"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            self.repo.index.add(files)
            logger.info(f"Staged {len(files)} files")
            return True, f"Staged {len(files)} files successfully"
        except Exception as e:
            logger.error(f"Failed to stage files: {e}")
            return False, str(e)
    
    def commit(self, message: str) -> Tuple[bool, str]:
        """Commit staged changes"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            commit = self.repo.index.commit(message)
            logger.info(f"Created commit: {commit.hexsha[:7]}")
            return True, f"Commit created: {commit.hexsha[:7]}"
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            return False, str(e)
    
    def create_branch(self, branch_name: str) -> Tuple[bool, str]:
        """Create a new branch"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            new_branch = self.repo.create_head(branch_name)
            logger.info(f"Created branch: {branch_name}")
            return True, f"Branch '{branch_name}' created successfully"
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            return False, str(e)
    
    def checkout_branch(self, branch_name: str) -> Tuple[bool, str]:
        """Switch to a different branch"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            self.repo.git.checkout(branch_name)
            logger.info(f"Checked out branch: {branch_name}")
            return True, f"Switched to branch '{branch_name}'"
        except Exception as e:
            logger.error(f"Failed to checkout branch: {e}")
            return False, str(e)
    
    def get_branches(self) -> Tuple[bool, List[str]]:
        """Get list of all branches"""
        if not self.repo:
            return False, []
        
        try:
            branches = [head.name for head in self.repo.heads]
            return True, branches
        except Exception as e:
            logger.error(f"Failed to get branches: {e}")
            return False, []
    
    def get_diff(self, file_path: Optional[str] = None) -> Tuple[bool, str]:
        """Get diff of changes"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            if file_path:
                diff = self.repo.git.diff(file_path)
            else:
                diff = self.repo.git.diff()
            
            return True, diff if diff else "No changes"
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return False, str(e)
    
    def get_log(self, max_count: int = 10) -> Tuple[bool, str]:
        """Get commit history"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            commits = list(self.repo.iter_commits(max_count=max_count))
            log_text = ""
            
            for commit in commits:
                log_text += f"{commit.hexsha[:7]} - {commit.author.name}\n"
                log_text += f"  {commit.message.strip()}\n"
                log_text += f"  {commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            return True, log_text if log_text else "No commits"
        except Exception as e:
            logger.error(f"Failed to get log: {e}")
            return False, str(e)
    
    def push(self, remote: str = "origin", branch: Optional[str] = None) -> Tuple[bool, str]:
        """Push changes to remote"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            if not branch:
                branch = self.repo.active_branch.name
            
            origin = self.repo.remote(remote)
            origin.push(branch)
            logger.info(f"Pushed to {remote}/{branch}")
            return True, f"Successfully pushed to {remote}/{branch}"
        except Exception as e:
            logger.error(f"Failed to push: {e}")
            return False, str(e)
    
    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> Tuple[bool, str]:
        """Pull changes from remote"""
        if not self.repo:
            return False, "No repository initialized"
        
        try:
            if not branch:
                branch = self.repo.active_branch.name
            
            origin = self.repo.remote(remote)
            origin.pull(branch)
            logger.info(f"Pulled from {remote}/{branch}")
            return True, f"Successfully pulled from {remote}/{branch}"
        except Exception as e:
            logger.error(f"Failed to pull: {e}")
            return False, str(e)

# Made with Bob
