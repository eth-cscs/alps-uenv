# Linaro Forge (DDT) debugger

- https://www.linaroforge.com/downloadForge

Linaro Forge (formerly known as DDT) allows source-level debugging of Fortran,
C, C++ and Python codes. It can be used for debugging serial, multi-threaded
(OpenMP), multi-process (MPI) and accelerated (Cuda, OpenACC) programs running
on research and production systems, including CSCS Alps system. It can be
executed either as a graphical user interface or from the command-line.

## Using the debugger

In order to debug your code on Alps, you need to:

- install the Forge/DDT client on your laptop,
- setup the user environment on Alps,
- build an executable with debug flags on Alps,
- launch a job with the debugger on Alps.


### Install the client on your laptop

We recommend to download and install the [desktop client](https://www.linaroforge.com/downloadForge) on your local workstation/laptop. It will connect with the debug jobs running on Alps, offering a better user experience compared to opening ddt with X11 forwarding. The client can be downloaded for a selection of operating systems.

Once installed, the client needs to be configured to connect to your preferred vcluster. For this, launch the client:

- mac: open /Applications/Linaro\ Forge\ Client\ 23.0.1.app/
- linux: $HOME/linaro/forge/23.0.1/bin/ddt

and setup the connection:

```
- open the 'Remote Launch' menu and click on 'configure' then 'Add' and set the fields, for example:
    - Connection Name: alps

    - Host Name: your-cscs-username-here@ela.cscs.ch your-cscs-username-here@clariden.cscs.ch
    # Note that the clariden vlcuster name can be replaced with another vcluster name

    - Remote install dir: uenv run IMG -- DDTDIR
      # here we tell the client to use the ddt installed in the uenv image
```

where you can replace `IMG` and `DDTDIR` with for example:

- `IMG`: full path to the uenv file and mount point, for example:
  - _/scratch/e1000/your-cscs-username-here/linaro-forge-23.0.3.squashfs:/user-tools_
- `DDTDIR`: full path to the tool, for example:
  - _/user-tools/linux-sles15-zen2/gcc-11.3.0/linaro-forge-23.0.3-3z4k6ijkcxcgqymv6mapv6xaela7m2q5/_

and

```
    - Remote Script:

    - Private Key: _path-to-your-home_/.ssh/cscs-key

    - Proxy through login node: yes (check the box)
```

Click `Test Remote Launch`. If the client can connect, you are ready to debug:
click on `ok` and `close` (to save the configuration). You can now connect by going to `Remote Launch` and choose the `Alps` entry. If the client fails to connect, look at the message, check your ssh configuration and make sure you can ssh without the client.

### Setup the environment

`linaro-forge-23.0.3.squashfs` provides the latest version of Linaro Forge (23.0.3).

- On Alps:
```bash
uenv start ./linaro-forge-23.0.3.squashfs
uenv modules use
module load linaro-forge
ddt --version
# Version: 23.0.3
```

### Build with debug flags

Once the uenv is loaded and activated, the program to debug must be compiled with the `-g` (for cpu) and `-G` (for gpu) debugging flags. For example, let's build a cuda code with  a user environment:

- on Alps:
```bash
uenv start store.squashfs
uenv modules use
module load gcc cray-mpich cuda
git clone -b ddt https://github.com/jgphpc/octree-miniapp \
octree-miniapp.git
make -C octree-miniapp.git/
```

### Launch the code with the debugger

Given the unusual way of loading the uenv, the DDT client must be launched in `Manual Launch` mode (assuming that it is connected to Alps via `Remote Launch`):

- on the client:
```
- open the 'Manual Launch' menu and
- set the fields, for example:
    - Number of processes: 12
    - CUDA: yes (check the box for gpu exeutables)
```
Listen and wait 

You can then launch ddt with the srun command (or a Slurm jobscript):

- on Alps:
```bash
unset CUDA_VISIBLE_DEVICES
srun --uenv=$UENV_SQFS,TOOL_SQFS \
-l -N3 -n12 -t10 -pnvgpu \
./octree-miniapp.git/cuda_visible_devices.sh \
$DDT_CLIENT
./octree-miniapp.git/neighbor_search.exe 120000
```

where for example:

- UENV_SQFS=$PWD/store.squashfs:/user-environment
- TOOL_SQFS=$PWD/linaro-forge-23.0.3.squashfs:/user-tools
- DDT_CLIENT=/user-tools/linux-sles15-zen2/gcc-11.3.0/linaro-forge-23.0.3-3z4k6ijkcxcgqymv6mapv6xaela7m2q5/bin/ddt-client


This screenshot shows a debugging session on 12 gpus:

![DDT](https://raw.githubusercontent.com/jgphpc/octree-miniapp/ddt/img/ddt.png)