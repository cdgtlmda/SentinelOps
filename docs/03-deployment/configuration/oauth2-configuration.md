# OAuth2 Configuration Guide

## Overview

SentinelOps implements OAuth2 with JWKS (JSON Web Key Set) verification for secure authentication. This guide covers the configuration requirements and implementation details.

## Configuration Requirements

### Environment Variables

Set the following environment variables for OAuth2:

```bash
# OAuth2 Provider Configuration
OAUTH2_CLIENT_ID=your-client-id
OAUTH2_CLIENT_SECRET=your-client-secret
OAUTH2_AUTHORIZATION_ENDPOINT=https://provider.com/oauth2/authorize
OAUTH2_TOKEN_ENDPOINT=https://provider.com/oauth2/token
OAUTH2_JWKS_URL=https://provider.com/.well-known/jwks.json
OAUTH2_ISSUER=https://provider.com
OAUTH2_SCOPES=openid profile email

# Optional: Token validation settings
OAUTH2_VERIFY_SIGNATURE=true
OAUTH2_VERIFY_EXPIRATION=true
OAUTH2_VERIFY_ISSUER=true
OAUTH2_VERIFY_AUDIENCE=true
```

## JWKS Verification Implementation

### Key Features

1. **Automatic Key Extraction**: Extracts signing keys from JWKS based on `kid` (Key ID)
2. **RSA Support**: Supports RSA keys with proper base64url decoding
3. **Key Caching**: Caches parsed keys and JWKS responses for performance
4. **Signature Verification**: Verifies JWT signatures using the correct public key

### How It Works

1. **Token Reception**: Client sends JWT in Authorization header
2. **Header Parsing**: Extract `kid` from JWT header
3. **JWKS Fetch**: Retrieve JWKS from provider (with caching)
4. **Key Extraction**: Find matching key by `kid` and extract RSA components
5. **Verification**: Verify JWT signature with extracted public key

### Code Flow

```python
# src/api/oauth2.py
async def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
    # Get JWKS
    jwks = await self._get_jwks()
    
    # Extract kid from token header
    unverified_header = jwt.get_unverified_header(id_token)
    kid = unverified_header.get("kid")
    
    # Get signing key for this kid
    signing_key = await self._get_signing_key(kid, jwks)    
    # Verify and decode token
    payload = jwt.decode(
        id_token,
        signing_key,
        algorithms=["RS256"],
        issuer=self.config.issuer,
        audience=self.config.client_id
    )
    
    return payload
```

## Supported OAuth2 Providers

The implementation works with any OAuth2 provider that:
- Provides a JWKS endpoint
- Uses RSA keys for signing
- Includes `kid` in JWT headers

### Tested Providers

- Google Identity Platform
- Auth0
- Okta
- Azure AD
- AWS Cognito

## Security Considerations

1. **JWKS Caching**: JWKS is cached for 1 hour to reduce latency
2. **HTTPS Only**: All OAuth2 endpoints must use HTTPS
3. **Token Expiration**: Tokens are validated for expiration
4. **Audience Verification**: Ensures tokens are for this application

## Troubleshooting

### Common Issues

1. **"No kid found in token header"**
   - Provider may not include kid in tokens
   - Check provider documentation for JWKS support

2. **"No signing key found for kid"**
   - JWKS may be out of sync
   - Clear cache and retry

3. **"Token signature verification failed"**
   - Ensure JWKS_URL is correct
   - Verify token hasn't been tampered with

### Debug Mode

Enable debug logging for OAuth2:

```python
# Set in logging configuration
logging.getLogger("src.api.oauth2").setLevel(logging.DEBUG)
```

## Testing

Run OAuth2 tests:

```bash
pytest tests/unit/oauth2/test_oauth2_jwks.py -v
```

The tests verify:
- JWKS key extraction
- Signature verification
- Caching behavior
- Error handling
