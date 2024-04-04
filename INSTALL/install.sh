#!/bin/bash

# Initial System Setup
dnf update -y
subscription-manager repos --enable codeready-builder-for-rhel-9-x86_64-rpms
dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm

# Install & Configure
## fail2ban
yum install -y fail2ban
cp ./conf/fail2ban_jail.local /etc/fail2ban/jail.local
cp ./conf/fail2ban_iptables-multiport.conf /etc/fail2ban/action.d/iptables-multiport.conf
systemctl start fail2ban
systemctl enable fail2ban

## SSL cert
openssl genrsa -out reform.bio.nyu.edu.key 2048
openssl req -out reform.bio.nyu.edu.csr -key reform.bio.nyu.edu.key -new -sha256
openssl req -in reform.bio.nyu.edu.csr -noout -text

echo "Request cert at https://www.nyu.edu/its/certificates/"
# Download "Certificate only, PEM encoded" and "Root/Intermediate(s) only, PEM encoded"
# Append interm chaing to cert
#   cat reform_bio_nyu_edu_interm.cer >> reform_bio_nyu_edu_cert.cer

## nginx
yum install nginx -y
cp ./conf/nginx.conf /etc/nginx/conf.d/default.conf
setsebool -P httpd_can_network_connect 1
# If permission fails for a cert or file execute:
# chcon -t httpd_config_t /path/to/key
systemctl start nginx
systemctl enable nginx

# Create Application User
useradd reform
mkdir /home/reform/reformWeb
git clone https://github.com/gencorefacility/reformWeb.git /home/reform/reformWeb/
python3 -m venv /home/reform/venv
source /home/reform/venv/bin/activate
pip install -r /home/reform/reformWeb/requirements.txt
echo "source ~/venv/bin/activate" >> /home/reform/.bashrc
chown -R reform:reform /home/reform

# Create data folders (uploads & downloads) outside of home folder
# Reason as /home generally has limited storage space
subdirectories=("downloads" "uploads" "results")
dataDir="/data"
for subdir in "${subdirectories[@]}"; do
    mkdir -p "${dataDir}/${subdir}"
    cp /home/reform/reformWeb/${subdir}/.gitignore ${dataDir}/${subdir}/.gitignore
    rm -Rf /home/reform/reformWeb/${subdir}
    ln -s ${dataDir}/${subdir} /home/reform/reformWeb/${subdir}
done

##  redis server
yum install -y redis
systemctl start redis
systemctl enable redis

## redis workers
cp ./conf/systemd_worker.service /etc/systemd/system/rqworker\@.service
for i in {1..3}
do
   systemctl start rqworker@$i.service
   systemctl enable rqworker@$i.service
done

# supervisord for gunicorn
dnf install -y supervisor
mkdir -p /var/log/reform
cp ./conf/supervisor_reform.ini /etc/supervisord.d/reform.ini
systemctl start supervisord
systemctl enable supervisord
