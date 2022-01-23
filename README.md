# Code for accessing AviSys data directly from the native data files

Just run `python SightingsTOcsv.py` from your AviSys data folder.

There are three supported command-line arguments. They are not case-sensitive.

1. The `AviSys` option (the default) produces a CSV file that is similar to the one that AviSys generates, except that "field notes", if any, are included with the AviSys comments.

1. The `eBird` option produces a CSV file in a format that can be imported INTO eBird, also with "field notes" included with comments.

1. The `MyEBird` option produces a CSV file in a format similar to that of the `MyEBirdData.csv` file that you can export FROM eBird.
It is for use for input to programs that support that format.

Each option also produces a second file, `FieldNotes.txt`, that includes just the contents of the field notes.

There are a few things that you will want to check in the .csv file before exporting it to another program.

- SightingsTOcsv does not provide any features for subsetting observations. If you want to export only certain observations you will need to create the full .csv file and then edit it to delete unwanted observations.
- AviSys defaults to recording a count of 1 individual if you do not specifically enter a count; there is no distinction between a count of 1 meaning no count entered and a count of 1 meaning you recorded seeing 1 individual. In the .csv files produced by SightingsTOcsv, if all observations for a particular date and location have a count of 1, the count will be replaced with X, meaning no count. There may be cases where you will want to edit to change Xs to 1.
- The first row of the spread sheet provides column headings, to make it easier to understand the columns in Excel. In the AviSys.sightings.eBird.csv file, you must delete this row before uploading to eBird.
- If you edit the .csv in Excel or similar spreadsheet program, it may change the date format in an undesirable way. In particular, Scythebill will not be able to import the AviSys.sightings.MyEBirdData.csv file after saving from Excel, unless you set the date format in the date column. You must set it to the YYYY-MM-DD format.
- In the AviSys.sightings.MyEBirdData.csv file, the column “Number of Observers” has a value of 1 throughout. You might want to change this in some cases.

