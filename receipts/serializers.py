from rest_framework import serializers
from receipts.models import ReceiptMetaData, Receipt, LineItem

class ReceiptMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptMetaData
        fields = '__all__'

class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = ['description', 'quantity', 'unit_price', 'total']

class ReceiptDataSerializer(serializers.ModelSerializer):
    receipt_meta_data = serializers.IntegerField(source='receipt_file.id', read_only=True)
    line_items = LineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Receipt
        fields = [
            'id', 'purchased_at', 'merchant_name', 'total_amount', 'currency',
            'payment_method', 'category', 'receipt_meta_data', 'line_items'
        ]
