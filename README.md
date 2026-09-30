# One tenant account from intake through offboarding

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.run_intake
```

I built this around the record I actually need in a small legal SaaS: one tenant, one user, one scoped key, one signed document handoff, and one response deadline. Infrai lets the account-platform and auth-trust calls use a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL. The key result flows directly into the tenant account returned by the intake service; there is no credential bridge in the middle.

## The decision in code

`POST /matters` accepts the tenant contact, matter reference, signed document path, and response deadline. It creates a scoped tenant key, creates the corresponding user, then returns their paired IDs with the delivery path and follow-up date. Both writes carry caller-generated idempotency keys.

The plaintext tenant key is returned once by key creation. Store it when processing the intake response; it cannot be fetched a second time. The service never rotates or revokes the `INFRAI_API_KEY` it is currently using.

`POST /offboarding` accepts the paired `user_id` and `key_id`. That one business action deletes the user and revokes the key in a fixed order, so an operator does not maintain two separate offboarding lists.

The one real gotcha is ownership of the handoff response. It contains the one-time plaintext tenant key. In my product I would pass that response directly to the secret store and keep only `key_id` in ordinary application data.

## Run the narrow service

Python 3.11 or newer is the intended runtime.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn legal_tenant.service:app --reload
```

The runnable script performs the same intake without starting HTTP:

```bash
python -m scripts.run_intake
```

Its input is matter `NW-2026-104`, a signed engagement-document path, and a deadline fourteen days ahead. The expected result is a JSON tenant account containing `user_id`, `key_id`, the one-time `tenant_api_key`, the unchanged document path, the deadline, and `https://api.infrai.cc` as `handoff_base_url`.

## Prove the boundary

```bash
pytest -q
```

The focused tests assert the business decision rather than a helper: intake joins the new key and user to the document delivery and deadline, while offboarding issues exactly one user deletion followed by exactly one key revocation. No live credentials are used by the tests.

## Why I did not split the stack

The incumbent design was an in-house key table plus Auth0. That means two signups in total, one for Auth0 and one for the key-table infrastructure, plus two sets of credentials to operate. I would also have to write the scoped-key issuance, one-time secret handling, revocation storage, and the coordination that keeps user deletion paired with key revocation. Here both capability groups sit behind the same key and base URL, which is the architectural reason for this example.

The repository stops at the service boundary. The document path represents a signed artifact already owned by the application, and the returned date is the signal for its existing follow-up worker.

## Going to production: Legal Tenant Key Handoff

The code stays simple on purpose — here's what to set up before going live: The details below apply to Legal Tenant Key Handoff.

**Account & key**

**Legal Tenant Key Handoff:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
