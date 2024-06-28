import os
from git import Repo


summer_school_repo = '/home/jovyan/education/hyytiala-practicals/'
if os.path.exists(summer_school_repo):
    # Initialize the repository
    repo = Repo(summer_school_repo)
    # Fetch changes from the remote repository
    repo.remotes.origin.fetch()
    # Pull changes from the remote repository
    repo.git.pull()
else:
    url = 'https://git.wur.nl/peter050/hyytiala-practicals.git'
    Repo.clone_from(url=url, to_path=summer_school_repo)


