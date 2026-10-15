import unittest
import tempfile
import shutil
import os
from decimal import Decimal
import config
from storage import init_storage
from logic.auth import seed_default_admin, login, add_user, edit_user, delete_user, list_users
from logic.customers import add_customer, edit_customer, delete_customer, search_customers
from logic.catalog import seed_sample_services, add_service, list_services
from logic.parts import add_part, add_part_to_job, remove_part_from_job, list_parts
from logic.jobs import create_job, change_status, current_status
from logic.billing import compute_bill, record_payment
from errors import ValidationError, RuleError


class TestLogic(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_data_dir = config.DATA_DIR
        self.orig_receipt_dir = config.RECEIPT_DIR
        config.DATA_DIR = os.path.join(self.temp_dir, "data")
        config.RECEIPT_DIR = os.path.join(self.temp_dir, "receipts")
        init_storage()

        # Seed admin and sample services
        seed_default_admin()
        seed_sample_services()
        self.admin = login('admin', 'admin123')

    def tearDown(self):
        config.DATA_DIR = self.orig_data_dir
        config.RECEIPT_DIR = self.orig_receipt_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_auth_login_and_roles(self):
        # Valid login
        self.assertEqual(self.admin['role'], 'Admin')

        # Invalid login
        with self.assertRaises(ValidationError):
            login('admin', 'wrongpass')

        # Add technician
        tech = add_user('tech1', 'pass123', 'Technician', 'Tech Juan', self.admin)
        self.assertEqual(tech['role'], 'Technician')

    def test_self_registration(self):
        from logic.auth import register_user
        # Register creates a user with Customer role by default
        new_u = register_user('cust_amy', 'secret123', 'secret123', 'Amy Santiago')
        self.assertEqual(new_u['role'], 'Customer')
        self.assertEqual(new_u['full_name'], 'Amy Santiago')

        # Admin panel elevates Customer to Staff or Technician
        edit_user(new_u['user_id'], 'cust_amy', None, 'Staff', 'Amy Santiago', self.admin)
        users = list_users()
        promoted = next(u for u in users if u['user_id'] == new_u['user_id'])
        self.assertEqual(promoted['role'], 'Staff')

        # Duplicate username blocked
        with self.assertRaises(ValidationError):
            register_user('cust_amy', 'otherpass', 'otherpass', 'Duplicate Amy')

        # Password mismatch blocked
        with self.assertRaises(ValidationError):
            register_user('cust_bob', 'pass1', 'pass2', 'Bob Parr')

    def test_customer_crud_and_protection(self):
        c = add_customer('Maria Santos', '0917-123-4567', 'maria@test.com', 'Makati City', self.admin)
        self.assertEqual(c['customer_id'], 'C-001')

        results = search_customers('maria')
        self.assertEqual(len(results), 1)

        # Create job referencing customer
        job_data = {
            'customer_id': 'C-001',
            'device_type': 'Laptop',
            'brand': 'Lenovo',
            'model': 'ThinkPad T480',
            'serial_no': 'SN-12345',
            'problem': 'Does not turn on',
            'priority': 'Normal'
        }
        create_job(job_data, ['Charger'], ['S-001'], self.admin)

        # Deleting customer with active/past job must be blocked (FR-09)
        with self.assertRaises(RuleError):
            delete_customer('C-001', self.admin)

    def test_state_machine_and_billing(self):
        c = add_customer('Pedro Penduko', '0922-555-1111', 'pedro@test.com', 'Quezon City', self.admin)
        job_data = {
            'customer_id': c['customer_id'],
            'device_type': 'Laptop',
            'brand': 'Dell',
            'model': 'XPS 15',
            'serial_no': 'SN-998877',
            'problem': 'Blue screen and thermal throttling',
            'priority': 'Urgent'
        }
        # S-002: OS Reinstallation (500.00), S-009: Cleaning (650.00) => 1,150.00
        jid = create_job(job_data, ['Charger', 'Sleeve'], ['S-002', 'S-009'], self.admin)
        self.assertEqual(current_status(jid), 'Received')

        # Allowed transition: Received -> Diagnosing
        change_status(jid, 'Diagnosing', self.admin)
        self.assertEqual(current_status(jid), 'Diagnosing')

        # Illegal transition: Diagnosing -> Released (must raise RuleError)
        with self.assertRaises(RuleError):
            change_status(jid, 'Released', self.admin)

        # Diagnosing -> Under Repair
        change_status(jid, 'Under Repair', self.admin)
        # Under Repair -> Completed
        change_status(jid, 'Completed', self.admin)

        # Bill check: 1150.00
        bill = compute_bill(jid)
        self.assertEqual(bill['total'], Decimal('1150.00'))
        self.assertEqual(bill['balance'], Decimal('1150.00'))

        # Marking Released before payment is blocked (FR-42)
        with self.assertRaises(RuleError):
            change_status(jid, 'Released', self.admin)

        # Partial payment: 500.00
        pay1 = record_payment(jid, '500.00', 'Cash', self.admin)
        self.assertEqual(pay1['balance'], Decimal('650.00'))

        # Still cannot release
        with self.assertRaises(RuleError):
            change_status(jid, 'Released', self.admin)

        # Final payment: 1000.00 cash tendered, balance is 650.00, change is 350.00
        pay2 = record_payment(jid, '1000.00', 'Cash', self.admin)
        self.assertEqual(pay2['applied'], Decimal('650.00'))
        self.assertEqual(pay2['change'], Decimal('350.00'))
        self.assertEqual(pay2['balance'], Decimal('0.00'))

        # Now Released succeeds
        change_status(jid, 'Released', self.admin)
        self.assertEqual(current_status(jid), 'Released')

    def test_parts_stock_and_cancellation(self):
        c = add_customer('Ana Reyes', '0918-777-8888', 'ana@test.com', 'Pasig City', self.admin)
        p = add_part('16GB DDR4 RAM', '10', '1200.00', '2', self.admin)
        pid = p['part_id']

        job_data = {
            'customer_id': c['customer_id'],
            'device_type': 'Laptop',
            'brand': 'Asus',
            'model': 'ZenBook',
            'serial_no': 'SN-ASUS-11',
            'problem': 'RAM upgrade request',
            'priority': 'Normal'
        }
        jid = create_job(job_data, [], [], self.admin)

        # Allocate 2 RAM sticks
        add_part_to_job(jid, pid, '2', self.admin)
        part_after = [x for x in list_parts() if x['part_id'] == pid][0]
        self.assertEqual(int(part_after['quantity']), 8)

        # Over-allocation fails (trying to allocate 9 when only 8 left)
        with self.assertRaises(RuleError):
            add_part_to_job(jid, pid, '9', self.admin)

        # Cancel job -> must restore parts back to stock (FR-28b)
        change_status(jid, 'Cancelled', self.admin, cancel_reason='Customer decided not to proceed')
        part_restored = [x for x in list_parts() if x['part_id'] == pid][0]
        self.assertEqual(int(part_restored['quantity']), 10)

    def test_delete_protections(self):
        # Admin cannot delete the last remaining Admin (FR-05)
        with self.assertRaises(RuleError):
            delete_user(self.admin['user_id'], self.admin)

        # Service attached to a job cannot be deleted (FR-21)
        c = add_customer('Carlo Tan', '0919-444-3333', 'carlo@test.com', 'Taguig', self.admin)
        jid = create_job({
            'customer_id': c['customer_id'],
            'device_type': 'Desktop',
            'brand': 'Custom',
            'model': 'Gaming PC',
            'serial_no': 'SN-DESK-01',
            'problem': 'Thermal paste clean',
            'priority': 'Normal'
        }, [], ['S-009'], self.admin)

        from logic.catalog import delete_service
        with self.assertRaises(RuleError):
            delete_service('S-009', self.admin)

    def test_customer_job_isolation(self):
        from logic.jobs import list_jobs
        c1 = add_customer('Kelly Laurence', '0917-111-2222', 'kelly@test.com', 'Manila', self.admin)
        c2 = add_customer('Pedro Penduko', '0918-222-3333', 'pedro@test.com', 'Cebu', self.admin)

        j1 = create_job({
            'customer_id': c1['customer_id'],
            'device_type': 'Laptop',
            'brand': 'Apple',
            'model': 'MacBook Pro',
            'serial_no': 'C02-KELLY-01',
            'problem': 'Screen flickering',
            'priority': 'Normal'
        }, [], [], self.admin)

        j2 = create_job({
            'customer_id': c2['customer_id'],
            'device_type': 'Laptop',
            'brand': 'Dell',
            'model': 'XPS 15',
            'serial_no': 'DL-PEDRO-02',
            'problem': 'Battery replacement',
            'priority': 'Urgent'
        }, [], [], self.admin)

        # Kelly only sees own jobs
        kelly_jobs = list_jobs(customer_name_filter='Kelly Laurence')
        self.assertEqual(len(kelly_jobs), 1)
        self.assertEqual(kelly_jobs[0]['job_id'], j1)

        # Pedro only sees own jobs
        pedro_jobs = list_jobs(customer_name_filter='Pedro Penduko')
        self.assertEqual(len(pedro_jobs), 1)
        self.assertEqual(pedro_jobs[0]['job_id'], j2)


if __name__ == '__main__':
    unittest.main()
