"""Background services for automated tasks."""

import schedule
import time
import threading
from backend import create_app
from backend.models import db, Batch, Inventory, Alert
from datetime import datetime, date, timedelta
from sqlalchemy import and_


class BackgroundServices:
    """Manage background services for the SCMS."""
    
    def __init__(self):
        self.app = create_app()
        self.running = False
        self.thread = None
    
    def start(self):
        """Start background services."""
        if self.running:
            return
        
        self.running = True
        
        # Schedule tasks
        schedule.every(1).hours.do(self.check_expiration_alerts)
        schedule.every(2).hours.do(self.check_low_stock_alerts)
        schedule.every().day.at("09:00").do(self.daily_cleanup)
        
        # Start scheduler thread
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        
        print("Background services started")
    
    def stop(self):
        """Stop background services."""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Background services stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread."""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def check_expiration_alerts(self):
        """Check for products expiring soon and create alerts."""
        with self.app.app_context():
            try:
                # Get batches expiring in the next 7 days
                alert_threshold = date.today() + timedelta(days=7)
                expiring_batches = Batch.query.filter(
                    Batch.expiration_date <= alert_threshold,
                    Batch.status == 'In Stock',
                    Batch.current_quantity > 0
                ).all()
                
                alerts_created = 0
                for batch in expiring_batches:
                    # Check if alert already exists
                    existing_alert = Alert.query.filter_by(
                        alert_type='Expiration',
                        target_id=batch.batch_id,
                        target_table='Batches',
                        status='New'
                    ).first()
                    
                    if not existing_alert:
                        days_until_expiry = (batch.expiration_date - date.today()).days
                        
                        alert = Alert(
                            alert_type='Expiration',
                            target_id=batch.batch_id,
                            target_table='Batches',
                            message=f'Batch {batch.manufacturer_batch_number} of {batch.product.product_name} expires in {days_until_expiry} days',
                            status='New'
                        )
                        db.session.add(alert)
                        alerts_created += 1
                
                db.session.commit()
                
                if alerts_created > 0:
                    print(f"Created {alerts_created} expiration alerts")
                    
            except Exception as e:
                print(f"Error checking expiration alerts: {e}")
                db.session.rollback()
    
    def check_low_stock_alerts(self):
        """Check for low stock items and create alerts."""
        with self.app.app_context():
            try:
                # Get inventory items below reorder point
                low_stock_items = Inventory.query.filter(
                    and_(
                        Inventory.reorder_point.isnot(None),
                        Inventory.quantity_on_hand <= Inventory.reorder_point
                    )
                ).all()
                
                alerts_created = 0
                for inventory in low_stock_items:
                    # Check if alert already exists
                    existing_alert = Alert.query.filter_by(
                        alert_type='Low Stock',
                        target_id=inventory.inventory_id,
                        target_table='Inventory',
                        status='New'
                    ).first()
                    
                    if not existing_alert:
                        alert = Alert(
                            alert_type='Low Stock',
                            target_id=inventory.inventory_id,
                            target_table='Inventory',
                            message=f'Low stock: {inventory.batch.product.product_name} at {inventory.location} - {inventory.quantity_on_hand} units remaining (reorder at {inventory.reorder_point})',
                            threshold_value=inventory.reorder_point,
                            status='New'
                        )
                        db.session.add(alert)
                        alerts_created += 1
                
                db.session.commit()
                
                if alerts_created > 0:
                    print(f"Created {alerts_created} low stock alerts")
                    
            except Exception as e:
                print(f"Error checking low stock alerts: {e}")
                db.session.rollback()
    
    def daily_cleanup(self):
        """Perform daily cleanup tasks."""
        with self.app.app_context():
            try:
                # Mark old alerts as resolved
                old_date = datetime.utcnow() - timedelta(days=30)
                old_alerts = Alert.query.filter(
                    Alert.created_at < old_date,
                    Alert.status == 'New'
                ).all()
                
                for alert in old_alerts:
                    alert.status = 'Resolved'
                    alert.resolved_at = datetime.utcnow()
                
                # Update batch statuses for expired items
                expired_batches = Batch.query.filter(
                    Batch.expiration_date < date.today(),
                    Batch.status == 'In Stock'
                ).all()
                
                for batch in expired_batches:
                    batch.status = 'Expired'
                
                db.session.commit()
                
                if old_alerts or expired_batches:
                    print(f"Daily cleanup: {len(old_alerts)} alerts resolved, {len(expired_batches)} batches marked expired")
                    
            except Exception as e:
                print(f"Error in daily cleanup: {e}")
                db.session.rollback()


# Global instance
background_services = BackgroundServices()


def start_background_services():
    """Start background services."""
    background_services.start()


def stop_background_services():
    """Stop background services."""
    background_services.stop()


if __name__ == "__main__":
    # Run background services standalone
    start_background_services()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_background_services()