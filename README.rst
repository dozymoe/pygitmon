------
gitmon
------

Run command when the upstream git branch was updated.

Example work file named git-monitor.yaml:

    - path: ~/work/company-website-dev
      command: ansible-playbook playbook-develop-company.yml

    - path: ~/work/company-website-prod
      remote: origin
      branch: production
      force: 1
      command: ansible-playbook playbook-deploy-company.yml

The first item ignores the default values, which are remote=origin, branch=main,
force=0. If you didn't set command, gitmon will only update the repository.

Usage
-----

Example:

    python3 -m gitmon git-monitor.yaml

