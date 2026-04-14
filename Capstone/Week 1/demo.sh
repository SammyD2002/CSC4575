#!/bin/bash
# Start both docker images
do_good () {
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
echo 'Standard Transmission:'
echo '\tStarting Server...'
docker exec bob_node python server.py > server.log &
sleep 1
echo '\tSending Message...'
docker exec alice_node python client.py > client.log

docker compose down
echo 'SERVER OUTPUT:'
cat ./server.log
echo 'CLIENT OUTPUT:'
cat ./client.log

}
rm ./server.log
rm ./client.log
