# editors

Provides text editors and useful command line tools, mounted at `/user-tools`.


!!! warning

    The image has to be mounted at `/user-tools`, not the default `/user-environment` location.
    If loading the image alone, explicitly mount it at the right location
    ```
    # if using v5 or lower uenv explicitly provide the mount point
    > uenv start editors:/user-tools --view=ed

    # if using v6 or later uenv the mount point is automatically inferred
    > uenv start editors --view=ed
    ```
    If loading the image alongside another (in this example we use the modules view, see below):
    ```
    # if using v5 or lower uenv:
    > uenv start prgenv-gnu/24.7:v3 editors --view=editors:modules

    # if using v6 or later uenv:
    > uenv start prgenv-gnu/24.7:v3,editors --view=editors:modules
    ```

## packages

Text editors:

* emacs
* nano
* neovim
* vim

Useful command line tools:

* fd
* direnv
* lazygit
* node-js
* ripgrep
* screen
* tree-sitter

Compilers and languages:

* lua
* python
* go
* rust

## interfaces

The uenv provides both a view called `ed` that will make all of the tools available. For example:
```
> uenv start editors:/user-tools --view=ed
loading the view editors:ed
> which nvim
/user-tools/env/ed/bin/nvim
> which emacs
/user-tools/env/ed/bin/emacs
> which fd
/user-tools/env/ed/bin/fd
```

Alternatively, the modules interface can be used to load individual tools:
```
> uenv start editors:/user-tools --view=modules
loading the view editors:ed
> module avail

----------------- /user-tools/modules ------------------
   direnv    go         neovim     rust
   emacs     lazygit    node-js    screen
   fd        lua        python     tree-sitter
   gcc       nano       ripgrep    vim

> module load screen
> screen --version
Screen version 4.09.01 (GNU) 20-Aug-23
```

## releases

### 24.7

* `v1`: did not provide neovim
* `v2`: same as v1 with neovim added (fixed a libtool bug that caused an error when building the `libvterm` dependency of neovim)

## systems

The uenv is designed for deployment on all vClusters - it does not have any GPU-specific code and all of the tools it provides can be built on x86 and ARM CPUs.

To find which versions (if any) are available on your target system:
```
uenv image find editors
```

