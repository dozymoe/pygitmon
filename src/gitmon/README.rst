------
gitmon
------

Run command when the upstream git branch was updated.

Example work file named git-monitor.yaml:

    - | path: ~/work/company-website-dev
      | command: ansible-playbook playbook-develop-company.yml

    - | path: ~/work/company-website-prod
      | remote: origin
      | branch: production
      | force: 1
      | commands:
      |  - ansible-playbook playbook-deploy-company.yml

The first item ignores the default values, which are remote=origin, branch=main,
force=0. If you didn't set command, gitmon will only update the repository.

In the next example we have three additional fields:

    - | path: ~/work/company-website-prod
      | remote: origin
      | branch: main
      | force: 1
      | repo_url: git@github.com:username/company-website
      | ssh_keyfile: ~/.ssh/company-key
      | ssh_keyfile_password: company-password

If the path is empty, we will try to create a new clone. And if the url scheme is not
http, we will assume it was ssh, and if ssh_keyfile is set we will use that when
cloning or updating the path.


Usage
-----

Example:

    python3 -m gitmon git-monitor.yaml

