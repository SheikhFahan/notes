---
name: email-provider-auth
description: Use when a task touches email account sign-in or a mail provider — IMAP or SMTP connections, OAuth scopes or consent screens, app passwords, refresh tokens or XOAUTH2 for Microsoft (Outlook.com, Hotmail, Live, Microsoft 365), Gmail or Google Workspace, iCloud, Fastmail or Yahoo — including adding or changing a provider, or a mail account reporting "cannot send", "wrong password", 535 5.7.139, an AADSTS error, invalid_grant, or a TLS certificate error on connect. Use before planning, not after the first failure, and even when the user never says "authentication".
---

# Email provider authentication

Everything here was measured against a live server, published by the provider,
or is a design rule stated with the measured consequence of breaking it.
Nothing is inferred. Claims carry a tag:

| Tag | Means |
|---|---|
| `[MEASURED <date>]` | Someone ran it and read the answer. A bare `[MEASURED]` means the run happened and the date was not written down. |
| `[VENDOR]` | The provider publishes it. |
| `[RULE]` | A design rule, with the measured consequence of breaking it. |
| `[UNVERIFIED]` | Believed, never tested. Treat as a question, not a fact. |

If you need a fact that is not here, measure it and add it with a tag. Do not
fill the gap from memory — every expensive mistake in these files started as a
reasonable-sounding assumption.

> **These facts have dates, and providers change.** Most `[MEASURED]` facts are
> from September 2026. If a result here disagrees with what you observe, trust
> your observation and re-run the probe the section describes — the
> measurement technique is what does not go stale.

## Load only what the task needs

**By provider or symptom:**

| The task involves | Read |
|---|---|
| Microsoft — an Outlook.com/Hotmail/Live/MSN address, or any domain whose MX is Microsoft | `references/microsoft.md`, starting at §0 |
| Gmail or Google Workspace | `references/google.md` |
| iCloud, Fastmail, Yahoo — or any TLS-looking pairing failure | `references/app-password-providers.md`. **Not** Microsoft app passwords: those are §2 here and `microsoft.md` §7 |
| Writing the client — or diagnosing a silent 401 or a stale "cannot send" marker | `references/implementation.md` |
| A verbatim server string | `references/errors.md` |
| A client running on Node or Bun | `references/runtime-node.md`, alongside the above |

**By client type.** The flow in `implementation.md` is for a **desktop or
native client** — a public OAuth client that cannot keep a secret, redirecting
to loopback.

| Client | What applies |
|---|---|
| Desktop / native app | Everything. |
| CLI with a browser to hand | Same as desktop — the loopback flow works. `[UNVERIFIED]` Headless / device-code sign-in: not covered. |
| Web server (confidential client), server-side integration | Provider facts, scopes, consent lines, server errors and transport rules all hold; the flow in `implementation.md` does not — you use a different redirect and a different client type. Microsoft's "Web" platform is a confidential client that wants a secret and does not get port-insensitive loopback matching `[VENDOR]` (`microsoft.md` §2). |
| Single-page app | Microsoft SPA refresh tokens are capped at **24 hours** `[VENDOR]` — a mail client would die every day. |
| iOS / macOS using MSAL | Microsoft emits `msauth.<bundle-id>://auth` `[VENDOR]`; an HTTP loopback listener is not MSAL. |
| Delegated access to *someone else's* mailbox; Google client types other than Desktop | Not covered. Vendor facts hold; the flow does not. |

**By language.** None required. Everything outside `implementation.md` and
`runtime-node.md` is protocol, portal and server fact — the same in Python, Go,
Rust, Java, C# or anything else. `implementation.md` snippets are TypeScript for
illustration; each says what is protocol and what is a runtime detail to
translate. The portal and permission sections need no codebase at all.

**Thunderbird is the control**, and it is worth setting up before you need it:
a mature, publisher-verified mail client you can point at the same mailbox to
see whether a refusal is yours or the provider's. Several "this must be a bug
in the client" theories died that way, in minutes. `[RULE]` Compare against it;
never ship under it — running under another vendor's client registration is
impersonation.

---

## 1. Resolve the address before anything else

