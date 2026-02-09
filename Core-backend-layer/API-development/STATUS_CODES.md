# HTTP Status Codes Reference Guide

Consistent and correct use of HTTP status codes is a cornerstone of well-designed RESTful APIs. Status codes communicate the outcome of every request in a standardized way, enabling clients to programmatically handle responses without parsing message bodies for error context. When an entire engineering team agrees on which codes to return and when, the result is a predictable, self-documenting API surface that reduces integration friction, simplifies debugging, and improves the developer experience for both internal and external consumers.

This guide serves as the canonical reference for our API projects. Every endpoint should return status codes that align with the definitions and conventions documented here.

---

## 1xx — Informational

Informational codes indicate that the server has received the request headers and the client should proceed with the request body or continue waiting.

| Code | Name | Description | Example Scenario |
|------|------|-------------|------------------|
| **100** | **Continue** | The server has received the request headers and the client should proceed to send the request body. | A client uploading a large file sends an `Expect: 100-continue` header; the server responds with `100` to signal it is ready to accept the body. |
| **101** | **Switching Protocols** | The server is switching protocols as requested by the client via an `Upgrade` header. | A client requests an upgrade from HTTP/1.1 to WebSocket; the server agrees and responds with `101`. |
| **102** | **Processing** | The server has received the request and is still processing it (WebDAV). | A batch import request is accepted and the server signals that processing is underway but not yet complete. |

> **Note:** In typical REST API development, 1xx codes are handled at the transport layer and rarely returned explicitly by application code.

---

## 2xx — Success

Success codes indicate that the client's request was received, understood, and accepted.

| Code | Name | Description | Example Scenario |
|------|------|-------------|------------------|
| **200** | **OK** | The request succeeded. The response body contains the requested resource or the result of the operation. | `GET /api/products/42` returns the product details. `PUT /api/products/42` updates the product and returns the updated resource. |
| **201** | **Created** | A new resource was successfully created. The response **should** include a `Location` header pointing to the new resource. | `POST /api/products` creates a new product. The response returns the created product with its server-assigned ID and a `Location: /api/products/43` header. |
| **202** | **Accepted** | The request has been accepted for processing, but processing is not yet complete. Use for asynchronous operations. | `POST /api/reports/generate` enqueues a report generation job. The response returns a job ID the client can poll for status. |
| **204** | **No Content** | The request succeeded but there is no content to return. The response body **must** be empty. | `DELETE /api/products/42` successfully deletes the product. No body is returned. |
| **206** | **Partial Content** | The server is returning only part of the resource due to a `Range` header sent by the client. | A client requests bytes 0–1023 of a large file download; the server returns that chunk with appropriate `Content-Range` headers. |

---

## 3xx — Redirection

Redirection codes indicate that further action is needed from the client to complete the request.

| Code | Name | Description | Example Scenario |
|------|------|-------------|------------------|
| **301** | **Moved Permanently** | The resource has been permanently moved to a new URI. Clients and search engines should update their references. | `GET /api/v1/users` is permanently relocated to `/api/v2/users`. The response includes a `Location` header with the new URI. |
| **302** | **Found** | The resource temporarily resides at a different URI. The client should continue using the original URI for future requests. | A short-link endpoint temporarily redirects to a campaign landing page. |
| **304** | **Not Modified** | The resource has not been modified since the version indicated by the client's `If-None-Match` or `If-Modified-Since` headers. No body is returned. | `GET /api/products/42` with `If-None-Match: "etag-abc"` — the resource hasn't changed, so the server returns `304` to save bandwidth. |
| **307** | **Temporary Redirect** | The request should be repeated at another URI, preserving the original HTTP method. | A load balancer temporarily redirects a `POST` request to a different backend node, and the client must resend the `POST` (not downgrade to `GET`). |
| **308** | **Permanent Redirect** | Like `301`, but the client **must** preserve the original HTTP method when following the redirect. | An API version migration permanently redirects `POST /api/v1/orders` to `POST /api/v2/orders` without changing the method. |

---

## 4xx — Client Errors

Client error codes indicate that the request contains bad syntax, invalid data, or cannot be fulfilled due to a client-side issue.

| Code | Name | Description | Example Scenario |
|------|------|-------------|------------------|
| **400** | **Bad Request** | The server cannot process the request due to malformed syntax, invalid JSON, or missing required fields. This is the general-purpose client error when no more specific 4xx code applies. | `POST /api/products` with a malformed JSON body (`{"name": "Laptop", price:}`) — the server cannot parse the request. |
| **401** | **Unauthorized** | The request lacks valid authentication credentials. The client must authenticate before accessing the resource. | `GET /api/admin/dashboard` without an `Authorization` header or with an expired JWT token. |
| **403** | **Forbidden** | The server understood the request and the client is authenticated, but the client does not have permission to access the resource. | A user with the `USER` role attempts `DELETE /api/products/42`, which requires the `ADMIN` role. Authentication succeeded, but authorization failed. |
| **404** | **Not Found** | The requested resource does not exist on the server. | `GET /api/products/9999` where no product with ID 9999 exists in the database. |
| **405** | **Method Not Allowed** | The HTTP method is not supported for the requested resource. The response **should** include an `Allow` header listing valid methods. | `DELETE /api/auth/login` — the login endpoint only accepts `POST`. |
| **406** | **Not Acceptable** | The server cannot produce a response matching the `Accept` headers sent by the client. | A client sends `Accept: application/xml` but the API only supports `application/json`. |
| **408** | **Request Timeout** | The server timed out waiting for the client to finish sending the request. | A client opens a connection but fails to send the request body within the server's timeout window. |
| **409** | **Conflict** | The request conflicts with the current state of the target resource. | `POST /api/auth/register` with an email that already exists in the system. Also applies to concurrent update conflicts where optimistic locking detects a version mismatch. |
| **410** | **Gone** | The resource existed previously but has been permanently removed. Unlike `404`, this explicitly communicates that the resource will not return. | `GET /api/promotions/summer-2024` — the promotion has ended and been permanently deleted. |
| **413** | **Payload Too Large** | The request body exceeds the server's size limit. | A client attempts to upload a 500 MB file to an endpoint with a 50 MB limit. |
| **415** | **Unsupported Media Type** | The request's `Content-Type` is not supported by the endpoint. | `POST /api/products` with `Content-Type: text/plain` when the endpoint only accepts `application/json`. |
| **422** | **Unprocessable Entity** | The request is syntactically valid JSON but contains semantic validation errors. The server understands the structure but cannot process the content. | `POST /api/products` with `{"name": "", "price": -5}` — the JSON parses correctly, but an empty name and negative price fail business validation rules. |
| **429** | **Too Many Requests** | The client has sent too many requests in a given time window (rate limiting). The response **should** include a `Retry-After` header. | A client exceeds 100 requests per minute to `/api/products`. The server responds with `429` and `Retry-After: 30`. |

