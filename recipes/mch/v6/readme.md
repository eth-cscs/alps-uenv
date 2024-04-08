```bash
version="v6-rc2"
mount="/scratch/mch/bcumming/mch-environment/$version"
sw="$SCRATCH/software"

stack-config -c ./cache.yaml -m $mount -r $sw/alps-uenv/recipes/mch/v6 -s $sw/alps-cluster-config/tasna -b /dev/shm/$USER/$version
```
