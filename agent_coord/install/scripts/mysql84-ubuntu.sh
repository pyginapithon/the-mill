#!/bin/bash
# MySQL 8.4 LTS from MySQL's apt repo. Ubuntu's mysql-server package is MariaDB.
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y curl ca-certificates gnupg openssl
tmp=$(mktemp)
curl -fsSL -o "$tmp" https://dev.mysql.com/get/mysql-apt-config_0.8.36-1_all.deb
debconf-set-selections <<'EOF'
mysql-apt-config mysql-apt-config/select-server select mysql-8.4-lts
mysql-apt-config mysql-apt-config/select-product select Ok
EOF
dpkg -i "$tmp"
rm -f "$tmp"
apt-get update
apt-get install -y mysql-community-server
install -d /etc/mysql/mysql.conf.d
cat > /etc/mysql/mysql.conf.d/mill.cnf <<'EOF'
[mysqld]
bind-address = 127.0.0.1
mysqlx = 0
local_infile = 0
skip-name-resolve
EOF
systemctl enable --now mysql
systemctl restart mysql
mysql --protocol=socket -u root <<'SQL'
ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'root';
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
FLUSH PRIVILEGES;
SQL
