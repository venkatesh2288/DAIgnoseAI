import os
import io
import base64
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY
        ))
    
    def generate_report(self, uploaded_file, output_path):
        """Generate comprehensive PDF report"""
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=0.8*inch)
        story = []
        
        # Title and Header
        self._add_header(story, uploaded_file)
        
        # File Information
        self._add_file_info(story, uploaded_file)
        
        # Medical Summary
        if uploaded_file.summary:
            self._add_medical_summary(story, uploaded_file.summary)
        
        # Lab Values Table
        if uploaded_file.chart_data and uploaded_file.chart_data.get('lab_values_table'):
            self._add_lab_values_table(story, uploaded_file.chart_data['lab_values_table'])
        
        # Risk Assessment
        if uploaded_file.risk_assessment:
            self._add_risk_assessment(story, uploaded_file.risk_assessment)
        
        # Recommendations
        if uploaded_file.recommendations:
            self._add_recommendations(story, uploaded_file.recommendations)
        
        # Charts (if available)
        if uploaded_file.chart_data and uploaded_file.chart_data.get('lab_values_table'):
            self._add_charts(story, uploaded_file.chart_data['lab_values_table'])
        
        # Footer
        self._add_footer(story)
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def _add_header(self, story, uploaded_file):
        """Add report header"""
        title = Paragraph("Diagn'AI'zer - AI-Powered Medical Analysis", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        subtitle = Paragraph(f"Report for: {uploaded_file.original_filename}", self.styles['Heading3'])
        story.append(subtitle)
        story.append(Spacer(1, 15))
    
    def _add_file_info(self, story, uploaded_file):
        """Add file information section"""
        story.append(Paragraph("File Information", self.styles['SectionHeader']))
        
        info_data = [
            ['Original Filename:', uploaded_file.original_filename],
            ['File Type:', uploaded_file.file_type.upper()],
            ['Upload Date:', uploaded_file.upload_date.strftime('%B %d, %Y at %I:%M %p')],
            ['File Size:', f"{uploaded_file.file_size / 1024:.1f} KB"],
            ['Analysis Status:', 'Complete' if uploaded_file.analysis_complete else 'Pending']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
    
    def _add_medical_summary(self, story, summary):
        """Add medical summary section"""
        story.append(Paragraph("Detailed Medical Analysis", self.styles['SectionHeader']))
        
        # Clean and format summary text
        cleaned_summary = self._clean_html_text(summary)
        summary_para = Paragraph(cleaned_summary, self.styles['CustomBodyText'])
        story.append(summary_para)
        story.append(Spacer(1, 15))
    
    def _add_lab_values_table(self, story, lab_values):
        """Add lab values table"""
        story.append(Paragraph("Laboratory Values Analysis", self.styles['SectionHeader']))
        
        # Table headers
        table_data = [['Test Parameter', 'Current Value', 'Normal Range', 'Status', 'Risk Level']]
        
        # Add lab values data
        for value in lab_values:
            table_data.append([
                value.get('parameter', ''),
                value.get('current_value', ''),
                value.get('normal_range', ''),
                value.get('status', ''),
                value.get('risk_level', '')
            ])
        
        lab_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1*inch, 1*inch])
        lab_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Add color coding for status
        for i, value in enumerate(lab_values, 1):
            status = value.get('status', '').lower()
            if 'normal' in status or 'perfect' in status:
                lab_table.setStyle(TableStyle([('BACKGROUND', (3, i), (3, i), colors.lightgreen)]))
            elif 'slightly' in status:
                lab_table.setStyle(TableStyle([('BACKGROUND', (3, i), (3, i), colors.yellow)]))
            elif 'high' in status or 'low' in status:
                lab_table.setStyle(TableStyle([('BACKGROUND', (3, i), (3, i), colors.lightcoral)]))
        
        story.append(lab_table)
        story.append(Spacer(1, 20))
    
    def _add_risk_assessment(self, story, risk_assessment):
        """Add risk assessment section"""
        story.append(Paragraph("Overall Health Assessment", self.styles['SectionHeader']))
        
        cleaned_assessment = self._clean_html_text(risk_assessment)
        assessment_para = Paragraph(cleaned_assessment, self.styles['CustomBodyText'])
        story.append(assessment_para)
        story.append(Spacer(1, 15))
    
    def _add_recommendations(self, story, recommendations):
        """Add recommendations section"""
        story.append(Paragraph("Health Tips & Recommendations", self.styles['SectionHeader']))
        
        cleaned_recommendations = self._clean_html_text(recommendations)
        recommendations_para = Paragraph(cleaned_recommendations, self.styles['CustomBodyText'])
        story.append(recommendations_para)
        story.append(Spacer(1, 15))
    
    def _add_charts(self, story, lab_values):
        """Add visual charts to PDF"""
        story.append(Paragraph("Visual Analysis", self.styles['SectionHeader']))
        
        # Create status distribution chart
        status_counts = {}
        for value in lab_values:
            status = value.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            chart_image = self._create_status_chart(status_counts)
            if chart_image:
                story.append(chart_image)
                story.append(Spacer(1, 15))
    
    def _create_status_chart(self, status_counts):
        """Create status distribution pie chart"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            labels = list(status_counts.keys())
            sizes = list(status_counts.values())
            colors_map = {
                'Normal': '#28a745', 'Perfect': '#28a745',
                'Slightly High': '#ffc107', 'Slightly Low': '#ffc107',
                'High': '#dc3545', 'Low': '#dc3545',
                'Very High': '#343a40', 'Very Low': '#343a40'
            }
            
            chart_colors = [colors_map.get(label, '#6c757d') for label in labels]
            
            ax.pie(sizes, labels=labels, colors=chart_colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('Lab Values Status Distribution', fontsize=14, fontweight='bold')
            
            # Save to memory buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            # Create ReportLab image
            img = Image(buffer, width=5*inch, height=3.75*inch)
            plt.close(fig)
            
            return img
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
    
    def _add_footer(self, story):
        """Add footer with disclaimer"""
        story.append(Spacer(1, 30))
        
        disclaimer_style = ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        disclaimer_text = """
        <b>Medical Disclaimer:</b> This analysis is for informational purposes only and should not replace 
        professional medical advice. Please consult with your healthcare provider for proper medical 
        evaluation and treatment.
        <br/><br/>
        Generated by Diagn'AI'zer - AI-Powered Medical Analysis on {date}
        """.format(date=datetime.now().strftime('%B %d, %Y at %I:%M %p'))
        
        disclaimer = Paragraph(disclaimer_text, disclaimer_style)
        story.append(disclaimer)
    
    def _clean_html_text(self, text):
        """Clean HTML tags and format text for PDF"""
        import re
        # Remove HTML tags but preserve line breaks
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.strip()
        return text