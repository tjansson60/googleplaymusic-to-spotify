#!/usr/bin/env python

import util

input_file     = 'data/takeout-20200628T085613Z-001.zip'
processed_file = 'data/takeout-20200628T085613Z-001-processed.xlsx'

# Parse the google takeout file into a pandas dataframe
df = util.read_google_takeout_zipfile(input_file)
print(df.describe())
print(df.head(3).T)

# Export the dataframe to something more useful:
df.to_excel(processed_file, index=False)
print(f'Processed file written to: {processed_file}')
