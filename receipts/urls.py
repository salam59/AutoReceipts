from django.urls import path
from .views import UploadReceiptView, ValidateReceiptView, ProcessReceiptView, ListReceiptsView, ReceiptDetailView

urlpatterns = [
    path('upload', UploadReceiptView.as_view(), name='upload-receipt'),
    path('validate/<int:receipt_id>', ValidateReceiptView.as_view(), name='validate-receipt'),
    path('process/<int:receipt_id>', ProcessReceiptView.as_view(), name='process-receipt'),
    path('receipts', ListReceiptsView.as_view(), name='list-receipts'),
    path('receipts/<int:id>', ReceiptDetailView.as_view(), name='receipt-detail'),
] 