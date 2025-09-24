# pid4notebooks
A repository for ICOS’s interactive Jupyter notebook service. Users can launch notebooks via pre-configured Docker 
images using JupyterHub.

The service includes:
- **Pylib examples** – showcasing how to use ICOS Python libraries to access and analyze data.
- **ICOS notebooks** – developed within the ICOS Carbon Portal, demonstrating scientific analyses and project outputs.
- **Education notebooks & workshops** – material for teaching, training, and ICOS educational events.
- **DOI/PID notebooks** – linked to persistent identifiers and scientific publications.


## 🗂 Project structure
| Directory / File     | Purpose                                                                  |
| -------------------- |--------------------------------------------------------------------------|
| `hub/`               | JupyterHub configuration, templates, and build files.                    |
| `notebooks/`         | Contains content and build directories for different notebook categories.|
| `docker-compose.yml` | Orchestrates services (hub, proxy, login, notebook images, etc.).        |


## Best Practices & Tips

### Adding new notebooks to the interface
Currently, the pylib-examples, icos-notebooks, DOI/PID notebooks, and some education notebooks share the same Docker 
image. The mapping between each notebook and its corresponding Docker image is defined in the file: 
`hub/templates/custom_options_form.html`

In the aforementioned file, each notebook is represented by a `div` element like this:
```html
<div class="form-check">
    <input class="form-check-input" type="radio" name="env" id="ex1_data" value="pylib-examples:latest&nb=ex1_data.ipynb">
    <label class="form-check-label" for="ex1_data">ex1_data.ipynb</label>
</div>
```
The value attribute `pylib-examples:latest&nb=ex1_data.ipynb` is passed to the JupyterHub configuration.  
In this example, JupyterHub launches a container with:
- docker image: `pylib-examples:latest`. The docker image is already built by the `docker-compose.yml` file.
- default url: `ex1_data.ipynb`. The notebook `ex1_data.ipynb` automatically opens when the container starts.

So to add a new notebook, we simply duplicate the `div` element and make these next changes:
- id="ex1_data" &#10132; id="awesome_knoughtbiuk"
- value="pylib-examples:latest&nb=ex1_data.ipynb" &#10132; value="awesome-image:latest&nb=awesome_knoughtbiuk.ipynb"
- for="ex1_data" &#10132; for="awesome_knoughtbiuk"
- ex1_data.ipynb</label> &#10132; awesome_knoughtbiuk.ipynb</label> 
<hr>
## todo
### operations
- connection to registry (docker images)
- ansible
- registry backup?
- deploy manual version to explore-test
- figure out how jbuild works and deploy from pid4notebooks to explore-data

### others
- doi notebook start without login & update link on landing page 
- size of jupyter notebooks and related data (check education/General/data 229M)
- What do we do with Jupyter repository?