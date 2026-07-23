from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import LogEntry
from .serializers import LogEntrySerializer


@api_view(['GET'])
def logs_list(request):
    logs = LogEntry.objects.all().order_by('-umg_fecha_registro')[:100]
    serializer = LogEntrySerializer(logs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)