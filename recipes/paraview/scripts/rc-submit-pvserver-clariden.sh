#!/bin/bash  -l 
# updated Thu Dec  1 02:29:09 PM CET 2022 to add v5.11 for Eiger
# updated Tue Nov 15 03:46:08 PM CET 2022 to add v5.11 for daint-gpu
# updated Tue Jun  7 10:26:45 PM CEST 2022 to use generic hostname command
# updated Thu Feb 17 08:49:14 AM CET 2022 for Eiger, version 5.10
# updated Thu Feb 17 15:56:49 CET 2022 for Daint (GPU version), version 5.10
# updated Thu Feb 17 04:06:33 PM CET 2022: Removed version 5.9

# usage
echo ""
echo "Usage : %1:Session name ($1)"
echo "        %2:Job Wall Time ($2)"
echo "        %3:server-num-nodes ($3)"
echo "        %4:server-num-tasks-per-node ($4)"
echo "        %5:server-port ($5)"
echo "        %6:login node ($6)"
echo "        %7:Version number ($7)"
echo "        %8:Queue's name (normal/debug) ($8)"
echo "        %9:Memory per Node (standard or high) ($9)"
echo "        %10:Account (csstaff or other) ($10)"
echo "        %11:Reservation ("" or other) ($11)"

# Create a temporary filename to write our launch script into
TEMP_FILE=`mktemp`

# this enables us to connect to the generic name "daint.cscs.ch" from the client
HOST_NAME=`hostname`.cscs.ch
# HOST_NAME=148.187.134.95

echo "Temporary FileName is :" $TEMP_FILE

nservers=$[$3 * $4]

# Create a job script
echo "#!/bin/bash -l"                              >> $TEMP_FILE
echo "#SBATCH --job-name=$1"                       >> $TEMP_FILE
echo "#SBATCH --nodes=$3"                          >> $TEMP_FILE
echo "#SBATCH --ntasks-per-node=$4"                >> $TEMP_FILE
echo "#SBATCH --ntasks=$nservers"                  >> $TEMP_FILE
echo "#SBATCH --time=$2"                           >> $TEMP_FILE
echo "#SBATCH --account=${10}"                     >> $TEMP_FILE
echo "#SBATCH --partition=$8"                      >> $TEMP_FILE
#echo "#SBATCH --cpus-per-task=256"              >> $TEMP_FILE
#echo "#SBATCH --ntasks-per-core=2"              >> $TEMP_FILE
#echo "#SBATCH --threads-per-core=2"             >> $TEMP_FILE
#echo "#SBATCH --hint=multithread"               >> $TEMP_FILE
#  if [ "$9" = "high" ]; then
#    echo "#SBATCH --mem=497G"                   >> $TEMP_FILE
#  fi

# only ask for a reservation if in the normal queue and no greater than 5 nodes
if [ "$8" = "normal" ];then
  if [ ! -z "${11}" ]; then
    if [ ! "$3" -gt "5" ]; then
      echo "#SBATCH --reservation=${11}"           >> $TEMP_FILE
    fi
  fi
fi

MACHINE_NAME=clariden
export SPACK_ROOT=$SCRATCH/spack-$MACHINE_NAME
export SPACK_USER_CONFIG_PATH=~/.spack-$MACHINE_NAME
export SPACK_SYSTEM_CONFIG_PATH=/user-environment/config
export SPACK_USER_CACHE_PATH=/user-environment/cache
source $SPACK_ROOT/share/spack/setup-env.sh

# Which rendering backend are we using
if [ "$7" = "clariden-5.11-NVIDIA" ]; then
  # paraview 5.11 nvidia EGL 
  SQUASH_IMG=/scratch/aistor/biddisco/clariden-paraview-EGL-2023-08-23.squashfs
  SQUASH_CMD="squashfs-mount $SQUASH_IMG:/user-environment"
  PV_HASH="/sqd4oxb"
  PV_SERVER=$($SQUASH_CMD -- spack location -i paraview $PV_HASH)/bin/pvserver
  echo "Using hash $PV_HASH from squashfs $SQUASH_IMG"
  echo "pvserver : $PV_SERVER"

elif [ "$7" = "clariden-5.11-osmesa" ]; then
  # paraview 5.11 osmesa
  PV_HASH="/ltilqh4"
  PV_SERVER=$($SQUASH_CMD spack location -i paraview $PV_HASH)/bin/pvserver
  OSMESA_PATH=$($SQUASH_CMD spack location -i /qadzwvd)/lib
  echo "export LD_LIBRARY_PATH=$OSMESA_PATH:\$LD_LIBRARY_PATH" >> $TEMP_FILE
  echo "echo Library path is \$LD_LIBRARY_PATH" >> $TEMP_FILE

fi

echo "" >> $TEMP_FILE
echo "srun -n $nservers -N $3 --cpu_bind=sockets --uenv-file=$SQUASH_IMG $PV_SERVER --reverse-connection --client-host=$HOST_NAME --server-port=$5" >> $TEMP_FILE

cat $TEMP_FILE

# submit the job

sbatch $TEMP_FILE

# wipe the temp file
#rm $TEMP_FILE

