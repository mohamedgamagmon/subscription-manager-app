"""
تطبيق إدارة اشتراكات العملاء - نسخة أندرويد
باستخدام Kivy Framework
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from datetime import datetime, timedelta
import sqlite3
import os

# تعيين ألوان الخلفية
Window.clearcolor = get_color_from_hex('#1a1a2e')


class DatePicker(BoxLayout):
    """مكون اختيار التاريخ"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(5)
        self.size_hint_y = None
        self.height = dp(50)
        
        # اليوم
        self.day = Spinner(
            text='01',
            values=[str(i).zfill(2) for i in range(1, 32)],
            size_hint_x=0.3,
            background_color=get_color_from_hex('#16213e'),
            color=(1, 1, 1, 1)
        )
        
        # الشهر
        self.month = Spinner(
            text='01',
            values=[str(i).zfill(2) for i in range(1, 13)],
            size_hint_x=0.3,
            background_color=get_color_from_hex('#16213e'),
            color=(1, 1, 1, 1)
        )
        
        # السنة
        current_year = datetime.now().year
        self.year = Spinner(
            text=str(current_year),
            values=[str(i) for i in range(current_year - 1, current_year + 3)],
            size_hint_x=0.4,
            background_color=get_color_from_hex('#16213e'),
            color=(1, 1, 1, 1)
        )
        
        self.add_widget(self.year)
        self.add_widget(self.month)
        self.add_widget(self.day)
    
    def get_date(self):
        """الحصول على التاريخ المحدد"""
        try:
            return datetime(int(self.year.text), int(self.month.text), int(self.day.text))
        except ValueError:
            return datetime.now()
    
    def set_date(self, date_obj):
        """تعيين التاريخ"""
        self.year.text = str(date_obj.year)
        self.month.text = str(date_obj.month).zfill(2)
        self.day.text = str(date_obj.day).zfill(2)


