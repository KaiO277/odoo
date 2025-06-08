{
    "name": "Attendance Location Log",
    "version": "1.0",
    "summary": "Hiển thị danh sách vị trí chấm công từ GPS",
    "description": "Module hiển thị vị trí chấm công dựa trên GPS và liên kết với chấm công trong Odoo.",
    "author": "Nghia",
    "website": "https://yourcompany.com",  # thêm dòng này để tránh cảnh báo
    "category": "Human Resources",
    "license": "LGPL-3",  # QUAN TRỌNG: giúp loại bỏ cảnh báo trong log
    "depends": ["hr_attendance"],
    "data": [
        "views/attendance_location_views.xml",
    ],
    "installable": True,
    "application": False,
}
