# Authentication and Authorization

This directory contains comprehensive implementations of authentication and authorization across several web frameworks such as FastAPI, Flask, Django and Spring Boot. Each implementation demonstrates best practices and security patterns.

## What is authentication vs. authorization?

### Authentication (AuthN)
**Authentication** is the process of verifying **who you are**. It confirms the identity of a user attempting to access a system.

**Examples:**
- Logging in with username and password.
- Providing a fingerprint or face scan.
- Entering a one-time code from our phone (2FA/MFA).
- Using a social login (Google, Facebook, GitHub).

**Key question:** *"Are you who you claim to be?"*

### Authorization (AuthZ)
**Authorization** is the process of verifying **what you are allowed to do**. Once our identity is confirmed, authorization determines what resources we can access and what actions we can perform.

**Examples:**
- A regular user can view products but cannot delete them.
- A manager can create and edit products.
- An admin can manage all users and products.
- A user can only edit their own profile.

**Key question:** *"What are you allowed to do?"*

### The relationship
Authentication always comes **before** authorization. We must first prove who we are (authentication) before the system can determine what we are allowed to do (authorization).


## Core authentication concepts

### 1. Password-based authentication

**How it works:**
1. User provides credentials (username/email + password).
2. System verifies credentials against stored data.
3. If valid, user is authenticated.

**Security requirements:**
- Never store passwords in plain text.
- Use strong hashing algorithms (bcrypt, Argon2, scrypt).
- Each password gets a unique salt (random string of characters added to a password before hashing it).
- Enforce password complexity requirements.
- Implement password reset functionality.

### 2. Session-based authentication

**How it works:**
1. User logs in with credentials
2. Server creates a session and stores it (in-memory, database or Redis).
3. Server sends session ID to client as a cookie.
4. Client sends cookie with each subsequent request.
5. Server validates session ID to authenticate user.

**Characteristics:**
- Stateful: Server must maintain session data.
- Storage: Sessions stored on server.
- Cookies: Session ID sent via HTTP-only cookies.
- Scalability: Requires session sharing across servers or sticky sessions.

**Pros:**
- Easy to implement.
- Session can be invalidated immediately (logout, security breach).
- Less data sent with each request.

**Cons:**
- Requires server-side storage.
- Difficult to scale horizontally.
- CSRF attacks possible (requires CSRF protection).

**Session-based flow example:**
```
1. User submits login form (username + password)
   ↓
2. Server validates credentials
   ↓
3. Server creates session in database/Redis
   Session: {id: "abc123", user_id: 1, expires: "..."}
   ↓
4. Server sends session ID as cookie
   Set-Cookie: session_id=abc123; HttpOnly; Secure
   ↓
5. Client automatically sends cookie with requests
   Cookie: session_id=abc123
   ↓
6. Server looks up session, retrieves user_id
   ↓
7. Server loads user data and checks permissions
   ↓
8. Server returns response
```

### 3. Token-based authentication (JWT)

**How it works:**
1. User logs in with credentials.
2. Server creates a JWT token containing user info and expiration.
3. Server sends token to client.
4. Client stores token (localStorage, sessionStorage or cookie).
5. Client sends token in authorization header with each request.
6. Server validates and decodes token.

**JWT structure:**
```
Header.Payload.Signature
```

- Header: Token type and hashing algorithm.
- Payload: User data (claims) like user ID, role, expiration.
- Signature: Hash of header + payload + secret key.

**Characteristics:**
- Stateless: No server-side storage needed.
- Self-contained: Token contains all user info.
- Scalable: Works across multiple servers.
- Portable: Can be used across different domains.

**Pros:**
- No server-side storage.
- Scalable horizontally.
- Works for APIs and microservices.
- Can be used across different applications.

**Cons:**
- Cannot be invalidated before expiration (requires blacklist).
- Larger payload sent with each request.
- If secret key is compromised, all tokens are invalid.
- Token size increases with more claims.

