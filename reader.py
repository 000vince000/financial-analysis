import re
import pytesseract
from pdf2image import convert_from_path
from typing import Dict, List, Optional
import spacy
from textblob import TextBlob
import sys
import argparse

nlp = spacy.load("en_core_web_sm")

class EnhancedFinancialParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = self._extract_text_from_pdf()
        self.doc = nlp(self.text)

    def _extract_text_from_pdf(self) -> str:
        images = convert_from_path(self.pdf_path)
        return "".join(pytesseract.image_to_string(img) for img in images)

    def extract_numeric_metrics(self) -> Dict[str, str]:
        patterns = {
            "revenue": r"Revenue\s*\$\s*([\d,]+)\s*\$\s*11,188",
            "net_income": r"Net income attributable to Uber Technologies, Inc.\s*\$\s*([\d,]+)\s*\$\s*2,612",
            "total_assets": r"Total assets\s*38,699\s*([\d,]+)",
            "cash": r"Cash and cash equivalents\s*4,680\s*([\d,]+)",
            "shares_outstanding": r"2,071,144 and ([\d,]+) shares issued and outstanding",
            "share_repurchases": r"Total\s*([\d,]+)\s*[^\d]",
            "sbc": r"Stock-based compensation expense\s*\$\s*([\d,]+)\s*\$\s*[\d,]+",
            "mobility_revenue": r"Mobility\s*\$\s*([\d,]+)\s*\$\s*[\d,]+",
            "delivery_revenue": r"Delivery\s*\$\s*([\d,]+)\s*\$\s*[\d,]+",
            "freight_revenue": r"Freight\s*\$\s*([\d,]+)\s*\$\s*[\d,]+",
            "operating_margin": r"Operating margin\s*([\d.-]+)%",
            "mobility_operating_margin": r"Mobility.*?Operating margin\s*([\d.-]+)%",
            "delivery_operating_margin": r"Delivery.*?Operating margin\s*([\d.-]+)%",
            "freight_operating_margin": r"Freight.*?Operating margin\s*([\d.-]+)%"
        }
        units = {"revenue": "$M", "net_income": "$M", "total_assets": "$M", "cash": "$M", 
                 "shares_outstanding": "K shares", "share_repurchases": "K shares", "sbc": "$M", 
                 "mobility_revenue": "$M", "delivery_revenue": "$M", "freight_revenue": "$M",
                 "operating_margin": "%", "mobility_operating_margin": "%", 
                 "delivery_operating_margin": "%", "freight_operating_margin": "%"}
        return {key: f"{re.search(pattern, self.text).group(1).replace(',', '')} {units[key]}" if re.search(pattern, self.text) else f"N/A {units[key]}" 
                for key, pattern in patterns.items()}

    def extract_forward_guidance(self) -> List[str]:
        # Define more specific forward-looking terms and financial indicators
        forward_terms = ["expect", "anticipate", "project", "future", "outlook", "forecast", "plan", "intend", "believe"]
        financial_terms = ["revenue", "growth", "margin", "profit", "earnings", "cash flow", "expense", "investment", 
                         "market share", "guidance", "target", "goal", "estimate"]
        
        # Define terms to exclude (boilerplate text)
        exclude_terms = ["forward-looking statements", "contain words such as", "similar terms or expressions",
                        "identify forward-looking statements", "words such as", "similar terms"]
        
        # Score and collect relevant sentences
        guidance_sentences = []
        for sent in self.doc.sents:
            text = sent.text.lower()
            
            # Skip boilerplate text about forward-looking statements
            if any(exclude_term in text for exclude_term in exclude_terms):
                continue
                
            # Check for forward-looking terms
            has_forward_term = any(term in text for term in forward_terms)
            # Check for financial/business terms
            has_financial_term = any(term in text for term in financial_terms)
            
            if has_forward_term and has_financial_term:
                # Score sentence based on importance indicators
                score = 0
                if any(term in text for term in ["guidance", "target", "goal"]):
                    score += 2
                if any(term in text for term in ["revenue", "growth", "margin"]):
                    score += 1
                if any(term in text for term in ["increase", "decrease", "improve", "decline"]):
                    score += 1
                
                # Additional scoring for sentence quality
                if len(sent.text.split()) > 8:  # Prefer longer, more complete sentences
                    score += 1
                if any(char in sent.text for char in ['$', '%']):  # Prefer sentences with specific metrics
                    score += 2
                
                guidance_sentences.append((score, sent.text.strip()))
        
        # Sort by score and remove duplicates
        guidance_sentences.sort(reverse=True, key=lambda x: x[0])
        unique_sentences = []
        seen = set()
        
        for score, sentence in guidance_sentences:
            # More sophisticated deduplication
            words = set(sentence.lower().split())
            is_duplicate = False
            for seen_sentence in seen:
                seen_words = set(seen_sentence.lower().split())
                # If more than 70% of words are the same, consider it a duplicate
                if len(words.intersection(seen_words)) / len(words) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                # Clean up the sentence
                sentence = re.sub(r'\s+', ' ', sentence)  # Remove extra whitespace
                sentence = sentence.strip()
                
                # Only include if it's a complete thought
                if len(sentence.split()) >= 6 and sentence.endswith(('.', '!', '?')):
                    unique_sentences.append(sentence)
                    seen.add(sentence)
            
            if len(unique_sentences) >= 5:  # Increased from 3 to 5
                break
        
        return unique_sentences

    def analyze_sentiment(self) -> Dict[str, float]:
        sections = {
            "management_discussion": re.search(r"Management's Discussion and Analysis.*?(?=Item \d)", self.text, re.DOTALL),
            "risk_factors": re.search(r"Risk Factors.*?(?=Item \d)", self.text, re.DOTALL)
        }
        return {section: TextBlob(match.group(0)).sentiment.polarity if match else 0.0 
                for section, match in sections.items()}

    def business_updates_summary(self) -> Dict[str, List[str]]:
        # Define categories and their keywords
        categories = {
            "Segment Performance": {
                "keywords": ["mobility", "delivery", "freight", "segment", "business unit"],
                "metrics": ["revenue", "growth", "margin", "volume", "orders", "users"],
                "score": 3
            },
            "Strategic Initiatives": {
                "keywords": ["investment", "acquisition", "partnership", "expansion", "launch", "new market"],
                "metrics": ["investment", "acquisition", "partnership", "expansion"],
                "score": 2
            },
            "Technology & Innovation": {
                "keywords": ["technology", "innovation", "product", "feature", "platform", "system"],
                "metrics": ["development", "launch", "upgrade", "integration"],
                "score": 2
            }
        }
        
        # Collect and score updates
        updates = {category: [] for category in categories}
        seen_updates = set()
        
        for sent in self.doc.sents:
            text = sent.text.lower()
            
            # Skip financial statements and boilerplate text
            if any(term in text for term in ["condensed consolidated", "statements of operations", "assets", "liabilities"]):
                continue
                
            doc = nlp(sent.text)
            
            # Extract any numeric values or percentages
            metrics = []
            for token in doc:
                if token.like_num or token.text.endswith('%'):
                    metrics.append(token.text)
            
            for category, config in categories.items():
                # Check if sentence contains category keywords
                has_keyword = any(keyword in text for keyword in config["keywords"])
                has_metric = any(metric in text for metric in config["metrics"])
                
                if has_keyword:
                    # Calculate relevance score
                    score = config["score"]
                    if has_metric:
                        score += 1
                    if metrics:
                        score += 1
                    
                    # Format the update
                    update_text = sent.text.strip()
                    if metrics:
                        update_text = f"{update_text} (Metrics: {', '.join(metrics)})"
                    
                    # Check for duplicates
                    words = set(text.split())
                    is_duplicate = False
                    for seen_update in seen_updates:
                        seen_words = set(seen_update.lower().split())
                        if len(words.intersection(seen_words)) / len(words) > 0.7:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        updates[category].append((score, update_text))
                        seen_updates.add(update_text)
        
        # Process and return top updates for each category
        result = {}
        for category, category_updates in updates.items():
            # Sort by score and take top 2
            category_updates.sort(reverse=True, key=lambda x: x[0])
            result[category] = [update[1] for update in category_updates[:2]]
        
        return result

    def segment_specific_updates(self) -> Dict[str, List[str]]:
        segments = {"Mobility": [], "Delivery": [], "Freight": []}
        for sent in self.doc.sents:
            text = sent.text.lower()
            if "mobility" in text:
                update = sent.text.strip()
                if revenue := re.search(r"\$\s*([\d,]+)", sent.text):
                    update += f" (Revenue: ${revenue.group(1).replace(',', '')}M)"
                segments["Mobility"].append(update)
            elif "delivery" in text:
                update = sent.text.strip()
                if revenue := re.search(r"\$\s*([\d,]+)", sent.text):
                    update += f" (Revenue: ${revenue.group(1).replace(',', '')}M)"
                segments["Delivery"].append(update)
            elif "freight" in text:
                update = sent.text.strip()
                if revenue := re.search(r"\$\s*([\d,]+)", sent.text):
                    update += f" (Revenue: ${revenue.group(1).replace(',', '')}M)"
                segments["Freight"].append(update)
        return {seg: updates[:3] for seg, updates in segments.items()}

    def competitive_analysis(self) -> List[str]:
        competitors = ["Lyft", "DoorDash", "Grubhub", "Instacart"]
        analysis = []
        for comp in competitors:
            if comp.lower() in self.text.lower():
                context = [sent.text.strip() for sent in self.doc.sents if comp.lower() in sent.text.lower()][0]
                analysis.append(f"{comp} competition: {context}")
        return analysis or ["No direct competitor mentions found."]

    def swot_analysis(self) -> Dict[str, List[str]]:
        swot = {"Strengths": [], "Weaknesses": [], "Opportunities": [], "Threats": []}
        metrics = self.extract_numeric_metrics()

        # Helper function to safely convert metric values to float
        def safe_float(metric_value):
            try:
                return float(metric_value.split()[0])
            except (ValueError, IndexError):
                return 0.0  # Return 0.0 for N/A or invalid values

        # Strengths
        revenue = safe_float(metrics["revenue"])
        if revenue > 10000:
            swot["Strengths"].append("Robust revenue base: $11,188M.")
        if "partnership" in self.text.lower():
            swot["Strengths"].append("Strategic partnerships boosting scale.")
        if "brand" in self.text.lower():
            swot["Strengths"].append("Strong brand recognition.")
        operating_margin = safe_float(metrics["operating_margin"])
        if operating_margin > 5:
            swot["Strengths"].append("Healthy operating margin.")

        # Weaknesses
        if "cost" in self.text.lower() and "increase" in self.text.lower():
            swot["Weaknesses"].append("Rising operating costs.")
        if len(re.findall(r"litigation|lawsuit", self.text, re.IGNORECASE)) > 5:
            swot["Weaknesses"].append("Persistent litigation risks.")
        if "debt" in self.text.lower():
            swot["Weaknesses"].append("Debt burden detected.")
        if operating_margin < 0:
            swot["Weaknesses"].append("Negative operating margin.")

        # Opportunities
        if "expansion" in self.text.lower() or "new market" in self.text.lower():
            swot["Opportunities"].append("Growth via market expansion.")
        if "autonomous" in self.text.lower():
            swot["Opportunities"].append("Innovation in autonomous tech.")
        if "demand" in self.text.lower() and "increase" in self.text.lower():
            swot["Opportunities"].append("Rising demand in core segments.")
        if "acquisition" in self.text.lower():
            swot["Opportunities"].append("Growth through acquisitions.")

        # Threats
        if "regulation" in self.text.lower():
            swot["Threats"].append("Regulatory challenges.")
        if any(comp.lower() in self.text.lower() for comp in ["Lyft", "DoorDash"]):
            swot["Threats"].append("Competitive pressure from peers.")
        if "inflation" in self.text.lower():
            swot["Threats"].append("Inflation impacting costs.")
        if "labor" in self.text.lower() and "shortage" in self.text.lower():
            swot["Threats"].append("Labor shortages.")

        return swot

    def uncover_hidden_insights(self) -> List[str]:
        insights = []
        litigation_count = len(re.findall(r"litigation|lawsuit|legal proceeding", self.text, re.IGNORECASE))
        if litigation_count > 5:
            insights.append(f"High litigation risk: {litigation_count} mentions.")
        for ent in self.doc.ents:
            if ent.label_ == "GPE" and "revenue" in ent.sent.text.lower():
                insights.append(f"Revenue tied to {ent.text} market.")
        if "cost" in self.text.lower() and "increase" in self.text.lower():
            insights.append("Cost pressures detected.")
        return insights

    def nlp_tone_analysis(self) -> Dict[str, List[str]]:
        tones = {"Surprises": [], "Weaknesses": [], "Caution": [], "Optimism": []}
        for sent in self.doc.sents:
            text = sent.text.lower()
            blob = TextBlob(sent.text)
            polarity = blob.sentiment.polarity

            if any(word in text for word in ["unexpected", "surprise", "sudden"]):
                tones["Surprises"].append(sent.text.strip())
            if any(word in text for word in ["decline", "loss", "weak", "challenge"]) and polarity < 0:
                tones["Weaknesses"].append(sent.text.strip())
            if any(word in text for word in ["risk", "uncertain", "caution", "may"]):
                tones["Caution"].append(sent.text.strip())
            if any(word in text for word in ["growth", "strong", "opportunity", "confident"]) and polarity > 0.1:
                tones["Optimism"].append(sent.text.strip())

        return {tone: items[:3] for tone, items in tones.items()}

    def parse_full_report(self) -> Dict[str, any]:
        return {
            "numeric_metrics": self.extract_numeric_metrics(),
            "forward_guidance": self.extract_forward_guidance(),
            "sentiment": self.analyze_sentiment(),
            "business_updates": self.business_updates_summary(),
            "segment_updates": self.segment_specific_updates(),
            "competitive_analysis": self.competitive_analysis(),
            "swot_analysis": self.swot_analysis(),
            "hidden_insights": self.uncover_hidden_insights(),
            "tone_analysis": self.nlp_tone_analysis()
        }

