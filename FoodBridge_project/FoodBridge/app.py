from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'foodbridge-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodbridge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20), nullable=False)  # 'donor', 'charity', 'admin'
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    pickup_location = db.Column(db.String(200), nullable=False)
    pickup_address = db.Column(db.String(200), nullable=False)
    pickup_city = db.Column(db.String(50), nullable=False)
    pickup_state = db.Column(db.String(50), nullable=False)
    pickup_zip = db.Column(db.String(10), nullable=False)
    available_from = db.Column(db.DateTime, nullable=False)
    available_until = db.Column(db.DateTime, nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    contact_email = db.Column(db.String(120))
    status = db.Column(db.String(20), default='available')  # 'available', 'claimed', 'completed'
    claimed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    claimed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    donor = db.relationship('User', foreign_keys=[donor_id], backref='donations')
    claimer = db.relationship('User', foreign_keys=[claimed_by])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    donation_id = db.Column(db.Integer, db.ForeignKey('donation.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')
    donation = db.relationship('Donation')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        name = request.form['name']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        zip_code = request.form.get('zip_code', '')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            user_type=user_type,
            name=name,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            is_verified=(user_type == 'donor')  # Auto-verify donors, charities need admin approval
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        if user_type == 'charity':
            flash('Your charity account will need admin approval before you can access donations.')
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_verified and user.user_type == 'charity':
                flash('Your charity account is pending admin approval.')
                return redirect(url_for('login'))
            
            login_user(user)
            
            # Redirect based on user type
            if user.user_type == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.user_type == 'charity':
                return redirect(url_for('charity_dashboard'))
            else:  # donor
                return redirect(url_for('donor_dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/donor/dashboard')
@login_required
def donor_dashboard():
    if current_user.user_type != 'donor':
        flash('Access denied')
        return redirect(url_for('index'))
    
    donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    return render_template('donor_dashboard.html', donations=donations)

@app.route('/donor/post', methods=['GET', 'POST'])
@login_required
def post_donation():
    if current_user.user_type != 'donor':
        flash('Access denied')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        donation = Donation(
            donor_id=current_user.id,
            food_type=request.form['food_type'],
            quantity=request.form['quantity'],
            description=request.form.get('description', ''),
            pickup_location=request.form['pickup_location'],
            pickup_address=request.form['pickup_address'],
            pickup_city=request.form['pickup_city'],
            pickup_state=request.form['pickup_state'],
            pickup_zip=request.form['pickup_zip'],
            available_from=datetime.strptime(request.form['available_from'], '%Y-%m-%dT%H:%M'),
            available_until=datetime.strptime(request.form['available_until'], '%Y-%m-%dT%H:%M'),
            contact_name=request.form['contact_name'],
            contact_phone=request.form['contact_phone'],
            contact_email=request.form.get('contact_email', '')
        )
        
        db.session.add(donation)
        db.session.commit()
        
        # Notify nearby charities
        notify_charities_about_donation(donation)
        
        flash('Donation posted successfully!')
        return redirect(url_for('donor_dashboard'))
    
    return render_template('post_donation.html')

@app.route('/charity/dashboard')
@login_required
def charity_dashboard():
    if current_user.user_type != 'charity':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Get available donations (basic location matching by city for MVP)
    available_donations = Donation.query.filter(
        Donation.status == 'available',
        Donation.pickup_city == current_user.city,
        Donation.available_until > datetime.utcnow()
    ).order_by(Donation.created_at.desc()).all()
    
    # Get donations claimed by this charity
    claimed_donations = Donation.query.filter_by(
        claimed_by=current_user.id
    ).order_by(Donation.claimed_at.desc()).all()
    
    return render_template('charity_dashboard.html', 
                         available_donations=available_donations,
                         claimed_donations=claimed_donations)

@app.route('/charity/claim/<int:donation_id>')
@login_required
def claim_donation(donation_id):
    if current_user.user_type != 'charity':
        flash('Access denied')
        return redirect(url_for('index'))
    
    donation = Donation.query.get_or_404(donation_id)
    
    if donation.status != 'available':
        flash('This donation is no longer available')
        return redirect(url_for('charity_dashboard'))
    
    donation.status = 'claimed'
    donation.claimed_by = current_user.id
    donation.claimed_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Donation claimed successfully! Please contact the donor for pickup arrangements.')
    return redirect(url_for('charity_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    pending_charities = User.query.filter_by(user_type='charity', is_verified=False).all()
    all_donations = Donation.query.order_by(Donation.created_at.desc()).limit(20).all()
    
    stats = {
        'total_donors': User.query.filter_by(user_type='donor').count(),
        'total_charities': User.query.filter_by(user_type='charity', is_verified=True).count(),
        'pending_charities': len(pending_charities),
        'active_donations': Donation.query.filter_by(status='available').count(),
        'completed_donations': Donation.query.filter_by(status='completed').count()
    }
    
    return render_template('admin_dashboard.html', 
                         pending_charities=pending_charities,
                         donations=all_donations,
                         stats=stats)

@app.route('/admin/verify_charity/<int:user_id>')
@login_required
def verify_charity(user_id):
    if current_user.user_type != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    
    flash(f'Charity {user.name} has been verified')
    return redirect(url_for('admin_dashboard'))

def notify_charities_about_donation(donation):
    """Send notifications to charities in the same city about new donation"""
    charities = User.query.filter(
        User.user_type == 'charity',
        User.is_verified == True,
        User.city == donation.pickup_city
    ).all()
    
    for charity in charities:
        notification = Notification(
            user_id=charity.id,
            donation_id=donation.id,
            message=f'New {donation.food_type} donation available in {donation.pickup_city}. Quantity: {donation.quantity}'
        )
        db.session.add(notification)
    
    db.session.commit()

def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@foodbridge.com',
                user_type='admin',
                name='System Administrator',
                is_verified=True
            )
            admin.set_password('admin123')  # Change this in production
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username='admin', password='admin123'")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)