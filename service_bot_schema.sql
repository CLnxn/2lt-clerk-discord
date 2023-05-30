USE service_bot;
CREATE TABLE users (
    id INT PRIMARY KEY,
    permission INT DEFAULT 0 
);

CREATE TABLE NS (
    user_id INT UNIQUE,
    ord_date DATE DEFAULT NULL,
    pay_amt DECIMAL(20,2) DEFAULT NULL,
    pay_dom INT DEFAULT NULL,
	FOREIGN KEY (user_id) REFERENCES users(id) 
);

CREATE TABLE reminders(
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    content TEXT,
    date_created DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);