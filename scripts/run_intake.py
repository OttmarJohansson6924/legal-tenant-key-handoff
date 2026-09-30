from datetime import date, timedelta

from legal_tenant.infrai_client import InfraiClient
from legal_tenant.matter_intake import (
    MatterIntake,
    MatterIntakeService,
    OffboardingRequest,
    TenantAccount,
)


def main() -> None:
    client = InfraiClient()
    service = MatterIntakeService(client)
    result: TenantAccount | None = None
    try:
        result = service.open_matter(
            MatterIntake(
                tenant_name="Northwind Legal",
                contact_email="chenhua@changba.com",
                contact_name="Avery Chen",
                matter_reference="NW-2026-104",
                signed_document_path="documents/NW-2026-104/signed-engagement.pdf",
                response_deadline=date.today() + timedelta(days=14),
            )
        )
        print(result.model_dump_json(indent=2))
    finally:
        if result is not None:
            service.offboard(
                OffboardingRequest(
                    tenant_name=result.tenant_name,
                    user_id=result.user_id,
                    key_id=result.key_id,
                )
            )
        client.close()


if __name__ == "__main__":
    main()
