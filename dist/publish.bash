#!/bin/bash -ex

CHARM=wallabag
SERIES=trusty
CHARM_DIR=${JUJU_REPOSITORY}/${SERIES}/${CHARM}

BZR_URL=lp:\~cmars/charms/trusty/wallabag/trunk

if [ ! -d "${CHARM_DIR}" ]; then
	echo "cannot find charm, try building it"
	exit 1
fi

rm -rf ${CHARM_DIR}/.bzr

_work=$(mktemp -d)
trap "rm -rf ${_work}" EXIT

pushd ${_work}
bzr branch $BZR_URL charm
cp -r charm/.bzr ${CHARM_DIR}/.bzr
popd

pushd ${CHARM_DIR}
bzr add .
bzr commit -m "Publish charm at $(date +%s)"
bzr push $BZR_URL
popd

