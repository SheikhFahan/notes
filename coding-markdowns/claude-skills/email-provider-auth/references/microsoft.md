# Microsoft mail authentication

Entra ID (Azure AD) v2.0, Exchange Online, Outlook.com and Microsoft Graph.
Tags as in `SKILL.md`. Identifiers are placeholders — the live values for an
install live in its own OAuth client config file, never in source or in this
document.

**Contents**

1. Two accounts are involved, and they are not the same thing
2. The app registration — every setting that is not optional
3. Declaring permissions
4. The two OAuth requests
5. Scope re-prefixing
6. Work/school mailboxes — enabling SMTP AUTH
7. Personal mailboxes — what is and is not possible
8. Sending through Graph
9. Probes that write nothing and send nothing
10. The consumer-consent outage, and everything it refuted
11. Documented limits worth knowing

---

## 1. Two accounts are involved, and they are not the same thing

- **The account that owns the client ID** — the app registration.
- **The account being signed in** — the mailbox.

They need different settings and they do not have to be related. One
registration can serve mailboxes anywhere, provided its supported account types
are set correctly (§2). Confusing the two costs a day: the mailbox settings are
in a different portal from the registration settings, and neither portal shows
the other's.

## 2. The app registration — every setting that is not optional

Portal: `https://entra.microsoft.com` → Applications → App registrations → New
registration. The name is free.

**Host it in a real Entra tenant, not a personal Microsoft account.**
`[MEASURED]` A registration created from a personal MSA has no sign-in logs and
no support channel; one inside a work/school tenant has both. `[VENDOR]`
Registrations cannot be moved between tenants — only recreated. `[VENDOR]`
"Apps that are registered by using a Microsoft account can't be publisher
verified." Note the sign-in logs report needs Entra ID P1/P2; a Free tenant can
hold the registration but cannot read the logs (P1 has a 30-day trial).

**Supported account types — this one is not optional.** Choose *"Accounts in
any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and
personal Microsoft accounts (e.g. Skype, Xbox)"*. `[VENDOR]` Pick
single-tenant and personal `@outlook.com` addresses can never sign in. The
value to verify afterwards is `signInAudience ==
AzureADandPersonalMicrosoftAccount`.

**Platform: "Mobile and desktop applications".** Authentication → Add a
platform. Every other choice is wrong, for a different reason:

| Platform | Why not |
|---|---|
| Web | `[VENDOR]` Confidential client — wants a secret, and does not get loopback port-insensitive matching |
| Single-page app | `[VENDOR]` SPA refresh tokens are capped at **24 hours**; a mail client would die every day |
| iOS / macOS | `[VENDOR]` Emits `msauth.<bundle-id>://auth` for MSAL; an HTTP loopback listener is not MSAL |
| Android | Not applicable |

**Redirect URIs — add both**, under that platform, in "Custom redirect URIs":

```
http://localhost/callback
http://127.0.0.1/callback
```

Leave the suggested tick-boxes (`…/oauth2/nativeclient`, `msal<guid>://auth`)
unticked. `[MEASURED]` **The port is ignored by Microsoft's loopback matching;
the path is not.** A URI registered without `/callback` returns
`invalid_request: The provided value for the input parameter 'redirect_uri' is
not valid.` `[VENDOR]` Entra documents port-insensitive matching for hostname
`localhost`; it also recommends the IP literal `127.0.0.1` over `localhost`,
notes that `http` + `127.0.0.1` currently requires the `replyUrlsWithType`
manifest attribute — **adding the URI under the Mobile-and-desktop platform
sets that attribute for you**, which is why §3 says not to hand-edit the
manifest; the two are not in conflict, and hand-editing is how registrations
get into states the portal will not show you — that `[::1]` is not supported, and that
**query parameters are not allowed** in redirect URIs for any registration that
signs in personal Microsoft accounts.

**Allow public client flows.** Authentication → Advanced settings → "Enable
the following mobile and desktop flows" = Yes.

**No client secret, no certificate.** Certificates & secrets must read 0/0/0.
`[VENDOR]` Public clients "must not use secrets or certificates when redeeming
an authorization code."

**Install the client ID** wherever your app reads it from — a config file
outside the repo, or an environment variable. `[RULE]` Changing the client ID
invalidates every stored refresh token, so every Microsoft account must be
re-paired afterwards. Back the file up before editing it.

