import logging
from pathlib import Path
import subprocess
#-
import pygit2

_logger = logging.getLogger(__name__)

def process_work_subject(work_subject):
    """Check git repository for remote updates and run a command
    """
    assert 'path' in work_subject
    assert 'command' in work_subject
    remote_name = work_subject.get('remote', 'origin')
    branch_name = work_subject.get('branch', 'main')
    use_force = int(work_subject.get('force', '0'))

    run_command = False

    work_path = Path(work_subject['path']).expanduser()
    repo_path = pygit2.discover_repository(work_path)
    assert repo_path is not None
    repo = pygit2.Repository(repo_path)

    # Get updates
    latest_commit = fetch_remote(repo, remote_name, branch_name)
    if latest_commit != repo.head.target:
        run_command = True

    merge_result, _ = repo.merge_analysis(latest_commit)
    if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
        _logger.info("Workspace %s is up to date", work_path)
    elif not (merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD) and not use_force:
        # We have merge conflicts, was told not to force update
        _logger.warning("Workspace %s has merge conflicts, do nothing", work_path)
        return
    else:
        # Update working files
        _logger.info("Updating workspace %s", work_path)
        remote_id = repo.lookup_reference(
                f'refs/remotes/{remote_name}/{branch_name}')\
                .target
        repo.checkout_tree(repo.get(remote_id))
        local_ref = repo.lookup_reference(f'refs/heads/{branch_name}')
        local_ref.set_target(remote_id)
        repo.head.set_target(remote_id)

    if run_command:
        subprocess.call(work_subject['command'], shell=True)


def fetch_remote(repo, remote_name, branch_name):
    """Update remote information and peek latest commit
    """
    if remote_name not in repo.remotes.names():
        raise RuntimeError(f"Unknown remote: {remote_name}")
    remote = repo.remotes[remote_name]
    remote.fetch()
    for remote_head in remote.ls_remotes():
        if remote_head['symref_target'] != f'refs/heads/{branch_name}':
            continue
        return remote_head['oid']
    raise RuntimeError(f"Unknown branch: {branch_name}")
