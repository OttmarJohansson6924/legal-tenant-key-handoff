from __future__ import annotations

from datetime import date
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field


class Gateway(Protocol):
    base_url: str

    def request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        raise AssertionError("Gateway protocol method called directly")


class MatterIntake(BaseModel):
    tenant_name: str = Field(min_length=1)
    contact_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    contact_name: str = Field(min_length=1)
    matter_reference: str = Field(min_length=1)
    signed_document_path: str = Field(min_length=1)
    response_deadline: date


class TenantAccount(BaseModel):
    tenant_name: str
    user_id: str
    key_id: str
    tenant_api_key: str
    signed_delivery: str
    follow_up_on: date
    handoff_base_url: str


class OffboardingRequest(BaseModel):
    tenant_name: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    key_id: str = Field(min_length=1)


class OffboardingResult(BaseModel):
    tenant_name: str
    user_deleted: bool
    key_revoked: bool


class MatterIntakeService:
    def __init__(self, gateway: Gateway) -> None:
        self.gateway = gateway

    def open_matter(self, intake: MatterIntake) -> TenantAccount:
        operation_id = str(uuid4())
        key_data = self.gateway.request(
            method="POST",
            path="/v1/account/keys/create",
            body={
                "name": f"{intake.tenant_name} matter access",
                "scopes": ["legal:matter"],
                "idempotency_key": f"{operation_id}:key",
            },
        )
        user_data = self.gateway.request(
            method="POST",
            path="/v1/auth/user/create",
            body={
                "email": str(intake.contact_email),
                "name": intake.contact_name,
                "metadata": {
                    "tenant_name": intake.tenant_name,
                    "matter_reference": intake.matter_reference,
                },
                "mode": "tenant",
                "idempotency_key": f"{operation_id}:user",
            },
        )
        return TenantAccount(
            tenant_name=intake.tenant_name,
            user_id=str(user_data["id"]),
            key_id=str(key_data["id"]),
            tenant_api_key=str(key_data["key"]),
            signed_delivery=intake.signed_document_path,
            follow_up_on=intake.response_deadline,
            handoff_base_url=self.gateway.base_url,
        )

    def offboard(self, account: OffboardingRequest) -> OffboardingResult:
        self.gateway.request(
            method="DELETE",
            path=f"/v1/auth/user/delete/{account.user_id}",
        )
        self.gateway.request(
            method="DELETE",
            path=f"/v1/account/keys/revoke/{account.key_id}",
        )
        return OffboardingResult(
            tenant_name=account.tenant_name,
            user_deleted=True,
            key_revoked=True,
        )
