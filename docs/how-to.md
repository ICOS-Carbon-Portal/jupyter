# How to...

In this guide you find more information on 

- Restarting your Jupyter server 
- Working in Projects 
- Installing Python packages
- Working in Virtual Environments
- Working with Github Repoitories

## Restart your Jupyter server

Restarting your Jupyter server refreshes your session and ensures that it uses the latest environment and permissions.

You should restart your server if:

* You have been added to a new project and cannot see the project folder.
* You have installed or updated Python packages that require a fresh session.
* The Jupyter Hub has been updated and you want to use the latest software environment.
* You experience unexpected behaviour that may be resolved by starting a new session.

### Restart the server

1. Got to **File → Hub Control Panel**.
2. Click **Stop My Server**.
3. Wait until the server has stopped.
4. Click **Start My Server**.


## Working in Projects

Project spaces on the ICOS Collaborative Jupyter Hub allow groups of users to work together in a shared environment.

A project folder is only visible to members of that project.

### Join an existing project

To join an existing project:

1. Make sure you have a personal ICOS Jupyter Hub account.
2. Request [access to the project](<https://www.icos-cp.eu/data-services/services/jupyter-notebook/project-membership-application>).
3. Once approved, restart your Jupyter server if the project folder does not appear.

If you still cannot see the project folder, contact:

**jupyter-info@icos-ri.eu**

### Create a new project

If you have a research idea and want to collaborate with others using ICOS data or derived products, you can [request a dedicated project space](<https://www.icos-cp.eu/data-services/services/jupyter-notebook/collaboration-space-application>).

When applying, provide a brief description of:

- The scientific objective
- The planned use of the Jupyter Hub environment
- The expected participants

### Project owner

The person who requested the project is the project owner.

The project owner is responsible for:

- Inviting new members
- Managing project membership, i.e. coordinate with ICOS CP Jupyter Team to add or remove members
- Coordinating project activities
- Overseeing the project workspace
- Contacting the ICOS CP Jupyter Team for technical requests
- Requesting updates to the Store folder


### How collaboration works

Project collaboration follows the same principles as working in a Linux or Unix group environment.

Files and folders stored directly in the project group folder are:

- Visible to all project members
- Editable by all project members

This is a true collaborative space. If multiple users work on the same notebook at the same time, changes may conflict or be overwritten.

### Recommended practices

To avoid accidental interference with other project members:

- Create your own copy of notebooks or scripts before editing.
- Use a personal subfolder inside the project directory for development work.
- Alternatively, work in your home directory and link to input files in the project folder when needed.
- Keep stable versions separate from active development files.
- Coordinate with collaborators before editing shared notebooks.

### The store folder

Each project contains a **store** folder.

The Store folder is intended for stable, approved versions of notebooks, scripts, and project material.

- All project members can view the contents.
- The folder is read-only for project members.
- Only the ICOS CP Jupyter Team can update the folder.

If you want to archive scripts or notebooks in the Store folder, contact: 

**jupyter-info@icos-ri.eu**

### Project data and mounted drives

Some projects use data hosted on the ICOS fileshare or on an external research drive.

These data sources may be mounted inside the project folder to provide read-only access to larger datasets or model results.

Mounted data should not be modified by notebooks or scripts running on the Jupyter Hub.


## Python Packages

You can install additional Python packages in your personal Jupyter Hub account.

!!! note

    Packages installed in your personal account are only available to you. Other users and project members will not automatically have access to them.

### Install a package from a notebook

In a notebook cell, run:

`!pip install myPackage`

Replace `myPackage` with the name of the package you want to install.

### Install a package from a terminal

Open a terminal and run:

`pip install myPackage`

### Upgrade a package

To upgrade an existing package:

`pip install <package-name> -U`

### List installed packages

To list installed packages:

`pip list`

### Show details for a package

To show information about a specific package:

`pip show <package-name>`

### Reset your personal Python packages

If package conflicts cause problems, you can remove all packages installed in your personal user environment.

Open a terminal and run:

`rm -rf ~/.local/lib/python*/site-packages/`

!!! note

    This removes packages installed in your personal account. It does not remove system packages.

Afterwards, reinstall only the packages you need.

Example:

`pip install halo`

### Upgrade all user-installed packages

You can try upgrading all user-installed packages with:

`pip list --user --format=freeze | cut -d = -f 1 | xargs -n1 python -m pip install -U --user`

!!! note

    This command may fail if package dependencies conflict. If many packages need updating, it can be useful to try, but success cannot be guaranteed.

### When to contact support

If your notebook still fails after upgrading or resetting packages, contact:

**jupyter-info@icos-ri.eu**


## Virtual Environments

A virtual environment lets you install and manage Python packages separately from the default Jupyter Hub environment.

This is useful when a notebook requires specific package versions or when you want to avoid conflicts with your personal Python environment.

### Create a directory for the environment

Open a terminal and create a directory for your environment:

`mkdir supersoftware`

`cd supersoftware`

### Create a virtual environment

Create a virtual environment named `super-env`:

`python -m venv super-env`


### Activate the environment

Activate the environment:

`source super-env/bin/activate`

### Install Jupyter kernel support

Install or upgrade `pip`, then install `ipykernel`:

`pip install --upgrade pip`
`pip install ipykernel`

### Register the environment as a Jupyter kernel

Register the environment so that it appears as a selectable notebook kernel:

`python -m ipykernel install --user --name super-env --display-name "super-env"`

Reload the the current definitions

`deactivate`

`source super-env/bin/activate`

### Use the new kernel

1. Open a new notebook.
2. Select the **super-env** kernel.
3. Run your notebook using the packages installed in that environment.

### Deactivate the environment

To return to the default environment in the terminal, run:

`deactivate`

### Remove a custom kernel

If you no longer need the kernel, you can remove it with:

`jupyter kernelspec uninstall super-env`


## Working with GitHub Repositories

You can access files from GitHub repositories directly in the ICOS Collaborative Jupyter Hub.

### Create a folder for repositories

After logging in to the Jupyter Hub, open a terminal and create a folder for your GitHub repositories:

```bash
mkdir github
cd github
```

### Clone a repository

Use `git clone` followed by the repository URL.

Example:

```bash
git clone https://github.com/ICOS-Carbon-Portal/pylib.git
```

This creates a local copy of the repository in your workspace.

### Use standard Git commands

Inside the repository folder, you can use standard Git commands, for example:

```bash
git status
git pull
git add .
git commit -m "Update notebook"
git push
```

### Learn more

For a general introduction to Git, see:

<https://git-scm.com/docs/gittutorial>


