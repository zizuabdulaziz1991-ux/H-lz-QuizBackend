from django.http import JsonResponse


class HealthCheckMiddleware:
    """/healthz'i ALLOWED_HOSTS ve SSL yonlendirmesinden once yanitlar (load balancer icin)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/healthz":
            return JsonResponse({"status": "ok"})
        return self.get_response(request)
