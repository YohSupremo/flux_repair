import unittest
import tempfile
import shutil
import os
import config
from storage import init_storage, insert, get_rows, update, delete, next_id


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_data_dir = config.DATA_DIR
        self.orig_backup_dir = config.BACKUP_DIR
        config.DATA_DIR = os.path.join(self.temp_dir, "data")
        config.BACKUP_DIR = os.path.join(self.temp_dir, "backups")
        init_storage()

    def tearDown(self):
        config.DATA_DIR = self.orig_data_dir
        config.BACKUP_DIR = self.orig_backup_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_files(self):
        self.assertTrue(os.path.exists(config.DATA_DIR))
        self.assertTrue(os.path.exists(os.path.join(config.DATA_DIR, "users.csv")))
        self.assertTrue(os.path.exists(os.path.join(config.DATA_DIR, "counters.csv")))

    def test_next_id_never_reused(self):
        id1 = next_id('C', 3)
        self.assertEqual(id1, 'C-001')
        id2 = next_id('C', 3)
        self.assertEqual(id2, 'C-002')

    def test_insert_and_get(self):
        row = {
            'user_id': 'U-001',
            'username': 'tester',
            'password': 'secretpassword',
            'role': 'Admin',
            'full_name': 'Test Admin'
        }
        insert('users', row)
        rows = get_rows('users')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['username'], 'tester')

    def test_update_and_delete(self):
        row = {
            'customer_id': 'C-001',
            'name': 'Juan Cruz',
            'contact_no': '09123456789',
            'email': 'juan@example.com',
            'address': 'Manila'
        }
        insert('customers', row)
        update('customers', 'customer_id', 'C-001', {'name': 'Juan Dela Cruz'})
        self.assertEqual(get_rows('customers')[0]['name'], 'Juan Dela Cruz')

        delete('customers', 'customer_id', 'C-001')
        self.assertEqual(len(get_rows('customers')), 0)


if __name__ == '__main__':
    unittest.main()
