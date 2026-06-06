from git import Repo, GitCommandError
from os import getenv
from pathlib import Path
from contextlib import chdir, suppress
from time import perf_counter
import requests, sys, logging, subprocess, shutil

logging.basicConfig(stream=sys.stdout, format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

git_repo = getenv('GIT_REPO')
token = getenv('GIT_TOKEN')
username = getenv('GIT_USERNAME')
match_pattern = getenv('MATCH_PATTERN', '*-diagram.py')
repo_branch = getenv('REPO_BRANCH', 'main')
commit_message = getenv('COMMIT_MESSAGE', 'docs: automated diagram updates from diagrams script')
dry_run = getenv('DRY_RUN', 'yes').lower()

start_time = perf_counter()
logger.info("Starting Diagrams Repo Runner")

remote_url = f"https://{username}:{token}@github.com/{username}/{git_repo}.git"
authenticated_url = f"https://{username}:{token}@://github.com"

local_path = "/app/github/git_clone"
file_list = []

def exit_message(log_type, message):
    end_time = perf_counter()
    execution_time = end_time - start_time
    processing_time = f"Total processing time {execution_time:.2f}s"
    with suppress(FileNotFoundError):
        shutil.rmtree(local_path)

    if log_type == "info":
        logger.info(message)
        logger.info(processing_time)
        sys.exit(0)
    elif log_type == "warning":
        logger.warning(message)
        logger.info(processing_time)
        sys.exit(0)
    else:
        logger.error(message)
        logger.info(processing_time)
        sys.exit(1)

# Input checks
checks = [(git_repo, 'git_repo'), (token, 'token'), (username, 'username'), (match_pattern, 'match_pattern'), (repo_branch, 'repo_branch'), (commit_message, 'commit_message'), (dry_run, 'dry_run')]

try:
    for variable, name in checks:
        if variable.strip() == "":
            exit_message('error', f"Missing {name}, please update your environment variables")
except AttributeError:
    exit_message('error', 'No environment variables passed in. Exiting.')

if dry_run not in ("yes", "no"):
    exit_message('error', 'Dry run setting not set properly')
else:
    if dry_run == "yes":
        logger.info('Starting dry run')
    else:
        logger.info('Starting live run')

try:
    response = requests.head(remote_url, allow_redirects=True, timeout=5).status_code

    if response < 400:
        logger.info('Git URL Verified. Continuing')
    else:
        exit_message('error', f"Error, invalid URL: {remote_url} Exiting.")
except requests.exceptions.RequestException as e:
    exit_message('error', f"An error occurred: {e}")

### Start the main portion of the script

# Delete folder if it still exists
with suppress(FileNotFoundError):
    shutil.rmtree(local_path)

# Clone the repo
try:
    repo = Repo.clone_from(remote_url, local_path, branch=repo_branch)
    logger.info("Clone complete")
except NameError:
    exit_message('error', "Unable to clone repo, please try again later.")

# Set remote origin
origin = repo.remotes.origin

# Pull from the specified branch
try:
    origin.pull(repo_branch)
    logger.info(f"Successfully pulled from {repo_branch}")
except GitCommandError as e:
    exit_message('error', f"Pull failed: {e.stderr}")
except Exception as e:
    exit_message('error', f"An error occurred: {e.stderr}")

# Find all files matching the pattern
logger.info(f"Looking for files matching: {match_pattern}")
for file_path in Path(local_path).rglob(match_pattern):
    if file_path.is_file():
        file_list.append({"path": file_path.parent, "file": file_path.name})

# Check that files were found
if not file_list:
    exit_message('error', f"No files matching pattern: {match_pattern} - Exiting now")

# Run diagrams against the files
try:
    for file in file_list:
        logger.info(f"Path: {file.get('path')} File: {file.get('file')}")
        with chdir(file.get('path')):
            file_name = str(file.get('file'))
            logger.info(f"Creating diagram for: {file.get('file')}")
            subprocess.run([sys.executable, file.get('file')])
except Exception as e:
    exit_message('error', f"An error occurred with the file: {e.stderr}")

if dry_run != "yes":
    # Stage the changed files
    repo.git.add(A=True)

    # Commit the changes
    if repo.is_dirty() or repo.untracked_files:
        logger.info(f"Committing changes with message: '{commit_message}'")
        repo.index.commit(commit_message)
    else:
        exit_message('info', "There were no changes to commit, exiting")

    # Push back up to repo
    try:
        origin.push(refspec=f"{repo.active_branch.name}:{repo_branch}")
        logger.info(f"Successfully pushed to {repo_branch}")
        exit_message('info', "All done here!")
    except GitCommandError as e:
        message = print(f"Push failed: {e.stderr}")
        exit_message('error', message)
    except Exception as e:
        exit_message('error', f"An error occurred: {e.stderr}")
else: 
    logger.info(f"Dry run completed! Files will be available until the next run.")
    sys.exit(0)