---

## 5xx — Server Errors

Server error codes indicate that the server failed to fulfill a valid request due to an internal issue.

| Code | Name | Description | Example Scenario |
|------|------|-------------|------------------|
| **500** | **Internal Server Error** | A generic server-side error occurred. Use this when no more specific 5xx code applies. **Never** expose stack traces or internal details to the client. | An unhandled `NullPointerException` occurs in the service layer while processing `GET /api/products`. The API returns a generic error message. |
| **501** | **Not Implemented** | The server does not support the functionality required to fulfill the request. | A client calls `PATCH /api/products/42` on an API that has not yet implemented partial updates. |
| **502** | **Bad Gateway** | The server, acting as a gateway or proxy, received an invalid response from an upstream server. | An API gateway forwards a request to a downstream microservice that returns a malformed response. |
| **503** | **Service Unavailable** | The server is temporarily unable to handle the request, typically due to maintenance or overload. The response **should** include a `Retry-After` header. | The product service is undergoing a scheduled database migration. The API returns `503` with `Retry-After: 300`. |
| **504** | **Gateway Timeout** | The server, acting as a gateway or proxy, did not receive a timely response from an upstream server. | An API gateway times out waiting for the order service to respond during a period of high load. |

---

## Best Practices

### Choosing the Right Success Code

- **Use `200` for successful reads and updates** that return a response body (`GET`, `PUT`, `PATCH`).
- **Use `201` for resource creation** (`POST`). Always include a `Location` header pointing to the new resource.
- **Use `202` for asynchronous operations** where the work is queued but not yet complete. Return a handle (job ID, URL) the client can use to check status.
- **Use `204` for successful operations with no response body** (`DELETE`, or `PUT` when you choose not to return the updated resource).
- **Never return `200` for a creation** — `201` communicates semantics that clients and documentation tools rely on.

### Distinguishing Client Error Codes

- **`400` vs `422`**: Use `400` when the request is structurally malformed (unparseable JSON, missing `Content-Type`). Use `422` when the JSON is valid but field values fail business validation (empty name, negative price, date in the past).
- **`401` vs `403`**: Use `401` when the client has **not authenticated** (missing or invalid credentials). Use `403` when the client **is authenticated** but lacks the required permissions. Never use `403` for unauthenticated requests.
- **`404` vs `410`**: Use `404` when a resource is simply not found. Use `410` when you need to explicitly communicate that a resource **previously existed** but has been permanently removed.
- **`409` for conflicts**: Prefer `409` over `400` when the error is caused by a state conflict rather than invalid input. Common cases include duplicate registrations, concurrent edit collisions, and optimistic locking failures.

### Error Response Body Structure

Adopt a consistent error response format across all endpoints:

```json
{
  "status": 422,
  "error": "Unprocessable Entity",
  "message": "Validation failed",
  "details": [
    {
      "field": "price",
      "message": "Price must be a positive number"
    },
    {
      "field": "name",
      "message": "Name is required"
    }
  ],
  "timestamp": "2025-01-15T10:30:00Z",
  "path": "/api/products"
}
```

- Always include the numeric `status` code in the body for easy client-side processing.
- Use a human-readable `message` for logging and debugging.
- Use a `details` array for field-level validation errors.
- Include a `timestamp` and `path` for traceability.

### Rate Limiting and Retry Headers

- When returning `429`, always include `Retry-After` (in seconds) so clients can back off gracefully.
- When returning `503`, include `Retry-After` to indicate when the service is expected to recover.
- Consider including `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers on all responses for proactive rate limit awareness.

### General Guidelines

- **Be specific**: If a more specific status code exists, use it instead of a generic one. `409 Conflict` is more informative than `400 Bad Request` for a duplicate email.
- **Be consistent**: Every endpoint in the API should follow the same conventions. Document deviations explicitly.
- **Do not leak internals**: `500` responses should never contain stack traces, database errors, or internal service names. Log those server-side and return a generic message to the client.
- **Use headers**: Leverage standard headers like `Location` (for `201`), `Allow` (for `405`), `Retry-After` (for `429`, `503`), and `WWW-Authenticate` (for `401`).
- **Document per-endpoint**: In the API documentation (OpenAPI/Swagger), list all possible status codes for each endpoint, not just the success case.

---

*This guide is treated as a living document. Update it as the team encounters new scenarios or adopts new conventions.*
