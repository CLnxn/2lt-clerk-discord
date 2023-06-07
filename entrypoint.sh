#!/bin/ash

source "/app/.env"
echo "DB PASSWORD: $DB_PASSWORD"
mkdir -p /run/mysqld
chown -R mysql:mysql /run/mysqld
mysql_install_db --user=mysql --ldata=/var/lib/mysql
mysqld --bind-address=127.0.0.1 --port=3306 --user=mysql --console --skip-networking=0 &

# Wait for mysql to start
while ! mysqladmin ping -h'localhost' --silent; do echo 'not up' && sleep .2; done
# if declared character buffer is more than what it actually contains,
# The carriage return char will be added, which causes all chars after it to start overwriting from the start pos
# password length must be more than or equal to -c Number (4 in this case)
function getEnvPW(){
    echo -n $DB_PASSWORD | head -c 4
}
mysql -u root << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '$(getEnvPW)';

CREATE DATABASE service_bot;
USE service_bot;
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    permission INT DEFAULT 0 
);

CREATE TABLE ns (
    user_id BIGINT UNIQUE,
    ord_date DATETIME DEFAULT NULL,
    pay_amt DECIMAL(20,2) DEFAULT NULL,
    pay_dom INT DEFAULT NULL,
	FOREIGN KEY (user_id) REFERENCES users(id) 
);

CREATE TABLE reminders(
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT,
    content TEXT NOT NULL,
    date_created DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
EOF

/usr/bin/supervisord -c /etc/supervisord.conf
# python /app/main.py