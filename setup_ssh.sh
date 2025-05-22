#!/bin/bash

# SSH-Schlüssel generieren, falls noch nicht vorhanden
[ -f id_rsa ] || ssh-keygen -t rsa -b 4096 -N "" -f ./id_rsa

# Kopiere den öffentlichen Schlüssel in den code-Ordner für Docker
cp id_rsa.pub ./code/authorized_keys
