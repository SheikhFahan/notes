---
name: email-provider-auth
description: Measured facts for authenticating email accounts — IMAP, SMTP, OAuth and app passwords for Microsoft (work and personal), Google, iCloud, Fastmail and Yahoo. Exact scope strings, the app-registration and cloud-console click-paths, which endpoint each permission actually authorizes, verbatim server errors and what each one means, and how to write the client. Use this whenever the task touches mail sign-in, IMAP or SMTP connections, OAuth scopes or consent screens, app passwords, refresh tokens, a "cannot send" or "wrong password" report on a mail account, or adding or changing a mail provider — including when the user never says the word "authentication". Read it BEFORE planning, not after the first failure: most of what is here is only discoverable by measurement that costs days.
---

# Email provider authentication

Everything here was either measured against a live server, published by the
provider, or is a design rule stated with the measured consequence of breaking
it. Nothing is inferred. Claims carry a tag:

| Tag | Means |
|---|---|
| `[MEASURED <date>]` | Someone ran it and read the answer. Dated wherever the date is on record; a bare `[MEASURED]` means the run happened and the date was not written down. |
| `[VENDOR]` | The provider publishes it. |
| `[RULE]` | A design rule, with the measured consequence of breaking it. |
| `[UNVERIFIED]` | Believed, never tested. Treat as a question, not a fact. |

If you need a fact that is not here, measure it and add it with a tag. Do not
fill the gap from memory — every expensive mistake below started as a
reasonable-sounding assumption.

> **These facts have dates, and providers change.** Everything marked
> `[MEASURED]` was true on the date beside it — most of it September 2026.
> Portal layouts get redesigned, scopes get deprecated, policies get reversed.
> The **measurement technique** beside each fact is what does not go stale: if
> a result here disagrees with what you observe, trust your observation, and
> re-run the probe the section describes rather than assuming either of you is
> confused. A fact that has aged out is still useful as a thing to re-test.

## What this covers, and what it assumes

**Scope:** signing a user's own mailbox into a **desktop or native mail
client** — a public OAuth client that cannot keep a secret, redirecting to
loopback. If you are building a server-side integration, a web app with a
confidential client, or delegated access to *someone else's* mailbox, the
vendor facts still hold but the flow in `references/implementation.md` does
not: you would use a different redirect and a different client type.

**Language and stack:** none required. Sections 1–9 here, and
`microsoft.md`, `google.md`, `app-password-providers.md` and `errors.md`, are
protocol, portal and server facts — they are the same in Python, Go, Rust,
Java, C# or anything else. `implementation.md` carries illustrative snippets in
TypeScript because they have to be in *some* language; each one says what is
protocol (portable) and what is a library or runtime detail (translate it). You
need no particular library, runtime or project layout, and you do not need a
codebase at all to use the portal and permission sections.

**Thunderbird is used throughout as a control**, and it is worth setting up
before you need it: a mature, publisher-verified mail client you can point at
the same mailbox to see whether a refusal is yours or the provider's. Several
"this must be a bug in the client" theories below died that way, in minutes.
`[RULE]` Compare against it; never ship under it — running under another
vendor's client registration is impersonation.

## Read these when you need them

| File | Open it when |
|---|---|
| `references/microsoft.md` | Anything Microsoft: registration, scopes, personal vs work, Graph sending, consent failures |
| `references/google.md` | Gmail or Workspace: console setup, the restricted scope, app passwords |
| `references/app-password-providers.md` | iCloud, Fastmail, Yahoo — and any TLS-looking pairing failure. **Not** Microsoft app passwords: those are §2 here and `microsoft.md` §7 |
| `references/implementation.md` | You are about to write code — **and** when diagnosing a silent 401, a stale "cannot send" marker, or a duplicated Sent copy |
| `references/errors.md` | You have a verbatim server string and need its meaning |

---

## 1. Resolve the address before anything else

