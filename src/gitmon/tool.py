import logging
from pathlib import Path
import subprocess
from urllib import parse as urlparse
#-
import pygit2

_logger = logging.getLogger(__name__)

def process_work_subject(work_subject):
    """Check git repository for remote updates and run a command
    """
    assert 'path' in work_subject
    repo_url = work_subject.get('repo_url')
    remote_name = work_subject.get('remote', 'origin')
    branch_name = work_subject.get('branch', 'main')
    use_force = int(work_subject.get('force', '0'))
    ssh_keyfile = work_subject.get('ssh_keyfile')
    ssh_keyfile_pass = work_subject.get('ssh_keyfile_password')
    command_logfile = work_subject.get('command_logfile')

    commands = work_subject.get('command', [])
    if commands:
        commands = [commands]
    commands.extend(work_subject.get('commands', []))

    options = {}
    if ssh_keyfile:
        options['ssh_keyfile'] = Path(ssh_keyfile).expanduser().resolve()
        options['ssh_keyfile_pass'] = ssh_keyfile_pass

    run_command = False

    work_path = Path(work_subject['path']).expanduser().resolve()
    repo_path = pygit2.discover_repository(work_path)
    if repo_path:
        # Get updates
        repo, latest_commit = update_repo(work_path, branch_name, remote_name,
                options)
        if latest_commit != repo.head.target:
            run_command = True

        merge_result, _ = repo.merge_analysis(latest_commit)
        if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
            _logger.info("Workspace %s is up to date", work_path)
        elif not (merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD) and\
                not use_force:
            # We have merge conflicts, was told not to force update
            _logger.warning("Workspace %s has merge conflicts, do nothing",
                    work_path)
            return
        else:
            # Update working files
            _logger.info("Updating workspace %s", work_path)
            update_work_directory(repo, remote_name, branch_name)

    elif repo_url:
        repo, _ = clone_repo(work_path, repo_url, branch_name, remote_name, options)
        run_command = True
        update_work_directory(repo, remote_name, branch_name)

    else:
        raise RuntimeError(f"Invalid git work directory in {work_path}")

    if run_command and commands:
        if command_logfile:
            log_path = Path(command_logfile).expanduser().resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open('wb') as f:
                for command in commands:
                    f.write(f"\n#!{command}\n\n".encode())
                    f.flush()
                    subprocess.call(command, shell=True, stdout=f, stderr=f)
        else:
            for command in commands:
                subprocess.call(command, shell=True)


def update_repo(path, branch_name, remote_name, options):
    """Update remote information and peek latest commit
    """
    repo = pygit2.Repository(path)
    if remote_name not in repo.remotes.names():
        raise RuntimeError(f"Unknown remote: {remote_name}")
    remote = repo.remotes[remote_name]

    return (repo, fetch_remote(remote, branch_name, options))


def clone_repo(path, url, branch_name, remote_name, options):
    """Create git working directory if not exists
    """
    _logger.info("Creating workspace %s from repository %s", path, url)
    repo = pygit2.init_repository(path)
    remote = repo.remotes.create(remote_name, url)

    return (repo, fetch_remote(remote, branch_name, options))


def fetch_remote(remote, branch_name, options):
    """Fetch from upstream, return last commit in branch
    """
    scheme, username = extract_info_from_url(remote.url)
    if not scheme and 'ssh_keyfile' in options:
        credentials = pygit2.Keypair(username, f"{options['ssh_keyfile']}.pub",
                options['ssh_keyfile'], options.get('ssh_keyfile_pass') or '')
        callbacks = pygit2.RemoteCallbacks(credentials=credentials)
    else:
        callbacks = None

    retries = 3
    while True:
        try:
            remote.fetch(callbacks=callbacks)
            break
        except pygit2.GitError as e:
            retries -= 1
            if not (retries and 'timed out' in str(e)):
                raise e

    for remote_head in remote.ls_remotes(callbacks=callbacks):
        if remote_head['symref_target'] != f'refs/heads/{branch_name}':
            continue
        return remote_head['oid']
    raise RuntimeError(f"Unknown branch: {branch_name}")


def update_work_directory(repo, remote_name, branch_name):
    """Reset the work directory with remote latest commit
    """
    remote_id = repo.lookup_branch(f'{remote_name}/{branch_name}',
            pygit2.GIT_BRANCH_REMOTE)\
            .target
    commit = repo.get(remote_id)
    repo.checkout_tree(commit)
    local_ref = repo.lookup_branch(branch_name)
    if local_ref:
        local_ref.set_target(remote_id)
    else:
        local_ref = repo.create_branch(branch_name, commit)
    repo.set_head(local_ref.name)


def extract_info_from_url(url, default='git'):
    """Extract username from github url
    """
    urlparts = urlparse.urlsplit(url)
    netloc = urlparts.netloc.split('@', 1)
    if len(netloc) <= 1:
        # Didn't find the credentials in the netloc
        return (urlparts.scheme, default)
    return (urlparts.scheme, netloc[0].split(':', 1)[0])