## 3. Declaring permissions

All permissions go under **Microsoft Graph**, all **Delegated**, even the ones
that are used against `outlook.office.com`:

```
IMAP.AccessAsUser.All      (Graph picker, group named "IMAP")
SMTP.Send                  (Graph picker, group named "SMTP")
Mail.Send                  (needed to send from a personal mailbox)
Mail.Read                  (only if you read mail through Graph)
User.Read                  (only if you call /me or /me/photo)
offline_access
openid
profile
```

`[MEASURED]` **"Office 365 Exchange Online" under "APIs my organization uses"
does NOT publish IMAP or SMTP scopes** — its only `*.AccessAsUser.All` entries
are EAS and EWS. Do not add anything there, and do not edit the manifest by
hand.

`[MEASURED]` "Admin consent required" is **No** for all of these. Do not click
"Grant admin consent" — each user consents for themselves at first sign-in,
which is what keeps the app self-serve.

**Why the names look mismatched.** The app *requests* these with a resource
prefix, because the token endpoint is addressed by resource:

```
https://outlook.office.com/IMAP.AccessAsUser.All
https://outlook.office.com/SMTP.Send
https://graph.microsoft.com/Mail.Send
offline_access openid profile
```

…but the permission *names* are published by Graph. Which API publishes a
permission and which resource a token is minted for are different things.

`[RULE]` **Verify the registration's live state instead of assuming it.** A
delegated permission that was never declared is invisible from the client side:
consent succeeds, a token is issued, and only the API call fails. Read it back
with `GET https://graph.microsoft.com/v1.0/applications?$filter=appId eq
'<YOUR-CLIENT-ID>'`, resolving permission GUIDs against Graph's own service
principal (`servicePrincipals?$filter=appId eq
'00000003-0000-0000-c000-000000000000'&$select=oauth2PermissionScopes`) rather
than hardcoding them. That read needs `Application.Read.All` on the **owning
tenant only**; end users are unaffected. To get such a token, either run your
own authorization-code flow asking for `Application.Read.All` while signed in
as an administrator of the owning tenant, or use Graph Explorer and consent
there. Revoke it afterwards if you do not
want a standing grant (Enterprise applications → your app → Permissions).

## 4. The two OAuth requests

Endpoints, for both classes:

```
https://login.microsoftonline.com/common/oauth2/v2.0/authorize
https://login.microsoftonline.com/common/oauth2/v2.0/token
```

`[VENDOR]` `/common` signs in personal **and** work/school accounts against one
registration.

`authorize` extras: `response_mode=query`. `[VENDOR]` Microsoft documents
`response_mode` as "recommended" and `query` as the default when requesting an
access token — which is what a loopback listener depends on. Sending it makes
the request state what it relies on. There is no `access_type` parameter;
Microsoft's refresh token comes from the `offline_access` scope.

**Work/school request** — two resources, seven scopes:

```
https://outlook.office.com/IMAP.AccessAsUser.All
https://outlook.office.com/SMTP.Send
offline_access openid profile
https://graph.microsoft.com/Mail.Read
https://graph.microsoft.com/User.Read
```

**Personal (MSA) request** — mail plus exactly one Graph scope:

```
https://outlook.office.com/IMAP.AccessAsUser.All
https://outlook.office.com/SMTP.Send
offline_access
https://graph.microsoft.com/Mail.Send
```

Why the consumer request is smaller:

- **No `openid`/`profile`.** Thunderbird sends neither, so there
  is no id_token and the identity line comes from the address the user typed.
- **No Graph mail read.** `[MEASURED 2026-09-19]` A consumer grant has none —
  `GET /me/mailFolders/inbox` answers 403 and `GET /me` answers 401 on the same
  token. Search falls back to a local index.
- **No POP**, although Thunderbird asks for it. `[MEASURED
  2026-09-19]` Microsoft renders `POP.AccessAsUser.All` with wording
  **identical** to the IMAP line, so asking for both prints "Read and write
  access to your email" twice on the live consent screen. If your app has no
  POP client the second line grants nothing and reads as a bug.
