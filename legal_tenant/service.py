from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .matter_intake import (
    MatterIntake,
    MatterIntakeService,
    OffboardingRequest,
    OffboardingResult,
    TenantAccount,
)

app = FastAPI(title="Legal tenant account handoff")


def matter_service() -> MatterIntakeService:
    return MatterIntakeService(InfraiClient())


def client_status(error: InfraiError) -> int:
    return error.status_code if 400 <= error.status_code < 500 else 502


@app.post("/matters", response_model=TenantAccount, status_code=201)
def open_matter(
    intake: MatterIntake,
    service: MatterIntakeService = Depends(matter_service),
) -> TenantAccount:
    try:
        return service.open_matter(intake)
    except InfraiError as error:
        raise HTTPException(
            status_code=client_status(error),
            detail={"code": error.code, "message": str(error)},
        ) from error


@app.post("/offboarding", response_model=OffboardingResult)
def offboard(
    account: OffboardingRequest,
    service: MatterIntakeService = Depends(matter_service),
) -> OffboardingResult:
    try:
        return service.offboard(account)
    except InfraiError as error:
        raise HTTPException(
            status_code=client_status(error),
            detail={"code": error.code, "message": str(error)},
        ) from error
