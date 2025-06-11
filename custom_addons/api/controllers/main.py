from odoo import http, SUPERUSER_ID
from odoo.http import request, db_list, Response
from odoo.exceptions import ValidationError
from functools import wraps
import json
import datetime
import logging

_logger = logging.getLogger(__name__)

messages = {
    'access': {'status': 'error', 'message': 'Access Denied: Invalid or missing API Key.', 'code': 401}
}

def authenticate(func):
    @wraps(func)
    def validate_api_key(*args, **kw):
        key = request.httprequest.headers.get('api-key')
        if not key:
            _logger.warning(f"Authentication failed for {func.__name__}: 'api-key' header missing.")
            return request.make_json_response(messages['access'], status=401)
        if not request.session.db:
            dbs = db_list()
            if not dbs:
                _logger.error("No database found.")
                return request.make_json_response(messages['access'], status=500)
            request.session.db = dbs[0]
        try:
            uid = request.env['res.users.apikeys'].with_user(SUPERUSER_ID)._check_credentials(scope='rpc', key=key)
        except Exception as e:
            _logger.error(f"Error during API Key credential check for {func.__name__}: {e}", exc_info=True)
            return request.make_json_response(messages['access'], status=401)
        if not uid:
            _logger.error(f"Authentication failed for {func.__name__}: Invalid API Key provided.")
            return request.make_json_response(messages['access'], status=401)
        request.update_env(user=uid)
        _logger.info(f"API Key authentication successful for user ID: {uid} on {func.__name__}")
        return func(*args, **kw)
    return validate_api_key

