#!/bin/sh

# Start server and background it, saving pid for later cancellation. The server
# takes some time to start up, so just sleep and wait for it.
#
# TODO(myenik): Come up with a better synchronization mechanism to detect that
# the server is ready other than sleep. Leaving this for now since it's just a
# demo...
python3 server.py &
SERVER_PID=$!
sleep 1

# Run sender task to completion
python3 sender.py

# Send ctrl+c to server and wait for termination
kill -s INT $SERVER_PID
wait