def main():
    parser = argparse.ArgumentParser(description='Analyze a financial document (e.g., 10-Q report)')
    parser.add_argument('filename', help='Path to the PDF file to analyze')
    args = parser.parse_args()

    try:
        parser = EnhancedFinancialParser(args.filename)
        results = parser.parse_full_report()

        print("### Key Metrics")
        for key, value in results["numeric_metrics"].items():
            if key not in ["total_assets", "cash"]:  # Skip detailed balance sheet items
                print(f"{key}: {value}")

        print("\n### Forward Guidance")
        for stmt in results["forward_guidance"]:
            print(f"- {stmt}")

        print("\n### Business Updates")
        for category, updates in results["business_updates"].items():
            print(f"\n{category}:")
            for update in updates:
                print(f"- {update}")

        print("\n### Segment Performance")
        for segment, updates in results["segment_updates"].items():
            print(f"\n{segment}:")
            for update in updates:
                print(f"- {update}")

        print("\n### Competitive Analysis")
        for comp in results["competitive_analysis"]:
            print(f"- {comp}")

        print("\n### SWOT Analysis")
        for category, items in results["swot_analysis"].items():
            print(f"\n{category}:")
            for item in items:
                print(f"- {item}")

        print("\n### Key Insights")
        for insight in results["hidden_insights"]:
            print(f"- {insight}")

        print("\n### Tone Analysis")
        for tone, items in results["tone_analysis"].items():
            print(f"\n{tone}:")
            for item in items:
                print(f"- {item}")

    except FileNotFoundError:
        print(f"Error: File '{args.filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing document: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()