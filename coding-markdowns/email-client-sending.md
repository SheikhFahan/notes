# Email client — sending and message design

Companion to the `email-provider-auth` skill
(`plugins/email-provider-auth/skills/email-provider-auth/`). These are app-design
rules for a mail client's send pipeline, message building and test
architecture. They are not authentication, so they were moved out of the
skill's `references/implementation.md`, verbatim. Tags (`[MEASURED]`,
`[VENDOR]`, `[RULE]`, `[UNVERIFIED]`) mean what the skill's `SKILL.md` says.
Section references like `microsoft.md` §8 point into the skill's
`references/` folder.

## 1. The sender — order of operations

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

## 2. Building the message — one render, two artifacts

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

## 3. Sent-folder copy on a Graph send

From the skill's `microsoft.md` §8, which keeps the provider facts (Graph files
its own Sent copy; how fast is `[UNVERIFIED]`):

`[RULE]` If you also append your own copy, dedupe
by a **pinned** Message-ID — generate it once, before building anything, and
use it in every artifact. Two independent MIME builds each invent their own
random id, and then the dedupe searches for an id the server's copy does not
carry.

**So do you still append your own copy?** `[RULE]` Yes, if anything in your app
is derived from the local "this was sent" row — an event, a thread update, a
read receipt. A Message-ID dedupe that searches first returns the **server's**
copy and its uid on a hit, so you get the row either way and never a duplicate.
Replacing the append with a plain folder resync drops whatever that row drives,
and outgoing mail starts arriving through the *received* path. If nothing is
derived from it, a resync is simpler and equally correct.

## 4. Structure and tests

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

## 5. Checklist additions for sending

- [ ] Send with Cc **and** Bcc. The blind recipient receives it; the To
      recipient's copy carries no `Bcc:` header.
- [ ] The Sent folder holds **exactly one** copy.
