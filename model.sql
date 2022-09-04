CREATE TABLE Customer (
    id SERIAL PRIMARY KEY,
    login VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    active BOOLEAN DEFAULT false,
    admin BOOLEAN DEFAULT false
);
CREATE TABLE Bill (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Customer(id),
    amount NUMERIC DEFAULT 0
);
CREATE TABLE Product (
    id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    description VARCHAR(140),
    price NUMERIC
);
CREATE TABLE History (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES Bill(id),
    amount NUMERIC NOT NULL
);
