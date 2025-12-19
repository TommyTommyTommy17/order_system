from django import forms
from .models import Order

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