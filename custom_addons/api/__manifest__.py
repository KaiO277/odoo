{
    'name': 'My Custom REST API',
    'version': '1.0',
    'category': 'Technical',
    'summary': 'Custom REST API for Odoo 18',
    'description': """
        This module provides custom REST API endpoints for external applications
        to interact with Odoo data.
    """,
    'author': 'Nghia',
    'website': 'https://www.test.com',
    'depends': ['base', 'product',  'hr_attendance'], # Đảm bảo thêm 'product' nếu bạn muốn thao tác với sản phẩm
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}