# Inspect local traffic records

Route `traffic_log_enabled` records local traffic independently of masking
matches and usage tracking. Desktop **Activity** shows recent request/response
records and keeps WebSocket messages/connections behind an optional filter.

The request/response detail offers body inspection and **HTTP headers**, including
received and forwarded values. WebSocket headers describe the HTTP connection
handshake. Repeated values are preserved. Authentication tokens, API keys and
Cookie/Set-Cookie values are masked before header storage; body regex rules do
not replace headers. Oversize or unsupported-text header sets have an explicit
omission state. These are parsed fields, not a byte-for-byte network capture;
transport-generated fields are not guaranteed. HTTP trailers are recorded in
separate sections after body EOF, with explicit interruption states.

```console
gjl audit query --classes traffic --exclude-transport --limit 5
gjl audit headers --event-id EVENT_ID
gjl audit bodies --event-id EVENT_ID
gjl audit body-read --event-id EVENT_ID --direction request --message-index 0
```

Use the `next_cursor` and the same filters/order for another metadata page.
`audit body-save` saves a complete body when needed. `audit export` exports
metadata only, excluding bodies and headers. Remote audit also receives metadata
only. Older recorded events may have no headers; this does not mean their bodies
are empty. An older daemon without the new local header endpoint still supports
existing body reads.

Local SQLite files have owner-only permissions and no automatic expiration.
The strict production `audit.db` schema and IPC v1 responses are preserved;
masked headers live in the adjacent `audit-headers.db`, linked by event ID and
deduplicated across identical handshake snapshots. Delete records through
Desktop or `gjl audit delete` so their headers are removed too. Saved exports
and body files have separate retention. Header references left after record
deletion by an older daemon are reconciled when the new daemon starts.

Desktop Settings → Storage shows disk space, database/WAL/SHM sizes, and unused
space. Records can move to another local drive on the next daemon start; the
original location remains active if transfer fails. Configuration and credentials
stay in place. Select individual records or several records in Activity or Usage
to delete them. The **Delete** button removes all matching filter results, while
**Delete all** is available in global views. Deletion and disk-space reclamation
are separate actions; reclamation reports measured bytes and includes headers.

```console
gjl storage status
gjl storage configure --expected-revision N --directory ABSOLUTE_FOLDER --confirm
gjl audit delete --event-ids EVENT_ID --confirm
gjl audit compact
gjl usage delete --sequences SEQUENCE --confirm
gjl usage compact
```
