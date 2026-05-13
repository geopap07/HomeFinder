"""
HomeFinder Portal - Main Application
5CM505 Software Engineering - Scenario 2 (Computer Science)
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import random
import string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'homefinder-secret-key-5CM505'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homefinder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ─── MODELS ──────────────────────────────────────────────────────────────────

class User(db.Model):
    """User model - RegisteredUser, Administrator, Supervisor"""
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    role       = db.Column(db.String(20), default='user')   # user / admin / supervisor
    twofa_token = db.Column(db.String(10), nullable=True)
    twofa_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active  = db.Column(db.Boolean, default=True)

    inquiries  = db.relationship('Inquiry', backref='user', lazy=True)
    favorites  = db.relationship('Favorite', backref='user', lazy=True)
    logs       = db.relationship('ActivityLog', backref='user', lazy=True)


class Property(db.Model):
    """Property listing model"""
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    location    = db.Column(db.String(200), nullable=False)
    price       = db.Column(db.Float, nullable=False)
    prop_type   = db.Column(db.String(20), nullable=False)   # residential / commercial / rental
    bedrooms    = db.Column(db.Integer, default=0)
    bathrooms   = db.Column(db.Integer, default=1)
    area_sqm    = db.Column(db.Integer, default=50)
    description = db.Column(db.Text, nullable=True)
    image_url   = db.Column(db.String(300), nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    admin_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    inquiries   = db.relationship('Inquiry', backref='property', lazy=True)
    favorites   = db.relationship('Favorite', backref='property', lazy=True)


class Inquiry(db.Model):
    """Inquiry submitted by user about a property"""
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    status      = db.Column(db.String(20), default='pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Favorite(db.Model):
    """Saved favorites"""
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    saved_at    = db.Column(db.DateTime, default=datetime.utcnow)


class ActivityLog(db.Model):
    """Activity log - retained for 3 months (NFR-4)"""
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action     = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    retained_until = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=90))


class Notification(db.Model):
    """Notifications sent to users"""
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    sent_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def log_activity(action, user_id=None):
    """Log user activity (NFR-4)"""
    log = ActivityLog(
        user_id=user_id or session.get('user_id'),
        action=action,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()


def generate_2fa_token():
    """Generate a 6-digit 2FA token (NFR-1: delivered within 30s)"""
    return ''.join(random.choices(string.digits, k=6))


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role not in ('admin', 'supervisor'):
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Landing page with featured properties"""
    properties = Property.query.filter_by(is_available=True).order_by(Property.created_at.desc()).limit(6).all()
    return render_template('index.html', properties=properties)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration (FR-1)"""
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        pwd   = request.form.get('password', '')
        pwd2  = request.form.get('password2', '')

        if not name or not email or not pwd:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if pwd != pwd2:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(pwd),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        log_activity(f'User registered: {email}', user.id)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login with 2FA (UC-1, NFR-1)"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pwd   = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, pwd):
            flash('Invalid email or password.', 'danger')
            log_activity(f'Failed login attempt: {email}')
            return render_template('login.html')

        # Generate 2FA token (NFR-1: within 30 seconds)
        token = generate_2fa_token()
        user.twofa_token  = token
        user.twofa_expiry = datetime.utcnow() + timedelta(seconds=30)
        db.session.commit()

        session['pending_2fa_user'] = user.id
        # In production this would be emailed; here we show it for demo
        flash(f'2FA Token (simulated email): {token}', 'info')
        log_activity(f'2FA token generated for: {email}', user.id)
        return redirect(url_for('verify_2fa'))

    return render_template('login.html')


@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """2FA token verification (NFR-1)"""
    if 'pending_2fa_user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        user  = User.query.get(session['pending_2fa_user'])

        if not user:
            return redirect(url_for('login'))

        if datetime.utcnow() > user.twofa_expiry:
            session.pop('pending_2fa_user', None)
            flash('2FA token expired. Please log in again.', 'danger')
            log_activity(f'2FA expired for user {user.email}', user.id)
            return redirect(url_for('login'))

        if token != user.twofa_token:
            flash('Invalid token. Try again.', 'danger')
            return render_template('verify_2fa.html')

        # Token valid — create session (NFR-2: single session)
        session.pop('pending_2fa_user', None)
        session['user_id']   = user.id
        session['user_name'] = user.name
        session['user_role'] = user.role

        user.twofa_token  = None
        user.twofa_expiry = None
        db.session.commit()

        log_activity('Successful login', user.id)
        flash(f'Welcome back, {user.name}!', 'success')

        if user.role in ('admin', 'supervisor'):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('properties'))

    return render_template('verify_2fa.html')


@app.route('/logout')
def logout():
    """Logout and destroy session"""
    user_id = session.get('user_id')
    log_activity('User logged out', user_id)
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ─── PROPERTY ROUTES ─────────────────────────────────────────────────────────

@app.route('/properties')
def properties():
    """Property search and filter (FR-2, FR-3 — UC-2)"""
    q         = request.args.get('q', '')
    prop_type = request.args.get('type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    bedrooms  = request.args.get('bedrooms', type=int)

    query = Property.query.filter_by(is_available=True)

    # SearchService: search by keyword
    if q:
        query = query.filter(
            db.or_(
                Property.title.ilike(f'%{q}%'),
                Property.location.ilike(f'%{q}%'),
                Property.description.ilike(f'%{q}%')
            )
        )
    # FilterService: apply filters
    if prop_type:
        query = query.filter_by(prop_type=prop_type)
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)

    results = query.order_by(Property.created_at.desc()).all()

    if 'user_id' in session:
        log_activity(f'Property search: q={q}, type={prop_type}')

    return render_template('properties.html', properties=results,
                           q=q, prop_type=prop_type,
                           min_price=min_price, max_price=max_price,
                           bedrooms=bedrooms)


@app.route('/property/<int:property_id>')
def property_detail(property_id):
    """Property detail view (UC-3)"""
    prop = Property.query.get_or_404(property_id)
    is_favorite = False
    if 'user_id' in session:
        is_favorite = Favorite.query.filter_by(
            user_id=session['user_id'],
            property_id=property_id
        ).first() is not None
        log_activity(f'Viewed property: {prop.title}')
    return render_template('property_detail.html', property=prop, is_favorite=is_favorite)


@app.route('/property/<int:property_id>/inquiry', methods=['POST'])
@login_required
def submit_inquiry(property_id):
    """Submit inquiry about a property (FR-6 — UC-6)"""
    prop    = Property.query.get_or_404(property_id)
    message = request.form.get('message', '').strip()

    if not message:
        flash('Please enter a message.', 'danger')
        return redirect(url_for('property_detail', property_id=property_id))

    inquiry = Inquiry(
        user_id=session['user_id'],
        property_id=property_id,
        message=message
    )
    db.session.add(inquiry)

    # Create notification (Observer Pattern)
    notif = Notification(
        user_id=session['user_id'],
        message=f'Your inquiry for "{prop.title}" has been received. We will contact you shortly.'
    )
    db.session.add(notif)
    db.session.commit()

    log_activity(f'Inquiry submitted for property: {prop.title}')
    flash('Inquiry submitted! Confirmation sent to your email.', 'success')
    return redirect(url_for('property_detail', property_id=property_id))


@app.route('/favorites')
@login_required
def favorites():
    """View saved favorites (FR-4 — UC-4)"""
    favs = Favorite.query.filter_by(user_id=session['user_id']).all()
    log_activity('Viewed favorites')
    return render_template('favorites.html', favorites=favs)


@app.route('/favorites/add/<int:property_id>', methods=['POST'])
@login_required
def add_favorite(property_id):
    """Save property to favorites (FR-4)"""
    existing = Favorite.query.filter_by(
        user_id=session['user_id'],
        property_id=property_id
    ).first()
    if not existing:
        fav = Favorite(user_id=session['user_id'], property_id=property_id)
        db.session.add(fav)
        db.session.commit()
        log_activity(f'Added property {property_id} to favorites')
        flash('Property saved to favorites!', 'success')
    else:
        flash('Already in favorites.', 'info')
    return redirect(url_for('property_detail', property_id=property_id))


@app.route('/favorites/remove/<int:property_id>', methods=['POST'])
@login_required
def remove_favorite(property_id):
    """Remove from favorites"""
    fav = Favorite.query.filter_by(
        user_id=session['user_id'],
        property_id=property_id
    ).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        log_activity(f'Removed property {property_id} from favorites')
        flash('Removed from favorites.', 'info')
    return redirect(url_for('favorites'))


@app.route('/notifications')
@login_required
def notifications():
    """View notifications"""
    notifs = Notification.query.filter_by(
        user_id=session['user_id']
    ).order_by(Notification.sent_at.desc()).all()
    # Mark all as read
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)


# ─── ADMIN ROUTES ─────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard (UC-4, UC-5)"""
    total_properties = Property.query.count()
    total_users      = User.query.filter_by(role='user').count()
    total_inquiries  = Inquiry.query.count()
    pending_inquiries = Inquiry.query.filter_by(status='pending').count()
    recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
    recent_logs      = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()

    log_activity('Admin dashboard accessed')
    return render_template('admin/dashboard.html',
        total_properties=total_properties,
        total_users=total_users,
        total_inquiries=total_inquiries,
        pending_inquiries=pending_inquiries,
        recent_inquiries=recent_inquiries,
        recent_logs=recent_logs
    )


