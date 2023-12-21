from django.conf import settings
from django.http import HttpResponsePermanentRedirect

class HttpsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is not secure (HTTP)
        if not request.is_secure():
            # Redirect to the HTTPS version of the URL
            url = request.build_absolute_uri(request.get_full_path())
            secure_url = url.replace("http://", "https://")
            return HttpResponsePermanentRedirect(secure_url)

        return self.get_response(request)
