from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange

TIME_FORMATS = ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M')


class TolerantDateTimeLocalField(DateTimeLocalField):
    """Nhận cả giá trị có giây — một số trình duyệt trả 'YYYY-MM-DDTHH:MM:SS'."""
    def process_formdata(self, valuelist):
        if not valuelist:
            return
        raw = valuelist[0].strip()
        for fmt in TIME_FORMATS:
            try:
                self.data = datetime.strptime(raw, fmt)
                return
            except ValueError:
                continue
        self.process_errors.append('Ngày giờ không đúng định dạng (hãy dùng ô chọn ngày giờ)')
        self.data = None


class EventForm(FlaskForm):
    """US-03/04A: validation máy chủ là bên quyết định; HTML5 chỉ hỗ trợ trình duyệt."""
    name = StringField('Tên sự kiện', validators=[
        DataRequired(message='Vui lòng nhập tên sự kiện'),
        Length(max=200, message='Tên sự kiện không được quá 200 ký tự'),
    ])
    description = TextAreaField('Mô tả', validators=[
        DataRequired(message='Vui lòng nhập mô tả'),
        Length(max=2000, message='Mô tả không được quá 2000 ký tự'),
    ])
    location = StringField('Địa điểm', validators=[
        DataRequired(message='Vui lòng nhập địa điểm'),
        Length(max=255, message='Địa điểm không được quá 255 ký tự'),
    ])
    start_time = TolerantDateTimeLocalField('Thời gian diễn ra', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng nhập thời gian diễn ra'),
    ])
    end_time = TolerantDateTimeLocalField('Thời gian kết thúc', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng nhập thời gian kết thúc'),
    ])
    registration_deadline = TolerantDateTimeLocalField('Thời hạn đăng ký', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng nhập thời hạn đăng ký'),
    ])
    max_attendees = IntegerField('Số lượng tối đa', validators=[
        DataRequired(message='Vui lòng nhập số lượng tối đa'),
        NumberRange(min=1, message='Số lượng tối đa phải là số nguyên từ 1 trở lên'),
    ])
    target_audience = StringField('Đối tượng tham gia', default='Toàn công ty')
    submit = SubmitField('Lưu sự kiện')

    creating = True  # khi tạo mới mới kiểm tra "sau thời điểm hiện tại" (BR11)

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False
        ok = True
        now = datetime.now()
        if self.start_time.data and self.end_time.data and self.end_time.data <= self.start_time.data:
            self.end_time.errors.append('Thời gian kết thúc phải sau thời gian diễn ra')
            ok = False
        if self.start_time.data and self.registration_deadline.data and self.registration_deadline.data > self.start_time.data:
            self.registration_deadline.errors.append('Thời hạn đăng ký phải trước hoặc bằng thời gian diễn ra')
            ok = False
        if self.creating:
            if self.start_time.data and self.start_time.data <= now:
                self.start_time.errors.append('Thời gian diễn ra phải sau thời điểm hiện tại')
                ok = False
            if self.registration_deadline.data and self.registration_deadline.data <= now:
                self.registration_deadline.errors.append('Thời hạn đăng ký phải sau thời điểm hiện tại')
                ok = False
        return ok
