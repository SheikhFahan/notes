# Google mail authentication

Gmail and Workspace. Tags as in `SKILL.md`.

## Two ways in, and both work

Unlike Microsoft, Google still accepts a password over IMAP — but only an **app
password**, not the account password. `[MEASURED 2026-09-14]`
`imap.gmail.com:993` advertises `AUTH=PLAIN` and `smtp.gmail.com:465`
advertises `AUTH LOGIN PLAIN`. So an app-password path is a real fallback, and
worth keeping: it is the escape hatch when OAuth is not available (see the
restricted-scope problem below).

## OAuth

```
authorize   https://accounts.google.com/o/oauth2/v2/auth
token       https://oauth2.googleapis.com/token
scopes      https://mail.google.com/   openid   profile
extras      access_type=offline   prompt=consent
```

- `https://mail.google.com/` covers IMAP, POP **and** SMTP in one scope. There
  is no separate API scope — the mail token is also the Gmail API token, so
  there is only ever one resource and one token.
- `openid` is what makes Google issue an id_token at all; `profile` is what
  puts `name` and `picture` into it. Both are ordinary non-sensitive scopes.
- `access_type=offline` is what asks for a refresh token at all.
  `prompt=consent` is what makes Google issue a **new** one on a repeat
  authorization instead of assuming you kept the first. Re-authenticating an
  existing account depends on both.
- `[VENDOR]` Google returns an id_token on the code exchange and on a fresh
  consent, but **not** on an ordinary refresh. So capture the profile at
  consent; do not expect to track it continuously.
- Google's Desktop client type issues a client **secret** and its token
  endpoint requires it. That is the opposite of Microsoft, which forbids one.
  Either way the value ships inside the binary — PKCE is the real protection.

## Console setup

`https://console.cloud.google.com` → new project, then:

1. **APIs & Services → Library → enable the Gmail API.** `[VENDOR]` Required
   before `https://mail.google.com/` is selectable in the scope picker. The
   XOAUTH2 protocol page does not mention this; the Cloud Console help does.
   If a Gmail API call returns 403 saying the API has not been used in the
   project, this is the gate.
2. **Google Auth Platform → Audience.** User type **External**. Add your own
   address as a **test user**.
3. **Data access.** Add the scope `https://mail.google.com/`.
4. **Clients → Create client → Application type: Desktop app.** Copy the client
   ID and secret. The console downloads them as
   `{ "installed": { "client_id": …, "client_secret": … } }` — accept that shape
   verbatim so the file can be moved into place rather than retyped.

## What the restricted classification costs

`[VENDOR]` Google classes `https://mail.google.com/` as **RESTRICTED**. The
consequences are the reason this is a planning-time fact, not an
implementation-time one:

- A project in **Testing** status works, but only for its explicitly listed
  test users.
- `[VENDOR]` A Testing-status project issues refresh tokens that **expire after
  7 days**.
- Publishing requires verification **and** a third-party security assessment.

`[RULE]` A lapsed 7-day testing token and a user-revoked grant both arrive as
`invalid_grant`. Both are fixed only by sending the human back through consent.
Retrying either is an infinite loop — make it a distinct error type at the
point it is raised, so callers cannot accidentally retry it.

`openid` and `profile` are non-sensitive, so the verification tier is set by
`mail.google.com` alone. Adding them lengthens the consent screen; it does not
make approval harder.

`[RULE]` For an open-source or widely distributed client, think about this
before shipping your own credential: a restricted scope means shared fate
(one abusive user's report affects every install), a pooled quota, and an
attractive target. An app-password fallback costs the user two minutes and
removes the dependency entirely.

Re-auth and revocation: `https://myaccount.google.com/permissions`.

## App passwords

`[VENDOR]` Shape: **sixteen lowercase letters**, no digits, spaces or symbols —
`/^[a-z]{16}$/`. Generated at `https://myaccount.google.com/apppasswords`.
`[VENDOR]` The option requires 2-Step Verification to be on, and Workspace
admins can withhold it entirely.

`[RULE]` The generator **displays** it as four groups of four
(`abcd efgh ijkl mnop`) — that spacing is typography, not part of the value.
Strip whitespace and zero-width characters from a pasted secret. Do **not**
apply the same stripping to providers whose separators are real (iCloud's
hyphens); see `app-password-providers.md`.

Knowing the published shape is worth it for one reason only: after the server
says no, it separates a rejected *account* password from a rejected *app*
password — three different problems that otherwise read identically.

- Typed value matches the shape → it is an app password, so it has been revoked
  or belongs to a different account. Tell them to generate a fresh one.
- Typed value does not match → they used their account password. Say what the
  right shape is and where to get it.

`[RULE]` Never use the shape to *refuse* input — a provider can change its
generator without telling you.

`[RULE]` When the server's own message already names the fix — Gmail's IMAP
`ALERT` reads `Application-specific password required:
https://support.google.com/accounts/answer/185833` — say nothing extra. The
provider's instruction beats yours, and two overlapping instructions read as a
contradiction.

## Verbatim failures

| String | Means |
|---|---|
| `Application-specific password required: https://support.google.com/accounts/answer/185833` | The account password was used. Quote it and add nothing. |
| `[AUTHENTICATIONFAILED] Invalid credentials (Failure)` | The app password is wrong, revoked, or for another account |
| `535-5.7.8 Username and Password not accepted.` | Same, from SMTP |
| `Gmail API has not been used in project … before` (403) | Console step 1 was skipped |
| `invalid_grant` on refresh | Revoked, or the 7-day testing token lapsed. Re-consent; never retry |

`[UNVERIFIED]` A Google app-password pairing has never been run end to end
here — it needs an account with 2-Step Verification enabled.
