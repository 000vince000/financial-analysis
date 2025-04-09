# Financial Document Reader

This tool is designed to analyze and extract key information from financial documents (like 10-Q reports) using OCR and NLP techniques.

## How It Works

The reader uses several key technologies to process and analyze financial documents:

1. **PDF to Text Conversion**: Uses `pdf2image` to convert PDF pages to images and `pytesseract` for OCR to extract text.

2. **Natural Language Processing**: Uses `spacy` for advanced text analysis and `textblob` for sentiment analysis.

3. **Key Information Extraction**: The tool can extract:
   - Numeric metrics (revenue, net income, assets, etc.)
   - Forward guidance statements
   - Business updates and segment-specific information
   - Competitive analysis
   - SWOT analysis
   - Sentiment analysis
   - Hidden insights and tone analysis

## Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (macOS):
```bash
brew install tesseract
```

4. Install Poppler (required for PDF processing):
```bash
brew install poppler
```

5. Download spaCy language model:
```bash
python -m spacy download en_core_web_sm
```

## Usage

### Command Line Usage

The simplest way to use the tool is from the command line:

```bash
python reader.py path/to/your/document.pdf
```

This will analyze the document and print all extracted information to the console.

### Programmatic Usage

You can also use the tool programmatically:

```python
from reader import EnhancedFinancialParser

# Initialize the parser with your PDF file
parser = EnhancedFinancialParser("your_document.pdf")

# Get a complete analysis
results = parser.parse_full_report()

# Or get specific analyses:
metrics = parser.extract_numeric_metrics()
guidance = parser.extract_forward_guidance()
sentiment = parser.analyze_sentiment()
updates = parser.business_updates_summary()
segments = parser.segment_specific_updates()
competitors = parser.competitive_analysis()
swot = parser.swot_analysis()
insights = parser.uncover_hidden_insights()
tone = parser.nlp_tone_analysis()
```

## Output Format

The `parse_full_report()` method returns a dictionary with the following structure:

```python
{
    "numeric_metrics": {
        "revenue": "value $M",
        "net_income": "value $M",
        "total_assets": "value $M",
        # ... other metrics
    },
    "forward_guidance": [
        "statement 1",
        "statement 2",
        # ... guidance statements
    ],
    "sentiment": {
        "management_discussion": float,
        "risk_factors": float
    },
    "business_updates": [
        "update 1",
        "update 2",
        # ... business updates
    ],
    "segment_updates": {
        "Mobility": ["update 1", "update 2"],
        "Delivery": ["update 1", "update 2"],
        "Freight": ["update 1", "update 2"]
    },
    "competitive_analysis": [
        "competitor 1 analysis",
        "competitor 2 analysis"
    ],
    "swot_analysis": {
        "Strengths": ["strength 1", "strength 2"],
        "Weaknesses": ["weakness 1", "weakness 2"],
        "Opportunities": ["opportunity 1", "opportunity 2"],
        "Threats": ["threat 1", "threat 2"]
    },
    "hidden_insights": [
        "insight 1",
        "insight 2"
    ],
    "tone_analysis": {
        "Surprises": ["statement 1", "statement 2"],
        "Weaknesses": ["statement 1", "statement 2"],
        "Caution": ["statement 1", "statement 2"],
        "Optimism": ["statement 1", "statement 2"]
    }
}
```

## Example

### Command Line Example
```bash
python reader.py uber_10q.pdf
```

### Programmatic Example
```python
from reader import EnhancedFinancialParser

# Initialize parser with a 10-Q report
parser = EnhancedFinancialParser("uber_10q.pdf")

# Get complete analysis
results = parser.parse_full_report()

# Print numeric metrics
print("### Numeric Metrics")
for key, value in results["numeric_metrics"].items():
    print(f"{key}: {value}")

# Print SWOT analysis
print("\n### SWOT Analysis")
for category, items in results["swot_analysis"].items():
    print(f"\n{category}:")
    for item in items:
        print(f"- {item}")
```

## Notes

- The tool is optimized for financial documents like 10-Q reports
- OCR quality depends on the PDF quality
- Some metrics and patterns are specifically tuned for certain types of financial documents
- The tool uses predefined patterns to extract numeric metrics, which may need adjustment for different document formats 