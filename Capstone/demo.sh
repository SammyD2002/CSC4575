#!/bin/bash
# Set variables for client and server file
CLIENT="client.py"
SERVER="server.py"
if [ $# -eq 1 ]
then
	CLIENT="$1"
fi
# Ensure client is a container path, not a local path
CLIENT=$(realpath --relative-to ./ "$CLIENT")
if [ $# -eq 2 ]
then
	SERVER="$2"
fi
# Ensure server is a container path, not a local path
SERVER=$(realpath --relative-to ./ "$SERVER")
# Set log files based on server and client python script names
SRVLOG="$(realpath $(basename -s '.py' $SERVER).log)"
SRVERR="$(realpath $(basename -s '.py' $SERVER).err.log)"
CLILOG="$(realpath $(basename -s '.py' $CLIENT).log)"
CLIERR="$(realpath $(basename -s '.py' $CLIENT).err.log)"
# Start both docker images
sudo docker compose up -d
if [ $? -ne 0 ]
then
	echo 'Failed to start docker images. Aborting demo...'
	exit 2
fi
echo initializing tcpdump...
# killing tcpdump is not required since it will exit when br-crypto disappears. sudo -b makes tcpdump run in background.
# This series of commands prints the first line of TCP Dump's output to the terminal while writing all of it to tcpdump.log. tcpdump.log is read later to count packets.
sudo -b tcpdump -q -i 'br-crypto' -w 'demo.pcap' -f 'tcp port 65432' 2>&1 | tee ./tcpdump.log | sed -n '1p' &
TEEPID=$!
echo 'Waiting for pip...'
sudo docker exec bob_node pip -q install cryptography &> /dev/null
sudo docker exec alice_node pip -q install cryptography &> /dev/null
SRVEXIT=-1
CLIEXIT=-1
do_srv () {
sudo docker exec bob_node python "$SERVER" 2> "$SRVERR" 1> "$SRVLOG"
SRVEXIT=$?
echo "DONE"
echo "BOB: SERVER EXITTED $SRVEXIT
SERVER OUTPUT:
$(cat ./server.log)
SERVER ERRORS:
$(cat ./server.err.log)"
sudo rm ./server.log
}
echo -e "\r"'Executing Demo Transmission:'
echo '    Starting Server...'
do_srv &
srvjob=$!
sleep 1
echo '    Sending Message...'
sudo docker exec alice_node python "$CLIENT" 2> "$CLIERR" 1> "$CLILOG"
CLIEXIT=$?
wait $srvjob
echo "ALICE: CLIENT EXITTED $CLIEXIT
CLIENT OUTPUT:
$(cat "$CLILOG")
CLIENT ERRORS:
$(cat "$CLIERR")"
sudo rm "$CLILOG"
echo "Shutting Down Containers..."
sudo docker compose down
wait "$TEEPID"
echo "TCPDUMP:
$(grep 'packets' ./tcpdump.log)"

