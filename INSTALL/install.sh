#!/bin/bash

dnf -y install https://rhn.cfs.its.nyu.edu/pub/katello-ca-consumer-latest.noarch.rpm
subscription-manager register --org="fas_biology" --activationkey="fas-bio-rh9-activation"

# Initial System Setup
dnf update -y
subscription-manager repos --enable codeready-builder-for-rhel-9-x86_64-rpms
dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm

# Install & Configure
## fail2ban
dnf install -y fail2ban
cp ./conf/fail2ban_jail.local /etc/fail2ban/jail.local
cp ./conf/fail2ban_iptables-multiport.conf /etc/fail2ban/action.d/iptables-multiport.conf
systemctl start fail2ban
systemctl enable fail2ban

# Limit SSH
## Only allow SSH connections through NYU net & VPN. Root can only login with SSH key.
echo """
Match Address 128.122.0.0/16,216.165.16.0/20,216.165.32.0/19,216.165.64.0/18,128.238.0.0/16,91.230.41.0/24,193.146.139.0/25,192.114.110.0/24,193.206.104.0/24,193.205.158.0/25,212.219.93.0/24,195.113.94.0/24,193.175.54.0/24,203.174.165.128/25,194.214.81.0/24,103.242.128.0/22,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
PermitRootLogin prohibit-password
AuthenticationMethods publickey password
""" > /etc/ssh/sshd_config.d/only_nyu_net.conf
systemctl reload sshd

## SSL cert
openssl genrsa -out reform.bio.nyu.edu.key 2048
openssl req -out reform.bio.nyu.edu.csr -key reform.bio.nyu.edu.key -new -sha256
openssl req -in reform.bio.nyu.edu.csr -noout -text

echo "Request cert at https://www.nyu.edu/its/certificates/"
# Download "Certificate only, PEM encoded" and "Root/Intermediate(s) only, PEM encoded"
# Append interm chaing to cert
#   cat reform_bio_nyu_edu_interm.cer >> reform_bio_nyu_edu_cert.cer

## nginx
dnf install nginx -y
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
dnf install -y redis
systemctl start redis
systemctl enable redis

# supervisord for gunicorn
dnf install -y supervisor
mkdir -p /var/log/reform
cp ./conf/supervisor*ini /etc/supervisord.d/
systemctl start supervisord
systemctl enable supervisord