- **`Mail.Send` is present** because SMTP is not an option at all (§7).
- **`SMTP.Send` is still present, and that is an open question.** A consumer
  mailbox can never use SMTP, so on this request the scope grants nothing
  usable. It is kept because it predates the Graph send door, because the same
  registration must declare it for work/school addresses, and because removing
  it has never been measured. `[UNVERIFIED]` Whether carrying both `SMTP.Send`
  and `Mail.Send` prints two send lines on the consent screen — if it does, one
  of them is exactly the kind of line that grants nothing and reads as a bug.

`[MEASURED 2026-09-19]` Mixing `outlook.office.com` and `graph.microsoft.com`
scopes in one `/authorize` **works**. It is one consent screen, not two.

`[RULE]` Build the consumer request field by field rather than by spreading
over the business one. Spreading lets a second-resource scope list leak in and
mint a token nobody consented to.

**Refresh leg.** `[VENDOR]` The refresh request "returns a token for the
resource specified in the first scope", so name the resource you want. `[VENDOR]`
"Refresh tokens aren't tied to a resource" — the same refresh token mints the
second-resource token.

`[MEASURED 2026-09-19]` A refresh naming only the two mail scopes echoed back
**all three** consented permissions, `Mail.Send` included. An ordinary mail
refresh does not narrow the grant.

## 5. Scope re-prefixing

`[MEASURED 2026-09-19]` Microsoft re-stamps every consented scope with whatever
resource the request named. The same grant, minutes apart:

```
code  → token   https://outlook.office.com/IMAP.AccessAsUser.All
                https://outlook.office.com/SMTP.Send
                https://outlook.office.com/Mail.Send

refresh → token https://graph.microsoft.com/Mail.Send
                https://graph.microsoft.com/IMAP.AccessAsUser.All
                https://graph.microsoft.com/SMTP.Send
```

`[MEASURED 2026-09-16 and 2026-09-18]` The same effect from the other
direction: a request naming only `graph.microsoft.com/User.Read` plus OIDC
scopes came back carrying every previously-consented permission, all stamped
`graph.microsoft.com/…`; on another day the identical set came back stamped
`outlook.office.com/…`.

**The prefix carries no information.** Match on the last path segment.

```ts
/** The permission NAME in a scope string. Anything that is not an https scope
 *  (offline_access, openid) and any scope whose path is empty
 *  (https://mail.google.com/) keeps its whole string. */
function permissionName(scope: string): string {
  if (!scope.startsWith("https://")) return scope;
  const leaf = scope.slice(scope.lastIndexOf("/") + 1);
  return leaf === "" ? scope : leaf;
}
```

**What breaks without it, and why it is silent.** Each refresh overwrites the
stored scope string with that leg's echo. Match full URIs and the stored
`outlook.office.com/Mail.Send` never equals the wanted
`graph.microsoft.com/Mail.Send`; the narrowing returns nothing; no Graph token
is minted; the resolver falls back to the *mail* token; Graph answers **401**.
Nothing logs an error, and the 401 looks like Microsoft's problem.

## 6. Work/school mailboxes — enabling SMTP AUTH

`[VENDOR]` Microsoft ships SMTP AUTH disabled for every tenant created after
January 2020. Sign-in and IMAP work out of the box; sending does not.

Enable it **per mailbox**, which leaves the tenant default safely off:

```
https://admin.microsoft.com/Adminportal/Home#/users
  → the user → "Mail" tab → "Manage email apps"
  → tick "Authenticated SMTP" → Save
```

Equivalents:

```
https://admin.exchange.microsoft.com/#/mailboxes
  → the mailbox → "Manage email apps settings"

Set-CASMailbox -Identity <upn> -SmtpClientAuthenticationDisabled $false
```

**It is not in `entra.microsoft.com`.** The Entra Users blade has no mail
settings at all. This is the single easiest wrong turn here.

- `[MEASURED 2026-09-18]` Took about 12 minutes to take effect. `[VENDOR]`
  Documented as up to 60.
- `[MEASURED]` Security Defaults did **not** need to be touched. The
  per-mailbox tick alone was sufficient, so tenant-wide MFA stays on. Do not
  disable Security Defaults to fix mail.
- `[MEASURED]` **XOAUTH2 does not bypass this switch.** Modern auth is still
  gated by `SmtpClientAuthenticationDisabled`.

