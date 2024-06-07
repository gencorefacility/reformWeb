#!/bin/bash

dnf -y install https://rhn.cfs.its.nyu.edu/pub/katello-ca-consumer-latest.noarch.rpm
subscription-manager register --org="fas_biology" --activationkey="fas-bio-rh9-activation"

# Initial System Setup
dnf update -y
subscription-manager repos --enable codeready-builder-for-rhel-9-x86_64-rpms
dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm

# Secure
# Partition Mounting Weakness
# Configuration remediation steps
# The specific way to modify the partition mount options varies from system to system. Consult your operating system's manual or mount man page.
# To check the partition mounting options on a unix system run 'mount'. Run the command as root if necessary.
# To check for partition mounting weakness we consider the following criteria:
# /tmp and /var should have the following options set:
# nosuid
# noexec
# /etc should have the following options set:
# nosuid
# noexec
# /home should have the following options set:
# nosuid
# All partitions other than '/', '/dev', '/sys', and '/proc' should have the following options set:
# nodev

# Disable ICMP redirect support
# Configuration remediation steps
# Issue the following commands as root:
# 
#    sysctl -w net.ipv4.conf.all.accept_redirects=0
#    sysctl -w net.ipv4.conf.default.accept_redirects=0
#    sysctl -w net.ipv4.conf.all.secure_redirects=0
#    sysctl -w net.ipv4.conf.default.secure_redirects=0
# These settings can be added to /etc/sysctl.conf to make them permanent.
echo """net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.default.accept_redirects=0
net.ipv4.conf.all.secure_redirects=0
net.ipv4.conf.default.secure_redirects=0""" >> /etc/sysctl.conf


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
## Block root login to every one ##
PermitRootLogin no

## No more password login  ##
PermitEmptyPasswords no
PasswordAuthentication no
PubkeyAuthentication no

Match Address 127.0.0.0/8,192.168.0.0/16,172.16.0.0/12,10.0.0.0/8,128.122.0.0/16,216.165.16.0/20,216.165.32.0/19,216.165.64.0/18,128.238.0.0/16,91.230.41.0/24,192.114.110.0/24,193.206.104.0/24,193.205.158.0/25,212.219.93.0/24,195.113.94.0/24,193.175.54.0/24,203.174.165.128/25,194.214.81.0/24,103.242.128.0/22
   PermitRootLogin yes
   PermitRootLogin without-password
   PubkeyAuthentication yes
   AuthenticationMethods publickey


Match User root
   PermitRootLogin no
   AuthenticationMethods publickey
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
dnf install python3-devel
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


# Create the following cron job
crontab -e
# add following command to the files, and save it.
0 1 * * * /bin/bash /home/reform/reformWeb/cleanup.sh

# Create local File folder for test site
mkdir -p /home/reform/reformWeb/staticData
cd /home/reform/reformWeb/staticData
# Create directory for reference sequences and upload Exampl Ref Sequences
# for example: 
mkdir ref 
cd ref
wget --no-check-certificate -nv ftp://ftp.ensembl.org/pub/release-88/fasta/mus_musculus/dna/Mus_musculus.GRCm38.dna.toplevel.fa.gz
wget --no-check-certificate -nv ftp://ftp.ensembl.org/pub/release-88/gff3/mus_musculus/Mus_musculus.GRCm38.88.gff3.gz
# Create directory for inserted and up-down-seq
mkdir ../inserted
mkdir ../up-down-seq
# Please upload files to inserted and up-down-seq.
# And change the local files path in jobs.py line 97