from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

import os

from receipts.models import ReceiptMetaData, Receipt, LineItem
from receipts.serializers import ReceiptMetaDataSerializer, ReceiptDataSerializer, LineItemSerializer
from receipts import utils
ACCEPTED_FORMATS = ['.png', '.pdf', '.jpg', '.jpeg']

class UploadReceiptView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'Attach PDF or Image please'})
        if not file_obj.name.lower().endswith(tuple(ACCEPTED_FORMATS)):
            return Response({'error': f'Not a Valid format - Supported Formats: {str(ACCEPTED_FORMATS)}'}, status=status.HTTP_400_BAD_REQUEST)
        receipt_meta = ReceiptMetaData.objects.create(file_name=file_obj.name)
        # Save file to disk in 'uploads/' directory
        os.makedirs('uploads', exist_ok=True)
        file_path = os.path.join('uploads', f'{receipt_meta.id}_{file_obj.name}')
        with open(file_path, 'wb+') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        receipt_meta.file_path = file_path
        receipt_meta.save()
        serializer = ReceiptMetaDataSerializer(receipt_meta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ValidateReceiptView(APIView):
    def get(self, request, receipt_id, *args, **kwargs):
        receipt_meta = get_object_or_404(ReceiptMetaData, id=receipt_id)
        file_path, file_id = receipt_meta.file_path, receipt_id
        receipt_or_not = utils.classify_receipt_or_not(file_path, file_id)
        if receipt_or_not == 'yes':
            receipt_meta.is_valid = True
            receipt_meta.invalid_reason = ''
        else:
            receipt_meta.is_valid = False
            receipt_meta.invalid_reason = 'Not a Receipt'
        receipt_meta.save()
        serializer = ReceiptMetaDataSerializer(receipt_meta)
        return Response(serializer.data)