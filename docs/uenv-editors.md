# editors

Provides text editors and useful command line tools, mounted at `/user-tools`.

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




## systems

The uenv is designed for deployment on all vClusters - it does not have any GPU-specific code and all of the tools it provides can be built on x86 and ARM CPUs.

To find which versions (if any) are available on your target system:
```
uenv find editors
```


