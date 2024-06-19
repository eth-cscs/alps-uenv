# ReFrame Testing Tutorial

This is a guide for creating ReFrame tests for uenv, and how to run them in the CI/CD pipeline.

1. Create or port tests in the [CSCS ReFrame tests repository](alps-uenv-repo)
2. Make a pull request to have the tests added to the `alps` branch of the repo
3. Add a `extras/reframe.yaml` file to your uenv recipe
4. Make a pull request to merge with the alps-uenv repository.

## Creating and finding tests

CSCS maintains a set of ReFrame tests in a [GitHub repository](alps-uenv-repo)

Development of ReFrame tests can be used to test both uenv and containerised environments is ongoing, in the `alps` branch of the repository.

Create the tests in the CSCS Reframe 

```bash
# download the reframe tests 
git clone -b alps git@github.com:eth-cscs/cscs-reframe-tests.git
cd cscs-reframe-tests

# start a branch for developing the tsts
git checkout -b arbor
```

```
# create a path for the checks
mkdir checks/apps/arbor
cd checks/apps/arbor
```

## Adding tests to a uenv

## Running tests

The ReFrame tests are run automatically in the CI/CD pipeline, in the `test` stage, directly after the `build` stage.



[alps-uenv-repo]: https://github.com/eth-cscs/alps-uenv
[cscs-reframe-repo]: https://github.com/eth-cscs/cscs-reframe-tests
