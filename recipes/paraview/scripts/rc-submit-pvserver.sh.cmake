#!/bin/bash  -l
# updated Jan-Aug 2024 to support stackinator generation
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

# ------------------------------------
# Create a temporary filename to write our launch script into
TEMP_FILE=`mktemp`
echo "Temporary FileName is :" $TEMP_FILE

# ------------------------------------
# this enables us to connect to the generic name "daint.cscs.ch" from the client
HOST_NAME=$(hostname).cscs.ch

# ------------------------------------
# variables set via cmake substitution
SQUASH_IMG=@UENV_IMAGE@
PARAVIEW_VERSION=@PARAVIEW_VERSION@
PARAVIEW_INSTALL_DIR=@PARAVIEW_INSTALL_DIR@
PARAVIEW_PLUGINS_DIR=@PARAVIEW_PLUGINS_DIR@
PV_LIBRARY_PATH=@PV_LIBRARY_PATH@
#
GPU_WRAPPER=$PARAVIEW_INSTALL_DIR/gpu_wrapper.sh
PV_SERVER=$PARAVIEW_INSTALL_DIR/bin/pvserver

# ------------------------------------
# compute number of pvservers to run from nodes * tasks per node
nservers=$[$3 * $4]
cpus_task=$[128 / $4]

# ------------------------------------
# Currently we are supporting only one version of paraview in a uenv
# so this version check is essentially obsolete:
if [ "$7" = "nvidia" ]; then
  # paraview nvidia EGL
  CONSTRAINT="gpu"
elif [ "$7" = "osmesa" ]; then
  # paraview osmesa
  CONSTRAINT="mc"
fi

# ------------------------------------
# Create a job script
echo "#!/bin/bash -l"                              >> $TEMP_FILE
echo "#SBATCH --job-name=$1"                       >> $TEMP_FILE
echo "#SBATCH --time=$2"                           >> $TEMP_FILE
echo "#SBATCH --nodes=$3"                          >> $TEMP_FILE
echo "#SBATCH --ntasks-per-node=$4"                >> $TEMP_FILE
echo "#SBATCH --ntasks=$nservers"                  >> $TEMP_FILE
echo "#SBATCH --partition=$8"                      >> $TEMP_FILE
echo "#SBATCH --account=${10}"                     >> $TEMP_FILE
echo "#SBATCH --constraint=${CONSTRAINT}"          >> $TEMP_FILE
echo "#SBATCH --uenv=${SQUASH_IMG}"                >> $TEMP_FILE
echo "#SBATCH --cpus-per-task=$cpus_task"          >> $TEMP_FILE

# TODO: check these and replace with something generic
echo "#SBATCH --ntasks-per-core=1"                 >> $TEMP_FILE
echo "#SBATCH --hint=nomultithread"                >> $TEMP_FILE

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

# ------------------------------------
# setup environment needed by paraview server
# ------------------------------------
echo ""                                                                         >> $TEMP_FILE
echo "spack load py-numpy"                                                      >> $TEMP_FILE
echo "export NVINDEX_PVPLUGIN_HOME=${PARAVIEW_PLUGINS_DIR}"                     >> $TEMP_FILE
echo "export LD_LIBRARY_PATH=$PV_LIBRARY_PATH:$LD_LIBRARY_PATH"                 >> $TEMP_FILE
echo "export PV_PLUGIN_PATH=$PARAVIEW_PLUGINS_DIR:$PARAVIEW_PLUGINS_DIR/lib64"  >> $TEMP_FILE

echo "" >> $TEMP_FILE
echo "srun -n $nservers -N $3 --cpu_bind=sockets $GPU_WRAPPER $PV_SERVER --reverse-connection --client-host=$HOST_NAME --server-port=$5" >> $TEMP_FILE

# ------------------------------------
# submit the job
# ------------------------------------
cat $TEMP_FILE
sbatch $TEMP_FILE

# ------------------------------------
# wipe the temp file
rm $TEMP_FILE