class CustomAPIController(http.Controller):

    @authenticate
    @http.route('/api/v1/products', type='http', auth='public', methods=['GET'], csrf=False)
    def get_products(self, **kw):
        try:
            limit = int(kw.get('limit', 10))
            offset = int(kw.get('offset', 0))
            search_domain = []
            if kw.get('search'):
                search_domain.append(('name', 'ilike', kw['search']))
            if kw.get('sale_ok') and kw['sale_ok'].lower() == 'true':
                search_domain.append(('sale_ok', '=', True))
            products = request.env['product.template'].search_read(
                search_domain,
                ['id', 'name', 'list_price', 'qty_available', 'default_code', 'description_sale'],
                limit=limit,
                offset=offset
            )
            return request.make_json_response({'status': 'success', 'data': products})
        except Exception as e:
            _logger.error(f"Error getting products: {e}", exc_info=True)
            return request.make_json_response({'status': 'error', 'message': str(e)}, status=500)

    @authenticate
    @http.route('/api/v1/products/<int:product_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_product_by_id(self, product_id):
        try:
            product = request.env['product.template'].search_read(
                [('id', '=', product_id)],
                ['id', 'name', 'list_price', 'qty_available', 'default_code', 'description_sale', 'sale_ok']
            )
            if not product:
                return request.make_json_response({'status': 'error', 'message': 'Product not found'}, status=404)
            return request.make_json_response({'status': 'success', 'data': product[0]})
        except Exception as e:
            _logger.error(f"Error getting product by ID {product_id}: {e}", exc_info=True)
            return request.make_json_response({'status': 'error', 'message': str(e)}, status=500)

    @authenticate
    @http.route('/api/v1/products', type='json', auth='public', methods=['POST'], csrf=False)
    def create_product(self, **data):
        try:
            if not data or not data.get('name'):
                return {'status': 'error', 'message': 'Product name is required.', 'code': 400}
            product_values = {
                'name': data.get('name'),
                'list_price': float(data.get('list_price', 0.0)),
                'type': data.get('type', 'product'),
                'default_code': data.get('default_code'),
                'description_sale': data.get('description_sale'),
                'sale_ok': data.get('sale_ok', False),
            }
            new_product = request.env['product.template'].create(product_values)
            return {'status': 'success', 'id': new_product.id, 'message': 'Product created successfully.'}
        except Exception as e:
            _logger.error(f"Error creating product: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e), 'code': 500}

    @authenticate
    @http.route('/api/v1/products/<int:product_id>', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_product(self, product_id, **data):
        try:
            product = request.env['product.template'].browse(product_id)
            if not product.exists():
                return {'status': 'error', 'message': 'Product not found.', 'code': 404}
            values_to_update = {}
            if 'name' in data:
                values_to_update['name'] = data['name']
            if 'list_price' in data:
                values_to_update['list_price'] = float(data['list_price'])
            if 'default_code' in data:
                values_to_update['default_code'] = data['default_code']
            if 'description_sale' in data:
                values_to_update['description_sale'] = data['description_sale']
            if 'sale_ok' in data:
                values_to_update['sale_ok'] = bool(data['sale_ok'])
            if values_to_update:
                product.write(values_to_update)
                return {'status': 'success', 'message': 'Product updated successfully.'}
            else:
                return {'status': 'error', 'message': 'No data provided for update.', 'code': 400}
        except Exception as e:
            _logger.error(f"Error updating product {product_id}: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e), 'code': 500}

    @authenticate
    @http.route('/api/v1/products/<int:product_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    def delete_product(self, product_id):
        try:
            product = request.env['product.template'].browse(product_id)
            if not product.exists():
                return request.make_json_response({'status': 'error', 'message': 'Product not found.'}, status=404)
            product.unlink()
            return request.make_json_response({'status': 'success', 'message': 'Product deleted successfully.'})
        except Exception as e:
            _logger.error(f"Error deleting product {product_id}: {e}", exc_info=True)
            return request.make_json_response({'status': 'error', 'message': str(e)}, status=500)

    # --- HR Attendance API Endpoints ---

    @authenticate
    @http.route('/api/v1/attendances', type='json', auth='public', methods=['POST'], csrf=False)
    def create_attendance(self, **data):
        try:
            employee_id = data.get('employee_id')
            check_in_str = data.get('check_in')
            if not employee_id:
                return {'status': 'error', 'message': 'employee_id is required.', 'code': 400}
            if not check_in_str:
                return {'status': 'error', 'message': 'check_in datetime is required.', 'code': 400}
            employee = request.env['hr.employee'].browse(employee_id)
            if not employee.exists():
                return {'status': 'error', 'message': 'Employee not found.', 'code': 404}
            try:
                check_in_dt = datetime.datetime.strptime(check_in_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return {'status': 'error', 'message': 'Invalid check_in datetime format. Use YYYY-MM-DD HH:MM:SS.', 'code': 400}
            attendance_values = {
                'employee_id': employee_id,
                'check_in': check_in_dt.strftime('%Y-%m-%d %H:%M:%S'),
            }
            new_attendance = request.env['hr.attendance'].create(attendance_values)
            return {'status': 'success', 'id': new_attendance.id, 'message': 'Attendance check-in recorded successfully.'}
        except Exception as e:
            _logger.error(f"Error creating attendance record: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e), 'code': 500}

    @authenticate
    @http.route('/api/v1/attendances', type='http', auth='public', methods=['GET'], csrf=False)
    def get_attendances(self, **kw):
        try:
            search_domain = []
            if kw.get('employee_id'):
                search_domain.append(('employee_id', '=', int(kw['employee_id'])))
            if kw.get('check_out') and kw['check_out'].lower() == 'false':
                search_domain.append(('check_out', '=', False))
            attendances = request.env['hr.attendance'].search_read(
                search_domain,
                ['id', 'employee_id', 'check_in', 'check_out'],
                limit=int(kw.get('limit', 10)),
                offset=int(kw.get('offset', 0))
            )
            for att in attendances:
                if isinstance(att.get('check_in'), datetime.datetime):
                    att['check_in'] = att['check_in'].strftime('%Y-%m-%d %H:%M:%S')
                if isinstance(att.get('check_out'), datetime.datetime):
                    att['check_out'] = att['check_out'].strftime('%Y-%m-%d %H:%M:%S')
            return request.make_json_response({'status': 'success', 'data': attendances})
        except Exception as e:
            _logger.error(f"Error getting attendance records: {e}", exc_info=True)
            return request.make_json_response({'status': 'error', 'message': str(e)}, status=500)

    @authenticate
    @http.route('/api/v1/attendances/<int:attendance_id>', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_attendance(self, attendance_id, **data):
        try:
            attendance = request.env['hr.attendance'].browse(attendance_id)
            if not attendance.exists():
                return {'status': 'error', 'message': 'Attendance record not found.', 'code': 404}
            values_to_update = {}
            check_out_str = data.get('check_out')
            if check_out_str:
                try:
                    check_out_dt = datetime.datetime.strptime(check_out_str, '%Y-%m-%d %H:%M:%S')
                    values_to_update['check_out'] = check_out_dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return {'status': 'error', 'message': 'Invalid check_out datetime format. Use YYYY-MM-DD HH:MM:SS.', 'code': 400}
            if values_to_update:
                attendance.write(values_to_update)
                return {'status': 'success', 'message': 'Attendance record updated successfully.'}
            else:
                return {'status': 'error', 'message': 'No data provided for update.', 'code': 400}
        except Exception as e:
            _logger.error(f"Error updating attendance record {attendance_id}: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e), 'code': 500}

    @authenticate
    @http.route('/api/v1/employees', type='http', auth='public', methods=['GET'], csrf=False)
    def get_employees(self, **kw):
        try:
            limit = int(kw.get('limit', 10))
            offset = int(kw.get('offset', 0))
            search_domain = []
            if kw.get('search'):
                search_domain.append(('name', 'ilike', kw['search']))
            employees = request.env['hr.employee'].search_read(
                search_domain,
                ['id', 'name', 'work_email', 'work_phone', 'department_id', 'job_id'],
                limit=limit,
                offset=offset
            )
            return request.make_json_response({'status': 'success', 'data': employees})
        except Exception as e:
            _logger.error(f"Error getting employee records: {e}", exc_info=True)
            return request.make_json_response({'status': 'error', 'message': str(e)}, status=500)