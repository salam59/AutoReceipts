from django.db import models
import hashlib
import os

class ReceiptMetaData(models.Model):
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)
    is_valid = models.BooleanField(default=False)
    invalid_reason = models.CharField(max_length=255, blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name
    
    def generate_file_hash(self):
        """Generate SHA-256 hash of the file content"""
        if not self.file_path or not os.path.exists(self.file_path):
            return None
        
        hash_sha256 = hashlib.sha256()
        try:
            with open(self.file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error generating hash for {self.file_path}: {e}")
            return None
    
    def save(self, *args, **kwargs):
        # Generate file hash if not already set and file exists
        if not self.file_hash and self.file_path and os.path.exists(self.file_path):
            self.file_hash = self.generate_file_hash()
        super().save(*args, **kwargs)

class Receipt(models.Model):
    purchased_at = models.DateTimeField(blank=True, null=True)
    merchant_name = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    payment_method = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    receipt_file = models.OneToOneField(ReceiptMetaData, on_delete=models.CASCADE, related_name='receipt_meta_data', blank=True, null=True)
    # prompt = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.merchant_name} - {self.total_amount}"
    
class LineItem(models.Model):
    description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='line_items', blank=True, null=True)

