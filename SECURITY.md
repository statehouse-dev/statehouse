# Security Policy

## Reporting Security Vulnerabilities

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in Statehouse, please report it privately:

📧 **Email**: [security@statehouse.dev](mailto:security@statehouse.dev)

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 5 business days
- **Status update**: Weekly until resolved

## Security Scope

Statehouse MVP security considerations:
- Local deployment only (no network exposure by default)
- No built-in authentication/authorization (out of scope for MVP)
- Data at rest protection depends on filesystem permissions
- gRPC TLS support planned but not required for MVP

## Out of Scope for MVP

- Multi-tenancy
- Authentication/Authorization
- Encryption at rest
- Network-level security
- DoS protection

These will be addressed in post-MVP releases.

## Disclosure Policy

We follow **coordinated disclosure**:
1. Report received and acknowledged
2. Vulnerability confirmed and patched
3. Patch released
4. Public disclosure after users have time to upgrade

---

**Note**: This policy will be refined as Statehouse matures toward production readiness.
