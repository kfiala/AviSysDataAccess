# Code for accessing AviSys data directly from the native data files

1. Just run `python SightingsTOcsv.py` from your AviSys data folder. The default argument is `AviSys` and the alternative argument is `eBird`.

1. The `AviSys` option produces a CSV file that is similar to the one that AviSys generates, except that "field notes", if any, are included with the AviSys comments.

1. The `eBird` option produces a CSV file in a format that can be imported into eBird, also with "field notes" included with comments.

1. Either option also produces a second file, `FieldNotes.txt`, that includes just the contents of the field notes.
