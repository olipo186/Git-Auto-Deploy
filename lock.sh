#!/bin/sh
cd $1

set -o noclobber
{ > status_waiting; }
if [ "$?" != "0" ]
then
    echo "Some other thread is alreay waiting. Exit."

    set +o noclobber
    cd -
    exit 1
else

    { > status_running; }
    while [ "$?" != "0" ]
    do
        echo "Some other thread is already building. Waiting 5 sec!"
        sleep 5
        { > status_running; }
    done
    rm status_waiting

    set +o noclobber
    cd -
    exit 0
fi
