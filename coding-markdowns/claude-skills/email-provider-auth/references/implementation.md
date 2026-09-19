# Writing the client

Tags as in `SKILL.md`.

**How to read the snippets.** They are TypeScript because they have to be in
some language. Nothing here needs TypeScript, Node, Bun, or any particular
library or project layout. Each section separates:

- **Protocol** — what goes on the wire: parameters, header names, grant types,
  status codes, the order of operations. Identical in every language.
- **Runtime detail** — an HTTP server, a SHA-256 call, a TLS option name. Your
  platform has an equivalent; translate it.

Where a rule depends on a specific library's behaviour rather than on the
protocol, it says so. If you are only setting up an app registration or a cloud
console, you do not need this file at all — see `microsoft.md` and `google.md`.

**Contents**

1. The flow, in order
2. PKCE
3. The loopback listener
4. The token endpoint
5. The two-resource rule
6. Narrowing scopes to what was granted
7. Storing the credential
8. Authenticating the transports
9. Choosing the send door
10. Building the message — one render, two artifacts
11. Surfacing failures
12. Structure and tests
13. A checklist before you call it done

---

## 1. The flow, in order

```
mint PKCE pair
 → bind a loopback listener on an OS-assigned port
 → open the browser at /authorize
 → wait for the redirect
 → verify state
 → exchange the code for tokens
 → (if a second resource is needed) mint that token from the refresh token
 → store the envelope
 → probe the account
```

`[RULE]` **This cannot be one RPC call.** A human at a consent screen takes
longer than any sane request timeout. Return a pairing id immediately and let
the UI poll phases (`waiting` → `exchanging` → `done` / `failed`). Hand back a
cancel function while the browser page is open, or a cancelled sign-in still
completes if the user finishes in the browser afterwards.

`[RULE]` Narrate every step to a log — what was asked for, what the provider
granted, and on failure where it stopped and what the server said. Never a
token. The single highest-value line is the one printing the scope string the
provider echoed back: it is the only way to see re-prefixing (§6).

## 2. PKCE

**Protocol:** a random verifier of 43–128 unreserved characters; the challenge
is `BASE64URL(SHA256(ASCII(verifier)))` with no padding; the method string is
`S256`. Every language has both primitives.

```ts
import { createHash, randomBytes } from "node:crypto";   // runtime detail

export const PKCE_METHOD = "S256" as const;

export function createPkcePair(entropy = () => randomBytes(32)) {
  // 32 bytes -> 43 base64url chars: the RFC 7636 minimum length and its
  // recommended entropy in one step.
  const verifier = entropy().toString("base64url");
  const challenge = createHash("sha256").update(verifier).digest("base64url");
  return { verifier, challenge };
}
```

A native app is a **public client**: the client secret ships inside the binary
and anyone can read it out, so the secret proves nothing. What proves the token
request came from the same program that started the flow is the verifier —
generated fresh per attempt, never sent to `/authorize`, only its SHA-256. An
attacker who intercepts the redirect gets a code they cannot spend.

`[RULE]` S256 only. `plain` exists in the RFC for devices that cannot hash and
offers none of the above.

## 3. The loopback listener

`[VENDOR]` RFC 8252 prescribes a loopback redirect for native apps; custom URI
schemes are no longer accepted by Google because another app can register the
same scheme and steal the code.

**Protocol — the listener's contract, in any language.** Bind an HTTP server on
`127.0.0.1` on port **0** so the OS assigns a free port; a desktop OAuth client
accepts any loopback port, so nothing is pre-registered. Serve one path, and on
a request to it, in this order:

1. **Path** — anything else is 404.
2. **`state`** — compare to the value you sent. Mismatch ends the flow.
3. **`error`** — if present, capture every field (below) and end the flow.
4. **`code`** — absent is a failure; present settles the flow.
5. Answer with a small HTML page telling the user to close the tab, then stop
   the server gracefully.

Step 2 comes first for a reason: **any page in the user's browser can reach
that port.** If you check `error` before `state`, a forged `error=` can kill a
live sign-in — the attack is not only a forged code.

