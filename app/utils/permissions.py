def can_manage(user, event):
    """BR15: Organizer chỉ quản lý sự kiện mình tạo hoặc của phòng ban mình; Admin toàn quyền (BR28)."""
    if user.has_role('Admin'):
        return True
    if not user.has_role('Organizer'):
        return False
    return event.organizer_id == user.id or event.department_id == user.department_id
