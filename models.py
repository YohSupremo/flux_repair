TABLES = {
    'users': ['user_id', 'username', 'password', 'role', 'full_name'],
    'customers': ['customer_id', 'name', 'contact_no', 'email', 'address'],
    'services': ['service_id', 'name', 'description', 'price'],
    'parts': ['part_id', 'name', 'quantity', 'unit_price', 'low_stock_threshold'],
    'jobs': [
        'job_id', 'customer_id', 'technician_id', 'received_by', 'device_type',
        'brand', 'model', 'serial_no', 'problem', 'device_condition', 'priority',
        'date_received', 'est_completion', 'diagnosis', 'notes', 'cancel_reason'
    ],
    'job_accessories': ['job_id', 'accessory'],
    'job_services': ['job_id', 'service_id', 'price'],
    'job_parts': ['job_id', 'part_id', 'quantity_used', 'unit_price'],
    'payments': ['payment_id', 'job_id', 'amount', 'method', 'payment_date', 'received_by'],
    'status_log': ['log_id', 'job_id', 'status', 'changed_at', 'changed_by'],
}

ROLES = ('Admin', 'Staff', 'Technician', 'Customer')
DEVICE_TYPES = ('Laptop', 'Desktop', 'All-in-One')
PRIORITIES = ('Normal', 'Urgent')
PAYMENT_METHODS = ('Cash', 'GCash', 'Card')
STATUSES = (
    'Received', 'Diagnosing', 'Waiting for Parts', 'Under Repair',
    'Completed', 'Released', 'Cancelled'
)

# Enforces FR-28a: Strict allowed status transitions
TRANSITIONS = {
    'Received': ['Diagnosing', 'Cancelled'],
    'Diagnosing': ['Waiting for Parts', 'Under Repair', 'Completed', 'Cancelled'],
    'Waiting for Parts': ['Under Repair', 'Cancelled'],
    'Under Repair': ['Waiting for Parts', 'Completed', 'Cancelled'],
    'Completed': ['Released', 'Cancelled'],
    'Released': [],
    'Cancelled': [],
}

ID_PREFIXES = {
    'users': ('U', 3),
    'customers': ('C', 3),
    'services': ('S', 3),
    'parts': ('P', 3),
    'jobs': ('J', 4),
    'payments': ('PAY', 4),
    'status_log': ('L', 5)
}
