# iCloud, Fastmail, Yahoo — and the TLS trap they exposed

Tags as in `SKILL.md`.

## The short version

`[MEASURED]` None of these publishes an OAuth flow for third-party mail
clients. All three take an **app password** over ordinary IMAP and SMTP. No
client ID exists or is needed, so there is nothing to register and nothing to
ship.

Hosts and ports are `[VENDOR]`; the app-password forms are `[VENDOR]` too.

| Provider | IMAP | SMTP | App password form |
|---|---|---|---|
| iCloud | `imap.mail.me.com:993` TLS | `smtp.mail.me.com:587` STARTTLS | `xxxx-xxxx-xxxx-xxxx` — **hyphens are part of the value** |
| Fastmail | `imap.fastmail.com:993` TLS | `smtp.fastmail.com:465` TLS | Four groups of four alphanumerics, spacing is display only |
| Yahoo | `imap.mail.yahoo.com:993` TLS | `smtp.mail.yahoo.com:465` TLS | Four groups of four alphanumerics, spacing is display only |

`[RULE]` Normalise a pasted secret by stripping zero-width characters always,
and whitespace **only** when the value matches the "four groups of four
alphanumerics" display form. iCloud's hyphenated form must survive untouched —
there the separators are what the provider expects back.

`[VENDOR]` None of these publishes a strict app-password *pattern* the way
Google does. `[RULE]` So after a refusal the most you can honestly say is that
this provider requires an app password rather than the account password —
guessing at a shape would let you reject a valid credential.

`[MEASURED 2026-09-14]` Apple's real refusal, once the socket actually
connects, looks like this — note the capability list, which is what a working
connection to iCloud looks like:

```
S: * OK [CAPABILITY XAPPLEPUSHSERVICE IMAP4 IMAP4rev1 SASL-IR AUTH=ATOKEN
        AUTH=PLAIN AUTH=ATOKEN2 AUTH=XOAUTH2] …
S: 1 NO [AUTHENTICATIONFAILED] Authentication Failed
```

`[MEASURED 2026-09-14]` Fastmail's, at 599 ms RTT with the fix in place:

```
S: * OK IMAP4 ready
S: 2 NO Incorrect username, password or access token.
```

## The trap: a TLS error on a socket that never connected

This is the one that matters, because it wastes a day pointing at Apple.

**Symptom.** Pairing an iCloud or Fastmail address fails instantly with:

```
The server's TLS certificate could not be verified
(Hostname/IP does not match certificate's altnames: Cert does not contain a DNS name).
code=ERR_TLS_CERT_ALTNAME_INVALID
```

`[MEASURED 2026-09-14]` The dialogue is **one line and it is the error**. Zero
`S:` lines — the server's IMAP greeting never arrived, so no byte was ever
exchanged. `[RULE]` A wire log with no server output at all is telling you the
connection never happened. Read that before reading the error text; it is the
fastest discriminator there is.

**Cause.** The general shape first, because it is not specific to one runtime:
any client that races several addresses for a host (Happy Eyeballs, RFC 8305)
may abandon an attempt and still run the TLS identity callback against that
dead socket. The callback is then handed an empty certificate, correctly
reports that it contains no matching name, and the message blames a certificate
that never existed. If your platform has an option to connect to one address at
a time, that option is the fix, whatever it is called.

The instance measured here: `[MEASURED 2026-09-14]` Bun's Happy Eyeballs connect path
(1.3.13, still present in 1.4.2) fires the `secureConnect` callback on a socket
that never connected, handing the TLS layer an **empty** certificate object.
The identity check then correctly reports that an empty certificate contains no
DNS name — and the message names a certificate that never arrived.

**Trigger conditions**, both needed: the host resolves to **≥2 addresses**, and
the **first attempt takes more than 250 ms** (the Happy Eyeballs timer).

`[MEASURED 2026-09-14]` The latency matrix that proved it:

```
                         TCP RTT   default   attemptTimeout:5000   autoSelectFamily:false
imap.mail.me.com          1542ms    FAIL            OK                     OK
imap.fastmail.com          516ms    FAIL            OK                     OK
imap.mail.yahoo.com         49ms      OK            OK                     OK
imap.gmail.com              53ms      OK            OK                     OK
outlook.office365.com       43ms      OK            OK                     OK
```

`[MEASURED 2026-09-14]` What a failing socket looks like, all at once:
`remoteAddress` undefined, `getProtocol()` null, `getCipher()` undefined,
`Object.keys(getPeerCertificate()).length === 0`, callback fired at 257–270 ms.

**Ruled out by measurement**: Apple's certificate (`CN=imap.mail.me.com`, SAN
carries the right DNS name among 100, `Verify return code: 0 (ok)`), the SAN's
size, the presence of AAAA records, Bun version skew, the provider config, and
the app password.

