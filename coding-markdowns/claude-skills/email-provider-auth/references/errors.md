# Verbatim server strings, and what each one means

Look up the string you actually received. Tags as in `SKILL.md`. Where a string
below is abbreviated with `…`, the part shown is the part that carries the
diagnosis.

**Two rows are not server output**, and are marked *(client-side)*: a wrapper
string your own library produced. They are here because that is what you will
see in your logs, and mistaking one for the server's verdict is a documented
way to send a user chasing the wrong fix.

## SMTP

| String | Means | Do |
|---|---|---|
| `535 5.7.139 Authentication unsuccessful, SmtpClientAuthentication is disabled for the **Mailbox**.` | An explicit per-mailbox block. The server **resolved the mailbox and matched the token to it**, then refused on policy `[MEASURED 2026-09-17]` | Work/school: an admin enables Authenticated SMTP per mailbox. Personal: no lever exists — send through the API instead (`microsoft.md` §7–8) |
| `535 5.7.139 … SmtpClientAuthentication is disabled for the **Tenant**.` | The per-mailbox value is unset and inheriting the tenant default | An admin sets it per mailbox, which leaves the tenant default off (`microsoft.md` §6) |
| `535 5.7.139 … basic authentication is disabled` | A third situation again. `[RULE]` Match on the **sentence**, never on `5.7.139` | Use OAuth |
| `535 5.7.3 Authentication unsuccessful` | **No policy sentence** → the server refused the **identity**, not the policy. A different failure from 5.7.139, and the contrast between the two is what proves a 5.7.139 is not a credential problem `[MEASURED 2026-09-17]` | Check the username actually owns the token |
| `535-5.7.8 Username and Password not accepted.` | `[MEASURED]` Google: wrong, revoked, or account-rather-than-app password | `google.md` |
| `550 5.7.30 Basic authentication is not supported for Client Submission.` | `[VENDOR]` Microsoft's SMTP AUTH deprecation | Use XOAUTH2 |
| `Invalid login: 535 …` *(client-side)* | The SMTP library's own prefix, not the server's. `[RULE]` Classify the **policy** sentence before any credential regex, or a policy refusal is reported as a bad password | — |

## IMAP

| String | Means | Do |
|---|---|---|
| `* CAPABILITY … AUTH=XOAUTH2 LOGINDISABLED …` | No password mechanism is offered at all `[MEASURED 2026-09-13]` | Hide the password field. Do **not** suggest an app password |
| `NO Basic authentication is disabled.` | Answered to `LOGIN` and to `AUTHENTICATE PLAIN` **before any account lookup** `[MEASURED 2026-09-16]` — so it is not about this account | OAuth is the only way in |
| `NO User is authenticated but not connected.` | The token is **valid** for the mail resource; the mailbox refused the session. On a new Outlook.com mailbox, IMAP access flaps `[MEASURED 2026-09-15]` | Check Settings → Mail → Forwarding and IMAP. Necessary but not sufficient — wait and retry (`microsoft.md` §7) |
| `NO [AUTHENTICATIONFAILED] Invalid credentials (Failure)` | The credential is wrong, revoked, or for another account | Distinguish account password from app password by shape, then advise (`google.md`) |
| `NO [ALERT] Application-specific password required: https://support.google.com/accounts/answer/185833` | The account password was used | Quote it and add **nothing** — the provider's own instruction beats yours |
| `NO Incorrect username, password or access token.` | `[MEASURED 2026-09-14]` Fastmail's generic refusal | — |
| `NO LOGIN failed.` | Microsoft's answer to a real app password on a real account `[VENDOR]` | Basic auth is gone; use OAuth |
| `Command failed` **and nothing else** *(client-side)* | `[MEASURED]` The IMAP library's generic wrapper for every tagged NO/BAD. The server's real sentence is on another field | Read `responseText` (`implementation.md` §11) |

## TLS and network

| String | Means | Do |
|---|---|---|
| `Cert does not contain a DNS name` / `ERR_TLS_CERT_ALTNAME_INVALID`, with **no server output at all** in the dialogue | **Not a certificate problem.** A Happy Eyeballs misfire ran the identity check on a socket that never connected `[MEASURED 2026-09-14]` | `app-password-providers.md`. Connect one address at a time. Never disable verification |
| `getaddrinfo ENOTFOUND` / `EAI_AGAIN` | `[VENDOR]` The server name could not be resolved | Distinguish from "unsupported provider" — this is retryable |
| `connect ECONNREFUSED` | `[VENDOR]` Wrong port, or the service is down | — |
| `self signed certificate in chain` | `[VENDOR]` A genuine verification failure — often a corporate MITM proxy | Do **not** attach app-password advice to this |

