from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import Database, User, ParkingLot, ParkingSpot, Reservation
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database and models
db = Database()
user_model = User(db)
parking_lot_model = ParkingLot(db)
parking_spot_model = ParkingSpot(db)
reservation_model = Reservation(db)

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_model.get_user_by_username(username)
        
        if user and user_model.verify_password(user, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash('Login successful!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user_id = user_model.create_user(username, email, password)
        
        if user_id:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists!', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    lots = parking_lot_model.get_all_lots()
    users = user_model.get_all_users()
    reservations = reservation_model.get_all_reservations()
    
    # Statistics
    total_lots = len(lots)
    total_spots = sum(lot['total_spots'] or 0 for lot in lots)
    occupied_spots = sum(lot['occupied_spots'] or 0 for lot in lots)
    total_users = len([u for u in users if u['role'] == 'user'])
    
    stats = {
        'total_lots': total_lots,
        'total_spots': total_spots,
        'occupied_spots': occupied_spots,
        'available_spots': total_spots - occupied_spots,
        'total_users': total_users,
        'active_reservations': len([r for r in reservations if r['status'] == 'active'])
    }
    
    return render_template('admin/dashboard.html', 
                         lots=lots, 
                         users=users, 
                         reservations=reservations,
                         stats=stats)

@app.route('/admin/lot/create', methods=['GET', 'POST'])
def admin_create_lot():
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        price_per_hour = float(request.form['price_per_hour'])
        max_spots = int(request.form['max_spots'])
        
        lot_id = parking_lot_model.create_lot(name, address, pin_code, price_per_hour, max_spots)
        
        if lot_id:
            flash('Parking lot created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Error creating parking lot!', 'danger')
    
    return render_template('admin/create_lot.html')

@app.route('/admin/lot/<int:lot_id>/edit', methods=['GET', 'POST'])
def admin_edit_lot(lot_id):
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    lot = parking_lot_model.get_lot_by_id(lot_id)
    if not lot:
        flash('Parking lot not found!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        price_per_hour = float(request.form['price_per_hour'])
        max_spots = int(request.form['max_spots'])
        
        if parking_lot_model.update_lot(lot_id, name, address, pin_code, price_per_hour, max_spots):
            flash('Parking lot updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Error updating parking lot!', 'danger')
    
    return render_template('admin/edit_lot.html', lot=lot)

@app.route('/admin/lot/<int:lot_id>/delete')
def admin_delete_lot(lot_id):
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    if parking_lot_model.delete_lot(lot_id):
        flash('Parking lot deleted successfully!', 'success')
    else:
        flash('Cannot delete parking lot with occupied spots!', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/lot/<int:lot_id>/spots')
def admin_view_spots(lot_id):
    if session.get('role') != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    lot = parking_lot_model.get_lot_by_id(lot_id)
    spots = parking_spot_model.get_spots_by_lot(lot_id)
    
    return render_template('admin/view_spots.html', lot=lot, spots=spots)

@app.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    lots = parking_lot_model.get_all_lots()
    reservations = reservation_model.get_user_reservations(user_id)
    active_reservation = reservation_model.get_active_reservation(user_id)
    
    return render_template('user/dashboard.html', 
                         lots=lots, 
                         reservations=reservations,
                         active_reservation=active_reservation)

@app.route('/user/book/<int:lot_id>')
def user_book_spot(lot_id):
    if session.get('role') != 'user':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    
    # Check if user already has an active reservation
    active_reservation = reservation_model.get_active_reservation(user_id)
    if active_reservation:
        flash('You already have an active parking reservation!', 'warning')
        return redirect(url_for('user_dashboard'))
    
    # Find available spot
    available_spot = parking_spot_model.get_available_spot(lot_id)
    
    if available_spot:
        if parking_spot_model.book_spot(available_spot['id'], user_id):
            flash('Parking spot booked successfully!', 'success')
        else:
            flash('Error booking parking spot!', 'danger')
    else:
        flash('No available spots in this parking lot!', 'warning')
    
    return redirect(url_for('user_dashboard'))

@app.route('/user/release/<int:spot_id>')
def user_release_spot(spot_id):
    if session.get('role') != 'user':
        flash('Access denied!', 'danger')
        return redirect(url_for('index'))
    
    user_id = session.get('user_id')
    cost = parking_spot_model.release_spot(spot_id, user_id)
    
    if cost:
        flash(f'Parking spot released! Total cost: ${cost:.2f}', 'success')
    else:
        flash('Error releasing parking spot!', 'danger')
    
    return redirect(url_for('user_dashboard'))

# API endpoints for charts data
@app.route('/api/admin/stats')
def api_admin_stats():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    lots = parking_lot_model.get_all_lots()
    
    # Prepare data for charts
    lot_names = [lot['prime_location_name'] for lot in lots]
    lot_occupancy = [lot['occupied_spots'] or 0 for lot in lots]
    lot_capacity = [lot['total_spots'] or 0 for lot in lots]
    
    return jsonify({
        'lot_names': lot_names,
        'lot_occupancy': lot_occupancy,
        'lot_capacity': lot_capacity
    })

@app.route('/api/user/stats')
def api_user_stats():
    if session.get('role') != 'user':
        return jsonify({'error': 'Access denied'}), 403
    
    user_id = session.get('user_id')
    reservations = reservation_model.get_user_reservations(user_id)
    
    # Calculate statistics
    total_reservations = len(reservations)
    total_cost = sum(r['parking_cost'] or 0 for r in reservations)
    active_count = len([r for r in reservations if r['status'] == 'active'])
    
    return jsonify({
        'total_reservations': total_reservations,
        'total_cost': total_cost,
        'active_reservations': active_count
    })

if __name__ == '__main__':
    app.run(debug=True)