from rest_framework import serializers

from service.models import Tender, Bid, Feedback


class TenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tender
        fields = ['id', 'name', 'description', 'status', 'service_type', 'version', 'created_at']


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = ['id', 'name', 'description', 'status', 'version', 'created_at']


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'description', 'created_at']

