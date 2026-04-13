#!/bin/bash
# Start both docker images
docker compose up -d
if [ $? -ne 0 ]
then
	echo 'Failed to start docker images. Aborting demo...'
	exit 2
fi
echo 'Waiting for pip...'
docker exec bob_node pip install cryptography > /dev/null
docker exec alice_node pip install cryptography > /dev/null

echo 'Starting Server...'
docker exec bob_node python server.py > server.log &
sleep 1
echo 'Running Client...'
docker exec alice_node python client.py > client.log
docker compose down
echo 'SERVER OUTPUT:'
cat ./server.log
echo 'CLIENT OUTPUT:'
cat ./client.log
rm ./server.log
rm ./client.log


