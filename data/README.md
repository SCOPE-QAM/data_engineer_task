# Source Data Files - Corporate Credit Rating Assessments

## Overview
This directory contains Excel-based corporate credit rating assessment files from two companies (A and B), each with multiple versions.

## Files

### Company A - Personal & Household Goods Sector
- **corporates_A_1.xlsm**: Version 1 (Industry risk: A)
- **corporates_A_2.xlsm**: Version 2 (Industry risk: BBB) ← Change detected
- **Currency**: EUR
- **Country**: Federal Republic of Germany
- **Accounting**: IFRS
- **Year-end**: December

### Company B - Automobiles & Parts Sector
- **corporates_B_1.xlsm**: Version 1 (Weights: 0.15/0.85)
- **corporates_B_2.xlsm**: Version 2 (Weights: 0.25/0.75) ← Change detected
- **Currency**: CHF
- **Country**: Swiss Confederation
- **Accounting**: IFRS
- **Year-end**: March

## File Structure
Each Excel file (.xlsm = macro-enabled) contains **5 sheets**.

### ⭐ MASTER Sheet (YOUR FOCUS)
- **40 rows × 13 columns**
- **THIS IS THE ONLY SHEET YOU NEED TO EXTRACT**
- Company metadata and configuration:
  - Rated entity name
  - Corporate sector classification
  - Rating methodologies applied
  - Industry risk scores and weights
  - Currency, country, accounting principles
  - Business year-end month
- **Challenge**: Non-standard structure
  - All columns named "Unnamed: 0-12"
  - Column 1 contains the field labels (e.g., "Rated Entity Name")
  - Column 2 contains the values
  - Key-value pair format, not standard table

### Requirements Sheet ⭐
- **8 rows × 1 column**
- **Business requirements for your data pipeline**
- Read this carefully - it defines success criteria!
- All 4 files have identical requirements

### Other Sheets (For Context Only - DO NOT Extract)
- **BusinessRiskProfiles**: Rating assessments (sparse data, 290×100)
- **ListData**: Reference data (680×47)
- **Settings**: Configuration metadata (7×7)

## Data Challenges

### 1. Non-Standard Key-Value Structure
MASTER sheet is not a standard table. You need custom parsing:
- Columns are "Unnamed: 0", "Unnamed: 1", "Unnamed: 2", etc.
- Row-based key-value pairs instead of column-based records
- Need to transform from vertical key-value format to horizontal table format

### 2. Version Tracking
Files A_1 vs A_2 and B_1 vs B_2 show the same company at different points in time:
- Company A: Industry risk changes from A to BBB
- Company B: Weights change from 0.15/0.85 to 0.25/0.75

Your data model must support version tracking and historical queries.

### 3. Multi-Currency
Company A uses EUR, Company B uses CHF. Consider currency handling in your model.

### 4. Data Quality
Some fields may be missing or malformed. Implement robust validation.

### 5. Idempotency
Re-processing the same file should not create duplicate records.

## Getting Started

1. **Open one file** and examine the MASTER sheet specifically
2. **Read the Requirements sheet** - your 8 business requirements are there
3. **Compare A_1 vs A_2 MASTER sheets** - see what changed and why versioning matters
4. **Design your schema** - how will you model this in a data warehouse?
5. **Plan your extraction logic** - how to parse the key-value structure?

## Business Context

These files simulate a credit rating analysis workflow where:
- Analysts perform multi-methodology assessments
- Companies are rated in discussion sessions (multiple versions per discussion)
- Ratings change over time (need for historical tracking)
- Multiple analysts contribute reviews (collaborative process)
- Reference data ensures consistency across assessments

Your pipeline should support all 8 requirements from the Requirements sheet while handling the data quality challenges inherent in Excel-based systems.

## Tips

- Use `pandas.read_excel()` with `sheet_name='MASTER'` to read the specific sheet
- The key-value structure means row 0 might be a header, and subsequent rows contain labels and values
- Look for patterns in how the data is organized (which column contains labels, which contains values)
- Think about how to handle missing or malformed data gracefully
- Consider creating a mapping of expected field names to handle variations

Good luck! 🚀