@app.route('/admin/properties')
@admin_required
def admin_properties():
    """Manage property listings"""
    props = Property.query.order_by(Property.created_at.desc()).all()
    return render_template('admin/properties.html', properties=props)


@app.route('/admin/properties/add', methods=['GET', 'POST'])
@admin_required
def admin_add_property():
    """Add new listing (FR-5)"""
    if request.method == 'POST':
        prop = Property(
            title       = request.form.get('title'),
            location    = request.form.get('location'),
            price       = float(request.form.get('price', 0)),
            prop_type   = request.form.get('prop_type'),
            bedrooms    = int(request.form.get('bedrooms', 0)),
            bathrooms   = int(request.form.get('bathrooms', 1)),
            area_sqm    = int(request.form.get('area_sqm', 50)),
            description = request.form.get('description'),
            image_url   = request.form.get('image_url', ''),
            admin_id    = session['user_id']
        )
        db.session.add(prop)
        db.session.commit()

        # Observer Pattern: notify all users who have subscribed
        users = User.query.filter_by(role='user').all()
        for u in users:
            notif = Notification(
                user_id=u.id,
                message=f'New listing available: {prop.title} in {prop.location}'
            )
            db.session.add(notif)
        db.session.commit()

        log_activity(f'Admin added property: {prop.title}')
        flash('Property added successfully!', 'success')
        return redirect(url_for('admin_properties'))

    return render_template('admin/add_property.html')