```ts
import { createServer } from "node:http";   // runtime detail; any HTTP server does

const LOOPBACK_PATH = "/callback";

const server = createServer((req, res) => {
  const url = new URL(req.url ?? "/", "http://127.0.0.1");
  const done = (title: string) => {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    res.end(`<!doctype html><meta charset="utf-8"><title>${title}</title><p>${title}`);
  };

  if (url.pathname !== LOOPBACK_PATH) { res.writeHead(404); return res.end("Not found"); }

  if (url.searchParams.get("state") !== expectedState) {
    fail(new Error("The sign-in state did not match. Start the sign-in again."));
    return done("Sign-in could not be verified");
  }
  const error = url.searchParams.get("error");
  if (error) { fail(new Error(describeRedirectError(error, url.searchParams))); return done("Sign-in cancelled"); }
  const code = url.searchParams.get("code");
  if (!code) { fail(new Error("The provider returned no authorization code.")); return done("Sign-in failed"); }
  settle({ code });
  done("Signed in — you can close this tab.");
});

server.listen(0, "127.0.0.1");
const { port } = server.address() as { port: number };
const redirectUri = `http://127.0.0.1:${port}${LOOPBACK_PATH}`;
```

`[RULE]` **Read every field of the redirect before answering it.** The query
string is gone afterwards, so a field you did not read is lost for good. That
mattered: Microsoft's `AADSTS` number rides inside `error_description` and
nowhere else, so reading only `error` left `server_error` as the whole of what
the app could say. Capture `error_description`, `error_codes`,
`correlation_id`, `trace_id`, `timestamp`, `error_uri` — and report "the
provider sent no description" explicitly, so it cannot be mistaken for a
description you dropped.

`[RULE]` Stop the server **gracefully**. Force-closing while the redirect that
just settled you is still being answered shows the user a connection error
instead of the "you can close this tab" page. Unref the timeout timer so the
listener cannot hold the process open.

Authorize URL parameters, in order: `response_type=code`, `client_id`,
`redirect_uri`, `scope` (space-joined), `state`, `code_challenge` +
`code_challenge_method`, any provider extras, `login_hint`.

`[RULE]` The `redirect_uri` sent to `/token` must be the **same string** you
sent to `/authorize`, not a rebuild. Providers compare them literally.

## 4. The token endpoint

`POST`, `content-type: application/x-www-form-urlencoded`, credentials in the
**body**, not in an Authorization header.

```ts
/** Absent fields are left OUT, not sent as the string "undefined". A public
 *  client has no client_secret; only some providers take a scope on refresh. */
function tokenForm(fields: Record<string, string | undefined>) {
  const form = new URLSearchParams();
  for (const [key, value] of Object.entries(fields)) {
    if (typeof value === "string" && value !== "") form.append(key, value);
  }
  return form;
}
```

Code exchange: `grant_type=authorization_code`, `code`, `code_verifier`,
`redirect_uri`, `client_id`, `client_secret?`, `scope?`.
Refresh: `grant_type=refresh_token`, `refresh_token`, `client_id`,
`client_secret?`, `scope?`.

`[RULE]` **Time-box it.** A token endpoint that never answers must fail, not
hang — under a per-credential lock (§7) a hung request holds everything behind
it. 15 s is generous.

`[RULE]` **A missing `expires_in` is not a licence to treat the token as
immortal.** Default to one hour.

`[RULE]` **A refresh response often omits `refresh_token`.** Keep the old one
when it does; dropping it strands the account permanently.

`[RULE]` **`invalid_grant` is terminal, and it is not an error like the
others.** It means revoked, or a short-lived testing token lapsed. Both are
fixed only by sending the human back through consent; retrying is an infinite
loop. Raise it as a distinct type. In ecosystems where a module can be bundled more
than once — JavaScript especially — detect it **by name** rather than by class
identity, because two bundled copies of the same file are two different
classes. Where that cannot happen, an ordinary type check is fine:

```ts
export function isReauthRequired(caught: unknown): boolean {
  return caught instanceof Error && caught.name === "ReauthRequiredError";
}
```

`[RULE]` **If the code exchange returns no refresh token, fail the pairing.**
The account would work for an hour and then die with no way back. Failing now,
with "revoke this app's access and sign in again", is the kinder outcome.

An id_token from the token endpoint over TLS may be decoded without verifying
its signature — `[VENDOR]` OpenID Connect Core §3.1.3.7 item 6 permits exactly
this for tokens received directly from the endpoint. Use it for the display
name and picture only.

## 5. The two-resource rule

`[MEASURED]` `/authorize` may name scopes from several resources; `/token` may
not (`AADSTS28000`). So:

1. Ask for **everything** on `/authorize` — one consent screen.
2. Redeem the code naming **only the resource you need first** — for a mail
   client that is the mail resource, because the pairing probe uses that token
   against IMAP immediately.
3. Mint the second-resource token afterwards from the **same refresh token**,
   by naming that resource's scopes on a refresh call.

```ts
// Strip the API scopes from the code leg; ask for them on the refresh leg.
const scopesForCodeLeg = provider.apiScopes
  ? provider.scopes.filter((s) => !provider.apiScopes!.includes(s))
  : undefined;
