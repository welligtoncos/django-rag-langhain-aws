from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

@extend_schema(
    description="Endpoint de teste para verificar se a API está funcionando",
    responses={200: {'description': 'Sucesso'}}
)
@api_view(['GET'])
def hello_api(request):
    return Response({
        'message': 'API RAG funcionando!',
        'status': 'success'
    })