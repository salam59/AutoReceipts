from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

import os, json
from datetime import datetime

from receipts.models import ReceiptMetaData, Receipt, LineItem
from receipts.serializers import ReceiptMetaDataSerializer, ReceiptDataSerializer
from receipts import utils

ACCEPTED_FORMATS = ['.png', '.pdf', '.jpg', '.jpeg']

class UploadReceiptView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """
        Create a new receipt meta data entry, and save the file to disk
        in 'uploads/' directory. Checks for duplicates using file hash.

        Returns:
            Response: A JSON response with the new receipt meta data entry or duplicate info.
        """
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'Attach PDF or Image please'})
        if not file_obj.name.lower().endswith(tuple(ACCEPTED_FORMATS)):
            return Response({'error': f'Not a Valid format - Supported Formats: {str(ACCEPTED_FORMATS)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read file content and generate hash
        file_content = file_obj.read()
        file_hash = utils.generate_file_hash_from_content(file_content)
        
        # Check for existing file with same hash
        existing_receipt = ReceiptMetaData.objects.filter(file_hash=file_hash).first()
        if existing_receipt:
            duplicate_strategy = request.query_params.get('duplicate_strategy', 'reject')
            
            if duplicate_strategy == 'reject':
                return Response({
                    'error': 'Duplicate file detected',
                    'duplicate_info': {
                        'existing_id': existing_receipt.id,
                        'existing_file_name': existing_receipt.file_name,
                        'uploaded_at': existing_receipt.created_at.isoformat(),
                        'is_processed': existing_receipt.is_processed,
                        'is_valid': existing_receipt.is_valid
                    },
                    'message': 'Use duplicate_strategy=update to update existing receipt or duplicate_strategy=ignore to create new entry'
                }, status=status.HTTP_409_CONFLICT)
            
            elif duplicate_strategy == 'update':
                # Update existing receipt metadata
                existing_receipt.file_name = file_obj.name
                existing_receipt.updated_at = datetime.now()
                existing_receipt.save()
                
                # Update the file on disk
                os.makedirs('uploads', exist_ok=True)
                file_path = os.path.join('uploads', f'file-{existing_receipt.id}_{file_obj.name}')
                with open(file_path, 'wb+') as f:
                    f.write(file_content)
                existing_receipt.file_path = file_path
                existing_receipt.save()
                
                serializer = ReceiptMetaDataSerializer(existing_receipt)
                return Response({
                    'message': 'Existing receipt updated successfully',
                    'receipt': serializer.data
                }, status=status.HTTP_200_OK)
        
        # Create new receipt metadata
        receipt_meta = ReceiptMetaData.objects.create(file_name=file_obj.name, file_hash=file_hash)
        
        # Save file to disk in 'uploads/' directory
        os.makedirs('uploads', exist_ok=True)
        file_path = os.path.join('uploads', f'file-{receipt_meta.id}_{file_obj.name}')
        with open(file_path, 'wb+') as f:
            f.write(file_content)
        receipt_meta.file_path = file_path
        receipt_meta.save()
        
        serializer = ReceiptMetaDataSerializer(receipt_meta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ValidateReceiptView(APIView):
    def get(self, request, receipt_id, *args, **kwargs):
        """
        Validate a receipt by checking if it is a receipt or not.

        Returns:
            Response: A JSON response with the updated receipt meta data entry.
        """
        receipt_meta = get_object_or_404(ReceiptMetaData, id=receipt_id)
        file_path, file_id = receipt_meta.file_path, receipt_id
        receipt_or_not = utils.classify_receipt_or_not(file_path, file_id)
        if 'error' in receipt_or_not:
            return Response(receipt_or_not)
        else:
            receipt_or_not = json.loads(receipt_or_not).get('receipt_or_not')
        if receipt_or_not == 'yes':
            receipt_meta.is_valid = True
            receipt_meta.invalid_reason = ''
        else:
            receipt_meta.is_valid = False
            receipt_meta.invalid_reason = 'Not a Receipt'
        receipt_meta.save()
        serializer = ReceiptMetaDataSerializer(receipt_meta)
        return Response(serializer.data)

class ProcessReceiptView(APIView):
    def get(self, request, receipt_id, *args, **kwargs):
        """
        Process a receipt by extracting data from it and saving the extracted data.
        Handles duplicate processing scenarios.

        Args:
            request: The request object.
            receipt_id: The id of the receipt to be processed.

        Returns:
            Response: A JSON response with the extracted data.
        """
        # Check if receipt has already been processed
        receipt_data = Receipt.objects.filter(receipt_file=receipt_id)
        receipt_data_serializer = ReceiptDataSerializer(receipt_data, many=True)
        
        if receipt_data:
            duplicate_strategy = request.query_params.get('duplicate_strategy', 'return_existing')
            
            if duplicate_strategy == 'return_existing':
                return Response({
                    'message': 'Receipt already processed',
                    'receipt': receipt_data_serializer.data
                }, status=status.HTTP_200_OK)
            
            elif duplicate_strategy == 'reprocess':
                # Delete existing receipt data and reprocess
                receipt_data.delete()
                # Continue with processing below
            else:
                return Response({
                    'error': 'Receipt already processed',
                    'existing_data': receipt_data_serializer.data,
                    'message': 'Use duplicate_strategy=reprocess to reprocess or duplicate_strategy=return_existing to return existing data'
                }, status=status.HTTP_409_CONFLICT)
        
        receipt_meta = get_object_or_404(ReceiptMetaData, id=receipt_id)
        if not receipt_meta.is_valid:
            return Response({'error': f'Not a Valid Receipt - Reason :- {receipt_meta.invalid_reason}'}, status=status.HTTP_400_BAD_REQUEST)
    
        file_path = receipt_meta.file_path
        if not file_path or not os.path.exists(file_path):
            return Response({'error': 'File not found for this receipt.'}, status=status.HTTP_404_NOT_FOUND)
    
        try:
            extracted_result = utils.extract_receipt_data(file_path, str(receipt_meta.id))
            if isinstance(extracted_result, tuple):
                return Response({'error': extracted_result[1]}, status=status.HTTP_400_BAD_REQUEST)
            extracted_data = json.loads(extracted_result)
        except Exception as e:
            return Response({'error': f'Extraction failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not extracted_data:
            return Response({'error': 'No data extracted from receipt.'}, status=status.HTTP_400_BAD_REQUEST)

        receipt = Receipt.objects.create(
            merchant_name=extracted_data.get('merchant_name'),
            total_amount=extracted_data.get('total_amount'),
            currency=extracted_data.get('currency'),
            payment_method=extracted_data.get('payment_method'),
            category=extracted_data.get('category'),
            purchased_at=extracted_data.get('purchased_at'),
            receipt_file=receipt_meta,
        )
        line_items = extracted_data.get('line_items') or []
        for item in line_items:
            LineItem.objects.create(
                description=item.get('description'),
                quantity=item.get('quantity'),
                unit_price=item.get('unit_price'),
                total=item.get('total'),
                receipt=receipt
            )
        receipt_meta.updated_at = datetime.now()
        receipt_meta.is_processed = True
        receipt_meta.save()
        serializer = ReceiptDataSerializer(receipt)
        return Response(serializer.data)
    
class ListReceiptsView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Returns a list of all receipts.

        Returns:
            Response: A JSON response containing a list of receipts.
        """
        receipts = Receipt.objects.all()
        serializer = ReceiptDataSerializer(receipts, many=True)
        return Response(serializer.data)

class ReceiptDetailView(APIView):
    def get(self, request, id, *args, **kwargs):
        """
        Retrieve a single receipt by its id.

        Args:
            request: The request object.
            id: The id of the receipt to retrieve.

        Returns:
            Response: A JSON response with the receipt data.
        """
        receipt = get_object_or_404(Receipt, id=id)
        serializer = ReceiptDataSerializer(receipt)
        return Response(serializer.data)