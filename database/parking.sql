CREATE DATABASE IF NOT EXISTS parking_db;
USE parking_db;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    slot_name VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type ENUM('Two-wheeler','Four-wheeler') NOT NULL DEFAULT 'Four-wheeler',
    status ENUM('Available','Occupied') NOT NULL DEFAULT 'Available'
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    slot_id INT NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    vehicle_type ENUM('Two-wheeler','Four-wheeler') NOT NULL DEFAULT 'Four-wheeler',
    status ENUM('Confirmed','Cancelled') NOT NULL DEFAULT 'Confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_booking_slot FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
);

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    predicted_status ENUM('Occupied','Vacant') NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO parking_slots (slot_name, vehicle_type, status) VALUES
('S01','Four-wheeler','Available'), ('S02','Four-wheeler','Available'),
('S03','Four-wheeler','Available'), ('S04','Four-wheeler','Available'),
('S05','Four-wheeler','Available'), ('S06','Four-wheeler','Available'),
('S07','Four-wheeler','Available'), ('S08','Four-wheeler','Available'),
('S09','Four-wheeler','Available'), ('S10','Four-wheeler','Available'),
('S11','Two-wheeler','Available'), ('S12','Two-wheeler','Available'),
('S13','Two-wheeler','Available'), ('S14','Two-wheeler','Available'),
('S15','Two-wheeler','Available'), ('S16','Two-wheeler','Available'),
('S17','Two-wheeler','Available'), ('S18','Two-wheeler','Available'),
('S19','Two-wheeler','Available'), ('S20','Two-wheeler','Available');
