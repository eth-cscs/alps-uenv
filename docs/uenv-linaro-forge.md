# Linaro Forge (DDT) debugger

[Linaro Forge](https://www.linaroforge.com/downloadForge) (formerly known as DDT) allows source-level debugging of Fortran,
C, C++ and Python codes. It can be used for debugging serial, multi-threaded
(OpenMP), multi-process (MPI) and accelerated (Cuda, OpenACC) programs running
on research and production systems, including CSCS Alps system. It can be
executed either as a graphical user interface or from the command-line.

## Usage notes

The uenv is named `linaro-forge`, and the available versions on a cluster can be determined using the `uenv image find` command, for example:
```
> uenv image find linaro-forge
uenv/version:tag                        uarch date       id               size
linaro-forge/23.1.2:latest              gh200 2024-04-10 ea67dbb33801c7c3 342MB
```


The linaro tools are configured to be mounted in the `/user-tools` path so that they can be used alongside application and development uenv mounted at `user-environment`.

=== "sidecar"

    When using alongside another uenv, start a uenv session with both uenv with `linaro-forge` after the main uenv, to mount the images at the respective `/user-environment` and `/user-tools` locations:

    ```bash
    uenv start prgenv-gnu/24.2:v3 linaro-forge/32.1.2

    # test that everything has been mounted correctly
    # (will give warnings if there are problems)
    uenv status

    uenv view prgenv-gnu:default
    source /user-tools/acvitave

    # check that ddt is in the path
    ddt --version
    ```

    The `/user-tools/activate` script will make the forge executables available in your environment, and **must be run after** any other uenv view command.

=== "standalone"

    When using the uenv with no other environment mounted, you will need to explicitly set the `/user-tools` mount point:

    ```bash
    uenv start linaro-forge/32.1.2:/user-tools

    source /user-tools/acvitave

    # check that ddt is in the path
    ddt --version
    ```

    The `/user-tools/activate` script will make the forge executables available in your environment.

## Getting Started

In order to debug your code on Alps, you need to:

1. pull the linaro-forge uenv on the target Alps vCluster
- install the Forge/DDT client on your laptop
- build an executable with debug flags
- launch a job with the debugger on Alps.

### Pull the Linaro Forge uenv on the Alps cluster

The first step is to download the latest version of linaro-forge that is available on the cluster.
First, SSH into the target system, then use the `uenv image find` command to list the available versions on the system:

```
> uenv image find linaro-forge
uenv/version:tag                        uarch date       id               size
linaro-forge/23.1.2:latest              gh200 2024-04-10 ea67dbb33801c7c3 342MB
```

In this example, there is a single version available. Next we pull the image so that it is available locally.
```
> uenv image pull linaro-forge/23.1.2:latest
```

It will take a few seconds to download the image. Once complete, check that it was downloaded using the `uenv image ls` command:

```
> uenv image ls linaro-forge
uenv/version:tag                        uarch date       id               size
linaro-forge/23.1.2:latest              gh200 2024-04-05 ea67dbb33801c7c3 342MB
```

### Install the client on your laptop

We recommend installing the [desktop client](https://www.linaroforge.com/downloadForge) on your local workstation/laptop.
It can be configured to connect with the debug jobs running on Alps, offering a better user experience compared running remotely with X11 forwarding.
The client can be downloaded for a selection of operating systems, via the link above.

Once installed, the client needs to be configured to connect to the vCluster on which you are working.
First, start the client on your laptop.

=== "Linux"

    The path will change if you have installed a different version, or if it has been installed in a non-standard installation location.

    ```bash
    $HOME/linaro/forge/23.0.1/bin/ddt
    ```

=== "MacOS"

    The path will change if you have installed a different version, or if it has been installed in a non-standard installation location.

    ```bash
    open /Applications/Linaro\ Forge\ Client\ 23.0.1.app/
    ```

Next, configure a connection to the target system.
Open the *Remote Launch* menu and click on *configure* then *Add*. Examples of the settings are below.

=== "Eiger"

    | Field       | Value                                   |
    | ----------- | --------------------------------------- |
    | Connection  | `eiger`                                |
    | Host Name   | `bsmith@ela.cscs.ch bsmith@eiger.cscs.ch`  |
    | Remote Installation Directory | `uenv run linaro-forge/23.1.2:/user-tools -- /user-tools/env/forge/` |
    | Private Key | `$HOME/.ssh/cscs-key` |

=== "Santis"

    | Field       | Value                                   |
    | ----------- | --------------------------------------- |
    | Connection  | `santis`                                |
    | Host Name   | `bsmith@ela.cscs.ch bsmith@santis.cscs.ch`  |
    | Remote Installation Directory | `uenv run linaro-forge/23.1.2:/user-tools -- /user-tools/env/forge/` |
    | Private Key | `$HOME/.ssh/cscs-key` |


Some notes on the examples above:

* SSH Forwarding via `ela.scscs.ch` is used to access the cluster.
* the replace the username `bsmith` with your CSCS user name that you would normally use to open an SSH connection to CSCS.
* the Remote Installation Path is a little bit more complicated than
* the private keys should be the ones generated for CSCS MFA, and this field does not need to be set if you have added the key to your SSH agent.

Once configured, test and save the configuration:

1. check whether the concfiguration is correct, click `Test Remote Launch`.
2. Click on `ok` and `close` to save the configuration.
3. You can now connect by going to `Remote Launch` and choose the `Alps` entry. If the client fails to connect, look at the message, check your ssh configuration and make sure you can ssh without the client.

### Setup the environment

### Build with debug flags

Once the uenv is loaded and activated, the program to debug must be compiled with the `-g` (for cpu) and `-G` (for gpu) debugging flags. For example, let's build a cuda code with  a user environment:

```bash
uenv start prgenv-gnu:24.2:v2
uenv view default

# download the source code
git clone https://github.com/sekelle/octree-miniapp.git
cd o


# build the application
make -C octree-miniapp.git/
```

### Launch the code with the debugger

To use the DDT client with uenv, it must be launched in `Manual Launch` mode (assuming that it is connected to Alps via `Remote Launch`):

??? note

    the steps below do not manually launch - instead they directly launch using `ddt --connect srun ...` on the target cluster.

=== "on laptop"

    Start DDT, and connect to the target cluster using the drop down menu for Remote Launch.

    Then wait for the job to start (see the "on Alps" tab).

=== "on Alps"

    log into the system and launch with the srun command:

    ```bash
    # start a session with both the PE used to build your application
    # and the linaro-forge uenv mounted
    uenv start prgenv-gnu/24.2 linaro-forge/23.1.2
    ddt --connect srun -n2 -N2 ./a.out
    ```

Notes on using specific systems:

=== "santis"

    !!! warning

        Because Santis is not connected to the internet, some environment variables need to be set so that it can connect to the license server.

        ```bash
        export https_proxy=proxy.cscs.ch:8080
        export http_proxy=proxy.cscs.ch:8080
        export no_proxy=".local, .cscs.ch, localhost, 148.187.0.0/16, 10.0.0.0/8, 172.16.0.0/12"
        ```

        ???- note "default value of `http_proxy`"

            By default the `https_proxy` and `http_proxy` variables are set to `http://proxy.cscs.ch:8080`, as the transport is required for some other services to work. You will have to set them for a debugging session.

This screenshot shows a debugging session on 12 gpus:

![DDT](https://raw.githubusercontent.com/jgphpc/octree-miniapp/ddt/img/ddt.png)
