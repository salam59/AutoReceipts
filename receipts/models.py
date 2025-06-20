from django.db import models

class ReceiptMetaData(models.Model):
    file_name = models.CharField(max_length=255)
    # file_path = models.CharField(max_length=255)
    is_valid = models.BooleanField(default=False)
    invalid_reason = models.CharField(max_length=255, blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name

class Receipt(models.Model):
    purchased_at = models.DateTimeField(blank=True, null=True)
    merchant_name = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    payment_method = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    receipt_file = models.OneToOneField(ReceiptMetaData, on_delete=models.CASCADE, related_name='receipt_meta_data', blank=True, null=True)
    prompt = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.merchant_name} - {self.total_amount}"
    
class LineItem(models.Model):
    description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='line_items', blank=True, null=True)