**Security best practices:**
- Use strong secret keys.
- Set reasonable expiration times (15 minutes to 1 hour).
- Use refresh tokens for longer sessions.
- Never store sensitive data in JWT payload (it's base64, not encrypted).
- Use HTTPS to prevent token interception.

**JWT token flow example:**
```
1. User submits login form (username + password)
   ↓
2. Server validates credentials
   ↓
3. Server creates JWT token
   Token: {sub: "user@example.com", role: "USER", exp: "..."}
   ↓
4. Server sends token to client
   {access_token: "eyJ...", token_type: "bearer"}
   ↓
5. Client stores token (memory or localStorage)
   ↓
6. Client sends token with requests
   Authorization: Bearer eyJ...
   ↓
7. Server validates and decodes token
   ↓
8. Server gets user info from token payload
   ↓
9. Server checks permissions from token
   ↓
10. Server returns response
```

### 4. OAuth2 and social login
OAuth2 is an authorization framework that enables third-party applications to obtain limited access to a user's resources without exposing credentials.

**Common use cases:**
- "Login with Google".
- "Login with GitHub".
- "Login with Facebook".

**OAuth2 flow (authorization code):**
1. User clicks "Login with Google".
2. App redirects to Google login page.
3. User authenticates with Google.
4. Google redirects back to app with authorization code.
5. App exchanges code for access token.
6. App uses access token to get user info from Google.
7. App creates local user account or logs in existing user.

**Benefits:**
- Users don't need to create new passwords.
- Leverages existing trusted providers.
- Reduces registration friction.

**OAuth2 flow example:**
```
1. User clicks "Login with Google"
   ↓
2. App redirects to Google
   https://accounts.google.com/oauth/authorize?client_id=...
   ↓
3. User logs in to Google
   ↓
4. User authorizes app
   ↓
5. Google redirects back to app with code
   https://yourapp.com/callback?code=AUTHORIZATION_CODE
   ↓
6. App exchanges code for access token
   POST https://oauth2.googleapis.com/token
   ↓
7. App receives access token
   {access_token: "ya29...", expires_in: 3600}
   ↓
8. App requests user info from Google
   GET https://www.googleapis.com/oauth2/v1/userinfo
   Authorization: Bearer ya29...
   ↓
9. App receives user data
   {email: "user@gmail.com", name: "John Doe"}
   ↓
10. App creates or updates local user account
   ↓
11. App logs in user (creates session or JWT)
```

### 5. Multi-factor authentication (MFA/2FA)
Multi-factor authentication requires two or more verification factors:
1. **Something you know:** Password, PIN.
2. **Something you have:** Phone, hardware token, authenticator app.
3. **Something you are:** Fingerprint, face, retina.

**Common 2FA methods:**
- SMS code.
- Authenticator app (Google Authenticator, Authy).
- Email code.
- Hardware security key (YubiKey).

**Implementation flow:**
1. User logs in with password.
2. System generates and sends code to user's phone/email.
3. User enters code.
4. System verifies code.
5. User is authenticated.


## Core authorization concepts

### 1. Role-based access control (RBAC)
RBAC assigns permissions to roles, and users are assigned to roles.

**Structure:**
```
User → Role → Permissions
```

**Example roles:**
- USER: Can view products, update own profile.
- MANAGER: Can create/edit products, view reports.
- ADMIN: Can manage users, delete products, access all features.

**Pros:**
- Simple to understand and implement.
- Easy to manage (assign roles to users).
- Good for most applications.

**Cons:**
- Can become complex with many roles.
- Not granular enough for complex permissions.
- Role explosion (too many specific roles).

### 2. Permission-based access control
Permissions are more granular than roles. Each action has a specific permission.

**Example permissions:**
- `products.create`
- `products.edit`
- `products.delete`
- `users.manage`
- `reports.view`

**Structure:**
```
User → Permissions (directly or through roles)
```

**Pros:**
- Fine-grained control.
- Flexible permission assignment.
- Can combine with roles.

**Cons:**
- More complex to implement.
- More database queries for checks.
- Harder to manage many permissions.

### 3. Resource-based authorization (ownership)
Resource-based authorization checks if the user owns or has rights to a specific resource.

**Examples:**
- User can only edit their own profile.
- User can only delete their own posts.
- User can only view their own orders.

### 4. Attribute-based access control (ABAC)
ABAC uses attributes of the user, resource and environment to make authorization decisions.

**Attributes:**
- User attributes: Role, department, clearance level.
- Resource attributes: Owner, classification, type.
- Environment attributes: Time, location, device.

**Pros:**
- Very flexible and powerful.
- Can handle complex scenarios.
- Dynamic decisions based on context.

**Cons:**
- Complex to implement.
- Harder to debug and maintain.
- Performance overhead.


## Security best practices

### 1. Password security

✅ **DO:**
- Hash passwords with bcrypt, Argon2, or scrypt.
- Use unique salt for each password (automatic with bcrypt).
- Enforce minimum password length (8+ characters).
- Require mix of uppercase, lowercase, numbers, symbols.
- Implement password strength meter.
- Allow long passwords (64+ characters).
- Implement password history (prevent reuse).

❌ **DON'T:**
- Store passwords in plain text.
- Use MD5 or SHA1 for passwords (too fast to crack).
- Use the same salt for all passwords.
- Limit password length unnecessarily.
- Send passwords via email.

### 2. Token security

✅ **DO:**
- Use strong, random secret keys (256-bit minimum).
- Set appropriate expiration times.
- Implement refresh token mechanism.
- Use HTTPS to transmit tokens.
- Store tokens securely on client (HttpOnly cookies for web).
- Implement token rotation.
- Validate all token claims.

❌ **DON'T:**
- Store tokens in localStorage (vulnerable to XSS).
- Use weak secret keys.
- Set very long expiration times.
- Include sensitive data in JWT payload.
- Transmit tokens over HTTP.

### 3. Session security

✅ **DO:**
- Use secure, HTTP-only cookies.
- Set SameSite attribute (Strict or Lax).
- Regenerate session ID after login.
- Implement session timeout.
- Store sessions securely (encrypted if possible).
- Implement CSRF protection.

❌ **DON'T:**
- Use predictable session IDs.
- Store sessions in cookies.
- Allow session fixation attacks.
- Keep sessions alive indefinitely.

### 4. API security

✅ **DO:**
- Require authentication for all sensitive endpoints.
- Use HTTPS for all API calls.
- Implement rate limiting.
- Validate all inputs.
- Return appropriate HTTP status codes (401, 403, 404).
- Log authentication attempts.
- Implement API versioning.

❌ **DON'T:**
- Expose detailed error messages to clients.
- Allow unlimited login attempts.
- Trust client-provided data.
- Return different errors for "user not found" vs "wrong password" (user enumeration).

### 5. General security

✅ **DO:**
- Implement account lockout after failed attempts.
- Use HTTPS everywhere.
- Implement CORS properly.
- Sanitize all inputs (prevent XSS).
- Use parameterized queries (prevent SQL injection).
- Keep dependencies updated.
- Implement security headers (HSTS, CSP, X-Frame-Options).
- Log security events.

❌ **DON'T:**
- Trust user input.
- Expose internal implementation details.
- Use default credentials.
- Disable security features for convenience.