`[RULE]` Provider identity comes from **MX records**, not from the domain name.
A Workspace or Microsoft 365 domain looks like any other domain; only its MX
says who hosts it. Domains the provider itself owns short-circuit the lookup —
Microsoft's is an **exact-match table, not a glob** (`microsoft.md` §0).

`[RULE]` **Fail closed on an unrecognised domain.** Inventing `imap.<domain>`
sends the user's password to a host you guessed. And distinguish "this domain
has no MX" (a verdict — `ENOTFOUND`, `ENODATA`) from "the lookup did not
answer" (a timeout, retryable). Reporting a DNS timeout as "your domain is not
hosted by a supported provider" states something about the user's domain that
was never established, and leaves them nothing to do.

`[RULE]` Time-box the MX lookup (a few seconds). Onboarding must not stall on
a slow or blocked resolver.

`[VENDOR]` Sort MX records by priority ascending; the lowest number is the
primary exchange, and it decides.

## 2. The five providers

| Provider | IMAP | SMTP | Password works? | OAuth? | Sends via |
|---|---|---|---|---|---|
| Google | `imap.gmail.com:993` TLS | `smtp.gmail.com:465` TLS | App password only | Yes | SMTP |
| Microsoft work/school | `outlook.office365.com:993` TLS | `smtp.office365.com:587` STARTTLS | **No** | Yes | SMTP, after an admin enables it |
| Microsoft personal | `outlook.office365.com:993` TLS | `smtp-mail.outlook.com:587` STARTTLS | **No** | Yes | **Graph `POST /me/sendMail`** — SMTP is refused forever |
| iCloud | `imap.mail.me.com:993` TLS | `smtp.mail.me.com:587` STARTTLS | App password only | No | SMTP |
| Fastmail | `imap.fastmail.com:993` TLS | `smtp.fastmail.com:465` TLS | App password only | No | SMTP |
| Yahoo | `imap.mail.yahoo.com:993` TLS | `smtp.mail.yahoo.com:465` TLS | App password only | No | SMTP |

Hosts and ports are `[VENDOR]`. The "password works?" column is `[MEASURED]`
from pre-auth capability probes — see below.

**You can settle "does a password work here?" in thirty seconds with no
account.** Open the IMAP port with `openssl s_client` and read the greeting:

```
openssl s_client -connect imap.gmail.com:993 -crlf -quiet
```

What the probes returned: Microsoft advertises no password mechanism and
refuses `LOGIN` before any account lookup (`microsoft.md` §7); Gmail advertises
`AUTH=PLAIN` (`google.md`).

`[RULE]` Where a provider offers no password mechanism, do not show a password
field, do not run a password probe, and **never** show an "app password"
hint — an app password is basic authentication and is refused by the same
switch. `[VENDOR]` Microsoft: "The deprecation of basic authentication also
prevents the use of app passwords."

## 3. Microsoft in brief

Microsoft is where most of the difficulty is. Both of its mailbox classes share
**one IMAP host**, so only the address tells them apart. A **personal** mailbox
(Outlook.com, Hotmail, Live, MSN) is refused SMTP permanently — it sends through
Graph `POST /me/sendMail` with `Mail.Send`. A **work/school** mailbox has SMTP
AUTH off by default and an admin enables it per mailbox. Neither takes a
password or an app password. Read `microsoft.md` §0 before planning anything
Microsoft: the exact consumer-domain table, the fork, and seven Microsoft-only
traps (scope re-prefixing, `Mail.Send` ≠ `/me/messages`, the two `535 5.7.139`
endings, one resource per token request, the two SMTP hosts, the mailbox-less
403, refresh-token rotation).

## 4. Traps that apply to every provider

Each of these cost real time. Cause, then symptom.

1. **A native app is a public client, so the secret is not the boundary.**
   `[VENDOR]` Microsoft: public clients "must not use secrets or certificates
   when redeeming an authorization code." Google's Desktop client type issues a
   secret and its token endpoint requires it. Either way the value ships inside
   the binary and is readable from any copy. → PKCE S256 is what actually
   secures the flow. Never ship `plain`.

