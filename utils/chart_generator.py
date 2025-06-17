import re
import json
from typing import Dict, List, Any

class ChartGenerator:
    def __init__(self):
        self.common_lab_tests = {
            'glucose': {'unit': 'mg/dL', 'normal_range': (70, 100)},
            'cholesterol': {'unit': 'mg/dL', 'normal_range': (0, 200)},
            'triglycerides': {'unit': 'mg/dL', 'normal_range': (0, 150)},
            'hdl': {'unit': 'mg/dL', 'normal_range': (40, 60)},
            'ldl': {'unit': 'mg/dL', 'normal_range': (0, 100)},
            'hemoglobin': {'unit': 'g/dL', 'normal_range': (12, 16)},
            'hematocrit': {'unit': '%', 'normal_range': (36, 46)},
            'wbc': {'unit': 'K/uL', 'normal_range': (4.5, 11.0)},
            'rbc': {'unit': 'M/uL', 'normal_range': (4.2, 5.4)},
            'platelets': {'unit': 'K/uL', 'normal_range': (150, 450)},
            'creatinine': {'unit': 'mg/dL', 'normal_range': (0.6, 1.2)},
            'bun': {'unit': 'mg/dL', 'normal_range': (7, 20)},
            'alt': {'unit': 'U/L', 'normal_range': (7, 56)},
            'ast': {'unit': 'U/L', 'normal_range': (10, 40)},
            'bilirubin': {'unit': 'mg/dL', 'normal_range': (0.3, 1.2)},
        }
    
    def generate_chart_data(self, content: str, analysis: Dict) -> Dict[str, Any]:
        """Generate interactive chart data showing current vs normal ranges"""
        try:
            # Extract lab values from both content and analysis
            extracted_values = self._extract_lab_values(content)
            
            # Also extract from analysis if available
            if analysis and 'lab_values' in analysis:
                for lab_val in analysis['lab_values']:
                    extracted_values.append({
                        'name': lab_val.get('parameter', ''),
                        'value': self._parse_numeric_value(lab_val.get('value', '')),
                        'unit': lab_val.get('unit', ''),
                        'reference_range': lab_val.get('reference_range', ''),
                        'status': lab_val.get('status', 'unknown'),
                        'clinical_significance': lab_val.get('clinical_significance', '')
                    })
            
            if not extracted_values:
                return None
            
            # Generate interactive chart with selectable values
            chart_data = {
                'interactive_comparison': self._create_interactive_comparison_chart(extracted_values),
                'lab_values_list': extracted_values,  # For the selector
                'status_distribution': self._create_status_chart(extracted_values),
                'summary_stats': self._create_summary_stats(extracted_values)
            }
            
            return chart_data
            
        except Exception as e:
            print(f"Error generating chart data: {str(e)}")
            return None
    
    def _extract_lab_values(self, content: str) -> List[Dict]:
        """Extract lab values from content using regex patterns"""
        values = []
        content_lower = content.lower()
        
        # Common patterns for lab values
        patterns = [
            # Pattern: Test Name: Value Unit
            r'(\w+):\s*(\d+\.?\d*)\s*(\w+)',
            # Pattern: Test Name Value Unit
            r'(\w+)\s+(\d+\.?\d*)\s*(\w+)',
            # Pattern: Value mg/dL or similar
            r'(\d+\.?\d*)\s*(mg/dl|g/dl|k/ul|m/ul|u/l|%)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                if len(match) >= 2:
                    test_name = match[0].strip()
                    try:
                        value = float(match[1])
                        unit = match[2] if len(match) > 2 else ''
                        
                        # Check if this matches a known lab test
                        normalized_name = self._normalize_test_name(test_name)
                        if normalized_name in self.common_lab_tests:
                            test_info = self.common_lab_tests[normalized_name]
                            status = self._determine_status(value, test_info['normal_range'])
                            
                            values.append({
                                'name': normalized_name.title(),
                                'value': value,
                                'unit': unit or test_info['unit'],
                                'status': status,
                                'normal_range': test_info['normal_range']
                            })
                    except ValueError:
                        continue
        
        # Remove duplicates
        unique_values = []
        seen = set()
        for val in values:
            key = val['name'].lower()
            if key not in seen:
                seen.add(key)
                unique_values.append(val)
        
        return unique_values
    
    def _normalize_test_name(self, name: str) -> str:
        """Normalize test names to match our dictionary"""
        name_lower = name.lower().strip()
        
        # Map common variations
        name_mapping = {
            'blood glucose': 'glucose',
            'blood sugar': 'glucose',
            'total cholesterol': 'cholesterol',
            'chol': 'cholesterol',
            'trig': 'triglycerides',
            'hdl cholesterol': 'hdl',
            'ldl cholesterol': 'ldl',
            'hemoglobin': 'hemoglobin',
            'hgb': 'hemoglobin',
            'hct': 'hematocrit',
            'white blood cells': 'wbc',
            'white blood cell': 'wbc',
            'red blood cells': 'rbc',
            'red blood cell': 'rbc',
            'platelet count': 'platelets',
            'plt': 'platelets',
            'creatinine': 'creatinine',
            'blood urea nitrogen': 'bun',
            'alanine aminotransferase': 'alt',
            'aspartate aminotransferase': 'ast',
            'total bilirubin': 'bilirubin',
        }
        
        return name_mapping.get(name_lower, name_lower)
    
    def _determine_status(self, value: float, normal_range: tuple) -> str:
        """Determine if a value is normal, high, or low"""
        min_val, max_val = normal_range
        if value < min_val:
            return 'low'
        elif value > max_val:
            return 'high'
        else:
            return 'normal'
    
    def _parse_numeric_value(self, value_str: str) -> float:
        """Parse numeric value from string, handling units and ranges"""
        if not value_str:
            return None
        
        # Extract first number found
        match = re.search(r'(\d+\.?\d*)', str(value_str))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def _create_interactive_comparison_chart(self, values: List[Dict]) -> Dict:
        """Create interactive chart data for current vs normal range comparison"""
        chart_values = []
        
        for val in values[:10]:  # Limit to prevent overcrowding
            if val.get('value') is not None:
                normal_range = self._get_normal_range(val['name'])
                chart_values.append({
                    'parameter': val['name'],
                    'current_value': val['value'],
                    'unit': val.get('unit', ''),
                    'normal_min': normal_range[0] if normal_range else 0,
                    'normal_max': normal_range[1] if normal_range else val['value'] * 2,
                    'status': val.get('status', self._determine_status(val['value'], normal_range) if normal_range else 'unknown'),
                    'clinical_significance': val.get('clinical_significance', ''),
                    'reference_range': val.get('reference_range', f"{normal_range[0]}-{normal_range[1]}" if normal_range else "Not available")
                })
        
        return {
            'type': 'comparison_bar',
            'title': 'Lab Values vs Normal Ranges',
            'data': chart_values,
            'max_selectable': 5,
            'description': 'Select up to 5 values to compare current results with normal ranges'
        }
    
    def _get_normal_range(self, test_name: str) -> tuple:
        """Get normal range for a test, checking common variations"""
        normalized_name = self._normalize_test_name(test_name)
        return self.common_lab_tests.get(normalized_name, {}).get('normal_range', None)

    def _create_bar_chart(self, values: List[Dict]) -> Dict:
        """Create bar chart data"""
        if not values:
            return None
        
        labels = [val['name'] for val in values]
        data = [val['value'] for val in values]
        colors = []
        
        for val in values:
            if val['status'] == 'normal':
                colors.append('#28a745')  # Green
            elif val['status'] == 'high':
                colors.append('#dc3545')  # Red
            else:
                colors.append('#ffc107')  # Yellow
        
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Lab Values',
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Lab Test Results'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        }
    
    def _create_status_chart(self, values: List[Dict]) -> Dict:
        """Create pie chart showing status distribution"""
        if not values:
            return None
        
        status_counts = {'normal': 0, 'high': 0, 'low': 0}
        for val in values:
            status_counts[val['status']] += 1
        
        # Enhanced vibrant colors for better visual appeal
        return {
            'labels': ['Normal', 'High', 'Low'],
            'data': [status_counts['normal'], status_counts['high'], status_counts['low']],
            'backgroundColor': [
                '#10b981',  # Emerald green for normal
                '#ef4444',  # Bright red for high
                '#f59e0b'   # Amber for low
            ],
            'borderColor': '#ffffff',
            'borderWidth': 3,
            'hoverBackgroundColor': [
                '#059669',  # Darker green on hover
                '#dc2626',  # Darker red on hover
                '#d97706'   # Darker amber on hover
            ]
        }
    
    def _create_trend_chart(self, values: List[Dict]) -> Dict:
        """Create line chart for trend analysis (simplified)"""
        if not values:
            return None
        
        # For simplicity, create a comparison with normal ranges
        labels = [val['name'] for val in values]
        actual_values = [val['value'] for val in values]
        normal_midpoints = [(val['normal_range'][0] + val['normal_range'][1]) / 2 for val in values]
        
        return {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Your Results',
                        'data': actual_values,
                        'borderColor': '#007bff',
                        'backgroundColor': 'rgba(0, 123, 255, 0.1)',
                        'tension': 0.1
                    },
                    {
                        'label': 'Normal Range (Midpoint)',
                        'data': normal_midpoints,
                        'borderColor': '#28a745',
                        'backgroundColor': 'rgba(40, 167, 69, 0.1)',
                        'tension': 0.1
                    }
                ]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Results vs Normal Range'
                    }
                }
            }
        }
    
    def _create_summary_stats(self, values: List[Dict]) -> Dict:
        """Create summary statistics"""
        if not values:
            return None
        
        total_tests = len(values)
        normal_count = sum(1 for val in values if val['status'] == 'normal')
        high_count = sum(1 for val in values if val['status'] == 'high')
        low_count = sum(1 for val in values if val['status'] == 'low')
        
        return {
            'total_tests': total_tests,
            'normal_count': normal_count,
            'high_count': high_count,
            'low_count': low_count,
            'normal_percentage': round((normal_count / total_tests) * 100, 1) if total_tests > 0 else 0,
            'abnormal_percentage': round(((high_count + low_count) / total_tests) * 100, 1) if total_tests > 0 else 0
        }