```

`[RULE]` File the second token **beside** the mail token, each with its own
expiry, rather than overwriting. The transports are using the mail token right
now.

## 6. Narrowing scopes to what was granted

Two different accounts against one registration can hold two different grants.
Asking to refresh a scope the credential never received is a request that
should not be sent.

```ts
function permissionName(scope: string): string {
  if (!scope.startsWith("https://")) return scope;      // offline_access, openid
  const leaf = scope.slice(scope.lastIndexOf("/") + 1);
  return leaf === "" ? scope : leaf;                    // https://mail.google.com/
}

/** The scopes to name on a refresh leg, narrowed to what was actually granted.
 *  Null when the stored string says nothing useful — a credential stored before
 *  this field existed, or a provider whose refresh takes no scope at all — and
 *  the caller then falls back to the provider's own list. */
function scopesStillGranted(storedScope: string, wanted: string[]): string[] | null {
  const granted = new Set(storedScope.split(" ").filter(Boolean).map(permissionName));
  if (granted.size === 0) return null;
  const kept = wanted.filter((s) => granted.has(permissionName(s)));
  return kept.length === 0 ? null : kept;
}
```

Match on the **name**, never the full URI — see `microsoft.md` §5 for the
measurement that forces this and the silent 401 that results from getting it
wrong. The two guards above matter: a non-`https` scope and a scope with an
empty path both keep their whole string, which is what keeps Google unaffected.

`[RULE]` **Never mint a second-resource token from a grant that has none of
that resource's scopes.** Return null and let the caller decide, rather than
sending a request that will come back wrong.

## 7. Storing the credential

Model: the account row holds an **opaque reference** — a UUID — and nothing
else. The secret lives in the platform's credential store under that reference
— macOS Keychain, Windows Credential Manager, libsecret / Secret Service on
Linux. The database never sees a credential.

One string per keychain item, so:

```ts
type StoredCredential =
  | { kind: "password"; secret: string }
  | {
      kind: "oauth";
      provider: string;
      refreshToken: string;
      accessToken: string;
      expiresAt: number;                                  // epoch ms
      scope: string;
      api?: { accessToken: string; expiresAt: number };    // second resource
    };
