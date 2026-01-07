from .models import SystemConfig

class DynamicSessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # DBから設定値を取得（なければデフォルト30分）
            config = SystemConfig.objects.first()
            timeout = config.session_timeout_minutes if config else 30
            # セッションの有効期限を更新
            request.session.set_expiry(timeout * 60)
        return self.get_response(request)