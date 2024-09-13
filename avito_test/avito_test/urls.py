"""
URL configuration for avito_test project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from service.views import Ping, GetTender, CreateTender, GetUserTenders, TenderStatus, EditTender, RollbackTender, \
    CreateBid, UserBids, TenderBids, BidStatus, EditBid, SubmitDecision, SendFeedback, RollbackBid, GetFeedback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/ping/', Ping.as_view(), name='ping'),
    path('api/tenders/', GetTender.as_view(), name='tenders'),
    path('api/tenders/new/', CreateTender.as_view(), name='tenders-new'),
    path('api/tenders/my/', GetUserTenders.as_view(), name='tenders-my'),
    path('api/tenders/<uuid:tenderId>/status/', TenderStatus.as_view(), name='tender-status'),
    path('api/tenders/<uuid:tenderId>/edit/', EditTender.as_view(), name='tender-edit'),
    path('api/tenders/<uuid:tenderId>/rollback/<int:version>/', RollbackTender.as_view(), name='tender-rollback'),
    path('api/bids/new/', CreateBid.as_view(), name='bid-new'),
    path('api/bids/my/', UserBids.as_view(), name='bid-my'),
    path('api/bids/<uuid:tenderId>/list/', TenderBids.as_view(), name='bid-list'),
    path('api/bids/<uuid:bidId>/status/', BidStatus.as_view(), name='bid-status'),
    path('api/bids/<uuid:bidId>/edit/', EditBid.as_view(), name='bid-edit'),
    path('api/bids/<uuid:bidId>/submit-decision/', SubmitDecision.as_view(), name='bid-submit'),
    path('api/bids/<uuid:bidId>/feedback/', SendFeedback.as_view(), name='bid-feedback'),
    path('api/bids/<uuid:bidId>/rollback/<int:version>/', RollbackBid.as_view(), name='bid-rollback'),
    path('api/bids/<uuid:tenderId>/reviews/', GetFeedback.as_view(), name='get-feedback'),
]
