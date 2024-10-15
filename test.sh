#!/bin/bash

set -e

system=eiger
uenv=prgenv-gnu:24.7
uarch=zen2

echo "==== CLONING THE PIPELINE ===="
if [ -d ./uenv-pipeline ]; then
    echo "== cleaning up old copy"
    rm -rf uenv-pipeline
fi
git clone https://github.com/eth-cscs/uenv-pipeline.git

echo ""
echo "==== CONFIGURING THE PIPELINE ===="
./uenv-pipeline/configure-pipeline -c./config.yaml -r./recipes -s$system -u$uenv -a$uarch -o./pipeline.yml

echo ""
echo "==== GENERATING THE BUILD COMMAND ===="
echo '#!/bin/bash' > tmp.sh
echo 'TESTRUN="-t"' >> tmp.sh
grep '^#@@cmd@@' pipeline.yml | sed s'|#@@cmd@@||g' >> tmp.sh
chmod +x tmp.sh
cat tmp.sh

echo ""
echo "==== RUNNING THE BUILD COMMAND ===="
./tmp.sh
