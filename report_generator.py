"""
Enterprise Report Generator v2.0
Hybrid AI (Groq) + Template-based fallback system
Handles financial, sales, operational, and custom reports
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import numpy as np
from groq import Groq
import io
import sys
import traceback
import warnings
warnings.filterwarnings('ignore')

class ReportGenerator:
    """
    Production-grade report generator with multiple strategies:
    1. AI-Powered Analysis (Primary) - Uses Groq LLM
    2. Template-Based (Fallback) - Rule-based when AI fails
    3. Hybrid Mode - AI enhances template output
    4. Adaptive Mode - Dynamically selects best approach
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ReportGenerator with optional API key
        
        Args:
            api_key: Optional Groq API key. If not provided, will look for GROQ_API_KEY environment variable
        """
        self.client = None
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                self.ai_available = True
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")
                self.ai_available = False
        else:
            self.ai_available = False
            print("Warning: No GROQ_API_KEY found. Running in template-only mode.")
        
        # Business analysis frameworks
        self.FRAMEWORKS = {
            "financial": self._financial_framework,
            "sales": self._sales_framework,
            "operational": self._operational_framework,
            "general": self._general_framework
        }
        
        # Report templates for fallback mode
        self.TEMPLATES = self._load_templates()
        
        # Model configurations
        self.MODELS = {
            "high_quality": "llama-3.3-70b-versatile",
            "fast": "mixtral-8x7b-32768",
            "balanced": "llama-3.1-8b-instant"
        }
        
        # Default model
        self.default_model = self.MODELS["high_quality"]
    
    def _load_templates(self) -> Dict:
        """Structured templates for different report types"""
        return {
            "financial": {
                "sections": [
                    "Executive Summary",
                    "Revenue Analysis", 
                    "Cost Structure",
                    "Profitability Metrics",
                    "Cash Flow Assessment",
                    "Risk Factors",
                    "Recommendations"
                ],
                "kpis": ["Revenue", "Gross Margin", "Operating Margin", "Net Profit", "ROI", "Cash Conversion Cycle"],
                "default_focus": "profit"
            },
            "sales": {
                "sections": [
                    "Executive Summary",
                    "Pipeline Analysis",
                    "Conversion Metrics", 
                    "Performance by Segment",
                    "Trends & Forecasting",
                    "Action Items"
                ],
                "kpis": ["Total Sales", "Conversion Rate", "Average Deal Size", "Sales Cycle Length", "Win Rate", "Pipeline Value"],
                "default_focus": "growth"
            },
            "operational": {
                "sections": [
                    "Operations Overview",
                    "Efficiency Metrics",
                    "Quality Indicators",
                    "Capacity Utilization", 
                    "Bottleneck Analysis",
                    "Optimization Recommendations"
                ],
                "kpis": ["Throughput", "Cycle Time", "Quality Rate", "Capacity Utilization", "Cost Per Unit", "On-Time Delivery"],
                "default_focus": "full"
            },
            "general": {
                "sections": [
                    "Executive Summary",
                    "Data Overview",
                    "Key Insights",
                    "Trend Analysis",
                    "Recommendations"
                ],
                "kpis": ["Data Points", "Analysis Depth", "Action Items"],
                "default_focus": "full"
            }
        }
    
    # ==================== FRAMEWORK METHODS ====================
    
    def _financial_framework(self, df: pd.DataFrame, metrics: Dict) -> Dict:
        """Financial analysis framework"""
        analysis = {}
        
        if df is not None and len(df) > 0:
            # Calculate financial ratios
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            # Identify potential revenue and cost columns
            revenue_keywords = ['revenue', 'sales', 'income', 'gross']
            cost_keywords = ['cost', 'expense', 'cogs', 'operating']
            
            revenue_cols = [col for col in numeric_cols if any(kw in col.lower() for kw in revenue_keywords)]
            cost_cols = [col for col in numeric_cols if any(kw in col.lower() for kw in cost_keywords)]
            
            if revenue_cols and cost_cols:
                for rev_col in revenue_cols[:1]:  # Take first revenue column
                    for cost_col in cost_cols[:1]:  # Take first cost column
                        try:
                            analysis['gross_margin'] = {
                                'value': float(df[rev_col].sum() - df[cost_col].sum()),
                                'percentage': float((df[rev_col].sum() - df[cost_col].sum()) / df[rev_col].sum() * 100)
                                if df[rev_col].sum() != 0 else 0
                            }
                        except:
                            pass
            
            # Calculate growth rates if date column exists
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols and revenue_cols:
                try:
                    df_sorted = df.sort_values(date_cols[0])
                    if len(df_sorted) > 1:
                        first_rev = df_sorted.iloc[0][revenue_cols[0]]
                        last_rev = df_sorted.iloc[-1][revenue_cols[0]]
                        if first_rev != 0:
                            growth = (last_rev - first_rev) / first_rev * 100
                            analysis['revenue_growth'] = float(growth)
                except:
                    pass
        
        return analysis
    
    def _sales_framework(self, df: pd.DataFrame, metrics: Dict) -> Dict:
        """Sales analysis framework"""
        analysis = {}
        
        if df is not None and len(df) > 0:
            # Look for sales-specific columns
            stage_keywords = ['stage', 'status', 'phase']
            amount_keywords = ['amount', 'value', 'size']
            date_keywords = ['date', 'created', 'closed']
            
            stage_cols = [col for col in df.columns if any(kw in col.lower() for kw in stage_keywords)]
            amount_cols = df.select_dtypes(include=[np.number]).columns
            date_cols = [col for col in df.columns if any(kw in col.lower() for kw in date_keywords)]
            
            # Calculate conversion metrics if stage information exists
            if stage_cols and len(df) > 0:
                stage_col = stage_cols[0]
                unique_stages = df[stage_col].unique()
                analysis['stage_distribution'] = {
                    str(stage): int(len(df[df[stage_col] == stage]))
                    for stage in unique_stages[:10]  # Limit to 10 stages
                }
            
            # Calculate average deal size
            if len(amount_cols) > 0:
                amount_col = amount_cols[0]
                analysis['average_amount'] = float(df[amount_col].mean())
                analysis['total_amount'] = float(df[amount_col].sum())
        
        return analysis
    
    def _operational_framework(self, df: pd.DataFrame, metrics: Dict) -> Dict:
        """Operational analysis framework"""
        analysis = {}
        
        if df is not None and len(df) > 0:
            # Look for operational metrics
            efficiency_keywords = ['efficiency', 'throughput', 'output', 'production']
            time_keywords = ['time', 'duration', 'cycle']
            quality_keywords = ['quality', 'defect', 'error', 'reject']
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            # Calculate basic statistics for numeric columns
            for col in numeric_cols[:5]:  # Limit to 5 columns
                analysis[f'{col}_stats'] = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max())
                }
            
            # Identify potential bottlenecks (high variance)
            high_variance_cols = []
            for col in numeric_cols:
                if df[col].std() > df[col].mean() * 0.5:  # High variance threshold
                    high_variance_cols.append(col)
            
            if high_variance_cols:
                analysis['high_variance_metrics'] = high_variance_cols[:5]
        
        return analysis
    
    def _general_framework(self, df: pd.DataFrame, metrics: Dict) -> Dict:
        """General analysis framework"""
        analysis = {
            'data_summary': {
                'rows': len(df) if df is not None else 0,
                'columns': list(df.columns) if df is not None else [],
                'data_types': {col: str(df[col].dtype) for col in df.columns} if df is not None else {}
            }
        }
        
        if df is not None and len(df) > 0:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            # Basic statistics
            if len(numeric_cols) > 0:
                analysis['numeric_summary'] = {}
                for col in numeric_cols[:3]:  # Limit to 3 columns
                    analysis['numeric_summary'][col] = {
                        'mean': float(df[col].mean()),
                        'total': float(df[col].sum())
                    }
            
            # Check for missing values
            missing_values = df.isnull().sum().to_dict()
            analysis['missing_values'] = {k: int(v) for k, v in missing_values.items() if v > 0}
        
        return analysis
    
    # ==================== PUBLIC API ====================
    
    def generate_report(self, 
                       data_content: str, 
                       data_type: str = "text",
                       user_name: str = "User",
                       business_type: str = "General Business",
                       report_focus: str = "auto",
                       output_format: str = "markdown",
                       user_role: Optional[str] = None) -> str:  # Added user_role parameter
        """
        Main entry point for report generation
        
        Args:
            data_content: The data to analyze (CSV, text, etc.)
            data_type: Type of data ("csv", "text", "json", "auto")
            user_name: Name for report personalization
            business_type: Type of business/industry
            report_focus: "profit", "growth", "loss", "full", or "auto"
            output_format: "markdown" or "html"
            user_role: Optional user role for context (e.g., "Manager", "Analyst", "Executive")
            
        Returns:
            Generated report as string
        """
        try:
            # Step 1: Auto-detect data type if needed
            if data_type == "auto":
                data_type = self._detect_data_type(data_content)
            
            # Step 2: Detect what kind of data this is
            schema = self._detect_schema(data_content, business_type)
            
            # Step 3: Parse and calculate metrics
            df, metrics = self._extract_metrics(data_content, data_type, schema)
            
            # Step 4: Run framework analysis
            framework = self._select_framework(schema, business_type)
            framework_analysis = self.FRAMEWORKS[framework](df, metrics)
            metrics['framework_analysis'] = framework_analysis
            
            # Step 5: Auto-select focus if needed
            if report_focus == "auto":
                report_focus = self.TEMPLATES.get(framework, {}).get('default_focus', 'full')
            
            # Step 6: Generate report (AI first, fallback to template)
            report = self._generate_with_fallback(
                data_content=data_content,
                metrics=metrics,
                framework=framework,
                schema=schema,
                user_name=user_name,
                report_focus=report_focus,
                dataframe=df,
                user_role=user_role  # Pass user_role to internal methods
            )
            
            # Step 7: Format output
            if output_format == "html":
                report = self._convert_to_html(report)
            
            return report
            
        except Exception as e:
            # Ultimate fallback - structured error report
            error_trace = traceback.format_exc()
            return self._generate_error_report(str(e), data_content[:500], error_trace)
    
    # ==================== DETECTION & PARSING ====================
    
    def _detect_data_type(self, content: str) -> str:
        """Auto-detect the type of data"""
        if not content or len(content.strip()) == 0:
            return "text"
        
        # Check for CSV/TSV
        lines = content.strip().split('\n')
        if len(lines) > 1:
            # Check for CSV (comma-separated)
            if ',' in lines[0] and len(lines[0].split(',')) > 1:
                return "csv"
            # Check for TSV (tab-separated)
            elif '\t' in lines[0] and len(lines[0].split('\t')) > 1:
                return "csv"  # Will handle as CSV with tab separator
        
        # Check for JSON
        content_stripped = content.strip()
        if (content_stripped.startswith('{') and content_stripped.endswith('}')) or \
           (content_stripped.startswith('[') and content_stripped.endswith(']')):
            try:
                json.loads(content)
                return "json"
            except:
                pass
        
        return "text"
    
    def _detect_schema(self, content: str, business_type: str) -> Dict:
        """
        Analyze content to determine:
        - Is this financial data? (contains $, revenue, cost, profit)
        - Is this sales data? (contains leads, deals, customers)
        - Is this operational? (contains units, time, efficiency)
        """
        if not content:
            return {
                "type": "general",
                "confidence": 0.0,
                "indicators_found": {"financial": 0, "sales": 0, "operational": 0},
                "business_type": business_type
            }
        
        content_lower = content.lower()
        
        # Financial indicators
        financial_terms = ['revenue', 'profit', 'cost', 'margin', 'expense', 'budget', 
                          'cash flow', 'balance sheet', 'p&l', 'income', '$', 'dollar',
                          'financial', 'earning', 'expenditure']
        # Sales indicators  
        sales_terms = ['lead', 'deal', 'customer', 'pipeline', 'conversion', 'sales',
                      'opportunity', 'forecast', 'quota', 'win rate', 'client',
                      'prospect', 'account', 'territory']
        # Operational indicators
        operational_terms = ['production', 'inventory', 'supply chain', 'manufacturing',
                           'logistics', 'efficiency', 'throughput', 'quality',
                           'operation', 'process', 'capacity', 'output']
        
        scores = {
            "financial": sum(1 for term in financial_terms if term in content_lower),
            "sales": sum(1 for term in sales_terms if term in content_lower),
            "operational": sum(1 for term in operational_terms if term in content_lower)
        }
        
        # Determine primary type
        if max(scores.values()) > 0:
            primary_type = max(scores, key=scores.get)
            confidence = scores[primary_type] / (sum(scores.values()) + 0.001)
        else:
            primary_type = "general"
            confidence = 0.0
            
        return {
            "type": primary_type,
            "confidence": confidence,
            "indicators_found": scores,
            "business_type": business_type,
            "content_length": len(content)
        }
    
    def _extract_metrics(self, content: str, data_type: str, schema: Dict) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Parse data and calculate key metrics using Pandas
        Returns: (DataFrame or None, dict of calculated metrics)
        """
        metrics = {
            "row_count": 0,
            "column_count": 0,
            "numeric_columns": [],
            "calculated": {},
            "raw_sample": content[:1000],
            "parsing_method": data_type,
            "schema": schema
        }
        
        df = None
        
        try:
            if data_type == "csv":
                # Try to parse as CSV with multiple separators
                separators = [',', '\t', ';', '|']
                for sep in separators:
                    try:
                        df = pd.read_csv(io.StringIO(content), sep=sep)
                        metrics["separator"] = sep
                        break
                    except:
                        continue
                
                # If still None, try with no header
                if df is None:
                    try:
                        df = pd.read_csv(io.StringIO(content), header=None)
                        metrics["has_header"] = False
                    except:
                        pass
            
            elif data_type == "json":
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    elif isinstance(data, dict):
                        # Flatten nested dictionaries
                        df = pd.json_normalize(data)
                    else:
                        metrics["json_structure"] = type(data).__name__
                except json.JSONDecodeError:
                    # Try line-delimited JSON
                    try:
                        lines = [json.loads(line) for line in content.strip().split('\n') if line.strip()]
                        df = pd.DataFrame(lines)
                    except:
                        pass
            
            if df is not None:
                # Clean column names
                df.columns = [str(col).strip().replace(' ', '_').lower() for col in df.columns]
                
                metrics["row_count"] = len(df)
                metrics["column_count"] = len(df.columns)
                metrics["columns"] = list(df.columns)
                
                # Auto-detect numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                metrics["numeric_columns"] = numeric_cols
                
                # Calculate standard metrics for numeric columns (limit to 10 columns)
                for col in numeric_cols[:10]:
                    try:
                        col_data = df[col].dropna()
                        if len(col_data) > 0:
                            metrics["calculated"][col] = {
                                "sum": float(col_data.sum()),
                                "mean": float(col_data.mean()),
                                "median": float(col_data.median()),
                                "min": float(col_data.min()),
                                "max": float(col_data.max()),
                                "std": float(col_data.std()) if len(col_data) > 1 else 0.0,
                                "count": int(len(col_data)),
                                "missing": int(df[col].isnull().sum()),
                                "zeros": int((df[col] == 0).sum())
                            }
                    except:
                        continue
                
                # Detect date columns
                date_cols = []
                for col in df.columns:
                    # Check column name for date indicators
                    if any(keyword in col.lower() for keyword in ['date', 'time', 'year', 'month', 'day']):
                        try:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            if df[col].notna().any():
                                date_cols.append(col)
                        except:
                            pass
                
                if date_cols:
                    metrics["date_columns"] = date_cols
                    primary_date_col = date_cols[0]
                    date_range = df[primary_date_col].dropna()
                    if len(date_range) > 0:
                        metrics["date_range"] = {
                            "start": str(date_range.min()),
                            "end": str(date_range.max()),
                            "days": int((date_range.max() - date_range.min()).days) if len(date_range) > 1 else 0
                        }
                
                # Calculate data quality metrics
                metrics["data_quality"] = {
                    "total_cells": df.size,
                    "missing_cells": int(df.isnull().sum().sum()),
                    "missing_percentage": float(df.isnull().sum().sum() / df.size * 100) if df.size > 0 else 0,
                    "duplicate_rows": int(df.duplicated().sum()),
                    "duplicate_percentage": float(df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
                }
                
                # Sample data
                if len(df) > 0:
                    metrics["sample_data"] = df.head(5).to_dict(orient='records')
                    
        except Exception as e:
            metrics["parse_error"] = str(e)
            metrics["error_type"] = type(e).__name__
        
        return df, metrics
    
    def _select_framework(self, schema: Dict, business_type: str) -> str:
        """Select analysis framework based on detected schema"""
        detected = schema["type"]
        
        # Override with user selection if specific
        business_lower = business_type.lower()
        if any(term in business_lower for term in ["retail", "e-commerce", "store", "shop"]):
            if detected == "general":
                return "sales"
        elif any(term in business_lower for term in ["manufacturing", "factory", "production", "plant"]):
            if detected == "general":
                return "operational"
        elif any(term in business_lower for term in ["bank", "finance", "investment", "accounting"]):
            if detected == "general":
                return "financial"
        
        return detected if detected in self.FRAMEWORKS else "general"
    
    # ==================== GENERATION STRATEGIES ====================
    
    def _generate_with_fallback(self, 
                               data_content: str,
                               metrics: Dict,
                               framework: str,
                               schema: Dict,
                               user_name: str,
                               report_focus: str,
                               dataframe: Optional[pd.DataFrame] = None,
                               user_role: Optional[str] = None) -> str:  # Added user_role
        """
        Try AI first, if it fails or produces low-quality output,
        fall back to template-based generation
        """
        # Try AI generation if API is available
        if self.ai_available and self.client:
            try:
                ai_report = self._generate_ai_report(
                    data_content=data_content,
                    metrics=metrics,
                    framework=framework,
                    schema=schema,
                    user_name=user_name,
                    report_focus=report_focus,
                    dataframe=dataframe,
                    user_role=user_role  # Pass user_role
                )
                
                # Validate AI output
                if self._validate_report(ai_report):
                    print(f"✓ AI report generated successfully using {framework} framework")
                    return ai_report
                else:
                    print("⚠ AI report validation failed, using hybrid mode")
                    hybrid_report = self._generate_hybrid_report(
                        ai_report, 
                        data_content,
                        metrics,
                        framework,
                        schema,
                        user_name,
                        report_focus,
                        dataframe,
                        user_role  # Pass user_role
                    )
                    if self._validate_report(hybrid_report):
                        return hybrid_report
                    else:
                        print("⚠ Hybrid report validation failed, using template fallback")
                        return self._generate_template_report(
                            data_content, metrics, framework, schema, user_name, 
                            report_focus, dataframe, user_role  # Pass user_role
                        )
            except Exception as e:
                print(f"⚠ AI generation failed: {e}, using template fallback")
                return self._generate_template_report(
                    data_content, metrics, framework, schema, user_name, 
                    report_focus, dataframe, user_role  # Pass user_role
                )
        else:
            print("ℹ AI not available, using template-based generation")
            return self._generate_template_report(
                data_content, metrics, framework, schema, user_name, 
                report_focus, dataframe, user_role  # Pass user_role
            )
    
    def _generate_ai_report(self, 
                           data_content: str,
                           metrics: Dict,
                           framework: str,
                           schema: Dict,
                           user_name: str,
                           report_focus: str,
                           dataframe: Optional[pd.DataFrame] = None,
                           user_role: Optional[str] = None) -> str:  # Added user_role
        """
        Generate report using Groq LLM with detailed, structured prompting
        """
        if not self.client:
            raise ValueError("Groq client not initialized")
        
        # Select model based on data size
        model = self._select_model(data_content, metrics)
        
        # Build comprehensive prompt based on framework
        system_prompt = self._build_system_prompt(framework, report_focus, user_role)
        user_prompt = self._build_user_prompt(
            data_content=data_content,
            metrics=metrics,
            framework=framework,
            schema=schema,
            user_name=user_name,
            report_focus=report_focus,
            dataframe=dataframe,
            user_role=user_role  # Pass user_role
        )
        
        try:
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                temperature=0.2,  # Low temperature for consistent, analytical output
                max_tokens=4000,
                top_p=0.9,
                stream=False
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            # Try with fallback model
            if model != self.MODELS["fast"]:
                print(f"⚠ Primary model failed: {e}, trying fallback model")
                try:
                    chat_completion = self.client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        model=self.MODELS["fast"],
                        temperature=0.2,
                        max_tokens=4000,
                        top_p=0.9,
                        stream=False
                    )
                    return chat_completion.choices[0].message.content
                except:
                    raise
            else:
                raise
    
    def _select_model(self, data_content: str, metrics: Dict) -> str:
        """Select appropriate model based on data size and complexity"""
        content_length = len(data_content)
        row_count = metrics.get("row_count", 0)
        
        if content_length > 10000 or row_count > 1000:
            # Large datasets - use faster model
            return self.MODELS["fast"]
        elif content_length > 5000 or row_count > 500:
            # Medium datasets - use balanced model
            return self.MODELS.get("balanced", self.MODELS["high_quality"])
        else:
            # Small datasets - use high-quality model
            return self.MODELS["high_quality"]
    
    def _build_system_prompt(self, framework: str, report_focus: str, user_role: Optional[str] = None) -> str:
        """
        Detailed system prompts for each business framework
        These guide the AI to produce consistent, professional reports
        """
        
        base_prompt = f"""You are an expert Business Intelligence Analyst with 15+ years of experience.
Your task is to generate executive-level business reports that are:
1. Data-driven with specific insights
2. Actionable with clear recommendations
3. Professional in tone and structure
4. Concise but comprehensive
5. Based SOLELY on the data provided - do not make up numbers or facts

Target Audience: {user_role if user_role else 'Business Executives and Decision Makers'}

Always format your response with clear Markdown headers (## for sections, ### for subsections).
Include specific numbers, percentages, and calculations when possible.
Avoid generic statements - be specific to the data provided.
If certain analyses aren't possible with the given data, state this clearly.

Structure your report with clear sections and include a metadata section at the end:
**Report Metadata**
- Generated: [current date]
- Framework: [analysis type]
- Data Points: [number]
- Confidence: [high/medium/low]

Do not include any apologies or disclaimers about being an AI. Present as a human expert."""
        
        framework_prompts = {
            "financial": """
FINANCIAL ANALYSIS EXPERTISE:
- Analyze P&L, balance sheets, cash flow statements
- Calculate and interpret: Gross Margin, Operating Margin, Net Margin, ROE, ROA, Current Ratio
- Identify cost drivers and revenue trends
- Assess financial health and liquidity risks
- Provide specific recommendations for cost optimization or revenue growth
- Highlight anomalies and outliers in financial data

Structure your report with:
## Executive Summary (3-4 key findings)
## Financial Performance Overview
## Revenue Analysis (breakdown by segment if available)
## Cost Structure Analysis
## Profitability Metrics (with calculations)
## Cash Flow Assessment
## Risk Factors & Mitigation
## Strategic Recommendations (prioritized)

Always include a "Key Metrics Dashboard" section with calculated ratios and comparisons.""",
            
            "sales": """
SALES ANALYSIS EXPERTISE:
- Analyze sales pipelines, conversion funnels, and performance metrics
- Calculate: Conversion rates, Average Deal Size, Sales Cycle Length, Win/Loss ratios
- Identify top-performing segments and underperforming areas
- Assess pipeline health and forecast accuracy
- Recommend specific actions to improve sales performance
- Analyze seasonality and trends

Structure your report with:
## Executive Summary (pipeline health & key metrics)
## Sales Performance Overview
## Pipeline Analysis (by stage, source, or region)
## Conversion Metrics & Funnel Analysis
## Performance by Segment (product, region, rep)
## Trending & Forecasting
## Win/Loss Analysis (if data available)
## Action Plan (immediate 30-day, short-term 90-day, long-term)

Include specific numbers: "Conversion rate improved 15% from Q1" not "Conversion rate improved".
Use tables to present key metrics when appropriate.""",
            
            "operational": """
OPERATIONS ANALYSIS EXPERTISE:
- Analyze production efficiency, capacity utilization, and quality metrics
- Calculate: Throughput, Cycle Time, OEE (Overall Equipment Effectiveness), Quality Rate
- Identify bottlenecks and constraints using data
- Assess inventory levels and supply chain efficiency
- Recommend lean improvements and optimization strategies
- Calculate potential ROI for improvements

Structure your report with:
## Operations Overview
## Efficiency Metrics & Benchmarks
## Capacity Utilization Analysis
## Quality Indicators & Defect Analysis
## Bottleneck Identification
## Inventory & Supply Chain Assessment (if applicable)
## Cost Analysis (per unit, per hour)
## Optimization Recommendations with Estimated Impact

Focus on measurable improvements with ROI estimates.
Use bullet points for actionable recommendations.""",
            
            "general": """
GENERAL BUSINESS ANALYSIS:
- Provide comprehensive analysis of provided business data
- Identify key patterns, trends, and anomalies
- Calculate relevant KPIs based on data type
- Assess strengths, weaknesses, opportunities, threats (SWOT)
- Deliver actionable recommendations
- Highlight data quality issues if present

Structure your report with:
## Executive Summary (key insights)
## Data Overview & Quality Assessment
## Key Findings & Insights (with supporting data)
## Trend Analysis
## Risk Assessment
## Recommendations & Next Steps (prioritized)
## Data Limitations & Further Analysis Needed

Create clear action items with owners and timelines when possible."""
        }
        
        focus_context = {
            "profit": "FOCUS: Prioritize profitability analysis, cost optimization, margin improvement, and efficiency gains.",
            "growth": "FOCUS: Emphasize growth opportunities, market expansion, scaling strategies, and revenue enhancement.",
            "loss": "FOCUS: Concentrate on risk mitigation, cost reduction, problem-solving, and recovery strategies.",
            "full": "FOCUS: Provide balanced comprehensive analysis across all business dimensions."
        }
        
        # Role-specific context
        role_context = ""
        if user_role:
            role_lower = user_role.lower()
            if 'executive' in role_lower or 'ceo' in role_lower or 'director' in role_lower:
                role_context = "\n\nIMPORTANT: This report is for senior executives. Focus on strategic insights, high-level trends, and bottom-line impact. Keep it concise with clear executive summaries and actionable recommendations."
            elif 'manager' in role_lower:
                role_context = "\n\nIMPORTANT: This report is for managers. Include operational details, team performance metrics, and specific action plans for implementation."
            elif 'analyst' in role_lower:
                role_context = "\n\nIMPORTANT: This report is for analysts. Include detailed methodology, data quality assessment, statistical significance, and recommendations for further analysis."
        
        framework_prompt = framework_prompts.get(framework, framework_prompts["general"])
        focus_instruction = focus_context.get(report_focus, focus_context["full"])
        
        return base_prompt + "\n\n" + framework_prompt + "\n\n" + focus_instruction + role_context
    
    def _build_user_prompt(self, 
                          data_content: str,
                          metrics: Dict,
                          framework: str,
                          schema: Dict,
                          user_name: str,
                          report_focus: str,
                          dataframe: Optional[pd.DataFrame] = None,
                          user_role: Optional[str] = None) -> str:  # Added user_role
        """
        Build detailed user prompt with context and constraints
        """
        
        # Prepare data summary
        data_summary = f"""
DATA SUMMARY:
- Total Rows: {metrics.get('row_count', 'N/A')}
- Total Columns: {metrics.get('column_count', 'N/A')}
- Numeric Columns: {', '.join(metrics.get('numeric_columns', []))[:200]}
- Data Confidence: {schema.get('confidence', 0):.1%}
- Analysis Framework: {framework.upper()}
- User Role: {user_role if user_role else 'Not Specified'}
"""
        
        # Add calculated metrics if available
        if 'calculated' in metrics and metrics['calculated']:
            data_summary += "\nCALCULATED METRICS:\n"
            for col, calc in list(metrics['calculated'].items())[:5]:  # Limit to 5 columns
                data_summary += f"- {col}: Mean={calc.get('mean', 'N/A'):.2f}, Sum={calc.get('sum', 'N/A'):.2f}\n"
        
        # Add framework analysis
        if 'framework_analysis' in metrics:
            data_summary += "\nFRAMEWORK INSIGHTS:\n"
            for key, value in list(metrics['framework_analysis'].items())[:3]:
                data_summary += f"- {key}: {value}\n"
        
        # Truncate data if too long
        max_data_chars = 6000
        truncated_data = data_content[:max_data_chars]
        if len(data_content) > max_data_chars:
            truncated_data += f"\n\n[Note: {len(data_content) - max_data_chars} characters truncated for brevity]"
        
        # Add sample data if dataframe is available
        sample_data = ""
        if dataframe is not None and len(dataframe) > 0:
            sample_data = f"\n\nSAMPLE DATA (first 5 rows):\n{dataframe.head().to_string(index=False)}"
        
        prompt = f"""Generate a professional business report for {user_name}.

BUSINESS CONTEXT:
- Client/User: {user_name}
- User Role: {user_role if user_role else 'General Business User'}
- Industry/Sector: {schema['business_type']}
- Analysis Type: {framework.upper()} Analysis
- Report Focus: {report_focus.upper()}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{data_summary}

DATA QUALITY ASSESSMENT:
{json.dumps(metrics.get('data_quality', {}), indent=2)}

RAW DATA (truncated if long):
{truncated_data}{sample_data}

INSTRUCTIONS:
1. Base ALL analysis on the data provided above
2. Reference specific numbers and metrics from the data
3. If certain analyses can't be done due to data limitations, suggest what additional data would be needed
4. Provide actionable recommendations with clear next steps
5. Include a "Key Takeaways" section at the beginning
6. Format professionally with Markdown
7. Tailor the depth and technicality based on the user's role ({user_role})
8. End with a metadata section as instructed in system prompt

Remember: Quality over quantity. Better to have fewer but more accurate insights than many generic ones."""
        
        return prompt
    
    def _generate_hybrid_report(self, 
                               ai_report: str,
                               data_content: str,
                               metrics: Dict,
                               framework: str,
                               schema: Dict,
                               user_name: str,
                               report_focus: str,
                               dataframe: Optional[pd.DataFrame] = None,
                               user_role: Optional[str] = None) -> str:  # Added user_role
        """
        Combine AI output with template structure for higher reliability
        """
        # Extract sections from AI report
        sections = self._extract_sections_from_ai(ai_report)
        
        # Get template structure
        template = self.TEMPLATES.get(framework, self.TEMPLATES["general"])
        
        # Build report using template structure but AI content
        report_parts = []
        report_parts.append(f"# Business Intelligence Report\n")
        report_parts.append(f"**Generated for:** {user_name}\n")
        if user_role:
            report_parts.append(f"**User Role:** {user_role}\n")
        report_parts.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
        report_parts.append(f"**Framework:** {framework.title()} Analysis\n")
        report_parts.append(f"**Focus:** {report_focus.title()}\n")
        
        # Add key metrics upfront if available
        if 'calculated' in metrics and metrics['calculated']:
            report_parts.append("\n## Key Metrics at a Glance\n")
            for col, calc in list(metrics['calculated'].items())[:3]:
                report_parts.append(f"- **{col}:** Total = {calc.get('sum', 'N/A'):.2f}, Average = {calc.get('mean', 'N/A'):.2f}")
        
        # Use AI content for each template section
        for section in template['sections']:
            report_parts.append(f"\n## {section}\n")
            
            # Try to find matching content in AI report
            ai_content = self._find_section_in_ai(section, sections, ai_report)
            if ai_content:
                report_parts.append(ai_content)
            else:
                # Generate template-based content
                template_content = self._generate_template_section(
                    section, metrics, framework, report_focus, dataframe, user_role
                )
                report_parts.append(template_content)
        
        # Add data summary
        report_parts.append("\n## Data Summary & Methodology\n")
        report_parts.append(f"- Analysis performed using hybrid AI-Template approach")
        report_parts.append(f"- Data points analyzed: {metrics.get('row_count', 'N/A')}")
        report_parts.append(f"- Confidence score: {schema.get('confidence', 0):.1%}")
        report_parts.append(f"- User role considered: {user_role if user_role else 'Not specified'}")
        report_parts.append(f"- Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(report_parts)
    
    def _generate_template_report(self,
                                 data_content: str,
                                 metrics: Dict,
                                 framework: str,
                                 schema: Dict,
                                 user_name: str,
                                 report_focus: str,
                                 dataframe: Optional[pd.DataFrame] = None,
                                 user_role: Optional[str] = None) -> str:  # Added user_role
        """
        Generate report using template structure with calculated metrics
        """
        template = self.TEMPLATES.get(framework, self.TEMPLATES["general"])
        
        report_parts = []
        
        # Header
        report_parts.append(f"# Business Intelligence Report")
        report_parts.append(f"**Generated for:** {user_name}")
        if user_role:
            report_parts.append(f"**User Role:** {user_role}")
        report_parts.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        report_parts.append(f"**Industry:** {schema['business_type']}")
        report_parts.append(f"**Framework:** {framework.title()} Analysis")
        report_parts.append(f"**Focus:** {report_focus.title()}")
        report_parts.append(f"**Data Points:** {metrics.get('row_count', 'N/A')}")
        report_parts.append(f"**Confidence:** {schema.get('confidence', 0):.1%}")
        
        # Key Metrics Summary
        report_parts.append("\n## Key Metrics Summary\n")
        if 'calculated' in metrics and metrics['calculated']:
            for col, calc in list(metrics['calculated'].items())[:5]:
                report_parts.append(f"- **{col}:** Sum = {calc.get('sum', 'N/A'):.2f}, Avg = {calc.get('mean', 'N/A'):.2f}")
        else:
            report_parts.append("*No numeric metrics available for calculation*")
        
        # Template sections
        for section in template['sections']:
            report_parts.append(f"\n## {section}\n")
            content = self._generate_template_section(
                section, metrics, framework, report_focus, dataframe, user_role
            )
            report_parts.append(content)
        
        # Recommendations based on framework and user role
        report_parts.append("\n## Actionable Recommendations\n")
        recommendations = self._generate_recommendations(framework, metrics, report_focus, user_role)
        for i, rec in enumerate(recommendations, 1):
            report_parts.append(f"{i}. {rec}")
        
        # Data quality notes
        report_parts.append("\n## Data Quality Notes\n")
        dq = metrics.get('data_quality', {})
        if dq:
            report_parts.append(f"- Missing data: {dq.get('missing_percentage', 0):.1f}%")
            report_parts.append(f"- Duplicate rows: {dq.get('duplicate_percentage', 0):.1f}%")
        else:
            report_parts.append("*Data quality assessment not available*")
        
        # Next steps based on user role
        report_parts.append("\n## Next Steps & Further Analysis\n")
        next_steps = self._generate_next_steps(user_role, framework)
        for i, step in enumerate(next_steps, 1):
            report_parts.append(f"{i}. {step}")
        
        # Footer
        report_parts.append("\n---")
        report_parts.append(f"*Report generated automatically on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*")
        report_parts.append(f"*Method: Template-based analysis with calculated metrics*")
        if user_role:
            report_parts.append(f"*Tailored for: {user_role}*")
        
        return "\n".join(report_parts)
    
    def _generate_template_section(self,
                                  section: str,
                                  metrics: Dict,
                                  framework: str,
                                  report_focus: str,
                                  dataframe: Optional[pd.DataFrame] = None,
                                  user_role: Optional[str] = None) -> str:  # Added user_role
        """Generate content for a specific template section"""
        
        section_templates = {
            "Executive Summary": self._executive_summary_template,
            "Revenue Analysis": self._revenue_analysis_template,
            "Cost Structure": self._cost_structure_template,
            "Profitability Metrics": self._profitability_template,
            "Recommendations": self._recommendations_template,
            "Data Overview": self._data_overview_template,
            "Key Insights": self._key_insights_template,
            "Trend Analysis": self._trend_analysis_template,
            "Risk Assessment": self._risk_assessment_template
        }
        
        generator = section_templates.get(section, self._default_section_template)
        return generator(metrics, framework, report_focus, dataframe, user_role)
    
    def _executive_summary_template(self, metrics: Dict, framework: str, report_focus: str, 
                                   dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate executive summary"""
        summary = []
        
        # Tailor summary based on user role
        if user_role and 'executive' in user_role.lower():
            summary.append(f"**Executive Summary for {user_role}**")
            summary.append(f"This high-level analysis provides strategic insights based on {metrics.get('row_count', 'N/A')} data points.")
        else:
            summary.append(f"This {framework} analysis report provides insights based on {metrics.get('row_count', 'N/A')} data points.")
        
        if 'calculated' in metrics and metrics['calculated']:
            # Highlight top metrics
            for col, calc in list(metrics['calculated'].items())[:2]:
                summary.append(f"- Total {col}: {calc.get('sum', 'N/A'):.2f}")
                summary.append(f"- Average {col}: {calc.get('mean', 'N/A'):.2f}")
        
        summary.append(f"\n**Primary Focus:** {report_focus.title()}")
        summary.append(f"**Key Finding:** Analysis reveals patterns and opportunities for optimization.")
        
        return "\n".join(summary)
    
    def _revenue_analysis_template(self, metrics: Dict, framework: str, report_focus: str, 
                                  dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate revenue analysis section"""
        content = []
        
        # Look for revenue-like columns
        revenue_cols = [col for col in metrics.get('numeric_columns', []) 
                       if any(word in col.lower() for word in ['revenue', 'sales', 'income'])]
        
        if revenue_cols:
            for col in revenue_cols[:2]:  # Limit to 2 columns
                calc = metrics['calculated'].get(col, {})
                content.append(f"**{col} Analysis:**")
                content.append(f"- Total: {calc.get('sum', 'N/A'):.2f}")
                content.append(f"- Average: {calc.get('mean', 'N/A'):.2f}")
                content.append(f"- Range: {calc.get('min', 'N/A'):.2f} to {calc.get('max', 'N/A'):.2f}")
                if calc.get('std', 0) > 0:
                    cv = (calc.get('std', 0) / calc.get('mean', 1)) * 100
                    content.append(f"- Variability: {cv:.1f}% coefficient of variation")
        else:
            content.append("*No revenue-specific columns identified in the data.*")
            content.append("*Consider adding columns with names containing 'revenue', 'sales', or 'income' for detailed revenue analysis.*")
        
        return "\n".join(content)
    
    def _cost_structure_template(self, metrics: Dict, framework: str, report_focus: str,
                                dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate cost structure analysis"""
        content = []
        
        # Look for cost-like columns
        cost_cols = [col for col in metrics.get('numeric_columns', [])
                    if any(word in col.lower() for word in ['cost', 'expense', 'cogs', 'expenditure'])]
        
        if cost_cols:
            content.append("**Cost Structure Breakdown:**")
            for col in cost_cols[:3]:  # Limit to 3 columns
                calc = metrics['calculated'].get(col, {})
                content.append(f"- **{col}:** {calc.get('sum', 'N/A'):.2f} total, {calc.get('mean', 'N/A'):.2f} average")
            
            # Calculate total costs if multiple cost columns
            if len(cost_cols) > 1:
                total_cost = sum(metrics['calculated'].get(col, {}).get('sum', 0) for col in cost_cols)
                content.append(f"\n**Total Identified Costs:** {total_cost:.2f}")
        else:
            content.append("*No cost-specific columns identified.*")
            content.append("*For cost analysis, include columns with 'cost', 'expense', or similar terms.*")
        
        return "\n".join(content)
    
    def _profitability_template(self, metrics: Dict, framework: str, report_focus: str,
                               dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate profitability metrics"""
        content = []
        
        # Try to calculate profitability if revenue and cost data exists
        revenue_cols = [col for col in metrics.get('numeric_columns', [])
                       if any(word in col.lower() for word in ['revenue', 'sales', 'income'])]
        cost_cols = [col for col in metrics.get('numeric_columns', [])
                    if any(word in col.lower() for word in ['cost', 'expense', 'cogs'])]
        
        if revenue_cols and cost_cols:
            revenue = metrics['calculated'].get(revenue_cols[0], {}).get('sum', 0)
            cost = metrics['calculated'].get(cost_cols[0], {}).get('sum', 0)
            
            if revenue > 0:
                gross_profit = revenue - cost
                gross_margin = (gross_profit / revenue) * 100 if revenue > 0 else 0
                
                content.append("**Profitability Analysis:**")
                content.append(f"- Gross Profit: {gross_profit:.2f}")
                content.append(f"- Gross Margin: {gross_margin:.1f}%")
                content.append(f"- Revenue: {revenue:.2f}")
                content.append(f"- Costs: {cost:.2f}")
                
                if gross_margin > 30:
                    content.append(f"\n**Assessment:** Healthy profitability margin ({gross_margin:.1f}%)")
                elif gross_margin > 10:
                    content.append(f"\n**Assessment:** Moderate profitability ({gross_margin:.1f}%) - room for improvement")
                else:
                    content.append(f"\n**Assessment:** Low profitability ({gross_margin:.1f}%) - requires attention")
        else:
            content.append("*Insufficient data for detailed profitability analysis.*")
            content.append("*Required: Both revenue and cost columns in numeric format.*")
        
        return "\n".join(content)
    
    def _recommendations_template(self, metrics: Dict, framework: str, report_focus: str,
                                 dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate recommendations"""
        return self._generate_recommendations(framework, metrics, report_focus, user_role, as_list=True)
    
    def _data_overview_template(self, metrics: Dict, framework: str, report_focus: str,
                               dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate data overview"""
        content = []
        
        content.append(f"**Dataset Overview:**")
        content.append(f"- Total Rows: {metrics.get('row_count', 'N/A')}")
        content.append(f"- Total Columns: {metrics.get('column_count', 'N/A')}")
        content.append(f"- Numeric Columns: {len(metrics.get('numeric_columns', []))}")
        
        if 'data_quality' in metrics:
            dq = metrics['data_quality']
            content.append(f"\n**Data Quality:**")
            content.append(f"- Missing Values: {dq.get('missing_percentage', 0):.1f}%")
            content.append(f"- Duplicate Rows: {dq.get('duplicate_percentage', 0):.1f}%")
        
        if 'date_range' in metrics:
            dr = metrics['date_range']
            content.append(f"\n**Time Coverage:**")
            content.append(f"- From: {dr.get('start', 'N/A')}")
            content.append(f"- To: {dr.get('end', 'N/A')}")
            if 'days' in dr:
                content.append(f"- Duration: {dr['days']} days")
        
        return "\n".join(content)
    
    def _key_insights_template(self, metrics: Dict, framework: str, report_focus: str,
                              dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate key insights"""
        content = []
        
        content.append("**Key Insights from Data Analysis:**")
        
        if 'calculated' in metrics and metrics['calculated']:
            # Find columns with interesting patterns
            for col, calc in list(metrics['calculated'].items())[:3]:
                mean = calc.get('mean', 0)
                std = calc.get('std', 0)
                
                if std > 0:
                    cv = (std / mean) * 100 if mean != 0 else 0
                    if cv > 50:
                        content.append(f"- **High variability in {col}:** {cv:.1f}% coefficient of variation suggests inconsistent performance")
                    elif cv < 10:
                        content.append(f"- **Stable performance in {col}:** Low variability ({cv:.1f}%) indicates consistent results")
        
        # Check for data quality issues
        if metrics.get('data_quality', {}).get('missing_percentage', 0) > 20:
            content.append(f"- **Data quality concern:** {metrics['data_quality']['missing_percentage']:.1f}% missing values may affect analysis reliability")
        
        # Framework-specific insights
        if framework == "financial":
            content.append("- Financial analysis framework applied to identify revenue and cost patterns")
        elif framework == "sales":
            content.append("- Sales framework used to analyze performance and conversion metrics")
        elif framework == "operational":
            content.append("- Operational framework applied to assess efficiency and productivity")
        
        return "\n".join(content)
    
    def _trend_analysis_template(self, metrics: Dict, framework: str, report_focus: str,
                                dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate trend analysis"""
        content = []
        
        content.append("**Trend Analysis:**")
        
        if 'date_range' in metrics and 'calculated' in metrics and metrics['calculated']:
            dr = metrics['date_range']
            content.append(f"- Data covers period from {dr.get('start', 'N/A')} to {dr.get('end', 'N/A')}")
            
            # Simple trend detection based on first numeric column
            numeric_cols = metrics.get('numeric_columns', [])
            if numeric_cols and dataframe is not None and 'date_columns' in metrics:
                date_col = metrics['date_columns'][0]
                num_col = numeric_cols[0]
                
                try:
                    # Sort by date and calculate simple trend
                    df_sorted = dataframe.sort_values(date_col)
                    if len(df_sorted) > 2:
                        first_val = df_sorted.iloc[0][num_col]
                        last_val = df_sorted.iloc[-1][num_col]
                        
                        if first_val != 0:
                            trend_pct = ((last_val - first_val) / first_val) * 100
                            direction = "increasing" if trend_pct > 0 else "decreasing"
                            content.append(f"- **{num_col} trend:** {direction} by {abs(trend_pct):.1f}% over the period")
                except:
                    content.append("- Trend analysis requires proper date formatting and numeric data")
        else:
            content.append("*Trend analysis requires date-based data with time series.*")
            content.append("*Ensure your data includes a date column for time-based analysis.*")
        
        return "\n".join(content)
    
    def _risk_assessment_template(self, metrics: Dict, framework: str, report_focus: str,
                                 dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Generate risk assessment"""
        content = []
        
        content.append("**Risk Assessment:**")
        
        # Data quality risks
        dq = metrics.get('data_quality', {})
        if dq.get('missing_percentage', 0) > 10:
            content.append(f"- **Data Quality Risk:** {dq['missing_percentage']:.1f}% missing data may lead to inaccurate conclusions")
        
        # Statistical risks
        if 'calculated' in metrics and metrics['calculated']:
            for col, calc in list(metrics['calculated'].items())[:2]:
                std = calc.get('std', 0)
                mean = calc.get('mean', 0)
                
                if mean != 0 and std > 0:
                    if std > mean * 0.5:  # High volatility
                        content.append(f"- **Volatility Risk:** High variability in {col} (std/mean = {(std/mean):.2f}) indicates instability")
        
        # Framework-specific risks
        if framework == "financial":
            content.append("- **Financial Risk:** Revenue concentration or high fixed costs could impact stability")
        elif framework == "sales":
            content.append("- **Sales Risk:** Pipeline gaps or low conversion rates may affect future revenue")
        elif framework == "operational":
            content.append("- **Operational Risk:** Bottlenecks or quality issues could impact customer satisfaction")
        
        # Role-specific risk considerations
        if user_role and 'executive' in user_role.lower():
            content.append("- **Strategic Risk:** Market shifts or competitive pressures not captured in current data")
        
        return "\n".join(content)
    
    def _default_section_template(self, metrics: Dict, framework: str, report_focus: str,
                                 dataframe: Optional[pd.DataFrame], user_role: Optional[str] = None) -> str:
        """Default template for sections not specifically defined"""
        role_context = f" for {user_role}" if user_role else ""
        return f"Analysis of this section would provide insights into the {framework} aspects of the business{role_context}. Based on the data, key metrics and patterns can be identified to support decision-making. For more detailed analysis, ensure data includes relevant columns for {framework} analysis."
    
    def _generate_recommendations(self, framework: str, metrics: Dict, report_focus: str, 
                                 user_role: Optional[str] = None, as_list: bool = False) -> str:
        """Generate framework-specific recommendations"""
        recommendations = []
        
        if framework == "financial":
            recommendations = [
                "Review cost structure for optimization opportunities",
                "Analyze revenue streams for diversification potential",
                "Monitor cash flow and working capital requirements",
                "Conduct regular profitability analysis by product/service",
                "Implement financial controls for expense management"
            ]
        elif framework == "sales":
            recommendations = [
                "Focus on improving conversion rates in key pipeline stages",
                "Analyze win/loss reasons to improve sales effectiveness",
                "Segment customers for targeted sales strategies",
                "Regularly update sales forecasts based on pipeline health",
                "Provide additional training for underperforming segments"
            ]
        elif framework == "operational":
            recommendations = [
                "Identify and address production bottlenecks",
                "Implement quality control measures based on defect analysis",
                "Optimize inventory levels to reduce carrying costs",
                "Analyze capacity utilization for efficiency improvements",
                "Standardize processes to reduce variability"
            ]
        else:  # general
            recommendations = [
                "Collect additional data for more comprehensive analysis",
                "Establish regular reporting cadence for key metrics",
                "Validate data quality before making major decisions",
                "Cross-reference findings with operational knowledge",
                "Set up automated data collection where possible"
            ]
        
        # Adjust based on focus
        if report_focus == "profit":
            recommendations.insert(0, "Prioritize profitability improvement initiatives")
        elif report_focus == "growth":
            recommendations.insert(0, "Focus on growth-oriented investments and strategies")
        elif report_focus == "loss":
            recommendations.insert(0, "Immediate cost containment and risk mitigation")
        
        # Adjust based on user role
        if user_role:
            role_lower = user_role.lower()
            if 'executive' in role_lower:
                recommendations = [rec for rec in recommendations if not 'detailed' in rec.lower()]
                recommendations.insert(0, "Establish key performance indicators aligned with strategic goals")
            elif 'analyst' in role_lower:
                recommendations.append("Conduct deeper statistical analysis on identified patterns")
                recommendations.append("Build automated dashboards for ongoing monitoring")
        
        if as_list:
            return "\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations[:5])])
        else:
            return recommendations
    
    def _generate_next_steps(self, user_role: Optional[str], framework: str) -> List[str]:
        """Generate next steps based on user role"""
        steps = [
            "Review key metrics and validate against business expectations",
            "Implement priority recommendations within the next 30 days",
            "Schedule follow-up analysis in 30 days to track progress",
            "Consider collecting additional data for deeper insights"
        ]
        
        if user_role:
            role_lower = user_role.lower()
            if 'executive' in role_lower:
                steps.insert(0, "Present findings to leadership team for strategic alignment")
                steps.insert(1, "Allocate resources based on priority recommendations")
            elif 'manager' in role_lower:
                steps.insert(0, "Communicate insights to team members for implementation")
                steps.insert(1, "Set specific goals based on analysis findings")
            elif 'analyst' in role_lower:
                steps.insert(0, "Document analysis methodology and assumptions")
                steps.append("Explore additional analytical techniques for deeper insights")
        
        if framework == "financial":
            steps.append("Schedule financial review meeting with accounting team")
        elif framework == "sales":
            steps.append("Align sales team on identified opportunities and challenges")
        
        return steps
    
    def _extract_sections_from_ai(self, ai_report: str) -> Dict[str, str]:
        """Extract sections from AI-generated report"""
        sections = {}
        lines = ai_report.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            # Check for section headers (## or ### in Markdown)
            if line.startswith('## ') and not line.startswith('###'):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _find_section_in_ai(self, section_name: str, sections: Dict[str, str], full_report: str) -> str:
        """Find content for a section in AI-generated report"""
        # Exact match
        if section_name in sections:
            return sections[section_name]
        
        # Partial match
        for ai_section, content in sections.items():
            if section_name.lower() in ai_section.lower() or ai_section.lower() in section_name.lower():
                return content
        
        # Try to find in full report using keywords
        keywords = section_name.lower().split()
        lines = full_report.split('\n')
        in_section = False
        section_content = []
        
        for line in lines:
            if line.startswith('## '):
                # Check if this line contains any keywords
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in keywords):
                    in_section = True
                elif in_section:
                    break
            elif in_section:
                section_content.append(line)
        
        if section_content:
            return '\n'.join(section_content).strip()
        
        return ""
    
    def _validate_report(self, report: str) -> bool:
        """
        Validate that the generated report meets quality standards
        """
        if not report or len(report.strip()) < 100:
            return False
        
        # Check for essential elements
        has_sections = '##' in report  # Markdown sections
        has_content = len(report.split()) > 50  # At least 50 words
        
        # Check for excessive generic phrases
        generic_phrases = [
            "as an AI language model",
            "I cannot provide",
            "I don't have access",
            "based on the limited information",
            "without more data"
        ]
        
        generic_count = sum(1 for phrase in generic_phrases if phrase.lower() in report.lower())
        
        return has_sections and has_content and generic_count < 2
    
    def _convert_to_html(self, markdown_report: str) -> str:
        """
        Convert Markdown report to HTML (basic implementation)
        """
        if not markdown_report:
            return ""
        
        html = []
        in_list = False
        
        for line in markdown_report.split('\n'):
            # Headers
            if line.startswith('# '):
                html.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html.append(f'<h3>{line[4:]}</h3>')
            # Lists
            elif line.strip().startswith('- '):
                if not in_list:
                    html.append('<ul>')
                    in_list = True
                html.append(f'<li>{line.strip()[2:]}</li>')
            elif line.strip().startswith('* '):
                if not in_list:
                    html.append('<ul>')
                    in_list = True
                html.append(f'<li>{line.strip()[2:]}</li>')
            elif line.strip().startswith('1. '):
                if not in_list:
                    html.append('<ol>')
                    in_list = True
                html.append(f'<li>{line.strip()[3:]}</li>')
            else:
                if in_list:
                    html.append('</ul>' if line.strip().startswith('- ') or line.strip().startswith('* ') else '</ol>')
                    in_list = False
                if line.strip():
                    html.append(f'<p>{line.strip()}</p>')
                else:
                    html.append('<br>')
        
        # Close list if still open
        if in_list:
            html.append('</ul>')
        
        # Wrap in HTML document
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Intelligence Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        ul, ol {{ margin-left: 20px; }}
        li {{ margin-bottom: 5px; }}
        p {{ margin-bottom: 15px; }}
        .metadata {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; }}
        .highlight {{ background-color: #fffacd; padding: 2px 5px; }}
    </style>
</head>
<body>
{''.join(html)}
</body>
</html>"""
        
        return full_html
    
    def _generate_error_report(self, error_message: str, data_sample: str, error_trace: Optional[str] = None) -> str:
        """
        Generate a structured error report when everything fails
        """
        error_report = []
        error_report.append("# ⚠ Report Generation Error")
        error_report.append(f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        error_report.append(f"**Error:** {error_message}")
        
        if error_trace:
            error_report.append(f"\n**Technical Details:**")
            error_report.append(f"```\n{error_trace[:500]}\n```")
        
        error_report.append(f"\n**Data Sample (first 500 chars):**")
        error_report.append(f"```\n{data_sample}\n```")
        
        error_report.append("\n## Recommended Actions:")
        error_report.append("1. Check your data format (CSV, JSON, or structured text)")
        error_report.append("2. Verify data contains numeric columns for analysis")
        error_report.append("3. Ensure internet connectivity if using AI features")
        error_report.append("4. Try reducing data size if it's very large")
        error_report.append("5. Contact support with the error details above")
        
        error_report.append("\n---")
        error_report.append("*This error report was automatically generated*")
        
        return "\n".join(error_report)

# ==================== UTILITY FUNCTIONS ====================

def save_report(report_content: str, filename: str, format: str = "auto") -> bool:
    """
    Save generated report to file
    
    Args:
        report_content: The report content to save
        filename: Output filename
        format: "auto", "txt", "md", "html"
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Auto-detect format from filename
        if format == "auto":
            if filename.lower().endswith('.html'):
                format = "html"
            elif filename.lower().endswith('.md') or filename.lower().endswith('.markdown'):
                format = "md"
            else:
                format = "txt"
        
        # Ensure proper file extension
        if format == "html" and not filename.lower().endswith('.html'):
            filename += '.html'
        elif format == "md" and not filename.lower().endswith('.md'):
            filename += '.md'
        
        # Write file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✓ Report saved to: {filename}")
        return True
        
    except Exception as e:
        print(f"✗ Error saving report: {e}")
        return False

def analyze_file(filepath: str, 
                api_key: Optional[str] = None,
                business_type: str = "auto",
                user_role: Optional[str] = None,
                output_file: Optional[str] = None) -> str:
    """
    Convenience function to analyze a file and generate report
    
    Args:
        filepath: Path to data file
        api_key: Optional Groq API key
        business_type: Type of business/industry
        user_role: Optional user role for context
        output_file: Optional output file path
    
    Returns:
        Generated report as string
    """
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Auto-detect business type from filename
        if business_type == "auto":
            filename = os.path.basename(filepath).lower()
            if any(term in filename for term in ['sales', 'revenue', 'deal']):
                business_type = "Sales Business"
            elif any(term in filename for term in ['financial', 'profit', 'cost', 'expense']):
                business_type = "Financial Services"
            elif any(term in filename for term in ['operational', 'production', 'manufacturing']):
                business_type = "Manufacturing"
            else:
                business_type = "General Business"
        
        # Create generator and generate report
        generator = ReportGenerator(api_key=api_key)
        
        # Auto-detect data type from file extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.csv':
            data_type = 'csv'
        elif ext == '.json':
            data_type = 'json'
        else:
            data_type = 'auto'
        
        report = generator.generate_report(
            data_content=content,
            data_type=data_type,
            user_name="File Analysis",
            business_type=business_type,
            report_focus="auto",
            user_role=user_role
        )
        
        # Save to file if requested
        if output_file:
            save_report(report, output_file)
        
        return report
        
    except Exception as e:
        return f"Error analyzing file: {str(e)}"

# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Example 1: Basic usage with text data
    print("Example 1: Basic text analysis")
    generator = ReportGenerator()
    
    sample_data = """Month,Revenue,Cost,Profit
January,100000,70000,30000
February,120000,80000,40000
March,110000,75000,35000
April,130000,85000,45000
May,140000,90000,50000"""
    
    report = generator.generate_report(
        data_content=sample_data,
        data_type="csv",
        user_name="Acme Corporation",
        business_type="Retail",
        report_focus="profit",
        user_role="CEO"  # Now this parameter is accepted!
    )
    
    print(report[:500] + "...")  # Print first 500 chars
    
    # Example 2: Save to file
    save_report(report, "acme_report.md")
    
    # Example 3: File analysis with user role
    print("\nExample 2: File analysis with user role")
    # Uncomment to use:
    # report = analyze_file("data.csv", user_role="Sales Manager", output_file="analysis_report.html")
    # print(f"Generated report of {len(report)} characters")
    
    print("\nReport Generator ready for production use!")