```

`[RULE]` Store OAuth as a JSON envelope and a password **bare**. Anything that
does not parse as a well-formed envelope reads back as the password it has
always been. That asymmetry is what lets OAuth land in an app that already has
password accounts with **no migration** — and a migration over secrets has no
undo.

`[RULE]` Require a non-empty `refreshToken` for an envelope to count as usable.
Without one the access token expires within the hour and nothing can renew it.

`[RULE]` **Serialize per reference.** Microsoft rotates the refresh token on
every use, so every token read is a read-modify-write of one item, and two
concurrent readers strand the account. Use whatever mutual exclusion matches
your concurrency model: a promise chain keyed by reference on a single event
loop, a per-key lock with threads, and a **file lock** if two processes can
hold the same account open — the last case is easy to miss and the failure is
permanent.

`[RULE]` **Persist a refresh before returning it.** A refresh whose result is
used but not stored is repeated on every reconnect, and providers rate-limit
that.

`[RULE]` Refresh on a **skew**, not on expiry — five minutes covers clock drift
and a slow handshake without refreshing on every connect.

`[RULE]` A malformed second token reads as "no second token", never as "no
credential". The mail token is what the account lives on.

`[RULE]` The **app's own** client ID and secret are not secrets in the same
sense — see `SKILL.md` trap 5 — but the **user's** tokens are. Keep them in the
OS keychain, never in the database, never in a log.

## 8. Authenticating the transports

**Protocol — XOAUTH2 on the wire.** Most libraries hide this behind a config
object. If yours does not, or you are checking what it sends, this is the whole
mechanism. The SASL initial client response is one string with **`\x01`
separators and two of them at the end**:

```
user=<address>\x01auth=Bearer <access-token>\x01\x01
```

base64 it, and carry it on the protocol's own auth verb:

```
IMAP   A01 AUTHENTICATE XOAUTH2 <base64>
SMTP   AUTH XOAUTH2 <base64>
```

`[MEASURED]` That exact string is what a client sends that authenticates
successfully against Gmail, Outlook/Exchange Online and iCloud. The trailing
**two** `\x01` are not a typo — one closes the `auth` field, one closes the
list. A single terminator is the most common way to get this wrong, and the
server's answer is an ordinary auth failure that tells you nothing.

For comparison, the Basic-auth SASL payload — the one you are *not* using — is
`\0<user>\0<secret>`, also base64. Both of these are just base64, so both will
appear in full in any wire log unless you withhold them explicitly (below).

The shape of the exchange (the `OK` line's wording is the server's own and
varies):

```
C: A01 AUTHENTICATE XOAUTH2 dXNlcj0...        <- your base64 payload
S: A01 OK ...                                  <- authenticated
```

The three refusals worth recognising, quoted verbatim
`[MEASURED 2026-09-14/15]`:

```
S: 1 NO [AUTHENTICATIONFAILED] Authentication Failed      <- iCloud: token rejected
S: 2 NO Incorrect username, password or access token.     <- Fastmail: token rejected
S: 3 NO User is authenticated but not connected.          <- Exchange: token GOOD,
                                                             the mailbox refused the session
```

That third one is the one that misleads: the credential is fine and nothing
about it should be re-entered.

If your library does wrap it, pass the token **as a token**, never as a
password:

```ts
// IMAP                                     // SMTP
auth: authKind === "xoauth2"                auth: authKind === "xoauth2"
  ? { user: address, accessToken: token }     ? { type: "OAuth2", user: address, accessToken: token }
  : { user: address, pass: secret },          : { user: address, pass: secret },
```

`[RULE]` **Never set a password field alongside a token.** Libraries that
accept both commonly fall back to AUTH PLAIN, which puts an access token on the
wire as a password. If you build the AUTH command yourself this cannot happen —
but check, because the failure is silent and the token is long-lived.

`[RULE]` Decide `authKind` from the **stored envelope**, not from a column on
the account row. The envelope is the thing that is actually true.

`[RULE]` STARTTLS must be **mandatory**, not opportunistic. An opportunistic
upgrade permits a downgrade attack in which an active MITM strips the STARTTLS
advertisement and then sees the credential. Use the same hardened transport
builder for the pairing verify and for sending — a verify must not pass over a
connection the send path would refuse.

`[RULE]` Set explicit timeouts, and find out what your library's default
actually is first — some default to minutes, and some standard libraries
default to **no timeout at all**, which is worse. A wedged handshake will
otherwise pin whatever lease your send queue holds. 10 s connect, 10 s
greeting, 15 s socket is workable for SMTP if you have three separate knobs;
with a single timeout, set it to the smallest of those. IMAP needs a longer
socket timeout and an idle refresh before the RFC 2177 29-minute cutoff.

`[RULE]` If you log the wire dialogue for diagnosis, withhold three forms
explicitly: the raw secret, the XOAUTH2 blob
(`user=<addr>\x01auth=Bearer <token>\x01\x01`) and the AUTH PLAIN blob
(`\0<user>\0<secret>`). The last two are just base64 and will otherwise appear
in full.

## 9. Choosing the send door

Some mailboxes cannot use SMTP at all (`microsoft.md` §7). The door is a
property of the account class, and the check should be one function everything
agrees on:

```ts
// An EXACT-match table, never a glob. `hotmail.*` gets two-label TLDs wrong
// and will be implemented three different ways. Only domains the provider
// itself owns belong here — a custom domain is decided by MX, never by name.
const MICROSOFT_IMAP_HOST = "outlook.office365.com";   // ONE host, both classes