## 7. Personal mailboxes — what is and is not possible

**IMAP.** `[VENDOR]` Outlook.com ships POP & IMAP access off. The switch is
Settings → Mail → Forwarding and IMAP → "Let devices and apps use IMAP".
`[MEASURED 2026-09-15]` **Necessary but not sufficient**: a days-old mailbox
was refused twice with the switch on and accepted in between with nothing
changed. A new mailbox's IMAP access flaps. The refusal looks like
`NO User is authenticated but not connected.` — the token is valid for the mail
resource and the mailbox refused the session.

**Passwords.** `[MEASURED 2026-09-16]` Refused pre-auth on every host (see
`SKILL.md` §2). App passwords do not help — same switch.

**SMTP.** Refused by policy, permanently. The full live string:

```
535 5.7.139 Authentication unsuccessful, SmtpClientAuthentication is disabled
for the Mailbox. Visit https://aka.ms/smtp_auth_disabled for more information.
[<server>.PROD.OUTLOOK.COM <timestamp> <session-id>]
```

What rules out every other explanation, `[MEASURED 2026-09-17]` — one token,
two usernames × two hosts, minutes apart:

| Username | Host | Answer |
|---|---|---|
| the personal mailbox | `smtp-mail.outlook.com:587` | `535 5.7.139 … disabled for the Mailbox` |
| the personal mailbox | `smtp.office365.com:587` | `535 5.7.139 … disabled for the Mailbox` |
| an unrelated address | `smtp-mail.outlook.com:587` | `535 5.7.3 Authentication unsuccessful` |
| an unrelated address | `smtp.office365.com:587` | `535 5.7.3 Authentication unsuccessful` |

`5.7.3` with no policy sentence = the server refuses the **identity**.
`5.7.139` with the policy sentence = the server **resolved** the mailbox,
matched the token to it, and only then refused on policy. **The refusal happens
after successful identification**, which rules out username, alias, host and
credential in one measurement.

Also ruled out `[MEASURED 2026-09-15]`: Thunderbird, under its own
publisher-verified registration, gets the identical 535 on the same
mailbox. `[UNVERIFIED — second-hand]` A third-party bug reporter states they were told
by Microsoft support that SMTP AUTH cannot be manually enabled for an
individual personal mailbox. That is one person's account of a support
conversation, not something Microsoft publishes — it is consistent with the
535 measurements above and it is not independent evidence for them.

Two documentation gaps worth knowing: `aka.ms/smtp_auth_disabled` resolves to a
tenant-admin page that only applies to Exchange Online mailboxes and never
mentions Outlook.com or `5.7.139`; and `5.7.139` is absent from Microsoft's own
SMTP/NDR error reference, whose table skips from `5.7.136`.

`[RULE]` Pair such a mailbox **read-only** rather than refusing the whole
account. Thunderbird does not verify SMTP at setup at all, so its
users get a working mailbox and only the first send fails. Refusing the pairing
because the send leg failed is stricter than Thunderbird and, for this
class of mailbox, strictly worse for the user.

One aside: adding an Outlook.com account to Apple Mail uses **Exchange Web
Services**, not SMTP — its consent asks for "Read and Write Access via Exchange
Web Services", with no `SMTP.Send` and no IMAP. Apple Mail therefore cannot
serve as an SMTP control.

## 8. Sending through Graph

One call. `Mail.Send` authorizes this endpoint and no other.

```
POST https://graph.microsoft.com/v1.0/me/sendMail
Authorization: Bearer <the GRAPH token, never the mail token>
Content-Type: text/plain

<base64 of the whole RFC 5322 message>
```

`[MEASURED 2026-09-19, twice]` → **202 Accepted**, message delivered. The body
is a **single unwrapped base64 run** — no line breaks, no `\r\n` every 76
characters — which is what was measured working; nothing here says a wrapped
body fails, only that it was never tried.
`[VENDOR]` 202 "indicates that the request has been accepted; however, it
doesn't indicate that the request processing has completed."

**Bcc needs no separate channel.** `[MEASURED 2026-09-19]` With To and Bcc both
to controlled addresses: the blind recipient **received** it, and the To
recipient's copy, fetched back over IMAP, carried **no `Bcc:` header**. Those
two observations are the fact. (The obvious reading — Exchange takes the header
as the envelope and then strips it — is a *reading*, not something measured;
nothing here depends on it being the mechanism.) So the whole message goes as
one buffer, built keeping Bcc.

