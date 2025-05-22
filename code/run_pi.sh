#!/bin/bash

# Container bauen und starten
docker-compose build
docker-compose up -d

sleep 5

docker-compose exec master bash -c "\
chmod 600 /root/.ssh/id_rsa && \
ssh-keyscan worker1 worker2 >> /root/.ssh/known_hosts"

docker-compose exec master python pi.py --hosts worker1,worker2 --seg-size 100000
