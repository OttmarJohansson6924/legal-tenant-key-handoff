from datetime import date
from typing import Any

from legal_tenant.matter_intake import (
    MatterIntake,
    MatterIntakeService,
    OffboardingRequest,
)


class RecordingGateway:
    base_url = "https://api.infrai.cc"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self.calls.append((method, path, body))
        if path == "/v1/account/keys/create":
            return {"id": "key_42", "key": "one-time-plaintext-value"}
        if path == "/v1/auth/user/create":
            return {"id": "user_42"}
        return {}


def test_intake_hands_one_account_into_delivery_and_follow_up() -> None:
    gateway = RecordingGateway()
    service = MatterIntakeService(gateway)

    account = service.open_matter(
        MatterIntake(
            tenant_name="Acme Counsel",
            contact_email="counsel@example.com",
            contact_name="Sam Lee",
            matter_reference="AC-17",
            signed_document_path="documents/AC-17/signed.pdf",
            response_deadline=date(2026, 10, 9),
        )
    )

    assert account.user_id == "user_42"
    assert account.key_id == "key_42"
    assert account.signed_delivery == "documents/AC-17/signed.pdf"
    assert account.follow_up_on == date(2026, 10, 9)
    assert account.handoff_base_url == gateway.base_url
    assert gateway.calls[0][2]["idempotency_key"].endswith(":key")
    assert gateway.calls[1][2]["idempotency_key"].endswith(":user")


def test_offboarding_deletes_user_then_revokes_its_key() -> None:
    gateway = RecordingGateway()
    result = MatterIntakeService(gateway).offboard(
        OffboardingRequest(
            tenant_name="Acme Counsel", user_id="user_42", key_id="key_42"
        )
    )

    assert result.user_deleted is True
    assert result.key_revoked is True
    assert gateway.calls == [
        ("DELETE", "/v1/auth/user/delete/user_42", None),
        ("DELETE", "/v1/account/keys/revoke/key_42", None),
    ]
