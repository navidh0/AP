from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Django’s default admin site
    path('admin/', admin.site.urls),

    # Landing page (root URL)
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # App routes
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('doctor/', include(('doctor.urls', 'doctor'), namespace='doctor')),
    path('wallet/', include(('wallet.urls', 'wallet'), namespace='wallet')),
    path('booking/', include(('booking.urls', 'booking'), namespace='booking')),
]

# During development
if settings.DEBUG:

    # django-browser-reload for auto-reloading
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    
    # Serve media files 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
