# API reference

The full OpenAPI schema is regenerated at runtime — once the backend is
running, visit `http://localhost:8000/docs` for the interactive version.

This document catalogs the endpoints by responsibility, the request/response
shapes that matter, and the error modes each endpoint produces.

## Conventions

- All endpoints are prefixed with `/api/v1`.
- All requests/responses are JSON.
- All authenticated endpoints require `Authorization: Bearer <access_jwt>`.
- All timestamps are ISO 8601 in UTC.
- Errors use `application/problem+json` (`type`, `title`, `status`, `detail`).
- IDs are UUIDv4.

## Auth

### `POST /auth/login`
Request:
```json
{ "email": "doctor@consilium.md", "password": "doctor1234" }
```
Response 200:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```
Errors: `401 invalid_credentials`.

### `POST /auth/refresh`
Request:
```json
{ "refresh_token": "..." }
```
Errors: `401 invalid_refresh_token`.

### `GET /auth/me`
Response 200: the authenticated user (no `password_hash`).

## Recommendations

### `POST /cases/{case_id}/recommendations`
Creates a fresh recommendation. Internally calls the reasoning provider.
- Errors: `404 case_not_found`, `409 decision_class_out_of_scope`,
  `409 case_closed`, `409 recommendation_already_pending`.
- Response 201: full `Recommendation` with `latest_snapshot`.

### `POST /recommendations/{id}/accept`
- Errors: `404`, `409 invalid_state` (only valid when `state ∈ {answered, elicit_pending}`).

### `POST /recommendations/{id}/request-evidence`
- Errors: `404`, `409 invalid_state`.
- Behavior: re-invokes provider with `prior_snapshot_id`; appends a new
  `reasoning_snapshot` (sequence_number+1) and advances state.

### `POST /recommendations/{id}/escalate`
- Body (optional):
  ```json
  { "note": "Atypical presentation, want a second pair of eyes" }
  ```
- Errors: `404`, `403 reviewer_role_required`, `409 invalid_state`.

### `POST /recommendations/{id}/override`
- Body (required):
  ```json
  { "rationale": "..." }
  ```
- Errors: `400 missing_rationale`, `404`, `409 invalid_state`.

### `POST /recommendations/{id}/elicit`
- Body (required):
  ```json
  { "selected_option_id": "...", "free_text_response": "optional" }
  ```
- Errors: `400 missing_answer`, `404`, `409 invalid_state`.

## Reviewer

### `GET /review/queue`
Returns escalated recommendations, oldest first. Reviewer-only.

### `POST /review/{recommendation_id}/resolve`
Body:
```json
{ "final_recommendation_text": "...", "rationale": "..." }
```
Errors: `404`, `403 reviewer_only`, `409 invalid_state`.

## Audit

### `GET /audit/events`
Query params:
- `actor_user_id`
- `action` (e.g., `recommendation.accept`)
- `target_type`, `target_id`
- `from`, `to` (ISO 8601)
- `limit` (default 50, max 500), `cursor`

Response 200: paginated events, cursor-based.

### `GET /audit/events/export.csv`
Streams CSV. Admin-only. Use `from` / `to` to bound the export.

### `GET /audit/model-versions`
Lists distinct model versions and how many recommendations each produced.