class CustomerRow(BoxLayout):
    """صف العميل في القائمة"""
    def __init__(self, customer_data, on_click, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(100)
        self.spacing = dp(2)
        self.customer_data = customer_data
        self.on_click = on_click
        
        # تحديد اللون حسب الحالة
        status = customer_data['status']
        if status == 'expired':
            bg_color = get_color_from_hex('#b71c1c')
        elif status == 'warning':
            bg_color = get_color_from_hex('#f57f17')
        else:
            bg_color = get_color_from_hex('#1b5e20')
        
        # زر العميل
        btn = Button(
            background_color=bg_color,
            background_normal='',
            on_press=lambda x: self.on_click(customer_data)
        )
        
        # محتوى البطاقة
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        # الاسم
        name_label = Label(
            text=customer_data['name'],
            font_size=dp(18),
            bold=True,
            halign='right',
            valign='middle',
            color=(1, 1, 1, 1)
        )
        name_label.bind(size=name_label.setter('text_size'))
        
        # المعلومات
        info_text = f"الباقة: {customer_data['package']} | المبلغ: {customer_data['amount']} ج.م"
        info_label = Label(
            text=info_text,
            font_size=dp(14),
            halign='right',
            valign='middle',
            color=(0.9, 0.9, 0.9, 1)
        )
        info_label.bind(size=info_label.setter('text_size'))
        
        # تاريخ الانتهاء والحالة
        status_text = f"ينتهي في: {customer_data['end_date']} | {customer_data['status_text']}"
        status_label = Label(
            text=status_text,
            font_size=dp(12),
            halign='right',
            valign='middle',
            color=(1, 1, 1, 1)
        )
        status_label.bind(size=status_label.setter('text_size'))
        
        content.add_widget(name_label)
        content.add_widget(info_label)
        content.add_widget(status_label)
        
        btn.add_widget(content)
        self.add_widget(btn)


class SubscriptionManagerApp(App):
    """تطبيق إدارة الاشتراكات"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.packages = {
            "باقة 100 جنيه شهرياً": {"price": 100, "months": 1},
            "باقة 150 جنيه شهرياً": {"price": 150, "months": 1},
            "باقة 75 جنيه شهرياً": {"price": 75, "months": 1},
            "باقة 100 جنيه - 3 شهور": {"price": 100, "months": 3},
            "باقة  جنيه - 6 شهور": {"price": 0, "months": 6},
            "باقة  جنيه - سنة": {"price": 0, "months": 12},
            "أخرى": {"price": 0, "months": 0}
        }
        self.selected_customer = None
        self.setup_database()
    
    def setup_database(self):
        """إنشاء قاعدة البيانات"""
        self.conn = sqlite3.connect('subscriptions.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                package TEXT NOT NULL,
                amount REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                notification_days INTEGER DEFAULT 5,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def build(self):
        """بناء الواجهة"""
        self.title = 'إدارة اشتراكات العملاء'
        
        # التخطيط الرئيسي
        main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # شريط العنوان
        header = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            padding=dp(10)
        )
        header_bg = Button(
            background_color=get_color_from_hex('#16213e'),
            background_normal='',
            disabled=True
        )
        title_label = Label(
            text='إدارة اشتراكات العملاء',
            font_size=dp(24),
            bold=True,
            color=get_color_from_hex('#00d9ff')
        )
        header_bg.add_widget(title_label)
        header.add_widget(header_bg)
        main_layout.add_widget(header)
        
        # قسم المحتوى
        content_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        
        # قائمة العملاء (يسار)
        self.customers_list = self.create_customers_list()
        content_layout.add_widget(self.customers_list)
        
        # نموذج الإدخال (يمين)
        form_scroll = ScrollView(size_hint_x=0.5)
        self.form_layout = self.create_form()
        form_scroll.add_widget(self.form_layout)
        content_layout.add_widget(form_scroll)
        
        main_layout.add_widget(content_layout)
        
        # تحميل البيانات
        self.load_customers()
        
        # فحص التنبيهات
        self.check_notifications()
        
        return main_layout
    
    def create_customers_list(self):
        """إنشاء قائمة العملاء"""
        list_layout = BoxLayout(orientation='vertical', size_hint_x=0.5)
        
        # شريط البحث
        search_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        
        search_label = Label(
            text='بحث:',
            size_hint_x=0.2,
            color=(1, 1, 1, 1)
        )
        
        self.search_input = TextInput(
            size_hint_x=0.8,
            multiline=False,
            background_color=get_color_from_hex('#16213e'),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            hint_text='ابحث باسم العميل أو رقم الهاتف',
            hint_text_color=(0.7, 0.7, 0.7, 1)
        )
        self.search_input.bind(text=self.on_search)
        
        search_box.add_widget(search_label)
        search_box.add_widget(self.search_input)
        list_layout.add_widget(search_box)
        
        # قائمة العملاء القابلة للتمرير
        scroll = ScrollView()
        self.customers_container = BoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint_y=None
        )
        self.customers_container.bind(minimum_height=self.customers_container.setter('height'))
        
        scroll.add_widget(self.customers_container)
        list_layout.add_widget(scroll)
        
        return list_layout
    
    def create_form(self):
        """إنشاء نموذج الإدخال"""
        form = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(10)
        )
        form.bind(minimum_height=form.setter('height'))
        
        # خلفية النموذج
        form_bg = BoxLayout(orientation='vertical', spacing=dp(10))
        
        # عنوان النموذج
        form_title = Label(
            text='إضافة / تعديل عميل',
            font_size=dp(20),
            bold=True,
            size_hint_y=None,
            height=dp(40),
            color=get_color_from_hex('#00d9ff')
        )
        form.add_widget(form_title)
        
        # اسم العميل
        form.add_widget(self.create_label('اسم العميل:'))
        self.name_input = self.create_input()
        form.add_widget(self.name_input)
        
        # رقم الهاتف
        form.add_widget(self.create_label('رقم الهاتف:'))
        self.phone_input = self.create_input()
        form.add_widget(self.phone_input)
        
        # الباقة
        form.add_widget(self.create_label('الباقة:'))
        self.package_spinner = Spinner(
            text='اختر الباقة',
            values=list(self.packages.keys()),
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#16213e'),
            color=(1, 1, 1, 1)
        )
        self.package_spinner.bind(text=self.on_package_selected)
        form.add_widget(self.package_spinner)
        
        # المبلغ
        form.add_widget(self.create_label('المبلغ المدفوع:'))
        self.amount_input = self.create_input(input_type='number')
        form.add_widget(self.amount_input)
        
        # تاريخ البداية
        form.add_widget(self.create_label('تاريخ بداية الاشتراك:'))
        self.start_date_picker = DatePicker()
        form.add_widget(self.start_date_picker)
        
        # تاريخ النهاية
        form.add_widget(self.create_label('تاريخ انتهاء الاشتراك:'))
        self.end_date_picker = DatePicker()
        form.add_widget(self.end_date_picker)
        
        # أيام التنبيه
        form.add_widget(self.create_label('التنبيه قبل (أيام):'))
        self.notification_input = self.create_input(input_type='number')
        self.notification_input.text = '5'
        form.add_widget(self.notification_input)
        
        # ملاحظات
        form.add_widget(self.create_label('ملاحظات:'))
        self.notes_input = TextInput(
            multiline=True,
            size_hint_y=None,
            height=dp(100),
            background_color=get_color_from_hex('#16213e'),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )
        form.add_widget(self.notes_input)
        
        # الأزرار
        buttons_layout = GridLayout(cols=1, spacing=dp(5), size_hint_y=None, height=dp(220))
        
        # زر إضافة
        add_btn = Button(
            text='إضافة عميل',
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#00d9ff'),
            color=get_color_from_hex('#16213e'),
            bold=True,
            background_normal=''
        )
        add_btn.bind(on_press=self.add_customer)
        buttons_layout.add_widget(add_btn)
        
        # زر تحديث
        update_btn = Button(
            text='تحديث العميل',
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#ffa726'),
            color=get_color_from_hex('#16213e'),
            bold=True,
            background_normal=''
        )
        update_btn.bind(on_press=self.update_customer)
        buttons_layout.add_widget(update_btn)
        
        # زر حذف
        delete_btn = Button(
            text='حذف العميل',
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#ef5350'),
            color=(1, 1, 1, 1),
            bold=True,
            background_normal=''
        )
        delete_btn.bind(on_press=self.delete_customer)
        buttons_layout.add_widget(delete_btn)
        
        # زر مسح
        clear_btn = Button(
            text='مسح الحقول',
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#78909c'),
            color=(1, 1, 1, 1),
            bold=True,
            background_normal=''
        )
        clear_btn.bind(on_press=lambda x: self.clear_fields())
        buttons_layout.add_widget(clear_btn)
        
        form.add_widget(buttons_layout)
        
        return form
    
    def create_label(self, text):
        """إنشاء تسمية"""
        label = Label(
            text=text,
            size_hint_y=None,
            height=dp(30),
            halign='right',
            valign='middle',
            color=(1, 1, 1, 1)
        )
        label.bind(size=label.setter('text_size'))
        return label
    
    def create_input(self, input_type='text'):
        """إنشاء حقل إدخال"""
        return TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(50),
            background_color=get_color_from_hex('#16213e'),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            input_filter=input_type if input_type == 'number' else None
        )
    
    def on_package_selected(self, spinner, text):
        """عند اختيار باقة"""
        if text in self.packages and text != "أخرى":
            package = self.packages[text]
            self.amount_input.text = str(package['price'])
            self.calculate_end_date()
    
    def calculate_end_date(self):
        """حساب تاريخ الانتهاء"""
        package_name = self.package_spinner.text
        if package_name in self.packages:
            package = self.packages[package_name]
            if package['months'] > 0:
                start = self.start_date_picker.get_date()
                end = start + timedelta(days=package['months'] * 30)
                self.end_date_picker.set_date(end)
    
    def add_customer(self, instance):
        """إضافة عميل جديد"""
        # التحقق من البيانات
        if not self.name_input.text.strip():
            self.show_popup('خطأ', 'يرجى إدخال اسم العميل')
            return
        
        if not self.amount_input.text.strip():
            self.show_popup('خطأ', 'يرجى إدخال المبلغ')
            return
        
        try:
            amount = float(self.amount_input.text)
        except ValueError:
            self.show_popup('خطأ', 'المبلغ يجب أن يكون رقماً')
            return
        
        try:
            notification_days = int(self.notification_input.text)
        except ValueError:
            self.show_popup('خطأ', 'أيام التنبيه يجب أن تكون رقماً صحيحاً')
            return
        
        # إضافة إلى قاعدة البيانات
        try:
            self.cursor.execute('''
                INSERT INTO customers (name, phone, package, amount, start_date, end_date, notification_days, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.name_input.text.strip(),
                self.phone_input.text.strip(),
                self.package_spinner.text,
                amount,
                self.start_date_picker.get_date().strftime('%Y-%m-%d'),
                self.end_date_picker.get_date().strftime('%Y-%m-%d'),
                notification_days,
                self.notes_input.text.strip()
            ))
            
            self.conn.commit()
            self.load_customers()
            self.clear_fields()
            self.show_popup('نجح', 'تمت إضافة العميل بنجاح')
            
        except Exception as e:
            self.show_popup('خطأ', f'حدث خطأ: {str(e)}')
    
    def update_customer(self, instance):
        """تحديث بيانات عميل"""
        if not self.selected_customer:
            self.show_popup('تحذير', 'يرجى اختيار عميل للتحديث')
            return
        
        if not self.name_input.text.strip():
            self.show_popup('خطأ', 'يرجى إدخال اسم العميل')
            return
        
        try:
            amount = float(self.amount_input.text)
        except ValueError:
            self.show_popup('خطأ', 'المبلغ يجب أن يكون رقماً')
            return
        
        try:
            notification_days = int(self.notification_input.text)
        except ValueError:
            self.show_popup('خطأ', 'أيام التنبيه يجب أن تكون رقماً صحيحاً')
            return
        
        try:
            self.cursor.execute('''
                UPDATE customers
                SET name=?, phone=?, package=?, amount=?, start_date=?, end_date=?, notification_days=?, notes=?
                WHERE id=?
            ''', (
                self.name_input.text.strip(),
                self.phone_input.text.strip(),
                self.package_spinner.text,
                amount,
                self.start_date_picker.get_date().strftime('%Y-%m-%d'),
                self.end_date_picker.get_date().strftime('%Y-%m-%d'),
                notification_days,
                self.notes_input.text.strip(),
                self.selected_customer['id']
            ))
            
            self.conn.commit()
            self.load_customers()
            self.clear_fields()
            self.selected_customer = None
            self.show_popup('نجح', 'تم تحديث بيانات العميل بنجاح')
            
        except Exception as e:
            self.show_popup('خطأ', f'حدث خطأ: {str(e)}')
    
    def delete_customer(self, instance):
        """حذف عميل"""
        if not self.selected_customer:
            self.show_popup('تحذير', 'يرجى اختيار عميل للحذف')
            return
        
        # نافذة تأكيد الحذف
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        message = Label(
            text=f"هل أنت متأكد من حذف العميل '{self.selected_customer['name']}'؟",
            size_hint_y=0.7
        )
        
        buttons = BoxLayout(size_hint_y=0.3, spacing=dp(10))
        
        popup = Popup(
            title='تأكيد الحذف',
            content=content,
            size_hint=(0.8, 0.3)
        )
        
        def confirm_delete(instance):
            try:
                self.cursor.execute('DELETE FROM customers WHERE id=?', (self.selected_customer['id'],))
                self.conn.commit()
                self.load_customers()
                self.clear_fields()
                self.selected_customer = None
                popup.dismiss()
                self.show_popup('نجح', 'تم حذف العميل بنجاح')
            except Exception as e:
                self.show_popup('خطأ', f'حدث خطأ: {str(e)}')
        
        yes_btn = Button(
            text='نعم',
            background_color=get_color_from_hex('#ef5350'),
            background_normal=''
        )
        yes_btn.bind(on_press=confirm_delete)
        
        no_btn = Button(
            text='لا',
            background_color=get_color_from_hex('#78909c'),
            background_normal=''
        )
        no_btn.bind(on_press=popup.dismiss)
        
        buttons.add_widget(no_btn)
        buttons.add_widget(yes_btn)
        
        content.add_widget(message)
        content.add_widget(buttons)
        
        popup.open()
    
    def load_customers(self, search_term=''):
        """تحميل قائمة العملاء"""
        self.customers_container.clear_widgets()
        
        if search_term:
            self.cursor.execute('''
                SELECT * FROM customers 
                WHERE LOWER(name) LIKE ? OR LOWER(phone) LIKE ?
                ORDER BY end_date ASC
            ''', (f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
        else:
            self.cursor.execute('SELECT * FROM customers ORDER BY end_date ASC')
        
        customers = self.cursor.fetchall()
        today = datetime.now().date()
        
        for customer in customers:
            customer_id, name, phone, package, amount, start_date, end_date, notification_days, notes, created_at = customer
            
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            days_remaining = (end_date_obj - today).days
            
            # تحديد الحالة
            if days_remaining < 0:
                status = 'expired'
                status_text = f"منتهي منذ {abs(days_remaining)} يوم"
            elif days_remaining <= notification_days:
                status = 'warning'
                status_text = f"تحذير - باقي {days_remaining} يوم"
            else:
                status = 'active'
                status_text = f"نشط - باقي {days_remaining} يوم"
            
            customer_data = {
                'id': customer_id,
                'name': name,
                'phone': phone if phone else '-',
                'package': package,
                'amount': amount,
                'start_date': start_date,
                'end_date': end_date,
                'notification_days': notification_days,
                'notes': notes,
                'status': status,
                'status_text': status_text
            }
            
            row = CustomerRow(customer_data, self.on_customer_click)
            self.customers_container.add_widget(row)
    
    def on_customer_click(self, customer_data):
        """عند النقر على عميل"""
        self.selected_customer = customer_data
        
        # ملء الحقول
        self.name_input.text = customer_data['name']
        self.phone_input.text = customer_data['phone'] if customer_data['phone'] != '-' else ''
        self.package_spinner.text = customer_data['package']
        self.amount_input.text = str(customer_data['amount'])
        
        start_date = datetime.strptime(customer_data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(customer_data['end_date'], '%Y-%m-%d')
        
        self.start_date_picker.set_date(start_date)
        self.end_date_picker.set_date(end_date)
        
        self.notification_input.text = str(customer_data['notification_days'])
        self.notes_input.text = customer_data['notes'] if customer_data['notes'] else ''
    
    def on_search(self, instance, value):
        """البحث عن العملاء"""
        self.load_customers(value)
    
    def clear_fields(self):
        """مسح جميع الحقول"""
        self.name_input.text = ''
        self.phone_input.text = ''
        self.package_spinner.text = 'اختر الباقة'
        self.amount_input.text = ''
        self.start_date_picker.set_date(datetime.now())
        self.end_date_picker.set_date(datetime.now())
        self.notification_input.text = '5'
        self.notes_input.text = ''
        self.selected_customer = None
    
    def check_notifications(self):
        """فحص التنبيهات"""
        today = datetime.now().date()
        
        self.cursor.execute('SELECT * FROM customers')
        customers = self.cursor.fetchall()
        
        warnings = []
        expired = []
        
        for customer in customers:
            customer_id, name, phone, package, amount, start_date, end_date, notification_days, notes, created_at = customer
            
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            days_remaining = (end_date_obj - today).days
            
            if days_remaining < 0:
                expired.append(f"• {name} - انتهى منذ {abs(days_remaining)} يوم")
            elif 0 <= days_remaining <= notification_days:
                warnings.append(f"• {name} - باقي {days_remaining} يوم")
        
        if expired or warnings:
            notification_message = ""
            
            if expired:
                notification_message += "⚠️ اشتراكات منتهية:\n"
                notification_message += "\n".join(expired[:5])
                if len(expired) > 5:
                    notification_message += f"\n... و {len(expired) - 5} آخرين"
                notification_message += "\n\n"
            
            if warnings:
                notification_message += "🔔 تنبيهات الاشتراكات:\n"
                notification_message += "\n".join(warnings[:5])
                if len(warnings) > 5:
                    notification_message += f"\n... و {len(warnings) - 5} آخرين"
            
            self.show_popup('تنبيهات الاشتراكات', notification_message)
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        message_label = Label(
            text=message,
            size_hint_y=0.8,
            halign='right',
            valign='middle'
        )
        message_label.bind(size=message_label.setter('text_size'))
        
        close_btn = Button(
            text='إغلاق',
            size_hint_y=0.2,
            background_color=get_color_from_hex('#00d9ff'),
            background_normal=''
        )
        
        content.add_widget(message_label)
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def on_stop(self):
        """عند إغلاق التطبيق"""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == '__main__':
    SubscriptionManagerApp().run()