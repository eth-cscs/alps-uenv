```
cluster=clariden,arch=a100,uenv=gromacs:2023
# build all of the gromacs versions for all arch
cluster=eiger,arch=*,uenv=gromacs:*
# same as above (default value of arch is *)
cluster=eiger,uenv=gromacs:*
# build all the images on a target cluster
```

Implementation plan:
1. write a version that requires that cluster, arch and uenv are all explicitly defined with no wildcards
    * no need to fork multiple pipelines (one per config)
2. later extend to allow building multiple images.

Some ideas:
1. always require a cluster
    - this way we can reasonably constrain the target architectures