`[RULE]` Provider identity comes from **MX records**, not from the domain name.
A Workspace or Microsoft 365 domain looks like any other domain; only its MX
says who hosts it. Domains the provider itself owns short-circuit the lookup —
see the exact list in §3, which is an **exact-match table, not a glob**.

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

`[MEASURED 2026-09-13]` `outlook.office365.com:993` greets with
`AUTH=XOAUTH2 LOGINDISABLED` and advertises no password mechanism.
`[MEASURED 2026-09-16]` both `outlook.office365.com:993` and
`imap-mail.outlook.com:993` answer `LOGIN` **and** `AUTHENTICATE PLAIN` with
`NO Basic authentication is disabled.` — before any account is looked up, so
the answer does not depend on having credentials.
`[MEASURED 2026-09-14]` `imap.gmail.com:993` advertises `AUTH=PLAIN` and
`smtp.gmail.com:465` advertises `AUTH LOGIN PLAIN`.

`[RULE]` Where a provider offers no password mechanism, do not show a password
field, do not run a password probe, and **never** show an "app password"
hint — an app password is basic authentication and is refused by the same
switch. `[VENDOR]` Microsoft: "The deprecation of basic authentication also
prevents the use of app passwords."

## 3. The Microsoft fork — this is the whole difficulty

Both Microsoft classes share **one IMAP host**. The host therefore cannot tell
them apart; the address can. Consumer domains are `outlook.com`, `hotmail.*`,
`live.*`, `msn.com`. Anything else Microsoft-hosted (decided by MX) is
work/school.

**The consumer domain list is exact, not a pattern.** `hotmail.co.uk` is a
separate entry from `hotmail.com`; a glob like `hotmail.*` will be implemented
three different ways and get two-label TLDs wrong.

```
outlook.com   hotmail.com   hotmail.co.uk   live.com   msn.com
```

`[UNVERIFIED]` That list is not exhaustive — `hotmail.fr`, `live.co.uk` and
other national variants exist and are **not** in it. Widening it also moves
SMTP host selection, so measure before adding.

`[RULE]` **Both classes use the same IMAP host.** Do not split IMAP hosts the
way the SMTP hosts split (trap 8). If a send-door check keys on the IMAP host
and a consumer account was paired on a different one, the check silently
returns false and the account loses its only way to send, with no error
anywhere.

|  | Work / school | Personal (MSA) |
|---|---|---|
| Sign-in | OAuth, `/common` authority `[VENDOR]` | OAuth, `/common` authority `[VENDOR]` |
| IMAP | Works | Works, once the mailbox's IMAP toggle is on `[MEASURED 2026-09-15]` |
| SMTP AUTH | Disabled by default since Jan 2020; **an admin enables it per mailbox** | **Refused permanently. No lever exists.** |
| Sending | SMTP | Graph `POST /me/sendMail` |
| Graph mail read | Available with `Mail.Read` | `[MEASURED 2026-09-19]` A consumer grant has none: `GET /me/mailFolders/inbox` → 403 |

`[MEASURED 2026-09-14/15/17]` A personal mailbox answers
`535 5.7.139 Authentication unsuccessful, SmtpClientAuthentication is disabled
for the Mailbox.` on **both** documented SMTP hosts, with a token IMAP had
accepted seconds earlier, and reproduces identically under a different vendor's
publisher-verified client ID. Host, client, scopes and credential are all ruled
out by that one measurement. `[VENDOR]` Microsoft support told a third-party
reporter they cannot enable SMTP AUTH for an individual personal mailbox.

Details, click-paths and the Graph send contract: `references/microsoft.md`.

## 4. Permissions

Microsoft, requested with a **resource prefix** even though the permission
*names* are published by Graph:

