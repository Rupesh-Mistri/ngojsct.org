"""
URL configuration for ngojsct project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


from ngojsct_website.views import *
from ngojsct_mlm.views import *

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('',index,name="index"),


    #
    path('login', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('get_sponser_name_ajax/', get_sponser_name_ajax, name='get_sponser_name_ajax'),
    path('cascade_ajax/', cascade_ajax, name='cascade_ajax'),
    path('dashboard/', dashboard, name='dashboard'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)