@app.route('/admin/properties/edit/<int:property_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_property(property_id):
    """Edit existing listing"""
    prop = Property.query.get_or_404(property_id)
    if request.method == 'POST':
        prop.title       = request.form.get('title')
        prop.location    = request.form.get('location')
        prop.price       = float(request.form.get('price', 0))
        prop.prop_type   = request.form.get('prop_type')
        prop.bedrooms    = int(request.form.get('bedrooms', 0))
        prop.bathrooms   = int(request.form.get('bathrooms', 1))
        prop.area_sqm    = int(request.form.get('area_sqm', 50))
        prop.description = request.form.get('description')
        prop.image_url   = request.form.get('image_url', '')
        prop.is_available = 'is_available' in request.form
        db.session.commit()
        log_activity(f'Admin edited property: {prop.title}')
        flash('Property updated!', 'success')
        return redirect(url_for('admin_properties'))

    return render_template('admin/edit_property.html', property=prop)


@app.route('/admin/properties/delete/<int:property_id>', methods=['POST'])
@admin_required
def admin_delete_property(property_id):
    """Delete property listing"""
    prop = Property.query.get_or_404(property_id)
    name = prop.title
    # Delete related records first
    Inquiry.query.filter_by(property_id=property_id).delete()
    Favorite.query.filter_by(property_id=property_id).delete()
    db.session.delete(prop)
    db.session.commit()
    log_activity(f'Admin deleted property: {name}')
    flash('Property deleted.', 'warning')
    return redirect(url_for('admin_properties'))


@app.route('/admin/inquiries')
@admin_required
def admin_inquiries():
    """View all inquiries"""
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin/inquiries.html', inquiries=inquiries)


@app.route('/admin/inquiries/resolve/<int:inquiry_id>', methods=['POST'])
@admin_required
def resolve_inquiry(inquiry_id):
    """Mark inquiry as resolved"""
    inq = Inquiry.query.get_or_404(inquiry_id)
    inq.status = 'resolved'
    db.session.commit()
    flash('Inquiry marked as resolved.', 'success')
    return redirect(url_for('admin_inquiries'))


@app.route('/admin/reports')
@admin_required
def admin_reports():
    """Monthly reports for Supervisor (UC-5)"""
    from sqlalchemy import func

    # Inquiries per month
    monthly_inquiries = db.session.query(
        func.strftime('%Y-%m', Inquiry.created_at).label('month'),
        func.count(Inquiry.id).label('count')
    ).group_by('month').order_by('month').all()

    # Properties by type
    by_type = db.session.query(
        Property.prop_type,
        func.count(Property.id)
    ).group_by(Property.prop_type).all()

    # User registrations
    total_users = User.query.filter_by(role='user').count()
    total_favs  = Favorite.query.count()

    log_activity('Admin viewed reports')
    return render_template('admin/reports.html',
        monthly_inquiries=monthly_inquiries,
        by_type=by_type,
        total_users=total_users,
        total_favs=total_favs
    )


@app.route('/admin/users')
@admin_required
def admin_users():
    """View all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


# ─── API ENDPOINTS ────────────────────────────────────────────────────────────

@app.route('/api/notifications/count')
@login_required
def notification_count():
    """Get unread notification count (for navbar badge)"""
    count = Notification.query.filter_by(
        user_id=session['user_id'],
        is_read=False
    ).count()
    return jsonify({'count': count})


# ─── DATABASE SEED ────────────────────────────────────────────────────────────

def seed_database():
    """Seed database with sample data"""
    if User.query.first():
        return

    # Create admin user
    admin = User(
        name='Admin User',
        email='admin@homefinder.com',
        password=generate_password_hash('Admin123!'),
        role='admin'
    )
    supervisor = User(
        name='Supervisor User',
        email='supervisor@homefinder.com',
        password=generate_password_hash('Super123!'),
        role='supervisor'
    )
    test_user = User(
        name='John Smith',
        email='user@homefinder.com',
        password=generate_password_hash('User123!'),
        role='user'
    )
    db.session.add_all([admin, supervisor, test_user])
    db.session.commit()

    # Sample properties
    images = [
        'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800',
        'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800',
        'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800',
        'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800',
        'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800',
        'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800',
        'https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800',
        'https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=800',
        'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800',
    ]

    properties_data = [
        ('Luxury Villa with Pool', 'Kifisia, Athens', 850000, 'residential', 5, 4, 320, 'Stunning 5-bedroom villa with private pool and landscaped garden in the prestigious Kifisia area.'),
        ('Modern 3-Bed Apartment', 'Kolonaki, Athens', 320000, 'residential', 3, 2, 120, 'Beautifully renovated apartment in the heart of Kolonaki with panoramic city views.'),
        ('Studio Apartment', 'Glyfada, Athens', 750, 'rental', 0, 1, 35, 'Cosy studio apartment steps from the beach. Fully furnished with modern amenities.'),
        ('Commercial Office Space', 'Piraeus', 450000, 'commercial', 0, 2, 200, 'Prime office space in central Piraeus. Open plan with meeting rooms and reception area.'),
        ('2-Bed Sea View Apartment', 'Voula, Athens', 280000, 'residential', 2, 1, 85, 'Bright apartment with stunning sea views, minutes from the beach.'),
        ('Penthouse Suite', 'Psychiko, Athens', 1200000, 'residential', 4, 3, 280, 'Exceptional penthouse with rooftop terrace and 360-degree city views in exclusive Psychiko.'),
        ('Retail Shop Unit', 'Syntagma, Athens', 3500, 'rental', 0, 1, 80, 'Prime retail unit in the busiest commercial street in Athens. High footfall guaranteed.'),
        ('Family Home with Garden', 'Halandri, Athens', 420000, 'residential', 4, 2, 180, 'Spacious family home with large garden in quiet Halandri suburb, near schools.'),
        ('Investment Apartment', 'Thessaloniki', 95000, 'residential', 2, 1, 65, 'Ideal investment property in central Thessaloniki with existing rental income.'),
        ('Warehouse / Industrial', 'Aspropyrgos', 380000, 'commercial', 0, 2, 600, 'Large warehouse with loading docks and office space. Easy motorway access.'),
        ('Holiday Cottage', 'Aegina Island', 185000, 'residential', 2, 1, 75, 'Charming stone cottage on Aegina island, perfect holiday retreat.'),
        ('New Build Apartment', 'Maroussi, Athens', 195000, 'residential', 2, 1, 78, 'Brand new apartment in a modern complex with parking and communal garden.'),
    ]

    for i, (title, location, price, ptype, beds, baths, area, desc) in enumerate(properties_data):
        p = Property(
            title=title, location=location, price=price,
            prop_type=ptype, bedrooms=beds, bathrooms=baths,
            area_sqm=area, description=desc,
            image_url=images[i % len(images)],
            admin_id=admin.id
        )
        db.session.add(p)

    db.session.commit()
    print("✅ Database seeded successfully!")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True, port=5000)
