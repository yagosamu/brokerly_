from django.urls import path

from reports import views


app_name = 'reports'

urlpatterns = [
    path('', views.ReportMenuView.as_view(), name='menu'),
    path('<str:report_type>/', views.ReportDetailView.as_view(), name='detail'),
    path('<str:report_type>/csv/', views.ReportCsvView.as_view(), name='csv'),
    path(
        '<str:report_type>/pdf/request/',
        views.ReportPdfRequestView.as_view(),
        name='pdf_request',
    ),
    path(
        'pdf/status/<int:job_id>/',
        views.ReportPdfStatusView.as_view(),
        name='pdf_status',
    ),
    path(
        'pdf/download/<int:job_id>/',
        views.ReportPdfDownloadView.as_view(),
        name='pdf_download',
    ),
]
