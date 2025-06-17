import os
import google.generativeai as genai
import json
import re
from datetime import datetime

# Simple memory implementation without LangChain dependencies
class SimpleConversationMemory:
    def __init__(self, max_messages=10):
        self.messages = []
        self.max_messages = max_messages
    
    def add_user_message(self, message):
        self.messages.append({"type": "user", "content": message, "timestamp": datetime.now()})
        self._trim_messages()
    
    def add_ai_message(self, message):
        self.messages.append({"type": "assistant", "content": message, "timestamp": datetime.now()})
        self._trim_messages()
    
    def _trim_messages(self):
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count=6):
        return self.messages[-count:] if self.messages else []

class AIService:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize conversation memory for each session
        self.memories = {}
    
    def get_memory(self, session_id):
        """Get or create memory for a session"""
        if session_id not in self.memories:
            self.memories[session_id] = SimpleConversationMemory(max_messages=20)
        return self.memories[session_id]
    
    def analyze_lab_report(self, content):
        """Analyze lab report content using Gemini AI with standardized format"""
        prompt = f"""
        You are a highly qualified medical laboratory specialist. Analyze this lab report and provide a comprehensive assessment in the EXACT format specified below.

        ANALYSIS REQUIREMENTS:
        1. DETAILED SUMMARY: Explain EVERY lab value found, including current result, normal range, and health significance
        2. VALUES TABLE: Extract all test parameters with their values, units, normal ranges, and status
        3. HEALTH TIPS: Provide actionable lifestyle and health recommendations

        Lab Report Content:
        {content}

        MANDATORY OUTPUT FORMAT (JSON):
        {{
            "detailed_summary": "Comprehensive paragraph explaining every single lab value found in the report. For each parameter, include: what it measures, the patient's current value, the normal reference range, whether it's normal/high/low, and what this means for the patient's health. Use clear, professional language that patients can understand.",
            
            "lab_values_table": [
                {{
                    "parameter": "Test Name (e.g., Cholesterol Total)",
                    "current_value": "Patient's result with unit",
                    "normal_range": "Reference range with unit", 
                    "status": "One of: Normal, High, Very High, Slightly High, Low, Very Low, Slightly Low, Perfect",
                    "risk_level": "One of: No Risk, Low Risk, Moderate Risk, High Risk, Critical Risk"
                }}
            ],
            
            "overall_health_assessment": "Overall health risk assessment based on all parameters combined. Categorize as: Excellent Health, Good Health, Fair Health, Poor Health, or Critical Health. Explain the reasoning.",
            
            "health_tips": "Detailed, actionable health tips and lifestyle recommendations based on the specific lab results. Include dietary suggestions, exercise recommendations, and lifestyle modifications. Be specific and practical."
        }}

        IMPORTANT: 
        - Extract ALL numerical values from the report
        - If normal ranges aren't provided, use standard medical reference ranges
        - Status must be one of the specified categories
        - Risk level must reflect actual medical significance
        - Be thorough and include every test parameter found
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Fallback if JSON parsing fails
                    return {
                        "detailed_summary": response.text[:1000] + "..." if len(response.text) > 1000 else response.text,
                        "lab_values_table": [],
                        "overall_health_assessment": "Unable to parse detailed assessment",
                        "health_tips": "Please consult with a healthcare professional for personalized advice"
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured text
                return {
                    "detailed_summary": response.text[:1000] + "..." if len(response.text) > 1000 else response.text,
                    "lab_values_table": [],
                    "overall_health_assessment": "Unable to parse detailed assessment",
                    "health_tips": "Please consult with a healthcare professional for personalized advice"
                }
                
        except Exception as e:
            return {
                "detailed_summary": f"Error analyzing report: {str(e)}",
                "lab_values_table": [],
                "overall_health_assessment": "Analysis unavailable",
                "health_tips": "Please consult with a healthcare professional for personalized advice"
            }
    
    def _extract_section(self, text, start_marker, end_marker):
        """Extract text between two markers"""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""
        
        end_idx = text.find(end_marker)
        if end_idx == -1:
            return text[start_idx + len(start_marker):].strip()
        
        return text[start_idx + len(start_marker):end_idx].strip()
    
    def generate_medical_response(self, question, pubmed_results):
        """Generate professional medical response using PubMed research"""
        # Format PubMed results for context
        pubmed_context = ""
        if isinstance(pubmed_results, dict) and 'articles' in pubmed_results:
            articles = pubmed_results['articles'][:3]  # Use top 3 most relevant
            for i, article in enumerate(articles, 1):
                pubmed_context += f"\nArticle {i}: {article.get('title', 'N/A')}\n"
                pubmed_context += f"Abstract: {article.get('abstract', 'Not available')[:300]}...\n"
        
        prompt = f"""
        You are a professional medical AI assistant with access to current medical literature from PubMed.
        Provide a comprehensive, evidence-based response to the medical question below.

        Medical Question: {question}

        Recent PubMed Research Context:
        {pubmed_context}

        Instructions:
        - Provide accurate, evidence-based medical information
        - Reference the research findings when applicable
        - Include appropriate medical disclaimers
        - Suggest consulting healthcare professionals for diagnosis/treatment
        - Be professional, empathetic, and clear
        - Structure your response logically
        - If research is limited, acknowledge this

        IMPORTANT: Always include this disclaimer at the end:
        "This information is for educational purposes only and should not replace professional medical advice. Please consult with a qualified healthcare provider for personalized medical guidance."

        Response:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your question right now. Please try again or consult with a healthcare professional. Error: {str(e)}"

    def is_medical_query(self, query):
        """Determine if a query is medical-related and needs PubMed search"""
        medical_keywords = [
            'disease', 'symptom', 'symptoms', 'treatment', 'medicine', 'drug', 'therapy',
            'diagnosis', 'condition', 'syndrome', 'infection', 'virus', 'bacteria',
            'blood test', 'lab result', 'medical', 'health', 'clinical', 'patient',
            'diabetes', 'cancer', 'heart', 'blood', 'pressure', 'cholesterol',
            'pain', 'fever', 'headache', 'nausea', 'fatigue', 'diet', 'nutrition',
            'vitamin', 'supplement', 'exercise', 'weight', 'sleep', 'stress',
            'mental health', 'depression', 'anxiety', 'pregnant', 'pregnancy',
            'medication', 'pill', 'dose', 'side effect', 'allergy', 'immune',
            'vaccine', 'doctor', 'hospital', 'nurse', 'physician', 'surgeon',
            'what is', 'what are', 'what causes', 'how to', 'causes', 'prevent',
            'normal range', 'abnormal', 'high', 'low', 'elevated', 'deficiency'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in medical_keywords)
    
    def generate_chat_response(self, user_message, context="", pubmed_info="", session_id="default"):
        """Generate professional medical consultation response with memory and context"""
        memory = self.get_memory(session_id)
        
        # Build professional medical consultation prompt
        prompt_parts = []
        
        prompt_parts.append("""
        You are Dr. AI Assistant, a board-certified physician with extensive experience in laboratory medicine and clinical diagnostics. 
        You provide professional medical consultations based on evidence-based medicine and current clinical guidelines.
        
        PROFESSIONAL STANDARDS:
        - Use precise medical terminology with clear explanations
        - Reference specific lab values and clinical ranges when discussing results
        - Provide comprehensive analysis linking multiple biomarkers
        - Maintain professional tone while being accessible to patients
        - Always include appropriate medical disclaimers
        - Recommend follow-up with healthcare providers when indicated
        """)
        
        if context:
            prompt_parts.append(f"\nPATIENT LAB REPORT DATA:\n{context}\n")
        
        if pubmed_info:
            prompt_parts.append(f"\nCURRENT MEDICAL RESEARCH:\n{pubmed_info}\n")
        
        # Add conversation history
        chat_history = memory.get_recent_messages(6)
        if chat_history:
            prompt_parts.append("\nCONVERSATION HISTORY:")
            for msg in chat_history:
                if msg["type"] == "user":
                    prompt_parts.append(f"Patient: {msg['content']}")
                elif msg["type"] == "assistant":
                    prompt_parts.append(f"Dr. AI Assistant: {msg['content']}")
        
        prompt_parts.append(f"\nPATIENT QUESTION: {user_message}")
        prompt_parts.append("""
        
        RESPONSE REQUIREMENTS:
        1. Address the specific medical question with clinical expertise
        2. Reference relevant lab values and normal ranges when applicable
        3. Explain clinical significance and potential health implications
        4. Provide evidence-based recommendations
        5. Include appropriate medical disclaimers
        6. Suggest when to consult healthcare providers
        7. Maintain professional medical consultation tone
        
        Respond as Dr. AI Assistant would in a clinical consultation.
        """)
        
        full_prompt = "\n".join(prompt_parts)
        
        try:
            response = self.model.generate_content(full_prompt)
            response_text = response.text
            
            # Save to memory
            memory.add_user_message(user_message)
            memory.add_ai_message(response_text)
            
            return response_text
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again or rephrase your question."
            
            # Still save to memory
            memory.add_user_message(user_message)
            memory.add_ai_message(error_response)
            
            return error_response
    
    def generate_report_specific_response(self, question, context, filename):
        """Generate response for questions about a specific lab report using RAG context"""
        try:
            prompt = f"""
            You are Dr. AI Assistant, a board-certified physician specializing in laboratory medicine and clinical diagnostics. 
            
            A patient is asking about their specific lab report: "{filename}"
            
            Patient Question: {question}
            
            Lab Report Context:
            {context}
            
            Instructions:
            1. Answer the question specifically about THIS lab report using the provided context
            2. Reference specific values, findings, or recommendations from the report when relevant
            3. Explain medical terms in simple language
            4. If values are mentioned, indicate whether they are normal, high, or low
            5. Provide actionable insights based on the report findings
            6. Be supportive and encouraging while remaining medically accurate
            7. If the question cannot be answered from the report context, say so clearly
            
            Important disclaimers to include:
            - This analysis is for educational purposes only
            - Always consult healthcare providers for medical decisions
            - Lab results should be interpreted by qualified medical professionals
            
            Provide a comprehensive, professional response that directly addresses their question about this specific report.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"I apologize, but I'm having trouble analyzing your report right now. Please try again or consult with your healthcare provider about your lab results. Error: {str(e)}"