const CONSUMER_DOMAINS = new Set([
  "outlook.com", "hotmail.com", "hotmail.co.uk", "live.com", "msn.com",
]);

function isConsumerDomain(address: string): boolean {
  const at = address.lastIndexOf("@");
  if (at < 1 || at === address.length - 1) return false;
  return CONSUMER_DOMAINS.has(address.slice(at + 1).trim().toLowerCase());
}

function sendsThroughApi(account: { authKind: string; address: string; imapHost: string }): boolean {
  return account.authKind === "xoauth2"
    && account.imapHost.toLowerCase() === MICROSOFT_IMAP_HOST
    && isConsumerDomain(account.address);
}
```

`[RULE]` `MICROSOFT_IMAP_HOST` is singular on purpose — **both** Microsoft
classes use the same IMAP host, even though their SMTP hosts differ. Pair a
consumer account on any other IMAP host and this returns false, the account
loses its only send door, and nothing logs an error.

`[RULE]` If another part of the app makes the complementary decision — "which
accounts have an API *read* token" — assert in a test that the two are exact
complements. They are separate facts that must not drift.

`[RULE]` **Skip the SMTP verify at pairing for an API-door account.** It always
fails, and a failed verify that marks the account "cannot send" then blocks it
at every downstream gate.

`[RULE]` **An old marker must not outlive its meaning.** An account paired
before the API door existed carries "sending unavailable". It is still true
about SMTP and no longer true about the account, so the send path must ignore
it for an API-door row.

Order of operations in the sender, which matters more than it looks:

1. Resolve the credential — **a keychain read is not a transmission**, so it is
   safe before the claim, and failing here costs nothing.
2. **Claim the row** (pending → sending, with a lease) before any network I/O.
   `[RULE]` A double send is unrecoverable, so this is not at-least-once
   delivery. A crash mid-send strands the claim for an honest "may or may not
   have been sent"; nothing ever retransmits it.
3. Build the message.
4. Transmit.
5. **Past this line nothing may fail the row.** The mail has left. A failed
   Sent-folder copy is recorded as copy state, never as a send failure.

`[RULE]` If the account is offline, **wait unclaimed** rather than failing. An
offline send is a queue, not an error.

## 10. Building the message — one render, two artifacts

Render the body **once**, mint the Message-ID **once**, then produce two things
from the same input:

- **The structured payload** for SMTP: the `Bcc:` header must be absent from
  the bytes on the wire while the SMTP **envelope** (`RCPT TO`) still names
  every blind recipient. That is RFC-correct blind copying.

  `[RULE]` **Verify who does that stripping in your stack, before you send
  anything to a real person.** Some libraries remove the header for you when
  you hand them a structured message; some send exactly the bytes you give them
  and derive recipients from an explicit list, in which case the header goes
  out intact and every recipient sees the Bcc. Send a test message with a Bcc
  to two addresses you control and read the raw source of the To recipient's
  copy. Getting this wrong is a privacy incident, not a build failure, and it
  fails silently.
- **The raw bytes with Bcc kept**, for the Sent-folder copy. The user's own
  record should show who they blind-copied.

`[RULE]` **Pin the Message-ID before building anything.** Two independent
builds each invent their own random id, and then the Sent-folder dedupe
searches for an id the server's own auto-filed copy does not carry. This is a
real, reproduced race.

For an API send (`microsoft.md` §8), send the **keep-Bcc** bytes: `[MEASURED 2026-09-19]`
the server reads the header as the envelope, delivers the blind recipients, and
strips the header from the To recipient's copy.

`[RULE]` If the server files its own Sent copy (Gmail and Graph both do), keep
your append and dedupe by the pinned Message-ID — search first, append only on
a miss, and take the server copy's uid on a hit. That way the local "sent" row
exists either way, and anything derived from it still fires. See `microsoft.md`
§8 for when a plain folder resync is the better choice instead.

`[RULE]` Resolve special folders (Sent, Drafts, Trash, Junk) by the flags the
server advertises, never by hardcoded English names — providers localise them,
and Exchange advertises no `SPECIAL-USE` at all.

## 11. Surfacing failures

`[RULE]` **Quote the server; never paraphrase it.** Only the provider knows why
it said no, and paraphrasing is what hides the answer. The IMAP library throws
the same generic `Command failed` for every tagged NO — the server's sentence is
on a different field entirely (`responseText`; the SMTP library uses
`response`). Reading only `.message` reports one indistinguishable failure for
a mistyped app password, a revoked one, and "application-specific password
required".

`[RULE]` Classify **policy before credentials**. A mailbox-policy refusal
arrives wrapped in the SMTP library's `Invalid login:` prefix, which will match
any credential regex — and then the app tells the user to re-enter a credential
the server did not refuse.

`[RULE]` Keep the verdicts distinct, because each has a different fix: name not
resolved, connection refused, no certificate arrived, certificate failed
verification, credentials refused, mailbox policy. A single "could not connect"
is useless.

`[RULE]` **Attach advice only to the failure it fits.** App-password guidance
belongs on a credential refusal, never on a TLS or network failure.

`[RULE]` Report "could not tell" as itself. A timeout or an unexpected status
must never be recorded as a negative verdict — see the probe rule in
`microsoft.md` §9.

## 12. Structure and tests

`[RULE]` **Keep the transport layer free of UI and database imports**, and
enforce it with a test that walks the directory and fails on a forbidden
import. Without the test the rule is a comment nobody reads. The payoff is that
the engine can move to a background process later carrying its injected
interfaces, rather than being rewritten.

**Dependency injection is the test seam.** Every module exports a pure function
or class plus a `…Deps` type, and every impure edge is a field on it: `fetch`,
the clock, the sleep between retries, the transport factory, the MX resolver.

Three test patterns that work, in order of preference:

1. **A recorded fake `fetch`.** Construct real `Response` objects; assert on
   the recorded URL, method, headers and body. Nothing reaches the provider.
   ```ts
   function capture(response: () => Response) {
     const calls: { url: string; init: RequestInit }[] = [];
     const fetchImpl = (async (url, init = {}) => {
       calls.push({ url: String(url), init });
       return response();
     }) as unknown as typeof fetch;
     return { calls, deps: { fetchImpl, sleep: async () => undefined } };
   }
   ```
2. **Plain-function fakes that record call ORDER.** For a send pipeline the
   load-bearing assertion is not the output, it is the sequence:
   ```ts
   expect(order).toEqual(["claim", "createTransport", "sendMail", "append", "record", "markSent"]);
   ```
   Keep the MIME layer **real** so the recorded bytes carry the actual pinned
   Message-ID.
3. **A real socket server replaying measured dialogue.** For protocol
   behaviour, script a plain TCP server on `127.0.0.1:0` with the capability
   list and the refusal string you actually measured, and run the real client
   against it over a non-TLS endpoint. This is the only way to test
   credential redaction, and the only way to prove an alternate host was *not*
   contacted.

`[RULE]` Pin a published test vector where one exists — RFC 7636's PKCE vector
costs one test and catches a broken base64url encoder.

`[RULE]` Put the provider's real error strings in the tests **verbatim**. They
are the specification; a paraphrase in a fixture is a bug waiting to pass.

## 13. A checklist before you call it done

- [ ] Sign in, in a **private browser window**, and read the consent screen. Is
      every line something the app uses? A line that grants nothing reads as a
      bug.
- [ ] The scope the provider echoed back is logged, for both the code leg and
      the next refresh. Compare them (§6).
- [ ] The account pairs with sending **enabled**, where it should be.
- [ ] Send to an address you control. It arrives.
- [ ] Send with Cc **and** Bcc. The blind recipient receives it; the To
      recipient's copy carries no `Bcc:` header.
- [ ] The Sent folder holds **exactly one** copy.
- [ ] Leave the app running past the access-token lifetime (~1 h) and send
      again.
- [ ] Control: an account of the *other* class still works unchanged.
- [ ] Remove the account and re-add it.
- [ ] No token, password or app password appears in any log.