2. **A TLS error can mean the connection never happened.** The universal rule:
   a certificate failure reported with **zero bytes received from the server**
   is not a certificate failure. Any runtime that races two addresses (Happy
   Eyeballs, RFC 8305) can abandon an attempt and still run the identity check
   on the dead socket. → Read the wire log before the error text, and make your
   check distinguish "no certificate arrived" from "the certificate failed".
   `[MEASURED 2026-09-14]` iCloud and Fastmail hit it; Gmail, Yahoo and Outlook
   did not. Evidence and fix: `app-password-providers.md`; the Bun instance and
   Node code: `runtime-node.md` §1.

3. **Find where your IMAP library puts the server's sentence, before you write
   any error handling.** Libraries commonly raise one generic "command failed"
   for every tagged `NO`/`BAD` and put the server's actual words on a secondary
   field (Node libraries: `runtime-node.md` §2). → Read only the exception's
   main message and a mistyped app password, a revoked one, and
   "application-specific password required" all look identical. Quote the
   server; never paraphrase it.

4. **A missing refresh token is a broken account an hour later.** `[RULE]`
   If the code exchange returns no refresh token, fail the pairing now with
   "revoke this app's access and sign in again" rather than accepting an
   account that dies by lunchtime.

## 5. Diagnostic discipline

Four rules, each of which was learned the expensive way.

- **Probe the endpoint the scope under test actually covers.** See
  `microsoft.md` trap 2.
- **Always run a known-good control before blaming the provider.** A work
  account beside a personal one, or another vendor's registration beside yours,
  turns "this is broken" into "this is broken *for this class of account*" —
  which is a different, findable problem.
- **Never draw a scope conclusion from a window in which every request fails.**
  Four conclusions drawn during one such outage were later all false
  (`microsoft.md` §10).
- **Check the sign of your evidence.** Before recording a refutation, state
  what the hypothesis predicts and check that your result contradicts it. A
  confirming result filed as a refutation once removed the correct answer from
  the hypothesis space for two days (`microsoft.md` §10, the unsafe entry).

Run every interactive OAuth probe from a **private browser window**.
`login_hint` only suggests an account; a multi-login browser session silently
authenticates someone else and has caused more confusion here than any other
single factor.

## 6. Plan-mode pre-flight

Answer all eight before writing a plan. Each has a cheap source.

| # | Question | How to answer it |
|---|---|---|
| 1 | Consumer or business address? | Provider-owned domain list (`microsoft.md` §0), else MX |
| 2 | Does this provider take a password at all? | Pre-auth capability probe (§2) — no account needed |
| 3 | How many OAuth resources do I need? | One per API host in the scope list. Each extra resource is a second token, not a second sign-in |
| 4 | Which endpoint does each scope authorize? | `microsoft.md` §3, `google.md`. Assume nothing from the permission's name |
| 5 | Does the registration / console project actually declare them? | Read it back from the provider's API or portal. Do not assume it matches your notes |
| 6 | Which door sends for this mailbox class? | §2 and §3 here; `microsoft.md` §0 |
| 7 | What does the refresh leg do to the stored scope string? | It overwrites it, re-prefixed (`microsoft.md` trap 1). Plan the matching rule accordingly |
| 8 | What is my known-good control? | Name it before you start, not after the first surprise |

If you cannot answer one of these, the answer is a measurement, not a guess —
and it usually takes minutes. `microsoft.md` and `google.md` list the probes
that answer 2, 4 and 5 without sending mail or storing anything.

## 7. Refuted — do not re-derive these

Microsoft hypotheses already tested and cleared — wrong SMTP host, client ID,
alias username, too many permissions, `offline_access`, the registration, one
resource per `/authorize`, and more — are in `microsoft.md` §10. Read its
caveat first: most were measured during an outage window, and one entry is
marked unsafe.

## 8. Unverified

Open questions sit beside the facts they qualify, tagged `[UNVERIFIED]`:
Microsoft's in `microsoft.md` §12, Google app-password pairing end to end at
the end of `google.md`, and whether the SMTP leg hits the Happy Eyeballs
misfire in `app-password-providers.md` ("Where it goes").
