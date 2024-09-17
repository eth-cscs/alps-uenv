# Writing Documentation

The documentation for uenv is written with [Material for mkdocs](https://squidfunk.github.io/mkdocs-material/).

See the documentation for Material for details on all of the features that it provides.

## Getting Started

To view the documentation as you write, you can install Material for mkdocs using pip.

First, create Python virtual environment and install `mkdocs-material`
```bash
# create and activate a venv
python3 -m venv pyenv
source pyenv/bin/activate

# install required packages
pip install --upgrade pip
pip install mkdocs-material
```

!!! note

    If you just created the python virtual environment, you might have to restart it for the `mkdocs` executable to be added to `PATH`.

    ```bash
    # you have to deactivate and start again for mkdocs to be available
    deactivate
    source pyenv/bin/activate
    ```

The documentation is built using the `mkdocs` executable.
To view your documentation in your browser, run the mkdocs server:
```bash
mkdocs serve
```

Leave it running, and every time you save the markdown file the docs will be regenerated.

The docs can be viewed by using the link printed by `mkdocs serve`:

```
mkdocs serve                                                                                                  (pyenv) main [e2006ad] Δ ?
INFO    -  Building documentation...
INFO    -  Cleaning site directory
INFO    -  The following pages exist in the docs directory, but are not included in the "nav" configuration:
             - writing-docs.md
INFO    -  Documentation built in 0.15 seconds
INFO    -  [12:17:14] Watching paths for changes: 'docs', 'mkdocs.yml'
INFO    -  [12:17:14] Serving on http://127.0.0.1:8000/
```

And viewing it ( [http://127.0.0.1:8000/](http://127.0.0.1:8000/) typically) in your local browser.

### Documentation Layout

To add documentation for a uenv, create a file `docs/uenv-<uenv name>.md`, and look at existing documentation to get started.

For your docs to be generated, it has to be added to the index in the `mkdocs.yml` file in the root of the repository. For example, to add docs for a new environment called `wombat`:

```yaml
nav:
  - Home: index.md
  - 'uenv':
    - 'Overview': uenv-overview.md
    - 'wombat': uenv-wombat.md
```

