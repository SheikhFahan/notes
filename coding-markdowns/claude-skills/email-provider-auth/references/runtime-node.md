# Node and Bun specifics

Tags as in `SKILL.md`. Read this only if the client runs on Node or Bun. Each
item here is the runtime- or library-level half of a protocol rule that lives in
another file; on any other stack, apply that rule with your platform's
equivalent and skip this file.

## 1. TLS — the Happy Eyeballs misfire, and the identity-check override

The general rule, the full evidence (latency matrix, trigger conditions, what
a failing socket looks like, what was ruled out) and the verify steps are in
`app-password-providers.md`, "The trap". The Node/Bun half:

- **The measured instance.** `[MEASURED 2026-09-14]` Bun's Happy Eyeballs
  connect path (1.3.13, still present in 1.4.2) fires the `secureConnect`
  callback on a socket that never connected, handing the TLS layer an **empty**
  certificate object. Trigger: ≥2 addresses for the host and a first attempt
  slower than 250 ms.
- **The fix.** `autoSelectFamily: false` — connect one address at a time.
  Raising the per-attempt timeout also turns FAIL into OK, but only moves the
  threshold; prefer `autoSelectFamily: false`.
- `[VENDOR]` Upstream bug `oven-sh/bun#41271`, open. `[MEASURED 2026-09-14]`
  Upgrading Bun does not fix it.

**The override.** In Node and Bun the hostname check is `checkServerIdentity`,
where returning `undefined` means "identity OK". Supplying the callback at all
*replaces* Node's default hostname check, so you must call it yourself and
return its result.

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

Use that one options object for **both** the implicit-TLS connect and the
STARTTLS upgrade.

## 2. Where the libraries put the server's sentence

The rule is `SKILL.md` trap 3 and `implementation.md` §10: quote the server,
never paraphrase it.

- **imapflow** throws the same generic `Command failed` for every tagged
  NO/BAD `[MEASURED]`. The server's sentence is on `responseText`; reading only
  `.message` reports one indistinguishable failure for every refusal.
- **nodemailer** puts it on `response`.
- nodemailer wraps a mailbox-policy refusal in its own `Invalid login:` prefix
  *(client-side, not server output)*. Classify the **policy** sentence before
  any credential regex, or a policy refusal is reported as a bad password.

## 3. Standard-library pieces used in the snippets

The TypeScript in `implementation.md` uses `node:crypto` (`randomBytes`,
`createHash("sha256")`, `"base64url"` encoding) for PKCE and `node:http`
(`createServer`, `listen(0, "127.0.0.1")`) for the loopback listener. Those are
the runtime details; the protocol each implements is stated beside it.
