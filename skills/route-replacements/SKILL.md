---
name: route-replacements
description: Design or revise gjl Route-owned RE2 block and replace rules for decoded LLM request bodies, including sensitive text, prompt phrases, and model fields.
---

# Route body rules

Use this skill when the user wants gjl to block or change content in provider-bound requests. Start with [gjl operations](../gjl-operations/SKILL.md) if the Route or management workflow is unknown.

## Choose from observed bytes

1. Identify the Door or Gate Route and the client's transport. If shell access exists, use `gjl help`, `gjl config get`, and `gjl route list`; Desktop: dashboard canvas → **Routing** → select the Route → **Edit Route** → masking rules.
2. Inspect a representative *decoded body*. If its shape is unknown, enable the Route's `traffic_log_enabled` temporarily, make a harmless request, then use Desktop **Activity** → traffic event → **View Bodies**, or `gjl audit query --route-id ID --classes traffic` followed by `gjl audit bodies --event-id ID` and `gjl audit body-read`. Capture before adding a replacement when original bytes matter: the recorded outbound request reflects what was sent after replacement.
3. Pick `block` to reject a match or `replace` to rewrite it. All block rules check the original decoded body first; if none match, replace rules run in Route list order. Later replacements see earlier results. Use Go RE2 syntax and a Route-local rule ID. In JSON, escape regex backslashes again. Replacement text uses Go regexp expansion (`$1`, `${name}`, `$$`).
4. Test both intended matches and nearby nonmatches against the actual body format. Anchor a model rewrite to its JSON field and surrounding punctuation; a bare model name may also occur in prompts or examples. Check that the target model belongs to the same provider surface and is accepted upstream. A header-only model hint is outside body rules.
5. Apply the Route with the current configuration revision, make a harmless end-to-end request, and inspect its outcome in **Activity** or `gjl audit query`. Turn off temporary traffic logging when finished and delete unneeded records explicitly. Saved body files must be removed separately.

## Boundaries that change the answer

- Rules inspect decoded HTTP bodies (identity, gzip, deflate, zstd), uncompressed Connect JSON payloads, and WebSocket text messages. They do not rewrite headers, URLs, gRPC, Connect Protobuf/compressed frames, or WebSocket binary messages. A rule covers only matching content on an inspected path.
- Provider authentication is configured separately on the Route; a body rule cannot replace an auth header.
- Provider response bodies reach the client unchanged. Response `replace` rules sanitize only a bounded local recording copy; a response `block` match omits body persistence without blocking delivery.
- Traffic logging, match-only masking audit, and body-free usage tracking are independent Route switches. Local traffic bodies have no automatic expiry. Avoid copying sensitive content into prompts, logs, exported files, or example rules.

For client-side AI instructions, describe only the placeholder and behavior, for example: “gjl replaces matching outbound text with `<GJL_MASKED>`; keep that placeholder intact.” Never include the original secret.