This is why a single call is enough. Thunderbird's three-call flow
(create a draft, PATCH the Bcc recipients on, send by id) exists because Bcc
inside `sendMail`'s MIME is undocumented — but that flow opens with
`POST /me/messages`, which needs `Mail.ReadWrite`, a strictly larger grant.

**Graph files its own Sent copy.** `[MEASURED 2026-09-19]` Found in Sent Items
by Message-ID after a send. `[RULE]` If you also append your own copy, dedupe
by a **pinned** Message-ID — generate it once, before building anything, and
use it in every artifact. Two independent MIME builds each invent their own
random id, and then the dedupe searches for an id the server's copy does not
carry.

`[UNVERIFIED]` How fast Graph files that copy. A search that beats the filing
would produce two copies in Sent.

**So do you still append your own copy?** `[RULE]` Yes, if anything in your app
is derived from the local "this was sent" row — an event, a thread update, a
read receipt. A Message-ID dedupe that searches first returns the **server's**
copy and its uid on a hit, so you get the row either way and never a duplicate.
Replacing the append with a plain folder resync drops whatever that row drives,
and outgoing mail starts arriving through the *received* path. If nothing is
derived from it, a resync is simpler and equally correct.

`[RULE]` **Never retry a non-GET on 429.** The server may have acted on the
first one, and a re-issued send sends twice.

**An account paired before you added `Mail.Send`** consented to mail only, so
no Graph token can be minted and Graph answers 401. The remedy is remove and
re-add, not a silent retry — say so in those words.

## 9. Probes that write nothing and send nothing

**Is the send permission granted?** Post deliberately invalid base64. Graph
authorizes **before** it parses, so a body that cannot be decoded can never
become a message:

```
POST /v1.0/me/sendMail    Content-Type: text/plain    body: !!!not-base64!!!

400 ErrorMimeContentInvalidBase64String  → the scope IS granted
403 ErrorAccessDenied                    → it is not
```

`[MEASURED 2026-09-19 on both verdicts.]`

`[RULE]` Treat **only** those two codes as verdicts. Any other 400 could be
your own malformed request, and reading it as "you may send" would clear a real
block on the strength of your own bug. A **401 on this endpoint** means this
token is not accepted to send — most often the mail token was sent instead of
the Graph token, or the grant predates the scope (see step 1: a 401 on a
*different* endpoint proves much less). Anything else is "could not tell",
which must never be recorded as "the mailbox refuses to send". A 2xx for a body
that is not base64 means something you cannot explain; say so.

**Order the probes so a null result cannot be misread:**

1. `GET /v1.0/me` — informational only, and easy to misread.
   `[MEASURED 2026-09-19]` On a Graph token minted from a consumer grant that
   carries **only** `Mail.Send`, this answers **401** with an empty-message
   `UnknownError` — even though the token is a perfectly good Graph token. So a
   401 here does **not** on its own prove a wrong audience; it proves this
   token is not accepted for *this* endpoint. Read it together with the send
   probe, never instead of it.
2. `GET /v1.0/me/mailFolders/inbox` — **before** the send probe. A 404 or
   `MailboxNotEnabledForRESTAPI` means there is no mailbox Graph can see, and
   the send result is **void**, not negative. `[VENDOR]` That error's documented
   cause is a mailbox on a dedicated Exchange Server rather than a valid
   Microsoft 365 mailbox; the REST API covers Microsoft 365, Hotmail.com,
   Live.com, MSN.com and Outlook.com.
3. The send probe above.
4. `POST /v1.0/me/messages` with the same body — report it, but it is **not**
   the verdict. It tests `Mail.ReadWrite`.

**Is the SMTP refusal policy or credential?** Run one `AUTH XOAUTH2` against
each documented host with the same token and read the enhanced status code
(§7). Two hosts × two usernames is four handshakes and settles it completely.

**What did the grant actually come back as?** Print the `scope` the token
endpoint echoes on both the code leg and the next refresh. That is the only way
to see re-prefixing (§5).

