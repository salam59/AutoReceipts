from rest_framework import serializers
from receipts.models import ReceiptMetaData, ReceiptData

class ReceiptMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptMetaData
        fields = '__all__'

class ReceiptDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptData
        fields = '__all__'
