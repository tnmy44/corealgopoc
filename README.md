Harmonisation Core Algorithm

The core harmonisation algorithm should work for all complex use cases, and work specially well for Waterfall.

Requirements:

- Speed: First mapping within 30 seconds, overall harmonisation within 3 mins
- Accuracy: >90% on waterfall eval

# High level

Harmonisation core algorithm needs the following inputs:

1. Source table(s):
  1. Schema of each table
  2. Data samples for each table (randomly sampled 10000 rows)
2. Target table(s):
  1. Schema of each table
  2. Optionally description of each column
  3. Optionally example data for each column
3. Memory

### Algorithm

- Try deterministic matching
  - Fetch past mappings from Memory
  - For each target column:
    - Score mappings on these criteria:
      - Each source column should match a column in current source columns (See ***String Matching*** section)
      - Data profile of each column should be close to the data profile in the current sources (See ***Data Profiling*** section)
    - If there is a mapping with score >0.9 (?), use that mapping (after replacing the column names), otherwise fallback to LLM mode
    - Given the mapping, generate the output data and run validations:
      - Data profile should match against target data profile for that column
      - DQ checks should succeed against that column
    - If validations succeed, stream the mapping to FE
- Otherwise fallback to LLM:
  - Ask LLM to generate the SQL expression (for a batch of columns) using these info:
    - Target column name, type, description, example output data
    - Source columns with type, data samples
    - Few past mappings(?)
  - Stream mappings

## Memory

We still need to align on some aspects of memory:

- Where to store (KG, Metadata etc)
- What level (per team, shared for all teams in the env?)

But irrespective of the above details memory will have roughly this contract

Query:

 Retrieve mappings from past (approved) mappings

{

  "industry": "RMBS",

  "targetcolumns": "sellerloanid", "bankruptcyflag", "fullname", ...,

  "sourcecolumns": "firstnameraw", "lastnameraw", "investortapeid", ...

  # "sourcesamples": {"firstnameraw" : "

}

Response:



  "fullname": {

      "expressions": ,

      "sourcecolumns": {"firstname": , "lastname": },

      "metadata": {

        "mappingdate": "1 Jan, 2025",

        "tags": "MFA"

      }

    },

    {

      "expressions": ,

      "sourcecolumns": "firstname",

      "metadata": {

        "mappingdate": "1 Jan, 2026",

        "tags": "GSMBS"

      }

    },

  "sellerloanid":  {

      "expressions": ,

      "sourcecolumns": "investortapeid",

      "metadata": {

        "approvaltime": "1 Jan, 2025",

        "tags": "MFA"

      }

    } ,



------------

 # This array respresents 1 mapping (where the ref pipeline contained 2 reformats)

  {

    "expression": "concat(firstnamecleaned, lastname)",

    "target": "fullname"

  },

  {

    "expression": "trim(firstname)",

    "target": "firstnamecleaned"

  }



----------

< See data profiling section >

## String Matching

def stringmatch(str1, str2):

    Returns 0 for totally different strings, 1 for exactly the same strings.

TODO: Need to evaluate various fuzzy and semantic algorithms to find out which works best for our use case.

## Data profiling

For finding the SQL transformation for a given target column from past mappings, we need to compare the data profile of the past data to the current data for a given source column. This is required to ensure that the columns contain the same information and in the same format (eg. we don't want to blindly call TO_DATE(date_string, 'DD-MM-YYYY') on "1st Jan 1999")

*   Metrics which might be useful:
    
    *    Percent of nulls
        
    *    Distribution of data:
        
        *      Bucketing for numeric data and timestamps
            
        *      Pattern based distribution for string data
            
    *   Relevant metrics for each data type

Requirements:
- Define a structured format to store Data Profile information for each source column when adding it to the Memory capturing any information which might be relevant in future to decide whether the same SQL expression is applicable to the new data
- Use a appropriate library to extract these metrics from the data sample
- Write an algorithm (or use a library) to compare the data profiles of two sets of values and give a matching score
- Keep the algorighm implemenation clean and behind an interface so that we can test and compare multiple such algorithms
  
—------

## Questions

- Can storing data profiles samples have compliance related concerns (e.g. storing max of a column called “SSN”)

