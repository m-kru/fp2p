File types
----------

The whole fp2p concept is based on 3 files types:

1. mapping file - one or more per setup,
2. tree file - one per setup,
3. assignment file - oner pet setup.

These three types share the same format and syntax, however their semantics is different.
YAML [8] has been chosen as the file format.
Another user-friendly alternative was JSON [9], which is provided in the Python Standard Library.
However, YAML has been chosen as it is less verbose and allows placing comments in the files, what might be useful in case of documenting any peculiarities in the mappings.
