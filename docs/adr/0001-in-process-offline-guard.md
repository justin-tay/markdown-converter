# In-process Offline Guard instead of relying on configuration or an OS sandbox

Source documents may be confidential, so a Conversion Run must never reach the internet. Turning off markitdown's network features (URL/YouTube inputs, Azure Document Intelligence, AI-model image descriptions, audio transcription) is not enough on its own, because a dependency could still open a connection. An OS firewall or sandbox would be stronger, but it works differently on Windows and macOS and needs admin rights. We therefore install an in-process guard before any conversion code runs: it blocks every non-loopback socket connection and DNS lookup, sets library offline flags, and refuses URL Targets. A blocked attempt fails only that Source File with a clear "network access blocked" error, and a self-test command proves the guard is active.

## Consequences

- Setup (installing dependencies) is the only stage allowed to go online; machines with no internet use an Offline Bundle.
- Any future feature that needs the network (OCR via an AI model, Azure) is incompatible with this guard by design and must not be added as a default.
- The guard covers everything that goes through Python's `socket` module (connections, datagrams, name lookups). Code that uses the low-level `_socket` type directly, or native code with its own networking, would get past it; none of the pinned dependencies does this for document conversion. Data Owners who need more can add an OS firewall rule on top.
