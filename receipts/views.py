from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

import os

from receipts.models import ReceiptMetaData, Receipt, LineItem
from receipts.serializers import ReceiptMetaDataSerializer, ReceiptDataSerializer, LineItemSerializer

class UploadReceiptView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj or not file_obj.name.lower().endswith('.pdf'):
            return Response({'error': 'Only PDF files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        receipt_meta = ReceiptMetaData.objects.create(file_name=file_obj.name)
        # Save file to disk in 'uploads/' directory
        os.makedirs('uploads', exist_ok=True)
        file_path = os.path.join('uploads', f'{receipt_meta.id}_{file_obj.name}')
        with open(file_path, 'wb+') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        serializer = ReceiptMetaDataSerializer(receipt_meta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)