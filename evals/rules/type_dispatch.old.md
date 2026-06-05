**Rule: Incomplete type-dispatch / coercion.** A new `isinstance` ladder,
`match type(value)`, or `default`-style encoder hook that maps a value's type to
a serializable form, then returns the value **unchanged** (or raises) for
anything it didn't enumerate. Enumerate the value domain against the schema and
add the missing branch plus a catch-all.