`[RULE]` Every probe should print what it asked for, what came back, and never
a token. Redact the XOAUTH2 blob (`user=<addr>\x01auth=Bearer <token>\x01\x01`)
and the AUTH PLAIN blob (`\0<user>\0<secret>`) explicitly — both are just
base64 and will otherwise appear in a wire log.

## 10. The consumer-consent outage, and everything it refuted

`[MEASURED 2026-09-17/18]` For a period, every consumer sign-in returned a
redirect carrying **only** `error=server_error` and `state` — no
`error_description`, no `error_uri`, no correlation id.

That the channel does carry descriptions when the request is genuinely bad was
proved in the same window: an invalid scope returned
`error=invalid_scope` with `error_description = The provided value for the
input parameter 'scope' is not valid. The scope '…' does not exist.` in 0.5 s.

`[MEASURED]` Where the failure happens: across eight browser runs the request's
`sec-fetch-site` header split perfectly with the outcome. `none` → rejected at
the door with a description, in ~0.5 s. `cross-site` → bare `server_error` in
3.9–27.7 s, i.e. the browser reached the consumer identity service and came
back. **Every descriptionless refusal was emitted on the consumer leg.**

The control pair that localised it, `[MEASURED 2026-09-18 12:36Z]` — same
machine, same browser, same client ID, minutes apart:

```
a work/school account   7 scopes  → token issued, 1.4 s
a personal account      3 scopes  → server_error, 7.3 s
```

The personal account requested **fewer** scopes and still failed. The variable
was the account class.

**Refuted in that window** — each tested and cleared, and each still worth not
re-deriving:

| Claim | How it died |
|---|---|
| Application code | Stashed back to a known-good commit; same failure |
| `response_mode=query` | Failure predates it, reproduces without it |
| The app registration | Four separate registrations, including one created fresh in a real Entra tenant, all identical |
| The scope set | `openid profile offline_access` alone also fails |
| Too many permissions | Thunderbird's exact three scopes, in its exact request shape, with a human clicking Accept: `server_error` |
| One resource per `/authorize` | A Graph-only request with no mail scopes fails identically |
| It is the send/write scope | `Mail.ReadWrite` and a read-only, unrelated scope fail identically |
| `offline_access` | Dropping it changes nothing |
| The registration must declare the scope | Refuted from both directions — an undeclared scope succeeded, a declared one failed |
| Redirect URI / audience | Verified against the portal |
| The browser session | `prompt=login` with re-entered credentials |
| Smart Lockout | Tenant-only, triggered by bad passwords |
| The client ID | Thunderbird's publisher-verified registration fails the same |
| Tenant path, `login_hint`, `prompt`, `form_post`, waiting it out | All eliminated |

⚠ **One entry is unsafe.** "The consumer consent record is the variable" was
recorded as refuted because deleting the grant at
`https://account.live.com/consent/Manage` did not fix anything. Under the
hypothesis being tested — consent *rendering* is broken — deleting the grant
forces consent to render, so failure was the **predicted** outcome. It was
confirming evidence filed as a refutation, and it removed the correct answer
from the hypothesis space for two days. Do not rely on this entry in either
direction.

The outage cleared on its own. `[RULE]` **Never draw a scope conclusion from a
window in which every request fails.** Four conclusions drawn during this one
were later all shown false.

One more measured detail from the same window: the first hop is fine. An
unauthenticated `curl` of `/authorize`, in every variant including
Thunderbird's registration, returns 200 at the door. The refusal is
downstream.

## 11. Documented limits worth knowing

`[VENDOR]`

- Refresh tokens "replace themselves with a fresh token upon every use".
  Lifetime 90 days for non-SPA scenarios; 24 hours for SPA.
- Refresh tokens for public clients are revoked on "Password changed by user".
- Access token default lifetime is "a random value ranging between 60-90
  minutes".
- `AADSTS90094` — a multitenant app registered after 2020-11-08 requesting
  non-basic permissions from users outside its registering tenant hits
  "needs permission to access resources in your organization that only an admin
  can grant".
- `AADSTS70011` — scopes from two resources in one request, on a work account.
- A new Outlook.com account can carry a temporary low sending quota.
- Exchange advertises no `SPECIAL-USE`, no `CONDSTORE` and no `QRESYNC`
  `[MEASURED]`. Resolve special folders by the flags the server does give, and
  never by hardcoded English names.
