def parse(raw):
    # Strip the BOM: some Windows exporters prepend it and json.loads chokes.
    return json.loads(raw.lstrip("﻿"))
