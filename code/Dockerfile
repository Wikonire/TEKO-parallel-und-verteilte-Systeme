FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir /var/run/sshd && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    mkdir -p /root/.ssh

COPY authorized_keys /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

WORKDIR /app
COPY pi.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
