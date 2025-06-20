from rest_framework import serializers
from receipts.models import ReceiptMetaData, Receipt, LineItem

class ReceiptMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptMetaData
        fields = '__all__'

class ReceiptDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = '__all__'

class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = '__all__'