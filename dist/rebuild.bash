#!/bin/bash -e

if [ -z "${JUJU_REPOSITORY}" ]; then
	echo "JUJU_REPOSITORY not set"
	exit 1
fi

rm -rf ${JUJU_REPOSITORY}/trusty/wallabag/ && charm build
