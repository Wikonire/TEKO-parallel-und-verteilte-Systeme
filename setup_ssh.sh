#!/bin/bash

[ -f id_rsa ] || ssh-keygen -t rsa -b 4096 -N "" -f ./id_rsa
cp id_rsa.pub ./code/authorized_keys
