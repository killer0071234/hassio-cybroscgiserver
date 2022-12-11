#!/bin/bash

set -e
echo "Starting nginx server..."
nginx
cd /usr/local/bin/scgi_server/src
echo "Starting cybroscgiserver..."
python app.py
RETVAL=$?
exit $RETVAL
