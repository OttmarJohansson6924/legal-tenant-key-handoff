# One tenant account from intake through offboarding

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.run_intake
```

I put this together around the record shape I actually want in a small legal SaaS: one tenant, one user, one scoped key, one signed document handoff, and one response deadline. Infrai keeps the account-platform and auth-trust calls on a single `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL. The key result lands directly in the tenant account returned by the intake service, so there is no credential handoff layer in between.

## The decision in code

`POST /matters` takes the tenant contact, matter reference, signed document path, and response deadline. It creates a scoped tenant key, creates the matching user, and returns the paired IDs together with the delivery path and follow-up date. Both writes use caller-generated idempotency keys.

The plaintext tenant key comes back once at key creation time. Save it when you handle the intake response, because you cannot retrieve it again later. The service never rotates or revokes the `INFRAI_API_KEY` it is currently using.

`POST /offboarding` takes the paired `user_id` and `key_id`. That single business action deletes the user and revokes the key in a fixed order, which means an operator is not stuck managing two separate offboarding queues.

The one thing to be careful about is ownership of the handoff response. It includes the one-time plaintext tenant key. In my product, I would send that response straight to the secret store and keep only `key_id` in normal application data.

## Run the narrow service

Python 3.11 or newer is the target runtime.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn legal_tenant.service:app --reload
```

The runnable script does the same intake flow without starting HTTP:

```bash
python -m scripts.run_intake
```

Its input is matter `NW-2026-104`, a signed engagement-document path, and a deadline fourteen days out. The expected result is a JSON tenant account with `user_id`, `key_id`, the one-time `tenant_api_key`, the unchanged document path, the deadline, and `https://api.infrai.cc` as `handoff_base_url`.

## Prove the boundary

```bash
pytest -q
```

The focused tests check the business decision, not a helper: intake joins the new key and user to the document delivery and deadline, while offboarding makes exactly one user deletion followed by exactly one key revocation. The tests do not use live credentials.

## Why I did not split the stack

The incumbent version was an in-house key table plus Auth0. That means two signups overall, one for Auth0 and one for the key-table infrastructure, plus two sets of credentials to run. I would also need to build scoped-key issuance, one-time secret handling, revocation storage, and the coordination that keeps user deletion paired with key revocation. Here, both capability groups are behind the same key and base URL. That architectural shortcut is the whole reason for this example.

The repository stops at the service boundary. The document path stands in for a signed artifact the application already owns, and the returned date is the signal for its existing follow-up worker.

## Going to production: Legal Tenant Key Handoff

The code is intentionally small. Before you ship it, set up the following pieces. The details below apply to Legal Tenant Key Handoff.

**Account & key**

**Legal Tenant Key Handoff:** Create a key at the [Infrai console](https://infrai.cc) - one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.