import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

class Database:
    def __init__(self, db_path='parking_system.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create parking_lots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parking_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prime_location_name TEXT NOT NULL,
                address TEXT NOT NULL,
                pin_code TEXT NOT NULL,
                price_per_hour REAL NOT NULL,
                maximum_number_of_spots INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create parking_spots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parking_spots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER NOT NULL,
                spot_number INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'A',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lot_id) REFERENCES parking_lots (id) ON DELETE CASCADE
            )
        ''')
        
        # Create reservations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spot_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                parking_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                leaving_timestamp TIMESTAMP NULL,
                parking_cost REAL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                FOREIGN KEY (spot_id) REFERENCES parking_spots (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        
        # Create default admin user if not exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            admin_password = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role) 
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@parking.com', admin_password, 'admin'))
            conn.commit()
        
        conn.close()

class User:
    def __init__(self, db):
        self.db = db
    
    def create_user(self, username, email, password, role='user'):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role) 
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def get_user_by_username(self, username):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def verify_password(self, user, password):
        return check_password_hash(user['password_hash'], password)
    
    def get_all_users(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return users

class ParkingLot:
    def __init__(self, db):
        self.db = db
    
    def create_lot(self, name, address, pin_code, price_per_hour, max_spots):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO parking_lots (prime_location_name, address, pin_code, price_per_hour, maximum_number_of_spots)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, address, pin_code, price_per_hour, max_spots))
            
            lot_id = cursor.lastrowid
            
            # Create parking spots for this lot
            for i in range(1, max_spots + 1):
                cursor.execute('''
                    INSERT INTO parking_spots (lot_id, spot_number, status)
                    VALUES (?, ?, 'A')
                ''', (lot_id, i))
            
            conn.commit()
            return lot_id
        except Exception as e:
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_all_lots(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pl.*, 
                   COUNT(ps.id) as total_spots,
                   SUM(CASE WHEN ps.status = 'A' THEN 1 ELSE 0 END) as available_spots,
                   SUM(CASE WHEN ps.status = 'O' THEN 1 ELSE 0 END) as occupied_spots
            FROM parking_lots pl
            LEFT JOIN parking_spots ps ON pl.id = ps.lot_id
            GROUP BY pl.id
            ORDER BY pl.created_at DESC
        ''')
        lots = cursor.fetchall()
        conn.close()
        return lots
    
    def get_lot_by_id(self, lot_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parking_lots WHERE id = ?', (lot_id,))
        lot = cursor.fetchone()
        conn.close()
        return lot
    
    def update_lot(self, lot_id, name, address, pin_code, price_per_hour, max_spots):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current spot count
            cursor.execute('SELECT COUNT(*) as current_spots FROM parking_spots WHERE lot_id = ?', (lot_id,))
            current_spots = cursor.fetchone()['current_spots']
            
            # Update lot details
            cursor.execute('''
                UPDATE parking_lots 
                SET prime_location_name = ?, address = ?, pin_code = ?, 
                    price_per_hour = ?, maximum_number_of_spots = ?
                WHERE id = ?
            ''', (name, address, pin_code, price_per_hour, max_spots, lot_id))
            
            # Adjust parking spots if needed
            if max_spots > current_spots:
                # Add more spots
                for i in range(current_spots + 1, max_spots + 1):
                    cursor.execute('''
                        INSERT INTO parking_spots (lot_id, spot_number, status)
                        VALUES (?, ?, 'A')
                    ''', (lot_id, i))
            elif max_spots < current_spots:
                # Remove excess spots (only if they are available)
                cursor.execute('''
                    DELETE FROM parking_spots 
                    WHERE lot_id = ? AND spot_number > ? AND status = 'A'
                ''', (lot_id, max_spots))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_lot(self, lot_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if all spots are available
            cursor.execute('''
                SELECT COUNT(*) as occupied_count 
                FROM parking_spots 
                WHERE lot_id = ? AND status = 'O'
            ''', (lot_id,))
            occupied_count = cursor.fetchone()['occupied_count']
            
            if occupied_count > 0:
                return False  # Cannot delete if spots are occupied
            
            cursor.execute('DELETE FROM parking_lots WHERE id = ?', (lot_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()

class ParkingSpot:
    def __init__(self, db):
        self.db = db
    
    def get_spots_by_lot(self, lot_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ps.*, r.user_id, u.username, r.parking_timestamp
            FROM parking_spots ps
            LEFT JOIN reservations r ON ps.id = r.spot_id AND r.status = 'active'
            LEFT JOIN users u ON r.user_id = u.id
            WHERE ps.lot_id = ?
            ORDER BY ps.spot_number
        ''', (lot_id,))
        spots = cursor.fetchall()
        conn.close()
        return spots
    
    def get_available_spot(self, lot_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM parking_spots 
            WHERE lot_id = ? AND status = 'A' 
            ORDER BY spot_number LIMIT 1
        ''', (lot_id,))
        spot = cursor.fetchone()
        conn.close()
        return spot
    
    def book_spot(self, spot_id, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Update spot status
            cursor.execute('UPDATE parking_spots SET status = "O" WHERE id = ?', (spot_id,))
            
            # Create reservation
            cursor.execute('''
                INSERT INTO reservations (spot_id, user_id, status)
                VALUES (?, ?, 'active')
            ''', (spot_id, user_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def release_spot(self, spot_id, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculate parking cost
            cursor.execute('''
                SELECT r.*, pl.price_per_hour
                FROM reservations r
                JOIN parking_spots ps ON r.spot_id = ps.id
                JOIN parking_lots pl ON ps.lot_id = pl.id
                WHERE r.spot_id = ? AND r.user_id = ? AND r.status = 'active'
            ''', (spot_id, user_id))
            
            reservation = cursor.fetchone()
            if not reservation:
                return False
            
            # Calculate hours parked (minimum 1 hour)
            parking_time = datetime.now()
            start_time = datetime.fromisoformat(reservation['parking_timestamp'].replace('Z', ''))
            hours_parked = max(1, (parking_time - start_time).total_seconds() / 3600)
            total_cost = hours_parked * reservation['price_per_hour']
            
            # Update reservation
            cursor.execute('''
                UPDATE reservations 
                SET leaving_timestamp = CURRENT_TIMESTAMP, 
                    parking_cost = ?, 
                    status = 'completed'
                WHERE spot_id = ? AND user_id = ? AND status = 'active'
            ''', (total_cost, spot_id, user_id))
            
            # Update spot status
            cursor.execute('UPDATE parking_spots SET status = "A" WHERE id = ?', (spot_id,))
            
            conn.commit()
            return total_cost
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()

class Reservation:
    def __init__(self, db):
        self.db = db
    
    def get_user_reservations(self, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, ps.spot_number, pl.prime_location_name, pl.address
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.user_id = ?
            ORDER BY r.parking_timestamp DESC
        ''', (user_id,))
        reservations = cursor.fetchall()
        conn.close()
        return reservations
    
    def get_active_reservation(self, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, ps.spot_number, pl.prime_location_name, pl.address, pl.price_per_hour
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            WHERE r.user_id = ? AND r.status = 'active'
        ''', (user_id,))
        reservation = cursor.fetchone()
        conn.close()
        return reservation
    
    def get_all_reservations(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, ps.spot_number, pl.prime_location_name, u.username
            FROM reservations r
            JOIN parking_spots ps ON r.spot_id = ps.id
            JOIN parking_lots pl ON ps.lot_id = pl.id
            JOIN users u ON r.user_id = u.id
            ORDER BY r.parking_timestamp DESC
        ''')
        reservations = cursor.fetchall()
        conn.close()
        return reservations