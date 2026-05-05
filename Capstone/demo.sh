#!/bin/bash
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
sudo docker exec bob_node python server.py 2> server.err.log 1> server.log
SRVEXIT=$?
echo "DONE"
echo "BOB: SERVER EXITTED $SRVEXIT
SERVER OUTPUT:
$(cat ./server.log)
SERVER ERRORS:
$(cat ./server.err.log)"
sudo rm -r ./server.log
}
echo -e "\r"'Executing Demo Transmission:'
echo '    Starting Server...'
do_srv &
srvjob=$!
sleep 1
echo '    Sending Message...'
sudo docker exec alice_node python client.py 2> client.err.log 1> client.log
CLIEXIT=$?
wait $srvjob
echo "ALICE: CLIENT EXITTED $CLIEXIT
CLIENT OUTPUT:
$(cat ./client.log)
CLIENT ERRORS:
$(cat ./client.err.log)"
sudo rm -r ./client.log
echo "Shutting Down Containers..."
sudo docker compose down
wait "$TEEPID"
echo "TCPDUMP:
$(grep 'packets' ./tcpdump.log)"

