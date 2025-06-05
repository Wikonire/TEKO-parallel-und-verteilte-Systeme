#!/bin/bash
# Automatisiert den Start mehrerer Docker-Container (worker-Container), welche dann gemeinsam mit einem main-Container die parallele Berechnung durchführen.
: <<'END_COMMENT'
Container werden skaliert (je nach Anzahl Hosts).
SSH-Schlüssel werden generiert und Container für SSH-Zugriff vorbereitet.
Der Main-Container erhält die Container-Namen (Hostname).
Startet Berechnung via pi.py verteilt auf die Worker-Hosts.
END_COMMENT

if [ $# -eq 0 ]; then
    echo "Usage: $0 --hosts=host1,host2,..."
    exit 1
fi

for arg in "$@"; do
  case $arg in
    --hosts=*)
      HOSTS="${arg#*=}"
      shift
      ;;
    *)
      echo "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

IFS=',' read -ra HOST_ARRAY <<< "$HOSTS"

WORKER_COUNT=${#HOST_ARRAY[@]}
docker-compose up -d --scale worker=$WORKER_COUNT

sleep 5

# Dynamisch korrekte Containernamen holen:
WORKER_CONTAINER_IDS=$(docker-compose ps -q worker | head -n $WORKER_COUNT)
WORKER_CONTAINER_NAMES=()
> known_hosts.tmp
i=0

for container_id in $WORKER_CONTAINER_IDS; do
    container_name=$(docker inspect --format '{{.Name}}' "$container_id" | sed 's/^\///')
    WORKER_CONTAINER_NAMES+=("$container_name")
    # SSH-Keyscan auf echte Containernamen
    docker-compose exec main ssh-keyscan "$container_name" >> known_hosts.tmp 2>/dev/null
    ((i++))
done

# known_hosts in main-container kopieren
MAIN_CONTAINER=$(docker-compose ps -q main)
docker cp known_hosts.tmp "$MAIN_CONTAINER":/root/.ssh/known_hosts
rm known_hosts.tmp

# Hosts-Namen korrekt setzen (Container-Hostnamen verwenden)
HOSTS_COMMA_SEPARATED=$(IFS=','; echo "${WORKER_CONTAINER_NAMES[*]}")

# docker compose main und hosts starten
docker-compose run --rm main python pi.py --hosts="$HOSTS_COMMA_SEPARATED" --seg-size=100000