## OAuth — authorize and token endpoints

| String | Means | Do |
|---|---|---|
| `invalid_grant` | `[VENDOR]` Revoked by the user, or a short-lived (7-day, Google Testing) refresh token lapsed | Send the human back through consent. **Never retry** — it is an infinite loop |
| `invalid_request: The provided value for the input parameter 'redirect_uri' is not valid.` | The registered URI's **path** does not match. The **port** is ignored `[MEASURED]` | Register both `http://localhost/callback` and `http://127.0.0.1/callback` |
| `invalid_scope: … The scope '…' does not exist.` | A typo'd or non-existent permission | Also useful as a **calibration probe**: it proves the error channel does carry descriptions |
| `AADSTS28000: … scope is not valid because it contains more than one resource.` | Multi-resource at the **token** endpoint. Legal at `/authorize`, illegal at `/token` | Redeem per resource (`implementation.md` §5) |
| `AADSTS65001` / `consent_required` / `DelegationDoesNotExist` | `[VENDOR]` No delegated grant exists for this user+resource yet | Send an interactive authorization request. On an admin-only permission, this is the admin-consent wall |
| `AADSTS90094: … needs permission to access resources in your organization that only an admin can grant.` | `[VENDOR]` A multitenant app registered after 2020-11-08 requesting non-basic permissions from outside its own tenant | Pick permissions that are not admin-consent-required |
| `AADSTS70011` | `[VENDOR]` Two resources in one request, on a work account | As AADSTS28000 |
| `AADSTS70012: MsaServerError - A server error occurred.` | The closest **named** code to a bare consumer-side failure. `[UNVERIFIED]` Whether a descriptionless `server_error` is this code — no `error_codes` is returned with it | — |
| `error=server_error` with **no `error_description` at all** | `[MEASURED 2026-09-17/18]` Emitted on the consumer identity leg, 3.9–27.7 s in. Nothing on your side is the cause | Run a work-account control. Do **not** draw scope conclusions while this is happening (`microsoft.md` §10) |

`[RULE]` Read every redirect field before answering the request — the query
string is gone afterwards, and `AADSTS` numbers live only inside
`error_description` (`implementation.md` §3).

## Microsoft Graph

| Code | Status | Means | Do |
|---|---|---|---|
| `ErrorAccessDenied` | 403 | The permission is **not** granted **for this endpoint** `[MEASURED 2026-09-19]` | Work the ladder in `microsoft.md` §9 in order. Confirm the mailbox is not 404 first, and check which endpoint the scope actually authorizes — `Mail.Send` covers `/me/sendMail` and nothing else. `[MEASURED 2026-09-19]` A 403 on `GET /me/mailFolders/inbox` is *expected* on a consumer grant and is not the send verdict |
| `ErrorMimeContentInvalidBase64String` | 400 | Graph **authorized** the call and then failed to parse the body. On a deliberately invalid probe body this is the **pass** condition `[MEASURED 2026-09-19]` | `microsoft.md` §9 |
| `MailboxNotEnabledForRESTAPI` | 404 | `[VENDOR]` There is **no mailbox Graph can see** — documented cause is a mailbox on a dedicated Exchange Server rather than a valid Microsoft 365 mailbox | Any send verdict from this account is **void**, not negative. Fix the mailbox or the licence first |
| `UnknownError` with an empty message | 401 | This token is not accepted for **this endpoint**. Either you sent the mail token instead of the API token, or the grant lacks the scope this endpoint needs. `[MEASURED 2026-09-19]` A valid Graph token holding only `Mail.Send` answers exactly this on `GET /me` | Do not read it as "the token is bad". Check scope matching (`implementation.md` §6) and confirm against an endpoint the grant *does* cover. On an account paired before the scope existed: remove and re-add |
| — | 429 | Throttled | `[RULE]` Retry a GET; **never** re-issue a send. The server may have acted on the first one |
| — | 202 | Accepted. `[VENDOR]` "doesn't indicate that the request processing has completed" | Do not treat as delivery confirmation |

## Two verdicts that are not errors, and must not be recorded as failures

- **A timeout, or any status you did not plan for.** "Could not tell" is its
  own outcome. Recording it as "the mailbox refuses to send" clears or sets a
  real flag on the strength of a network hiccup.
- **A 403 from an account with no mailbox.** `[MEASURED 2026-09-19]` An account
  without an Exchange Online licence answers 403 to everything. Always confirm
  the mailbox is visible before concluding anything about a permission.
