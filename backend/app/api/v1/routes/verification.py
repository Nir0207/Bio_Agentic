from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_verification_service
from app.schemas.verification import VerificationRequest, VerificationResponse
from app.services.verification_service import VerificationService

router = APIRouter(prefix='/verification', tags=['verification'])


@router.post('/run', response_model=VerificationResponse)
def run(
    payload: VerificationRequest,
    service: VerificationService = Depends(get_verification_service),
    _=Depends(get_current_user),
) -> VerificationResponse:
    result = service.run(query=payload.query, orchestration_payload=payload.orchestration_payload)
    return VerificationResponse(payload=result)
