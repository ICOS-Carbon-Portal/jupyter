# Frequently Asked Questions

## Access and login

### How do I access the ICOS Collaborative Jupyter Hub?

Open your browser and go to:

<https://jupyter.icos-cp.eu>

Log in with your personal ICOS Jupyter Hub account.

If you do not yet have an account, [apply for a personal account](<https://www.icos-cp.eu/data-services/services/jupyter-notebook/personal-account-application>) through the ICOS Carbon Portal. Once your request has been approved, you will receive login credentials by email.

For access problems, contact:

**jupyter-info@icos-ri.eu**

### How do I access ExploreData?

Open your browser and go to:

<https://exploredata.icos-cp.eu>

Use your email address as username and request a password using the [ExploreData password request form](<https://www.icos-cp.eu/data-services/services/jupyter-notebook/exploredata-password>).

ExploreData is public and intended for exploring example notebooks. Your work is not saved permanently, but you can download your notebook.

## Updates and permissions

### Do I have the latest version of the Jupyter Hub environment?

The Jupyter Hub environment, libraries, notebooks, and permissions are updated regularly.
To make sure your session reflects the latest updates, restart your server.

1. Go to **File → Hub Control Panel**.
2. Click **Stop My Server**.
3. Wait until the server has stopped.
4. Click **Start My Server**.

We recommend doing this regularly.


### I was added to a project, but I cannot see the project folder.

Project permissions may not appear in an already running session.
Restart your server.

1. Go to **File → Hub Control Panel**.
2. Click **Stop My Server**.
3. Wait until the server has stopped.
4. Click **Start My Server**.


If the project folder is still missing, contact:

**jupyter-info@icos-ri.eu**


### My notebook worked before a Jupyter Hub update, but now it fails.

This can happen when:

- A Python package is outdated
- A package is incompatible with the current Python version
- Some parameters have been deprecated

You have several options:

- Upgrade the package causing the problem.
- Reset your personal Python packages if necessary.
- Create a clean virtual environment for the notebook.

For detailed instructions see:

- [Python Packages](how-to.md/#python-packages) in the How-to Guide

- [Virtual Environments](how-to.md/#virtual-environments) in the How-to Guide

If the problem remains, contact:

**jupyter-info@icos-ri.eu**


### I remember using an ICOS notebook previously, but I cannot find it anymore.

If you are looking for a notebook that was previously available on ExploreData or in the former *common* folder on the Collaborative Jupyter Hub, the [Timecapsule on ExploreData](exploredata.md/#timecapsule) is the best place to start your search.

The Timecapsule contains a snapshot of all public ICOS notebooks as they were available in November 2025. While these notebooks are no longer maintained, they remain available for reference and to support the reproducibility of previous analyses.


## Python packages

### Can I install a missing Python package?

Yes. You can install packages into your personal account using `pip`.

From a notebook:

`!pip install myPackage`

From a terminal:

`pip install myPackage`

Packages installed this way are only available to you.

### Can I work in a virtual Python environment?

Yes. You can create a virtual environment and register it as a Jupyter kernel.

See [Virtual Environments](how-to.md/#virtual-environments) in the How-to Guide.


## GitHub

### Can I access files from a GitHub repository?

Yes. You can clone repositories from GitHub into your Jupyter Hub workspace.

See [Working with GitHub Repositories](how-to.md/#working-with-github-repositories) in the How-to Guide.

## Licence and policies

### What licence applies to ICOS data?

See the [Data Licence](<https://www.icos-cp.eu/data-services/data-portal/data-licence>).

### Where can I find the ICOS Terms of Use?

See [Terms of Use](<https://www.icos-cp.eu/terms-of-use>).

### Where can I find the ICOS Privacy Policy?

See [Privacy Policy](<https://www.icos-cp.eu/privacy>).
