"""
Database initialization and migration logic for FixLink.
Provides a central location for custom table/column checks and initial data setup.
"""
import os
import logging
from . import db

logger = logging.getLogger(__name__)

def init_db(app):
    """
    Perform database initialization tasks:
    1. Create all tables.
    2. Handle custom "migrations" (column checks for existing DBs).
    3. Create default admin user if configured.
    """
    with app.app_context():
        # 1. Create all tables
        db.create_all()
        
        # 2. Custom Migrations
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        
        # --- Ticket Table Migrations ---
        if 'tickets' in inspector.get_table_names():
            ticket_columns = [col['name'] for col in inspector.get_columns('tickets')]
            
            # Simple column migrations for SQLite (using raw SQL for compatibility)
            migrations = [
                ('reporter_id', 'INTEGER REFERENCES users(id)'),
                ('assigned_professional_id', 'INTEGER REFERENCES professionals(id)'),
                ('complexity', 'VARCHAR(20)'),
                ('time_limit_hours', 'INTEGER'),
                ('deadline_datetime', 'DATETIME'),
                ('job_started_at', 'DATETIME'),
                ('job_completed_at', 'DATETIME'),
                ('completion_photo_filename', 'VARCHAR(255)'),
                ('cancellation_reason', 'TEXT'),
                ('cancelled_at', 'DATETIME'),
                ('cancelled_by_professional_id', 'INTEGER REFERENCES professionals(id)')
            ]
            
            for col_name, col_type in migrations:
                if col_name not in ticket_columns:
                    db.session.execute(db.text(
                        f'ALTER TABLE tickets ADD COLUMN {col_name} {col_type}'
                    ))
                    db.session.commit()
                    logger.info(f"Migration: Added column '{col_name}' to 'tickets' table.")

        # --- User Table Migrations ---
        if 'users' in inspector.get_table_names():
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            if 'profile_photo' not in user_columns:
                db.session.execute(db.text(
                    'ALTER TABLE users ADD COLUMN profile_photo VARCHAR(255)'
                ))
                db.session.commit()
                logger.info("Migration: Added column 'profile_photo' to 'users' table.")
        
        # --- Professional Table Migrations ---
        if 'professionals' in inspector.get_table_names():
            prof_columns = [col['name'] for col in inspector.get_columns('professionals')]
            if 'username' not in prof_columns:
                db.session.execute(db.text(
                    'ALTER TABLE professionals ADD COLUMN username VARCHAR(50)'
                ))
                db.session.commit()
                logger.info("Migration: Added column 'username' to 'professionals' table.")

        # 3. Create default admin user from environment variables
        from .models import User
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if admin_email and admin_password:
            if not User.query.filter_by(email=admin_email).first():
                admin_user = User(
                    name='Admin',
                    email=admin_email,
                    is_admin=True,
                    is_verified=True
                )
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                logger.info(f'Default admin user created: {admin_email}')
        elif not admin_email or not admin_password:
             logger.warning('ADMIN_EMAIL or ADMIN_PASSWORD not set. Skipping default admin creation.')
