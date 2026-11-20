"""Dữ liệu mẫu: 4 phòng ban, 3 tài khoản (A/B/C), 6 sự kiện đủ 6 trạng thái."""
from datetime import datetime, timedelta

from sqlalchemy import text

from app import create_app
from app.extensions import db
from app.models import Department, Event, Notification, Registration, User, UserRole


def seed():
    app = create_app()
    with app.app_context():
        # Xóa dữ liệu cũ và reset AUTO_INCREMENT để id demo luôn bắt đầu từ 1
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
        for model in (Notification, Registration, Event, UserRole, User, Department):
            db.session.execute(text(f'TRUNCATE TABLE {model.__tablename__}'))
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
        db.session.commit()

        depts = {}
        for name in ('HR', 'IT', 'Công đoàn', 'Truyền thông'):
            depts[name] = Department(name=name, is_active=True)
        db.session.add_all(depts.values())
        db.session.flush()

        a = User(email='a@xyz.com', full_name='Nguyễn Văn A', department_id=depts['IT'].id)
        a.set_password('123456')
        b = User(email='b@xyz.com', full_name='Trần Văn B', department_id=depts['HR'].id)
        b.set_password('123456')
        c = User(email='c@xyz.com', full_name='Lê Văn C', department_id=depts['Truyền thông'].id)
        c.set_password('123456')
        db.session.add_all([a, b, c])
        db.session.flush()

        db.session.add_all([
            UserRole(user_id=a.id, role='Employee'), UserRole(user_id=a.id, role='Organizer'),
            UserRole(user_id=b.id, role='Employee'),
            UserRole(user_id=c.id, role='Organizer'), UserRole(user_id=c.id, role='Admin'),
        ])
        db.session.flush()

        now = datetime.now()
        def ev(name, desc, start, end, max_att, deadline, org, dept, cancelled=False):
            return Event(name=name, description=desc, start_time=start, end_time=end,
                         location='Phòng họp tầng 3, trụ sở XYZ', max_attendees=max_att,
                         registration_deadline=deadline, target_audience='Toàn công ty',
                         organizer_id=org.id, department_id=dept.id, is_cancelled=cancelled)

        events = [
            # 1. Đang mở đăng ký
            ev('Hội thảo An toàn thông tin 2026', 'Chia sẻ về các mối đe dọa và thực hành an toàn thông tin cho toàn bộ nhân viên.',
               now + timedelta(days=7), now + timedelta(days=7, hours=3), 50, now + timedelta(days=5), c, depts['IT']),
            # 2. Đã đủ số lượng (max=2, sẽ seed 2 đăng ký còn hiệu lực)
            ev('Workshop Kỹ năng thuyết trình', 'Khóa thực hành kỹ năng thuyết trình trước đám đông, lớp nhỏ.',
               now + timedelta(days=3), now + timedelta(days=3, hours=2), 2, now + timedelta(days=2), a, depts['HR']),
            # 3. Hết hạn đăng ký
            ev('Đào tạo quy trình ISO mới', 'Phổ biến quy trình ISO 9001:2026 áp dụng từ quý sau.',
               now + timedelta(days=2), now + timedelta(days=2, hours=2), 100, now - timedelta(hours=2), c, depts['Truyền thông']),
            # 4. Đang diễn ra
            ev('Team building Công đoàn quý IV', 'Hoạt động gắn kết nhân viên do Công đoàn tổ chức.',
               now - timedelta(minutes=30), now + timedelta(hours=2, minutes=30), 80, now - timedelta(days=1), a, depts['Công đoàn']),
            # 5. Đã kết thúc
            ev('Tổng kết hoạt động tháng 10', 'Báo cáo kết quả hoạt động và định hướng tháng 11.',
               now - timedelta(days=2, hours=2), now - timedelta(days=2), 60, now - timedelta(days=3), c, depts['Truyền thông']),
            # 6. Đã hủy
            ev('Dã ngoại cuối năm', 'Chuyến dã ngoại 2 ngày tại Đà Lạt (đã hủy vì lịch công tác).',
               now + timedelta(days=10), now + timedelta(days=12), 40, now + timedelta(days=8), a, depts['Công đoàn'], cancelled=True),
        ]
        db.session.add_all(events)
        db.session.flush()

        # Đăng ký mẫu: workshop đủ chỗ (BR02 demo) + 1 đăng ký của B cho hội thảo + lịch sử hủy (BR01 demo)
        regs = [
            Registration(event_id=events[1].id, user_id=b.id, status='Confirmed'),
            Registration(event_id=events[1].id, user_id=c.id, status='Confirmed'),
            Registration(event_id=events[0].id, user_id=b.id, status='Registered'),
            Registration(event_id=events[3].id, user_id=a.id, status='Attended'),
            Registration(event_id=events[3].id, user_id=b.id, status='Confirmed'),
            Registration(event_id=events[4].id, user_id=c.id, status='Attended'),
            Registration(event_id=events[4].id, user_id=b.id, status='Cancelled'),  # BR01: được đăng ký lại
        ]
        for reg in regs:
            reg.set_active()
        db.session.add_all(regs)
        db.session.commit()

        print('Seed xong: 4 phòng ban, 3 tài khoản, 6 sự kiện, 7 đăng ký.')
        print('  a@xyz.com / 123456  → Employee + Organizer (Nguyễn Văn A)')
        print('  b@xyz.com / 123456  → Employee            (Trần Văn B)')
        print('  c@xyz.com / 123456  → Organizer + Admin   (Lê Văn C)')


if __name__ == '__main__':
    seed()
