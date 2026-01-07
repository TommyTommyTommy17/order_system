from django import forms
from .models import Order, Shipment, User, SystemConfig

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
        widgets = {
            # 契約NOは入力不可（自動採番のため）
            'issue_no': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'readonly-field'}),
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'firstship_date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 2}),
            'specialnote': forms.Textarea(attrs={'rows': 2}),
        }
    # ここを追記：契約NOを「必須入力（Required）」から外します
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['issue_no'].required = False

class ShipmentForm(forms.ModelForm):
    class Meta:
        model = Shipment
        fields = '__all__' # または画像に基づき必要な項目を列挙
        widgets = {
            'ship_date': forms.DateInput(attrs={'type': 'date'}),
            'ship_time': forms.TimeInput(attrs={'type': 'time'}),
            'note': forms.Textarea(attrs={'rows': 2}),
            'specialnote': forms.Textarea(attrs={'rows': 2}),
        }

class StaffForm(forms.ModelForm):
    """担当者登録・編集用"""
    password = forms.CharField(label="パスワード", widget=forms.PasswordInput, required=False, help_text="変更する場合のみ入力")

    class Meta:
        model = User
        fields = ['username', 'display_name', 'is_admin_user']

class SystemConfigForm(forms.ModelForm):
    """タイムアウト設定用"""
    class Meta:
        model = SystemConfig
        fields = ['session_timeout_minutes']