| Scope string | Authorizes | Consent line |
|---|---|---|
| `https://outlook.office.com/IMAP.AccessAsUser.All` | IMAP | "Read and write access to your email … Does not include permission to send mail." `[MEASURED 2026-09-19]` |
| `https://outlook.office.com/SMTP.Send` | SMTP AUTH | "Access to sending emails from your mailbox" `[MEASURED 2026-09-15]` |
| `https://outlook.office.com/POP.AccessAsUser.All` | POP | **Word-for-word identical to the IMAP line** `[MEASURED 2026-09-19]` — asking for both prints the same sentence twice and reads as a bug |
| `https://graph.microsoft.com/Mail.Send` | **Only** `POST /me/sendMail` | "Send email as you" `[MEASURED 2026-09-19]` |
| `https://graph.microsoft.com/Mail.Read` | Graph mail read `[VENDOR]` | |
| `https://graph.microsoft.com/User.Read` | `GET /me`, `/me/photo` `[VENDOR]` | |
| `offline_access` | Issues a refresh token | "Maintain access to data you have given the app access to" `[MEASURED 2026-09-15]` |
| `openid`, `profile` | Puts `name` in the id_token `[VENDOR]` | |

`[MEASURED 2026-09-19]` None of these showed "Admin consent required: Yes" in
the portal, and consumer users consented for themselves. `[UNVERIFIED]` Whether
every work/school tenant agrees: `[VENDOR]` `AADSTS90094` describes an admin
wall for a multitenant app registered after 2020-11-08 requesting "non-basic"
permissions from users outside its registering tenant, and whether `Mail.Send`
counts as non-basic there is not established.

**An open question about `SMTP.Send` on a consumer request.** A personal
mailbox can never use SMTP (§3), so on the face of it the scope grants nothing.
It is kept because it predates the Graph send door and because removing it has
not been measured — see §9. Do not remove it casually: it is also what a
work/school address on the same registration needs.

`[MEASURED 2026-09-19]` **`Mail.Send` authorizes exactly one endpoint.** On a
grant holding `Mail.Send`, with a readable mailbox, `POST /me/sendMail`
answers 202 and `POST /me/messages` answers 403 `ErrorAccessDenied` —
`/me/messages` needs `Mail.ReadWrite`, which is a different permission. A
draft-then-send flow therefore needs a strictly larger grant than a single
send does.

Google: `https://mail.google.com/` (IMAP, POP and SMTP in one scope), plus
`openid` and `profile` for the owner's name and picture. There is no separate
API scope — the mail token is the API token.
See `references/google.md` for what the restricted classification costs.

## 5. The traps

Each of these cost real time. Cause, then symptom.

1. **Scope re-prefixing.** `[MEASURED 2026-09-19]` Microsoft re-stamps every
   consented scope with whatever resource the *request* named. One grant came
   back as `https://outlook.office.com/Mail.Send` on the code leg and
   `https://graph.microsoft.com/Mail.Send` on the very next refresh. → Match
   scopes on the **permission name** (the last path segment), never the full
   URI. Exact matching loses a real grant, so the second-resource token stops
   being minted, the wrong token goes to the API, and you get a silent 401 that
   looks like the provider's fault.

2. **`Mail.Send` ≠ `/me/messages`.** → Every 403 you measure against the wrong
   endpoint is evidence about a permission you never asked for. Probe the
   endpoint the scope under test actually covers.

3. **`535 5.7.139` has two endings and the last word is the diagnosis.**
   "…disabled for the **Tenant**" means the per-mailbox value is unset and
   inheriting a tenant default — an admin fixes it. "…disabled for the
   **Mailbox**" is an explicit per-mailbox block, and on a consumer account no
   lever exists. → Match on the **sentence**, not on `5.7.139`; the same code
   also carries "basic authentication is disabled", a third situation.

4. **One resource per token request, many per authorize request.**
   `[MEASURED]` Redeeming scopes from two resources at the token endpoint
   returns `AADSTS28000: … scope is not valid because it contains more than
   one resource.` `[VENDOR]` `/authorize` explicitly "can cover multiple
   resources". → Consent once for everything; redeem the code for the resource
   you need first; mint the second token from the same refresh token
   afterwards.

