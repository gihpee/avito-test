from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from service.models import Tender, Organization, Employee, OrganizationResponsible, TenderVersion, Bid, \
    BidVersion, Feedback
from service.serializers import TenderSerializer, BidSerializer, FeedbackSerializer


def check_access(tender_id, username):
    tender = Tender.objects.get(id=tender_id)

    employee = Employee.objects.get(username=username)
    organization_responsibilities = OrganizationResponsible.objects.filter(user_id=employee)
    organizations = organization_responsibilities.values_list('organization_id', flat=True)

    if tender.organization in organizations:
        return True
    return False


def check_access_for_bid(bid_id, username):
    bid = Bid.objects.get(id=bid_id)

    employee = Employee.objects.get(username=username)

    if OrganizationResponsible.objects.filter(user_id=employee).exists():
        organization_responsibilities = OrganizationResponsible.objects.filter(user_id=employee)
        organization = organization_responsibilities.organization_id

        if bid.organization == organization:
            return True
    elif bid.creator == employee:
        return True
    return False


class Ping(APIView):
    def get(self, request):
        return Response('ok', status=status.HTTP_200_OK)


class GetTender(APIView):
    def get(self, request):
        service_type = request.query_params.get('serviceType')

        if service_type:
            tenders = Tender.objects.filter(service_type=service_type, status='Published')
        else:
            tenders = Tender.objects.all(status='Published')

        serializer = TenderSerializer(tenders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetUserTenders(APIView):
    def get(self, request):
        username = request.query_params.get('username')

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        employee = Employee.objects.get(username=username)

        if not OrganizationResponsible.objects.filter(user_id=employee).exists():
            return Response({'reason': f'user with username {username} does not belong to any organization'}, status=status.HTTP_400_BAD_REQUEST)

        organization_responsibilities = OrganizationResponsible.objects.filter(user_id=employee)
        organization_ids = organization_responsibilities.values_list('organization_id', flat=True)
        tenders = Tender.objects.filter(organization__in=organization_ids).order_by('name')

        serializer = TenderSerializer(tenders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateTender(APIView):
    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description')
        service_type = request.data.get('serviceType')
        organization_id = request.data.get('organizationId')
        creator_username = request.data.get('creatorUsername')

        if not (name and description and service_type and organization_id and creator_username):
            return Response({'reason': 'you must provide each of: name, description, serviceType, organizationId, creatorUsername'}, status=status.HTTP_400_BAD_REQUEST)

        organization = get_object_or_404(Organization, id=organization_id)
        employee = get_object_or_404(Employee, username=creator_username)

        if not OrganizationResponsible.objects.filter(organization_id=organization, user_id=employee).exists():
            return Response({'reason': f'user {creator_username} is not employee for organization {organization_id}'}, status=status.HTTP_403_FORBIDDEN)

        tender = Tender.objects.create(name=name, description=description, service_type=service_type, organization=organization, creator=employee)
        serializer = TenderSerializer(tender)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TenderStatus(APIView):
    def get(self, request, tenderId):
        username = request.query_params.get('username')

        tender = get_object_or_404(Tender, id=tenderId)

        if tender.status != 'Published':
            if not Employee.objects.filter(username=username).exists():
                return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

            if not check_access(tenderId, username):
                return Response({'reason': 'tender is not published, you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        return Response(tender.status, status=status.HTTP_200_OK)

    def put(self, request, tenderId):
        username = request.query_params.get('username')
        t_status = request.query_params.get('status')

        if not (tenderId and username and t_status):
            return Response({'reason': f'provide each of: username, status, tenderId'}, status=status.HTTP_400_BAD_REQUEST)

        tender = get_object_or_404(Tender, id=tenderId)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_access(tenderId, username):
            return Response({'reason': 'you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        if t_status not in ['Created', 'Published', 'Closed']:
            Response({'reason': f'status may be one of: Created, Published, Closed'}, status=status.HTTP_400_BAD_REQUEST)

        tender.status = t_status
        tender.save()

        serializer = TenderSerializer(tender)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EditTender(APIView):
    def patch(self, request, tenderId):
        username = request.query_params.get('username')

        name = request.data.get('name', '')
        description = request.data.get('description', '')
        service_type = request.data.get('serviceType', '')

        if len(name) > 255:
            return Response({'reason': 'name must be 255 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)
        if len(service_type) > 100:
            return Response({'reason': 'serviceType must be 100 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)
        if not (name or description or service_type):
            return Response({'reason': 'provide at least 1 param: name, description, serviceType'}, status=status.HTTP_400_BAD_REQUEST)

        tender = get_object_or_404(Tender, id=tenderId)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_access(tenderId, username):
            return Response({'reason': 'you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        tender_version = TenderVersion.objects.create(tender=tender, name=tender.name, description=tender.description, service_type=tender.service_type, version=tender.version)

        if name:
            tender.name = name
        if description:
            tender.description = description
        if service_type:
            tender.service_type = service_type
        tender.version += 1
        tender.save()

        serializer = TenderSerializer(tender)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RollbackTender(APIView):
    def put(self, request, tenderId, version):
        username = request.query_params.get('username')

        if len(username) > 50:
            return Response({'reason': 'username must be 50 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        tender = get_object_or_404(Tender, id=tenderId)
        tender_version = get_object_or_404(TenderVersion, tender=tender, version=version)

        if not check_access(tenderId, username):
            return Response({'reason': 'you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        last_version = TenderVersion.objects.create(tender=tender, name=tender.name, description=tender.description,
                                                    service_type=tender.service_type, version=tender.version)

        tender.name = tender_version.name
        tender.description = tender_version.description
        tender.service_type = tender_version.service_type
        tender.version += 1
        tender.save()

        serializer = TenderSerializer(tender)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateBid(APIView):
    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description')
        tender_id = request.data.get('tenderId')
        author_type = request.data.get('authorType')
        author_id = request.data.get('authorId')

        if not (name and description and tender_id and author_type and author_id):
            return Response({'reason': 'you must provide each of: name, description, tenderId, authorType, authorId'}, status=status.HTTP_400_BAD_REQUEST)

        if not Employee.objects.filter(id=author_id).exists():
            return Response({'reason': f'user with id {author_id} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        employee = Employee.objects.get(id=author_id)

        if author_type not in ['User', 'Organization']:
            return Response({'reason': 'authorType can be onlu User or Organization'}, status=status.HTTP_400_BAD_REQUEST)

        if author_type == 'Organization' and not OrganizationResponsible.objects.filter(user_id=employee).exists():
            return Response({'reason': 'authorType can not be Organization cause of user does not belong to any organization, switch it to User'}, status=status.HTTP_400_BAD_REQUEST)

        tender = get_object_or_404(Tender, id=tender_id)

        if tender.status != 'Published':
            return Response({'reason': 'tender is not published'}, status=status.HTTP_403_FORBIDDEN)

        if author_type == 'Organization':
            organization_responsible = OrganizationResponsible.objects.get(user_id=employee)
            organization = organization_responsible.organization_id
            bid = Bid.objects.create(name=name, description=description, author_type=author_type, creator=employee, organization=organization)
        else:
            bid = Bid.objects.create(name=name, description=description, author_type=author_type, creator=employee)

        serializer = BidSerializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserBids(APIView):
    def get(self, request):
        username = request.query_params.get('username')

        if len(username) > 50:
            return Response({'reason': 'username must be 50 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        employee = Employee.objects.get(username=username)
        bids = Bid.objects.filter(creator=employee).order_by('name')

        if OrganizationResponsible.objects.filter(user_id=employee).exists():
            organization_responsible = OrganizationResponsible.objects.get(user_id=employee)
            organization = organization_responsible.organization_id
            bids2 = Bid.objects.filter(organization=organization).order_by('name')
        else:
            bids2 = Bid.objects.none()

        combined_bids = (bids | bids2).distinct().order_by('name')

        serializer = BidSerializer(combined_bids, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TenderBids(APIView):
    def get(self, request, tenderId):
        username = request.query_params.get('username')

        if len(username) > 50:
            return Response({'reason': 'username must be 50 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        employee = Employee.objects.get(username=username)
        tender = get_object_or_404(Tender, id=tenderId)

        if not check_access(tenderId, username):
            return Response({'reason': 'you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        if not Bid.objects.filter(tender=tender, status='Published').exists():
            return Response({'reason': 'bids not found'}, status=status.HTTP_404_NOT_FOUND)

        bids = Bid.objects.filter(tender=tender, status='Published')
        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BidStatus(APIView):
    def get(self, request, bidId):
        username = request.query_params.get('username')

        bid = get_object_or_404(Bid, id=bidId)

        if bid.status != 'Published':
            if not Employee.objects.filter(username=username).exists():
                return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

            if not check_access_for_bid(bidId, username):
                return Response({'reason': 'bid is not published, you do not have access because you do not belong to bid organizarion or you are not bid creator'}, status=status.HTTP_403_FORBIDDEN)

        return Response(bid.status, status=status.HTTP_200_OK)

    def put(self, request, bidId):
        username = request.query_params.get('username')
        t_status = request.query_params.get('status')

        if not (bidId and username and t_status):
            return Response({'reason': f'provide each of: username, status, bidId'}, status=status.HTTP_400_BAD_REQUEST)

        bid = get_object_or_404(Bid, id=bidId)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_access_for_bid(bidId, username):
            return Response({'reason': 'you do not have access because you do not belong to bid organizarion or you are not bid creator'}, status=status.HTTP_403_FORBIDDEN)

        if t_status not in ['Created', 'Published', 'Cancelled']:
            Response({'reason': f'status may be one of: Created, Published, Cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        bid.status = t_status
        bid.save()

        serializer = BidSerializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EditBid(APIView):
    def patch(self, request, bidId):
        username = request.query_params.get('username')

        name = request.data.get('name', '')
        description = request.data.get('description', '')

        if len(name) > 255:
            return Response({'reason': 'name must be 255 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)
        if not (name or description):
            return Response({'reason': 'provide at least 1 param: name, description'}, status=status.HTTP_400_BAD_REQUEST)

        bid = get_object_or_404(Bid, id=bidId)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_access_for_bid(bidId, username):
            return Response({'reason': 'you do not have access because you do not belong to bid organizarion or you are not bid creator'}, status=status.HTTP_403_FORBIDDEN)

        bid_version = BidVersion.objects.create(bid=bid, name=bid.name, description=bid.description, version=bid.version)

        if name:
            bid.name = name
        if description:
            bid.description = description
        bid.version += 1
        bid.save()

        serializer = BidSerializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RollbackBid(APIView):
    def put(self, request, bidId, version):
        username = request.query_params.get('username')

        if len(username) > 50:
            return Response({'reason': 'username must be 50 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        bid = get_object_or_404(Bid, id=bidId)
        bid_version = get_object_or_404(BidVersion, bid=bid, version=version)

        if not check_access_for_bid(bidId, username):
            return Response({'reason': 'you do not have access because you do not belong to bid organizarion or you are not bid creator'}, status=status.HTTP_403_FORBIDDEN)

        last_version = BidVersion.objects.create(bid=bid, name=bid.name, description=bid.description, version=bid.version)

        bid.name = bid_version.name
        bid.description = bid_version.description
        bid.service_type = bid_version.service_type
        bid.version += 1
        bid.save()

        serializer = BidSerializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitDecision(APIView):
    def put(self, request, bidId):
        username = request.query_params.get('username')
        decision = request.query_params.get('decision')

        if len(username) > 50:
            return Response({'reason': 'username must be 50 cherecters length maximum'}, status=status.HTTP_400_BAD_REQUEST)

        if decision not in ['Approved', 'Rejected']:
            return Response({'reason': 'decision must be Approved or Rejected'}, status=status.HTTP_400_BAD_REQUEST)

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        bid = get_object_or_404(Bid, id=bidId)
        tender = bid.tender

        if not check_access(tender.id, username):
            return Response({'reason': 'you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        if bid.status == 'Cancelled':
            return Response({'reason': 'bid cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        if bid.approved is not None:
            return Response({'reason': 'bid already has decision'}, status=status.HTTP_400_BAD_REQUEST)

        if decision == 'Rejected':
            bid.approved = False
            bid.status = 'Cancelled'
        else:
            bid.approvements += 1
            responsible_employees = OrganizationResponsible.objects.filter(organization_id=tender.organization).count()
            if bid.approvements >= min(3, responsible_employees):
                bid.approved = True

        bid.save()
        serializer = BidSerializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SendFeedback(APIView):
    def put(self, request, bidId):
        review = request.query_params.get('bidFeedback')
        username = request.query_params.get('username')

        if not Employee.objects.filter(username=username).exists():
            return Response({'reason': f'user with username {username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        bid = get_object_or_404(Bid, id=bidId)
        tender = bid.tender

        if not check_access(tender.id, username):
            return Response({'reason': 'you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        if not bid.approved:
            return Response({'reason': 'you can not send feedback because bid was not approved'}, status=status.HTTP_400_BAD_REQUEST)

        feedback = Feedback.objects.create(bid=bid, description=review, executor=bid.creator)
        serializer = BidSerializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetFeedback(APIView):
    def get(self, request, tenderId):
        author_username = request.query_params.get('authorUsername')
        requester_username = request.query_params.get('requesterUsername')

        if not Employee.objects.filter(username=requester_username).exists():
            return Response({'reason': f'user with username {requester_username} does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        if not Employee.objects.filter(username=author_username).exists():
            return Response({'reason': f'user with username {author_username} does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        author = Employee.objects.get(username=author_username)

        tender = get_object_or_404(Tender, id=tenderId)

        if not Bid.objects.filter(tender=tender).exists():
            return Response({'reason': f'no bids found'}, status=status.HTTP_400_BAD_REQUEST)

        if not check_access(tender.id, requester_username):
            return Response({'reason': 'you do not have access because you do not belong to tender organizarion'}, status=status.HTTP_403_FORBIDDEN)

        feedbacks = Feedback.objects.get(executor=author)
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)







