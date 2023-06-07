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