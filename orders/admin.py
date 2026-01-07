from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SystemConfig

# カスタムユーザーモデルの登録
# 管理画面で「管理者権限」などの追加フィールドを編集できるようにします
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_admin_user', 'display_name')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('is_admin_user', 'display_name')}),
    )
    list_display = ['username', 'display_name', 'is_admin_user', 'is_staff']

admin.site.register(User, CustomUserAdmin)

# システム設定（N分）の登録
# これで「System configs」が画面に出るようになります
admin.site.register(SystemConfig)