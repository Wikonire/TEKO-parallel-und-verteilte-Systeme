# code/Dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y openssh-server \
    && mkdir /var/run/sshd \
    && echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
WORKDIR /app
COPY pi.py requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
# Public Key ins Image kopieren (für Demo):
# better: über volume oder Docker secret reinziehen
COPY id_rsa.pub /root/.ssh/authorized_keys
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
