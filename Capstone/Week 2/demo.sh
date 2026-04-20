#!/bin/bash
# Start both docker images
docker compose up -d
if [ $? -ne 0 ]
then
	echo 'Failed to start docker images. Aborting demo...'
	exit 2
fi
echo initializing tcpdump...
# killing tcpdump is not required since it will exit when br-crypto disappears. sudo -b makes tcpdump run in background.
sudo -b tcpdump -i 'br-crypto' -w 'demo.pcap' -f 'tcp port 65432'
echo 'Waiting for pip...'
docker exec bob_node pip -q install cryptography &> /dev/null
docker exec alice_node pip install cryptography &> /dev/null
SRVEXIT=-1
CLIEXIT=-1
do_srv () {
docker exec bob_node python server.py 2> server.err.log 1> server.log
SRVEXIT=$?
echo "SERVER EXITTED $SRVEXIT
SERVER OUTPUT:
$(cat ./server.log)
SERVER ERRORS:
$(cat ./server.err.log)"
rm ./server.log
}
echo 'Standard Transmission:'
echo '    Starting Server...'
do_srv &
srvjob=$!
sleep 1
echo '    Sending Message...'
docker exec alice_node python client.py 2> client.err.log 1> client.log
CLIEXIT=$?
wait $srvjob
echo "CLIENT EXITTED $CLIEXIT
CLIENT OUTPUT:
$(cat ./client.log)
CLIENT ERRORS:
$(cat ./client.err.log)"
rm ./client.log
docker compose down