5. **A native app is a public client, so the secret is not the boundary.**
   `[VENDOR]` Microsoft: public clients "must not use secrets or certificates
   when redeeming an authorization code." Google's Desktop client type issues a
   secret and its token endpoint requires it. Either way the value ships inside
   the binary and is readable from any copy. → PKCE S256 is what actually
   secures the flow. Never ship `plain`.

6. **A TLS error can mean the connection never happened.** The universal rule:
   a certificate failure reported with **zero bytes received from the server**
   is not a certificate failure. Any runtime that races two addresses (Happy
   Eyeballs, RFC 8305) can abandon an attempt and still run the identity check
   on the dead socket. → Read the wire log before the error text, and make your
   check distinguish "no certificate arrived" from "the certificate failed".
   The instance measured here `[MEASURED 2026-09-14]`: on Bun 1.3.13–1.4.2, a
   host with ≥2 DNS addresses whose first attempt exceeds 250 ms produces
   `Cert does not contain a DNS name` with an **empty** certificate object.
   iCloud and Fastmail hit it; Gmail, Yahoo and Outlook did not. Full evidence
   and the fix in `references/app-password-providers.md`.

7. **Find where your IMAP library puts the server's sentence, before you write
   any error handling.** Libraries commonly raise one generic "command failed"
   for every tagged `NO`/`BAD` and put the server's actual words on a secondary
   field — in the Node ecosystem,
   imapflow uses `responseText` and nodemailer uses `response`; yours will have
   an equivalent. Find it before you write any error handling. → Read only the
   exception's main message and a mistyped app password, a revoked one, and
   "application-specific password required" all look identical. Quote the
   server; never paraphrase it.

8. **Microsoft documents two SMTP hosts, and neither causes a policy refusal.**
   `smtp-mail.outlook.com` for Outlook.com/Hotmail/Live/MSN,
   `smtp.office365.com` for Microsoft 365. `[MEASURED 2026-09-15]` The same new
   personal mailbox is refused on both. → Split the hosts for conformance, and
   do not report the host as the cause.

9. **A 403 from a mailbox-less account says nothing about a permission.**
   `[MEASURED 2026-09-19]` An account with no Exchange Online licence answers
   403 to everything. → Check `GET /me/mailFolders/inbox` **before** concluding
   anything about a scope. What voids the result is a **404 /
   `MailboxNotEnabledForRESTAPI`** — there is no mailbox Graph can see.
   `[MEASURED 2026-09-19]` A **403** there is the *expected* answer on a
   consumer grant, which carries no Graph mail read at all, so on a personal
   account this check can never return 200 and a 403 is not a failure. Read it
   for the 404 only.

10. **Microsoft rotates the refresh token on every use.** → Every token read is
    a read-modify-write of one stored credential. Two concurrent readers will
    strand the account. Serialize per credential, and persist a refresh
    **before** returning it.

11. **A missing refresh token is a broken account an hour later.** `[RULE]`
    If the code exchange returns no refresh token, fail the pairing now with
    "revoke this app's access and sign in again" rather than accepting an
    account that dies by lunchtime.

## 6. Diagnostic discipline

Four rules, each of which was learned the expensive way.

- **Probe the endpoint the scope under test actually covers.** See trap 2.
- **Always run a known-good control before blaming the provider.** A work
  account beside a personal one, or another vendor's registration beside yours,
  turns "this is broken" into "this is broken *for this class of account*" —
  which is a different, findable problem.
- **Never draw a scope conclusion from a window in which every request fails.**
  During a consumer-consent outage every request returned a bare `server_error`.
  Four separate conclusions drawn in that window were later all false.
- **Check the sign of your evidence.** One refutation on record was confirming
  evidence filed backwards: deleting a consent grant *forces* the consent
  screen to render, so under the hypothesis "consent rendering is broken" a
  failure was the predicted outcome, not a refutation. Filing it as a
  refutation removed the correct answer from the hypothesis space for two days.
  Before recording a refutation, state what the hypothesis predicts and check
  that your result contradicts it.