**Fix.** `[MEASURED 2026-09-14]` Two settings each turn FAIL into OK:
`autoSelectFamily: false` and raising the per-attempt timeout. Prefer
`autoSelectFamily: false` — a longer timer only moves the threshold that
triggers the race, while connecting one address at a time removes the race.
This is also what a mainstream mail client does for mail sockets.

`[RULE]` **If your platform lets you override the hostname check, overriding
it REPLACES the default — it does not run alongside it.** So you must call the
default yourself and return its verdict. In Node and Bun that means
`checkServerIdentity`, where returning `undefined` means "identity OK". Supplying the callback at all *replaces* Node's default hostname check,
so you must call it yourself and return its result. Get this wrong and you have
silently disabled hostname verification for every host that does present a
certificate — a far worse bug than the one you set out to fix.

```ts
import { checkServerIdentity as nodeCheckServerIdentity } from "node:tls";
import type { ConnectionOptions, PeerCertificate } from "node:tls";

export const NO_CERTIFICATE_CODE = "ERR_TLS_NO_CERTIFICATE";

export function requireServerCertificate(
  hostname: string,
  cert: PeerCertificate,
): Error | undefined {
  // Neither a subject nor any SAN means this certificate was not verified —
  // it was never received. Say that, with a distinct code so nothing
  // downstream re-wraps it as a verification failure.
  if (cert.subject === undefined && cert.subjectaltname === undefined) {
    return Object.assign(
      new Error(`No server certificate arrived from ${hostname}; the secure connection was not completed.`),
      { code: NO_CERTIFICATE_CODE },
    );
  }
  // Everything else defers to Node, unchanged, so this is NEVER weaker than
  // the default.
  return nodeCheckServerIdentity(hostname, cert);
}

const IMAP_TLS_OPTIONS: ConnectionOptions = {
  // A net.connect option that tls.connect forwards; @types/node 20.x does not
  // list it on ConnectionOptions, hence the cast.
  ...({ autoSelectFamily: false } as ConnectionOptions),
  checkServerIdentity: requireServerCertificate,
};
```

**Where it goes.** One options object on the IMAP client, used for **both** the
implicit-TLS connect and the STARTTLS upgrade — a STARTTLS session that skips
it is unprotected. `[UNVERIFIED]` Whether the SMTP leg needs the same: the
SMTP client measured here connected by IP, which would side-step the bug, but
that has never been confirmed against a host slower than 250 ms. If your SMTP client
resolves names itself, apply it there too.

`[RULE]` Do not "fix" this by disabling certificate verification. The failure
is a connection failure wearing a certificate failure's clothes; loosening the
check would hide a real MITM later.

`[RULE]` Attach the app-password advice only to a failure where the server
actually **refused the credentials**. Before this was separated, a dead port, a
DNS failure and this TLS misfire all told the user to go generate an app
password.

**A trade-off this fix makes, deliberately:** with `autoSelectFamily` off, a
dead first address waits out the connection timeout instead of falling back.
`[MEASURED 2026-09-14]` It failed instantly with the *wrong* error before, so
nothing regresses — it is slower and correct rather than fast and wrong.

**How to verify, and how you will fool yourself.**

`[MEASURED 2026-09-14]` `imap.mail.me.com` sits behind an Akamai CNAME and its
answers rotate, so the bug is intermittent by construction. One green run
proves nothing — a run whose first address happened to answer in under 250 ms
passes on completely unfixed code.

1. Confirm the preconditions still hold on your network before testing:
   `dig +short imap.mail.me.com` returns ≥2 addresses, and a TCP connect to the
   first takes >250 ms. If they do not, you cannot reproduce it today and a
   pass means nothing.
2. Pair the slow host repeatedly, not once. Pair Fastmail too.
3. Pair with a **deliberately wrong** app password. You should now get Apple's
   real refusal *after* a real greeting — `* OK [CAPABILITY …]` then
   `NO [AUTHENTICATIONFAILED] Authentication Failed`. Server output at all is
   the proof the socket now connects.
4. Prove you did not weaken the check: a host with a genuinely bad chain must
   still fail with `self signed certificate in chain`, and a certificate for
   the wrong hostname must still be rejected.
5. Regression-test the classifier, not the connect path: assert that a cert
   object with no `subject` and no `subjectaltname` produces the
   no-certificate code and **not** the "could not be verified" wording. The
   connect-path bug itself is a Bun behaviour and cannot be reproduced against
   a local socket server.

`[VENDOR]` Upstream bug `oven-sh/bun#41271`, open. `[MEASURED 2026-09-14]`
Upgrading Bun does not fix it.

`[UNVERIFIED]` Whether the SMTP leg is affected the same way. The measured
SMTP client connects by IP, which would side-step it, but that has not been
confirmed against a host slower than 250 ms.