Run every interactive OAuth probe from a **private browser window**.
`login_hint` only suggests an account; a multi-login browser session silently
authenticates someone else and has caused more confusion here than any other
single factor.

## 7. Plan-mode pre-flight

Answer all eight before writing a plan. Each has a cheap source.

| # | Question | How to answer it |
|---|---|---|
| 1 | Consumer or business address? | Provider-owned domain list, else MX |
| 2 | Does this provider take a password at all? | Pre-auth capability probe (§2) — no account needed |
| 3 | How many OAuth resources do I need? | One per API host in the scope list. Each extra resource is a second token, not a second sign-in |
| 4 | Which endpoint does each scope authorize? | §4. Assume nothing from the permission's name |
| 5 | Does the registration / console project actually declare them? | Read it back from the provider's API or portal. Do not assume it matches your notes |
| 6 | Which door sends for this mailbox class? | §3 |
| 7 | What does the refresh leg do to the stored scope string? | It overwrites it, re-prefixed (trap 1). Plan the matching rule accordingly |
| 8 | What is my known-good control? | Name it before you start, not after the first surprise |

If you cannot answer one of these, the answer is a measurement, not a guess —
and it usually takes minutes. `references/microsoft.md` and
`references/google.md` list the probes that answer 2, 4 and 5 without sending
mail or storing anything.

## 8. Refuted — do not re-derive these

All tested and cleared. Full detail in `references/microsoft.md` §10.

⚠ **Read the whole list with one caveat.** Most of these were measured during
`[MEASURED 2026-09-17/18]`, a window in which *every* consumer sign-in failed —
the same window §6 says never to draw a scope conclusion from. They are sound
as "this is not the cause of the outage"; they are weaker as general claims
about scopes. The two that do not depend on that window are the SMTP host and
the client ID, both measured against a working control.

- "The wrong SMTP host causes the policy refusal." Both hosts, same account,
  same refusal.
- "The client ID is the cause." Thunderbird's publisher-verified registration
  gets the identical refusal on the same mailbox.
- "The username is an alias, not the primary address." The two usernames
  produce two *different* enhanced status codes, which is the opposite of what
  an alias problem looks like.
- "Microsoft allows only one resource per `/authorize`." A single-resource
  request fails identically during the outage; multi-resource is legal there.
- "It is the send/write scopes." A read-only, unrelated scope fails the same.
- "`offline_access` is the variable." Dropping it changes nothing.
- "The registration must list the scope for it to work." Refuted from both
  directions — an unlisted scope succeeded and a listed one failed.
- "The request asks for too many permissions." Thunderbird's exact three
  scopes, in Thunderbird's exact request shape, failed the same.
- "The registration is the variable." A brand-new registration failed
  identically.
- ⚠ "The consumer consent record is the variable" is recorded as refuted **and
  that refutation was withdrawn** as the sign error described in §6. Treat this
  entry as unsafe; do not rely on it in either direction.

## 9. Unverified

Written as questions because nobody has run them.

- Does a consumer request carrying both `SMTP.Send` and Graph `Mail.Send`
  print two send lines on the consent screen? If it does, one of them is
  redundant for an app that sends via Graph.
- Does an app password pass SMTP `AUTH LOGIN` on a real personal Microsoft
  mailbox? SMTP still advertises `AUTH LOGIN`; nobody has tried it with a
  genuine app password.
- Is a slow SMTP host affected by the Happy Eyeballs misfire the way IMAP is?
  The SMTP client measured here connected by IP, which would side-step it — but that
  has not been confirmed on a >250 ms host.
- Does a Google app-password pairing work end to end? It needs an account with
  2-Step Verification enabled; never run here.
- **What does a 403 on `/me/sendMail` mean when the mailbox IS visible and
  `Mail.Send` IS consented?** There is no record of that case. Conditional
  Access, Exchange application access policies and shared-mailbox sends
  (`/users/{id}/sendMail`) are all outside everything measured for this.
- Does dropping `SMTP.Send` from the consumer request change the consent
  screen, or anything else? Never tried.
