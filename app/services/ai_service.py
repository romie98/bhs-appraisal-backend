"""AI Service for OpenAI integration"""
import os
import openai
from typing import Dict, List, Optional, Any
from openai import OpenAI
import time

# Initialize OpenAI client
client = None

def get_openai_client():
    """Get or create OpenAI client instance"""
    global client
    if client is None:
        # Try to get from config first, then fallback to environment variable
        try:
            from app.core.config import settings
            api_key = settings.OPENAI_API_KEY
        except:
            api_key = None
        
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please add it to your .env file in the backend directory.\n"
                "1. Get your API key from: https://platform.openai.com/api-keys\n"
                "2. Add this line to backend/.env: OPENAI_API_KEY=sk-your-key-here"
            )
        client = OpenAI(api_key=api_key)
    return client


def send_to_ai(prompt: str, model: str = "gpt-4o", max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """
    Send a prompt to OpenAI API and return the response.
    
    Args:
        prompt: The text prompt to send to the AI
        model: The OpenAI model to use (default: gpt-4o, fallback to gpt-4 if gpt-5.1 not available)
        max_tokens: Maximum tokens in response (default: 2000)
        temperature: Sampling temperature (default: 0.7)
    
    Returns:
        str: The AI-generated response text
    
    Raises:
        ValueError: If API key is missing
        openai.APIError: For API-related errors
        openai.RateLimitError: For rate limit errors
        Exception: For other errors (timeouts, network issues, etc.)
    """
    try:
        openai_client = get_openai_client()
        
        # Try to use the specified model, fallback to gpt-4o if model not available
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for teacher appraisal and e-portfolio systems."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30  # 30 second timeout
            )
        except openai.NotFoundError:
            # Fallback to gpt-4o if specified model doesn't exist
            if model != "gpt-4o":
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for teacher appraisal and e-portfolio systems."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30
                )
            else:
                raise
        
        # Extract the response text
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            raise Exception("No response from AI model")
            
    except openai.RateLimitError as e:
        raise Exception(f"Rate limit exceeded. Please try again later. Error: {str(e)}")
    except openai.APIError as e:
        raise Exception(f"OpenAI API error: {str(e)}")
    except openai.APIConnectionError as e:
        raise Exception(f"Network connection error. Please check your internet connection. Error: {str(e)}")
    except openai.APITimeoutError as e:
        raise Exception(f"Request timeout. The AI service took too long to respond. Error: {str(e)}")
    except ValueError as e:
        raise ValueError(f"Configuration error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error communicating with AI: {str(e)}")


def extract_lesson_evidence(lesson_text: str) -> Dict[str, List[str]]:
    """
    Extract evidence from a lesson plan using AI analysis based on Jamaica Teacher Appraisal GP1-GP6.
    
    Args:
        lesson_text: The full lesson plan text to analyze
    
    Returns:
        Dict with keys: gp1, gp2, gp3, gp4, gp5, gp6, strengths, weaknesses
        Each key contains a list of evidence strings (1-3 sentences each)
    
    SPECIAL RULE: Hardware-related evidence (computer ports, components, etc.) is NEVER
    classified under GP6, GP5, GP4, or GP3. It must be classified as GP1 or GP2 only.
    """
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Detect hardware content before AI analysis
    hardware_detection = _detect_hardware_content(lesson_text)
    is_hardware = hardware_detection["is_hardware"]
    suggested_gp = hardware_detection["suggested_gp"]
    
    # Build hardware exclusion warning if hardware detected
    hardware_warning = ""
    if is_hardware:
        hardware_warning = f"""

CRITICAL CLASSIFICATION RULE FOR HARDWARE CONTENT:
The lesson plan contains computer hardware-related content (ports, components, cables, motherboards, etc.).
- This content MUST NEVER be classified under GP6 (Technology Integration), GP5 (Community Engagement), GP4 (Professional Development), or GP3 (Student Assessment & Feedback).
- Hardware content MUST ONLY be classified under GP1 (Subject Content Knowledge) or GP2 (Pedagogy & Teaching Strategies).

Classification Guidelines:
- If the lesson shows technical hardware identification, component explanation, or technical analysis → Classify as GP1
- If the lesson shows a teaching activity, student task, or teaching strategy using the hardware → Classify as GP2
- If both technical and teaching elements are present → Prioritize GP2

Suggested classification based on keywords: {suggested_gp if suggested_gp else "None"}
"""

    prompt = f"""Analyze the following lesson plan and extract evidence according to Jamaica Teacher Appraisal Guiding Principles (GP1-GP6).

Lesson Plan:
{lesson_text}
{hardware_warning}

Instructions:
1. Analyze the lesson plan using the Jamaica Teacher Appraisal guiding principles (GP1-GP6).
2. Extract only meaningful, specific evidence that demonstrates each GP.
3. Write clear, professional evidence items (1-3 sentences each).
4. Look for:
   - GP1 (Subject Content Knowledge): Content accuracy, curriculum alignment, subject expertise
   - GP2 (Pedagogy & Teaching Strategies): Teaching methods, instructional strategies, 5E structure, differentiation
   - GP3 (Student Assessment & Feedback): Assessment strategies, formative/sumulative assessment, feedback methods
   - GP4 (Professional Development): Reflection, professional growth, continuous learning
   - GP5 (Community Engagement): Parent involvement, community connections, collaboration
   - GP6 (Technology Integration): ICT use, digital tools, technology-enhanced learning
5. Also identify strengths and areas for improvement.
6. REMEMBER: If hardware content is detected, it must ONLY be classified under GP1 or GP2, NEVER GP3, GP4, GP5, or GP6.

Return your response as a JSON object with this exact structure:
{{
  "gp1": ["evidence item 1", "evidence item 2", ...],
  "gp2": ["evidence item 1", "evidence item 2", ...],
  "gp3": ["evidence item 1", "evidence item 2", ...],
  "gp4": ["evidence item 1", "evidence item 2", ...],
  "gp5": ["evidence item 1", "evidence item 2", ...],
  "gp6": ["evidence item 1", "evidence item 2", ...],
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["area for improvement 1", "area for improvement 2", ...]
}}

If no evidence is found for a particular GP, return an empty array for that key.
Only include meaningful evidence items. Be specific and reference actual content from the lesson plan."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=3000, temperature=0.3)
        
        # Parse JSON response
        import json
        # Try to extract JSON from the response (in case AI adds extra text)
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        evidence_data = json.loads(response_text)
        
        # Validate structure
        required_keys = ["gp1", "gp2", "gp3", "gp4", "gp5", "gp6", "strengths", "weaknesses"]
        for key in required_keys:
            if key not in evidence_data:
                evidence_data[key] = []
            elif not isinstance(evidence_data[key], list):
                evidence_data[key] = []
        
        # ENFORCE HARDWARE CLASSIFICATION RULES
        # If hardware content is detected, remove evidence from GP3, GP4, GP5, GP6
        if is_hardware:
            logger.info(f"Hardware content detected in lesson plan. Enforcing classification rules. Suggested GP: {suggested_gp}")
            
            # Remove hardware-related evidence from GP3, GP4, GP5, GP6
            for gp_key in ["gp3", "gp4", "gp5", "gp6"]:
                if evidence_data.get(gp_key):
                    # Filter out evidence items that mention hardware keywords
                    hardware_keywords = [
                        "port", "ports", "usb", "hdmi", "vga", "dvi", "ethernet",
                        "motherboard", "cpu", "ram", "hardware", "component", "components",
                        "cable", "cables", "connector", "connectors", "socket", "sockets"
                    ]
                    original_count = len(evidence_data[gp_key])
                    evidence_data[gp_key] = [
                        item for item in evidence_data[gp_key]
                        if not any(keyword in item.lower() for keyword in hardware_keywords)
                    ]
                    removed_count = original_count - len(evidence_data[gp_key])
                    if removed_count > 0:
                        logger.warning(f"Removed {removed_count} hardware-related evidence item(s) from {gp_key.upper()}. Hardware content must only be in GP1 or GP2.")
            
            # Ensure hardware content is classified in GP1 or GP2
            has_gp1 = len(evidence_data.get("gp1", [])) > 0
            has_gp2 = len(evidence_data.get("gp2", [])) > 0
            
            # Check if any hardware evidence was removed and needs to be reassigned
            hardware_evidence_found = False
            for gp_key in ["gp3", "gp4", "gp5", "gp6"]:
                if any(keyword in str(item).lower() for item in evidence_data.get(gp_key, [])
                       for keyword in ["port", "ports", "usb", "hdmi", "vga", "hardware", "component", "motherboard"]):
                    hardware_evidence_found = True
                    break
            
            # If hardware was detected but not in GP1 or GP2, add default evidence
            if not has_gp1 and not has_gp2 and is_hardware:
                if suggested_gp == "GP1":
                    evidence_data["gp1"] = ["Evidence demonstrates technical knowledge of computer hardware components and their functions."]
                    logger.info("Assigned hardware content to GP1 (Subject Content Knowledge)")
                elif suggested_gp == "GP2":
                    evidence_data["gp2"] = ["Evidence shows use of hardware images or components in teaching activities and lesson strategies."]
                    logger.info("Assigned hardware content to GP2 (Pedagogy & Teaching Strategies)")
                else:
                    # Default to GP1 if no clear suggestion
                    evidence_data["gp1"] = ["Evidence demonstrates technical knowledge of computer hardware components and their functions."]
                    logger.info("Assigned hardware content to GP1 (default)")
        
        return evidence_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error extracting lesson evidence: {str(e)}")


def extract_log_evidence(entry_text: str) -> Dict[str, any]:
    """
    Extract evidence from a log book entry using AI analysis based on Jamaica Teacher Appraisal GP3, GP4, GP6.
    
    Args:
        entry_text: The log book entry text to analyze
    
    Returns:
        Dict with keys: mappedGP (list of {gp, evidence}), summary (string)
    """
    prompt = f"""Analyze the following log book entry and extract evidence according to Jamaica Teacher Appraisal Guiding Principles (GP3, GP4, GP6).

Log Book Entry:
{entry_text}

Instructions:
1. Analyze the log entry using GP3 (Student Assessment & Feedback), GP4 (Professional Development), and GP6 (Technology Integration) criteria.
2. Identify evidence related to:
   - Student behaviour and diversity (GP3)
   - Teacher reflection and professional growth (GP4)
   - Ethical conduct, punctuality, leadership (GP4)
   - Technology integration and ICT use (GP6)
   - Assessment and feedback practices (GP3)
3. Convert log entries into formal, professional evidence statements (1-3 sentences each).
4. Only include evidence that clearly maps to GP3, GP4, or GP6.
5. Provide a brief 2-3 sentence summary of the entry.

Return your response as a JSON object with this exact structure:
{{
  "mappedGP": [
    {{"gp": 3, "evidence": "evidence statement 1"}},
    {{"gp": 4, "evidence": "evidence statement 2"}},
    {{"gp": 6, "evidence": "evidence statement 3"}}
  ],
  "summary": "2-3 sentence overview of the log entry"
}}

If no evidence is found for a particular GP, do not include it in the mappedGP array.
Only include meaningful evidence items that clearly demonstrate the GP."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=2000, temperature=0.3)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        evidence_data = json.loads(response_text)
        
        # Validate structure
        if "mappedGP" not in evidence_data:
            evidence_data["mappedGP"] = []
        if "summary" not in evidence_data:
            evidence_data["summary"] = ""
        
        # Validate GP numbers (only 3, 4, 6 allowed)
        valid_gps = [3, 4, 6]
        evidence_data["mappedGP"] = [
            item for item in evidence_data["mappedGP"]
            if isinstance(item, dict) and "gp" in item and "evidence" in item
            and item["gp"] in valid_gps
        ]
        
        return evidence_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error extracting log evidence: {str(e)}")


def extract_register_evidence(register_data: Dict) -> Dict[str, any]:
    """
    Extract evidence from register/attendance data using AI analysis based on Jamaica Teacher Appraisal GP3 and GP6.
    
    Args:
        register_data: Dict containing attendance data with keys like:
            - attendance_percentage
            - punctuality_percentage
            - notes (list of absence notes)
            - follow_ups (list of follow-up actions)
            - date_range (start and end dates)
    
    Returns:
        Dict with keys: gp3 (list), gp6 (list), patternsDetected (list), recommendedInterventions (list)
    """
    # Format the register data for the prompt
    notes_text = '\n'.join(register_data.get('notes', [])) if register_data.get('notes') else 'No notes provided'
    follow_ups_text = '\n'.join(register_data.get('follow_ups', [])) if register_data.get('follow_ups') else 'No follow-ups recorded'
    
    data_summary = f"""Attendance Period: {register_data.get('date_range', 'N/A')}
Overall Attendance: {register_data.get('attendance_percentage', 0)}%
Overall Punctuality: {register_data.get('punctuality_percentage', 0)}%

Absence Notes:
{notes_text}

Follow-ups Conducted:
{follow_ups_text}"""
    
    prompt = f"""Analyze the following attendance/register data and extract evidence according to Jamaica Teacher Appraisal Guiding Principles (GP3 and GP6 only).

Register Data:
{data_summary}

Instructions:
1. Analyze the attendance data using GP3 (Student Assessment & Feedback) and GP6 (Technology Integration) criteria.
2. Identify evidence related to:
   - Follow-ups with absent students (GP3)
   - Punctuality patterns and interventions (GP3)
   - Class behaviour trends (GP3)
   - Student welfare and safety concerns (GP3)
   - Use of technology for attendance tracking (GP6)
   - Digital tools for communication with parents/students (GP6)
3. Detect patterns in attendance, punctuality, and behaviour.
4. Recommend interventions based on the data.
5. Convert findings into formal, professional evidence statements (1-3 sentences each).

Return your response as a JSON object with this exact structure:
{{
  "gp3": ["evidence statement 1", "evidence statement 2", ...],
  "gp6": ["evidence statement 1", "evidence statement 2", ...],
  "patternsDetected": ["pattern 1", "pattern 2", ...],
  "recommendedInterventions": ["intervention 1", "intervention 2", ...]
}}

If no evidence is found for a particular GP, return an empty array.
Only include meaningful evidence items that clearly demonstrate the GP."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=2500, temperature=0.3)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        evidence_data = json.loads(response_text)
        
        # Validate structure
        required_keys = ["gp3", "gp6", "patternsDetected", "recommendedInterventions"]
        for key in required_keys:
            if key not in evidence_data:
                evidence_data[key] = []
            elif not isinstance(evidence_data[key], list):
                evidence_data[key] = []
        
        return evidence_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error extracting register evidence: {str(e)}")


def generate_appraisal_report(appraisal_data: Dict) -> Dict:
    """
    Generate a comprehensive appraisal report with scoring and categorization.
    
    Args:
        appraisal_data: Dict containing:
            - gp_evidence: Dict with gp1-gp6 evidence lists
            - attendance_patterns: Dict with attendance data
            - professional_development: List of PD activities
            - lesson_plan_quality: Dict with lesson plan metrics
            - class_performance_trends: Dict with performance data
    
    Returns:
        Dict with keys: scores, category, strengths, weaknesses, recommendations, actionPlan
    """
    import json
    
    # Format the data for the prompt
    evidence_summary = "GP EVIDENCE:\n"
    for gp_num in range(1, 7):
        gp_key = f"gp{gp_num}"
        evidence_list = appraisal_data.get("gp_evidence", {}).get(gp_key, [])
        if evidence_list:
            evidence_summary += f"GP{gp_num}: {len(evidence_list)} evidence items\n"
            for item in evidence_list[:3]:  # Show first 3
                evidence_summary += f"  - {item[:100]}...\n"
    evidence_summary += "\n"
    
    attendance_summary = f"""ATTENDANCE PATTERNS:
- Overall Attendance: {appraisal_data.get('attendance_patterns', {}).get('overall_attendance', 'N/A')}%
- Punctuality: {appraisal_data.get('attendance_patterns', {}).get('punctuality', 'N/A')}%
- Follow-ups Conducted: {appraisal_data.get('attendance_patterns', {}).get('follow_ups_count', 0)}
"""
    
    pd_summary = f"""PROFESSIONAL DEVELOPMENT:
- Activities: {len(appraisal_data.get('professional_development', []))} recorded
- Recent PD: {', '.join([pd.get('title', 'N/A')[:50] for pd in appraisal_data.get('professional_development', [])[:3]])}
"""
    
    lesson_summary = f"""LESSON PLAN QUALITY:
- Total Lessons: {appraisal_data.get('lesson_plan_quality', {}).get('total_lessons', 0)}
- Average Quality Score: {appraisal_data.get('lesson_plan_quality', {}).get('average_score', 'N/A')}
- Evidence Items: {appraisal_data.get('lesson_plan_quality', {}).get('evidence_count', 0)}
"""
    
    performance_summary = f"""CLASS PERFORMANCE TRENDS:
- Average Assessment Score: {appraisal_data.get('class_performance_trends', {}).get('average_score', 'N/A')}%
- Improvement Trend: {appraisal_data.get('class_performance_trends', {}).get('trend', 'N/A')}
- Students Meeting Standards: {appraisal_data.get('class_performance_trends', {}).get('meeting_standards', 'N/A')}%
"""
    
    prompt = f"""You are generating a comprehensive teacher appraisal report based on Jamaica Teacher Appraisal Instrument.

{evidence_summary}
{attendance_summary}
{pd_summary}
{lesson_summary}
{performance_summary}

Instructions:
1. Score each GP (GP1-GP6) on a 0-100 "credit score" scale based on:
   - Quantity and quality of evidence
   - Alignment with GP criteria
   - Impact on student learning
   - Professional growth demonstrated
   - Consistency and depth of practice

2. Determine overall category based on average score:
   - Exemplary: 90-100 average
   - Area of Strength: 75-89 average
   - Area for Improvement: 60-74 average
   - Unsatisfactory: Below 60 average

3. Identify key strengths across all GPs.

4. Identify areas needing improvement.

5. Provide specific, actionable recommendations.

6. Create a future action plan with prioritized steps.

Return your response as a JSON object with this exact structure:
{{
  "scores": {{
    "gp1": 87,
    "gp2": 92,
    "gp3": 79,
    "gp4": 85,
    "gp5": 76,
    "gp6": 88
  }},
  "category": "Area of Strength",
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1", "weakness 2", ...],
  "recommendations": ["recommendation 1", "recommendation 2", ...],
  "actionPlan": [
    {{
      "priority": "high/medium/low",
      "action": "action description",
      "timeline": "timeline description"
    }}
  ]
}}

Be fair, constructive, and specific in your scoring and feedback."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=4000, temperature=0.3)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        report_data = json.loads(response_text)
        
        # Validate structure
        if "scores" not in report_data:
            report_data["scores"] = {}
        if "category" not in report_data:
            report_data["category"] = "Area for Improvement"
        if "strengths" not in report_data:
            report_data["strengths"] = []
        if "weaknesses" not in report_data:
            report_data["weaknesses"] = []
        if "recommendations" not in report_data:
            report_data["recommendations"] = []
        if "actionPlan" not in report_data:
            report_data["actionPlan"] = []
        
        # Ensure all GP scores are present
        for gp_num in range(1, 7):
            gp_key = f"gp{gp_num}"
            if gp_key not in report_data["scores"]:
                report_data["scores"][gp_key] = 0
        
        # Validate scores are between 0-100
        for gp_key in report_data["scores"]:
            score = report_data["scores"][gp_key]
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                report_data["scores"][gp_key] = max(0, min(100, int(score) if isinstance(score, (int, float)) else 0))
        
        return report_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error generating appraisal report: {str(e)}")


def _detect_hardware_content(ocr_text: str) -> Dict[str, Any]:
    """
    Detect if the OCR text contains computer hardware-related content.
    
    Returns:
        Dict with:
        - is_hardware: bool - Whether hardware content is detected
        - gp1_keywords_found: list - GP1-related keywords found
        - gp2_keywords_found: list - GP2-related keywords found
        - suggested_gp: str - "GP1", "GP2", or None
    """
    text_lower = ocr_text.lower()
    
    # GP 1 Keywords (technical/hardware identification)
    gp1_keywords = [
        "identify the ports",
        "computer ports",
        "usb port",
        "hdmi",
        "vga",
        "hardware components",
        "motherboard",
        "technical analysis",
        "explain how this component works",
        "computer port",
        "internal components",
        "cables",
        "component identification",
        "technical explanation",
        "hardware analysis",
        "port identification",
        "computer hardware",
        "hardware diagram",
        "component diagram"
    ]
    
    # GP 2 Keywords (teaching/lesson activity)
    gp2_keywords = [
        "lesson",
        "students",
        "activity",
        "assignment",
        "teach",
        "classwork",
        "practice exercise",
        "group work based on the image",
        "use this image to teach",
        "teaching strategy",
        "ict",
        "demonstration",
        "student task",
        "lesson activity"
    ]
    
    gp1_found = [kw for kw in gp1_keywords if kw in text_lower]
    gp2_found = [kw for kw in gp2_keywords if kw in text_lower]
    
    # Additional hardware indicators
    hardware_indicators = [
        "port", "ports", "usb", "hdmi", "vga", "dvi", "ethernet",
        "motherboard", "cpu", "ram", "hardware", "component", "components",
        "cable", "cables", "connector", "connectors", "socket", "sockets"
    ]
    
    has_hardware_indicators = any(indicator in text_lower for indicator in hardware_indicators)
    
    is_hardware = len(gp1_found) > 0 or len(gp2_found) > 0 or has_hardware_indicators
    
    # Determine suggested GP
    suggested_gp = None
    if is_hardware:
        # If both GP1 and GP2 keywords found, prioritize GP2 (teaching context)
        if len(gp2_found) > 0:
            suggested_gp = "GP2"
        elif len(gp1_found) > 0:
            suggested_gp = "GP1"
        elif has_hardware_indicators:
            # Default to GP1 for pure hardware content
            suggested_gp = "GP1"
    
    return {
        "is_hardware": is_hardware,
        "gp1_keywords_found": gp1_found,
        "gp2_keywords_found": gp2_found,
        "suggested_gp": suggested_gp
    }


def analyze_photo_evidence(ocr_text: str) -> Dict[str, Any]:
    """
    Analyze OCR text from a photo and determine which GP(s) and GP subsections it best supports.

    Returns a strict JSON structure with GP1–GP6 keys, each containing:
    - subsections: List of subsection codes (e.g., ["GP1.1", "GP1.3"])
    - justifications: Dict mapping subsection codes to 1-sentence explanations
    
    SPECIAL RULE: Hardware-related evidence (computer ports, components, etc.) is NEVER
    classified under GP6, GP5, GP4, or GP3. It must be classified as GP1 or GP2 only.
    """
    import json
    import logging

    logger = logging.getLogger(__name__)
    
    # Detect hardware content before AI analysis
    hardware_detection = _detect_hardware_content(ocr_text)
    is_hardware = hardware_detection["is_hardware"]
    suggested_gp = hardware_detection["suggested_gp"]

    # Build hardware exclusion warning if hardware detected
    hardware_warning = ""
    if is_hardware:
        hardware_warning = f"""

CRITICAL CLASSIFICATION RULE FOR HARDWARE CONTENT:
The text contains computer hardware-related content (ports, components, cables, motherboards, etc.).
- This content MUST NEVER be classified under GP6 (Technology Integration), GP5 (Community Engagement), GP4 (Professional Development), or GP3 (Student Assessment & Feedback).
- Hardware content MUST ONLY be classified under GP1 (Subject Content Knowledge) or GP2 (Pedagogy & Teaching Strategies).

Classification Guidelines:
- If the evidence shows technical hardware identification, component explanation, or technical analysis → Classify as GP1
- If the evidence shows a lesson activity, student task, or teaching strategy using the hardware → Classify as GP2
- If both technical and teaching elements are present → Prioritize GP2

Suggested classification based on keywords: {suggested_gp if suggested_gp else "None"}
"""

    # STRICT JSON-ONLY PROMPT with GP subsections
    prompt = f"""You are an AI that must ONLY output strict JSON.

Never include explanations, markdown, or additional text.

Required JSON structure:
{{
  "GP1": {{
    "subsections": [],
    "justifications": {{}}
  }},
  "GP2": {{
    "subsections": [],
    "justifications": {{}}
  }},
  "GP3": {{
    "subsections": [],
    "justifications": {{}}
  }},
  "GP4": {{
    "subsections": [],
    "justifications": {{}}
  }},
  "GP5": {{
    "subsections": [],
    "justifications": {{}}
  }},
  "GP6": {{
    "subsections": [],
    "justifications": {{}}
  }}
}}

Analyze the following text that was extracted from a classroom photo (e.g., bulletin board, student work, classroom display, assessment, certificate, etc.).

Text:
{ocr_text}
{hardware_warning}

GP Subsection Reference:
GP1 - Subject Content Knowledge:
  GP1.1: Content Accuracy and Depth
  GP1.2: Curriculum Alignment
  GP1.3: Subject Expertise Demonstration
  GP1.4: Content Organization and Structure

GP2 - Pedagogy & Teaching Strategies:
  GP2.1: Curriculum Alignment and Planning
  GP2.2: Teaching Strategies and Methods
  GP2.3: Use of Assessment in Teaching
  GP2.4: Differentiation and Individualization
  GP2.5: Learning Environment Management

GP3 - Student Assessment & Feedback:
  GP3.1: Assessment Design and Implementation
  GP3.2: Feedback to Students
  GP3.3: Use of Assessment Data
  GP3.4: Student Progress Monitoring

GP4 - Professional Development:
  GP4.1: Reflective Practice
  GP4.2: Professional Growth Activities
  GP4.3: Collaboration with Colleagues
  GP4.4: Ethical Conduct and Professionalism

GP5 - Community Engagement:
  GP5.1: Parent/Guardian Communication
  GP5.2: Community Involvement
  GP5.3: School-Community Partnerships
  GP5.4: Student Welfare and Support

GP6 - Technology Integration:
  GP6.1: Use of ICT in Teaching
  GP6.2: Digital Tools and Resources
  GP6.3: Technology-Enhanced Learning
  GP6.4: Digital Literacy Development

Instructions:
1. Match the evidence to specific GP categories (GP1–GP6) AND their subsections (e.g., GP2.1, GP3.4).
2. For each matching subsection:
   - Add the subsection code to the "subsections" array (e.g., ["GP2.1", "GP2.3"]).
   - Add a 1-sentence justification in the "justifications" dict (e.g., {{"GP2.1": "Evidence shows alignment between activity and objectives."}}).
3. Only include subsections where there is clear evidence in the photo text.
4. If no evidence exists for a GP, return empty arrays and empty dict for that GP.
5. REMEMBER: If hardware content is detected, it must ONLY be classified under GP1 or GP2, NEVER GP3, GP4, GP5, or GP6.

IMPORTANT: Return ONLY the JSON object. No markdown, no prose, no code fences."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=2500, temperature=0.1)

        # Clean potential markdown wrappers
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Narrow to JSON object if there is extra text
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace + 1]

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Photo evidence AI JSON parse error: {e}. Raw: {cleaned[:300]}")
            # Fallback: empty structure
            return {f"GP{i}": {"subsections": [], "justifications": {}} for i in range(1, 7)}

        # Normalize structure
        result: Dict[str, Any] = {}
        for i in range(1, 7):
            key = f"GP{i}"
            gp_data = data.get(key, {})
            if not isinstance(gp_data, dict):
                gp_data = {}
            
            subsections = gp_data.get("subsections", [])
            if not isinstance(subsections, list):
                subsections = []
            # Ensure all subsection codes are strings
            subsections = [str(s) for s in subsections if s]
            
            justifications = gp_data.get("justifications", {})
            if not isinstance(justifications, dict):
                justifications = {}
            # Ensure all justifications are strings
            justifications = {str(k): str(v) for k, v in justifications.items() if k and v}
            
            result[key] = {
                "subsections": subsections,
                "justifications": justifications
            }

        # ENFORCE HARDWARE CLASSIFICATION RULES
        # If hardware content is detected, remove classifications from GP3, GP4, GP5, GP6
        if is_hardware:
            logger.info(f"Hardware content detected. Enforcing classification rules. Suggested GP: {suggested_gp}")
            
            # Remove hardware-related classifications from GP3, GP4, GP5, GP6
            for gp_to_clear in ["GP3", "GP4", "GP5", "GP6"]:
                if result[gp_to_clear]["subsections"] or result[gp_to_clear]["justifications"]:
                    logger.warning(f"Removing hardware classification from {gp_to_clear}. Hardware content must only be in GP1 or GP2.")
                    result[gp_to_clear] = {
                        "subsections": [],
                        "justifications": {}
                    }
            
            # Ensure hardware content is classified in GP1 or GP2
            has_gp1 = len(result["GP1"]["subsections"]) > 0 or len(result["GP1"]["justifications"]) > 0
            has_gp2 = len(result["GP2"]["subsections"]) > 0 or len(result["GP2"]["justifications"]) > 0
            
            # If neither GP1 nor GP2 has content, assign based on suggested GP
            if not has_gp1 and not has_gp2:
                if suggested_gp == "GP1":
                    result["GP1"] = {
                        "subsections": ["GP1.3"],  # Subject Expertise Demonstration
                        "justifications": {"GP1.3": "Evidence demonstrates technical knowledge of computer hardware components."}
                    }
                    logger.info("Assigned hardware content to GP1 (Subject Content Knowledge)")
                elif suggested_gp == "GP2":
                    result["GP2"] = {
                        "subsections": ["GP2.2"],  # Teaching Strategies and Methods
                        "justifications": {"GP2.2": "Evidence shows use of hardware images in teaching activities."}
                    }
                    logger.info("Assigned hardware content to GP2 (Pedagogy & Teaching Strategies)")
                else:
                    # Default to GP1 if no clear suggestion
                    result["GP1"] = {
                        "subsections": ["GP1.3"],
                        "justifications": {"GP1.3": "Evidence demonstrates technical knowledge of computer hardware components."}
                    }
                    logger.info("Assigned hardware content to GP1 (default)")

        return result
    except Exception as e:
        logger.error(f"Error analyzing photo evidence: {e}", exc_info=True)
        return {f"GP{i}": {"subsections": [], "justifications": {}} for i in range(1, 7)}


def extract_log_evidence(entry_text: str) -> Dict:
    """
    Extract evidence from a log book entry using AI analysis based on GP3, GP4, and GP6.
    
    Args:
        entry_text: The log book entry text to analyze
    
    Returns:
        Dict with keys: mappedGP (list of {gp, evidence}), summary (string)
    """
    prompt = f"""Analyze the following log book entry and extract evidence according to Jamaica Teacher Appraisal Guiding Principles (GP3, GP4, GP6).

Log Book Entry:
{entry_text}

Instructions:
1. Analyze the log entry using GP3 (Student Assessment & Feedback), GP4 (Professional Development), and GP6 (Technology Integration) criteria.
2. Identify evidence related to:
   - Student behaviour and diversity (GP3)
   - Teacher reflection and professional growth (GP4)
   - Ethical conduct, punctuality, leadership (GP4)
   - Technology integration if applicable (GP6)
3. Convert log entries into formal, professional evidence statements (1-3 sentences each).
4. Only include evidence that clearly demonstrates the GP criteria.
5. Provide a brief 2-3 sentence summary of the entry.

Return your response as a JSON object with this exact structure:
{{
  "mappedGP": [
    {{"gp": 3, "evidence": "evidence statement 1"}},
    {{"gp": 4, "evidence": "evidence statement 2"}},
    {{"gp": 6, "evidence": "evidence statement 3"}}
  ],
  "summary": "2-3 sentence overview of the log entry"
}}

Only include GPs (3, 4, or 6) where meaningful evidence exists. If no evidence is found for a GP, do not include it in mappedGP.
Be specific and reference actual content from the log entry."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=2000, temperature=0.3)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        evidence_data = json.loads(response_text)
        
        # Validate structure
        if "mappedGP" not in evidence_data:
            evidence_data["mappedGP"] = []
        if "summary" not in evidence_data:
            evidence_data["summary"] = ""
        
        # Validate mappedGP items
        if not isinstance(evidence_data["mappedGP"], list):
            evidence_data["mappedGP"] = []
        else:
            # Filter out invalid items
            evidence_data["mappedGP"] = [
                item for item in evidence_data["mappedGP"]
                if isinstance(item, dict) and "gp" in item and "evidence" in item
                and item["gp"] in [3, 4, 6]
            ]
        
        return evidence_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error extracting log evidence: {str(e)}")


def extract_register_evidence(register_data: Dict) -> Dict:
    """
    Extract evidence from register/attendance data using AI analysis based on GP3 and GP6.
    
    Args:
        register_data: Dict containing attendance data with keys like:
            - attendance_percentage (float)
            - punctuality_percentage (float)
            - notes (list of strings)
            - follow_ups (list of strings)
            - date_range (string)
    
    Returns:
        Dict with keys: gp3 (list), gp6 (list), patternsDetected (list), recommendedInterventions (list)
    """
    prompt = f"""Analyze the following attendance/register data and extract evidence according to Jamaica Teacher Appraisal Guiding Principles (GP3 and GP6).

Attendance Data:
- Attendance Percentage: {register_data.get('attendance_percentage', 'N/A')}%
- Punctuality Percentage: {register_data.get('punctuality_percentage', 'N/A')}%
- Date Range: {register_data.get('date_range', 'N/A')}
- Notes on Absences: {register_data.get('notes', [])}
- Follow-ups Done: {register_data.get('follow_ups', [])}

Instructions:
1. Analyze the register data using GP3 (Student Assessment & Feedback) and GP6 (Technology Integration) criteria.
2. Identify evidence related to:
   - Follow-ups with absent students (GP3)
   - Punctuality patterns and interventions (GP3)
   - Class behaviour trends (GP3)
   - Safety/welfare concerns addressed (GP3)
   - Use of technology for attendance tracking (GP6)
   - Digital tools for communication with parents (GP6)
3. Detect patterns in attendance, punctuality, and behaviour.
4. Recommend interventions based on the data.
5. Write clear, professional evidence statements (1-3 sentences each).

Return your response as a JSON object with this exact structure:
{{
  "gp3": ["evidence statement 1", "evidence statement 2", ...],
  "gp6": ["evidence statement 1", "evidence statement 2", ...],
  "patternsDetected": ["pattern 1", "pattern 2", ...],
  "recommendedInterventions": ["intervention 1", "intervention 2", ...]
}}

If no evidence is found for a GP, return an empty array. Only include meaningful evidence and patterns."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=2500, temperature=0.3)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        evidence_data = json.loads(response_text)
        
        # Validate structure
        required_keys = ["gp3", "gp6", "patternsDetected", "recommendedInterventions"]
        for key in required_keys:
            if key not in evidence_data:
                evidence_data[key] = []
            elif not isinstance(evidence_data[key], list):
                evidence_data[key] = []
        
        return evidence_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error extracting register evidence: {str(e)}")


def generate_appraisal_report(appraisal_data: Dict) -> Dict:
    """
    Generate a comprehensive appraisal report with scoring and categorization.
    
    Args:
        appraisal_data: Dict containing:
            - gp_evidence: Dict with gp1-gp6 evidence lists
            - attendance_patterns: Dict with attendance data
            - professional_development: List of PD activities
            - lesson_plan_quality: Dict with lesson plan metrics
            - class_performance_trends: Dict with performance data
    
    Returns:
        Dict with keys: scores, category, strengths, weaknesses, recommendations, actionPlan
    """
    import json
    
    # Format the data for the prompt
    evidence_summary = "GP EVIDENCE:\n"
    for gp_num in range(1, 7):
        gp_key = f"gp{gp_num}"
        evidence_list = appraisal_data.get("gp_evidence", {}).get(gp_key, [])
        if evidence_list:
            evidence_summary += f"GP{gp_num}: {len(evidence_list)} evidence items\n"
            for item in evidence_list[:3]:  # Show first 3
                evidence_summary += f"  - {item[:100]}...\n"
    evidence_summary += "\n"
    
    attendance_summary = f"""ATTENDANCE PATTERNS:
- Overall Attendance: {appraisal_data.get('attendance_patterns', {}).get('overall_attendance', 'N/A')}%
- Punctuality: {appraisal_data.get('attendance_patterns', {}).get('punctuality', 'N/A')}%
- Follow-ups Conducted: {appraisal_data.get('attendance_patterns', {}).get('follow_ups_count', 0)}
"""
    
    pd_summary = f"""PROFESSIONAL DEVELOPMENT:
- Activities: {len(appraisal_data.get('professional_development', []))} recorded
- Recent PD: {', '.join([pd.get('title', 'N/A')[:50] for pd in appraisal_data.get('professional_development', [])[:3]])}
"""
    
    lesson_summary = f"""LESSON PLAN QUALITY:
- Total Lessons: {appraisal_data.get('lesson_plan_quality', {}).get('total_lessons', 0)}
- Average Quality Score: {appraisal_data.get('lesson_plan_quality', {}).get('average_score', 'N/A')}
- Evidence Items: {appraisal_data.get('lesson_plan_quality', {}).get('evidence_count', 0)}
"""
    
    performance_summary = f"""CLASS PERFORMANCE TRENDS:
- Average Assessment Score: {appraisal_data.get('class_performance_trends', {}).get('average_score', 'N/A')}%
- Improvement Trend: {appraisal_data.get('class_performance_trends', {}).get('trend', 'N/A')}
- Students Meeting Standards: {appraisal_data.get('class_performance_trends', {}).get('meeting_standards', 'N/A')}%
"""
    
    prompt = f"""You are generating a comprehensive teacher appraisal report based on Jamaica Teacher Appraisal Instrument.

{evidence_summary}
{attendance_summary}
{pd_summary}
{lesson_summary}
{performance_summary}

Instructions:
1. Score each GP (GP1-GP6) on a 0-100 "credit score" scale based on:
   - Quantity and quality of evidence
   - Alignment with GP criteria
   - Impact on student learning
   - Professional growth demonstrated
   - Consistency and depth of practice

2. Determine overall category based on average score:
   - Exemplary: 90-100 average
   - Area of Strength: 75-89 average
   - Area for Improvement: 60-74 average
   - Unsatisfactory: Below 60 average

3. Identify key strengths across all GPs.

4. Identify areas needing improvement.

5. Provide specific, actionable recommendations.

6. Create a future action plan with prioritized steps.

Return your response as a JSON object with this exact structure:
{{
  "scores": {{
    "gp1": 87,
    "gp2": 92,
    "gp3": 79,
    "gp4": 85,
    "gp5": 76,
    "gp6": 88
  }},
  "category": "Area of Strength",
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1", "weakness 2", ...],
  "recommendations": ["recommendation 1", "recommendation 2", ...],
  "actionPlan": [
    {{
      "priority": "high/medium/low",
      "action": "action description",
      "timeline": "timeline description"
    }}
  ]
}}

Be fair, constructive, and specific in your scoring and feedback."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=4000, temperature=0.3)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        report_data = json.loads(response_text)
        
        # Validate structure
        if "scores" not in report_data:
            report_data["scores"] = {}
        if "category" not in report_data:
            report_data["category"] = "Area for Improvement"
        if "strengths" not in report_data:
            report_data["strengths"] = []
        if "weaknesses" not in report_data:
            report_data["weaknesses"] = []
        if "recommendations" not in report_data:
            report_data["recommendations"] = []
        if "actionPlan" not in report_data:
            report_data["actionPlan"] = []
        
        # Ensure all GP scores are present
        for gp_num in range(1, 7):
            gp_key = f"gp{gp_num}"
            if gp_key not in report_data["scores"]:
                report_data["scores"][gp_key] = 0
        
        # Validate scores are between 0-100
        for gp_key in report_data["scores"]:
            score = report_data["scores"][gp_key]
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                report_data["scores"][gp_key] = max(0, min(100, int(score) if isinstance(score, (int, float)) else 0))
        
        return report_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error generating appraisal report: {str(e)}")



# Missing functions added


def extract_assessment_evidence(assessment_data: Dict) -> Dict:
    """
    Extract evidence from assessment data using AI analysis based on GP2 and GP3.
    
    Args:
        assessment_data: Dict containing:
            - description: Assessment description
            - grade_distribution: Dict with grade breakdown (e.g., {"A": 5, "B": 10})
            - diagnostic_results: List of diagnostic results (optional)
            - total_students: Total number of students (optional)
            - average_score: Average score (optional)
    
    Returns:
        Dict with keys: gp2 (list), gp3 (list), performanceBreakdown (dict), recommendedActions (list)
    """
    import json
    
    description = assessment_data.get("description", "")
    grade_dist = assessment_data.get("grade_distribution", {})
    diagnostic = assessment_data.get("diagnostic_results", [])
    total_students = assessment_data.get("total_students", 0)
    avg_score = assessment_data.get("average_score", 0)
    
    prompt = f"""Analyze the following assessment data and extract evidence according to Jamaica Teacher Appraisal Guiding Principles (GP2 and GP3).

Assessment Description:
{description}

Grade Distribution:
{json.dumps(grade_dist, indent=2) if grade_dist else "Not provided"}

Total Students: {total_students}
Average Score: {avg_score}%

Diagnostic Results:
{json.dumps(diagnostic, indent=2) if diagnostic else "Not provided"}

Instructions:
1. Analyze the assessment using GP2 (Pedagogy & Teaching Strategies) and GP3 (Student Assessment & Feedback) criteria.
2. Identify evidence related to:
   - Differentiation strategies used (GP2)
   - Assessment design and alignment (GP2)
   - Learning gap identification (GP3)
   - Feedback mechanisms (GP3)
   - Student performance analysis (GP3)
3. Detect learning gaps and areas needing intervention.
4. Identify strengths in teaching and assessment practices.
5. Recommend student groups for extra support.
6. Write clear, professional evidence statements (1-3 sentences each).

Return your response as a JSON object with this exact structure:
{{
  "gp2": ["evidence statement 1", "evidence statement 2", ...],
  "gp3": ["evidence statement 1", "evidence statement 2", ...],
  "performanceBreakdown": {{
    "strengths": ["strength 1", "strength 2", ...],
    "areasNeedingIntervention": ["area 1", "area 2", ...],
    "recommendedStudentGroups": ["group description 1", "group description 2", ...]
  }},
  "recommendedActions": ["action 1", "action 2", ...]
}}

If no evidence is found for a GP, return an empty array. Be specific and reference actual assessment data."""

    try:
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=3000, temperature=0.3)
        
        # Parse JSON response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        evidence_data = json.loads(response_text)
        
        # Validate structure
        if "gp2" not in evidence_data:
            evidence_data["gp2"] = []
        elif not isinstance(evidence_data["gp2"], list):
            evidence_data["gp2"] = []
        
        if "gp3" not in evidence_data:
            evidence_data["gp3"] = []
        elif not isinstance(evidence_data["gp3"], list):
            evidence_data["gp3"] = []
        
        if "performanceBreakdown" not in evidence_data:
            evidence_data["performanceBreakdown"] = {
                "strengths": [],
                "areasNeedingIntervention": [],
                "recommendedStudentGroups": []
            }
        
        if "recommendedActions" not in evidence_data:
            evidence_data["recommendedActions"] = []
        elif not isinstance(evidence_data["recommendedActions"], list):
            evidence_data["recommendedActions"] = []
        
        return evidence_data
        
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse AI response as JSON: {str(e)}. Response: {response_text[:200]}")
    except Exception as e:
        raise Exception(f"Error extracting assessment evidence: {str(e)}")


def build_portfolio(all_evidence: Dict) -> Dict:
    """
    Build a comprehensive portfolio from all evidence sources.
    Organizes evidence into GP1-GP6 sections with summaries.
    
    This function uses STRICT JSON MODE to ensure the AI always returns valid JSON.
    Includes comprehensive error handling and logging for debugging.
    
    Args:
        all_evidence: Dict containing:
            - lesson_evidence: List of lesson evidence items
            - log_evidence: List of log evidence items
            - assessment_evidence: List of assessment evidence items
            - register_evidence: List of register evidence items
            - external_uploads: List of external upload evidence items
    
    Returns:
        Dict with keys: gp1-gp6 (each with evidence and summary), overall_summary
        
    Raises:
        Exception: If AI returns invalid JSON or other errors occur
    """
    import json
    import logging
    
    # Set up logging
    logger = logging.getLogger(__name__)
    
    # Collect all evidence by GP
    evidence_by_gp = {f"gp{i}": [] for i in range(1, 7)}
    
    # Process lesson evidence
    lesson_count = 0
    for item in all_evidence.get("lesson_evidence", []):
        if isinstance(item, dict):
            lesson_count += 1
            for gp_num in range(1, 7):
                gp_key = f"gp{gp_num}"
                if gp_key in item and isinstance(item[gp_key], list):
                    evidence_by_gp[gp_key].extend(item[gp_key])
    
    # Process log evidence
    log_count = 0
    for item in all_evidence.get("log_evidence", []):
        if isinstance(item, dict) and "mappedGP" in item:
            log_count += 1
            for gp_item in item["mappedGP"]:
                if isinstance(gp_item, dict) and "gp" in gp_item and "evidence" in gp_item:
                    gp_num = gp_item["gp"]
                    if 1 <= gp_num <= 6:
                        evidence_by_gp[f"gp{gp_num}"].append(gp_item["evidence"])
    
    # Process assessment evidence
    assessment_count = 0
    for item in all_evidence.get("assessment_evidence", []):
        if isinstance(item, dict):
            assessment_count += 1
            if "gp2" in item and isinstance(item["gp2"], list):
                evidence_by_gp["gp2"].extend(item["gp2"])
            if "gp3" in item and isinstance(item["gp3"], list):
                evidence_by_gp["gp3"].extend(item["gp3"])
    
    # Process register evidence
    register_count = 0
    for item in all_evidence.get("register_evidence", []):
        if isinstance(item, dict):
            register_count += 1
            if "gp3" in item and isinstance(item["gp3"], list):
                evidence_by_gp["gp3"].extend(item["gp3"])
            if "gp6" in item and isinstance(item["gp6"], list):
                evidence_by_gp["gp6"].extend(item["gp6"])
    
    # Process external uploads (assume they can map to any GP)
    upload_count = 0
    for item in all_evidence.get("external_uploads", []):
        if isinstance(item, dict) and "gp" in item:
            upload_count += 1
            gp_num = item["gp"]
            if 1 <= gp_num <= 6:
                evidence_text = item.get("evidence", item.get("description", ""))
                if evidence_text:
                    evidence_by_gp[f"gp{gp_num}"].append(evidence_text)
    
    # Log evidence counts for debugging
    logger.info(f"Portfolio builder: Processing {lesson_count} lessons, {log_count} logs, "
                f"{assessment_count} assessments, {register_count} register entries, "
                f"{upload_count} external uploads")
    
    # Remove duplicates (simple string matching)
    for gp_key in evidence_by_gp:
        unique_evidence = []
        seen = set()
        for ev in evidence_by_gp[gp_key]:
            if isinstance(ev, str):
                ev_lower = ev.lower().strip()
                if ev_lower and ev_lower not in seen:
                    seen.add(ev_lower)
                    unique_evidence.append(ev)
        evidence_by_gp[gp_key] = unique_evidence
    
    # Build structured evidence summary for AI
    # Format as JSON string to ensure proper structure
    evidence_data = {}
    for gp_num in range(1, 7):
        gp_key = f"gp{gp_num}"
        evidence_list = evidence_by_gp[gp_key]
        if evidence_list:
            # Truncate very long evidence items for prompt efficiency
            evidence_data[gp_key] = [ev[:500] if len(ev) > 500 else ev for ev in evidence_list]
        else:
            evidence_data[gp_key] = []
    
    # Convert evidence data to JSON string for the prompt
    evidence_json_str = json.dumps(evidence_data, indent=2, ensure_ascii=False)
    
    # STRICT JSON-ONLY PROMPT - No explanations, no markdown, no natural language
    prompt = f"""You are an AI that must ONLY output strict JSON.

Never include explanations, markdown, or additional text.

Required JSON structure:
{{
  "gp1": {{ "evidence": [], "summary": "" }},
  "gp2": {{ "evidence": [], "summary": "" }},
  "gp3": {{ "evidence": [], "summary": "" }},
  "gp4": {{ "evidence": [], "summary": "" }},
  "gp5": {{ "evidence": [], "summary": "" }},
  "gp6": {{ "evidence": [], "summary": "" }},
  "overall_summary": ""
}}

Organize the following teacher evidence into the JSON structure above.

If evidence is missing for a GP, return an empty array for that GP.

Evidence data:
{evidence_json_str}

IMPORTANT: Return ONLY the JSON object. No markdown, no code blocks, no explanations."""

    # Log the prompt (truncated for security - remove sensitive data if needed)
    logger.info(f"Portfolio builder: Sending prompt to AI (length: {len(prompt)} chars)")
    logger.debug(f"Portfolio builder: Prompt preview: {prompt[:200]}...")
    
    try:
        # Call AI with lower temperature for more consistent JSON output
        response_text = send_to_ai(prompt, model="gpt-4o", max_tokens=4000, temperature=0.1)
        
        # Log raw response (truncated)
        logger.info(f"Portfolio builder: Received AI response (length: {len(response_text)} chars)")
        logger.debug(f"Portfolio builder: Raw response preview: {response_text[:300]}...")
        
        # Clean the response - remove any markdown or extra text
        cleaned_response = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        
        cleaned_response = cleaned_response.strip()
        
        # Find JSON object boundaries (first { to last })
        first_brace = cleaned_response.find('{')
        last_brace = cleaned_response.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned_response = cleaned_response[first_brace:last_brace + 1]
        
        # JSON-safe parsing with comprehensive error handling
        try:
            portfolio_data = json.loads(cleaned_response)
        except json.JSONDecodeError as json_error:
            # Log the error and raw response for debugging
            logger.error(f"Portfolio builder: JSON parse error: {str(json_error)}")
            logger.error(f"Portfolio builder: Failed to parse response: {cleaned_response[:500]}")
            
            # Return safe error structure instead of crashing
            return {
                "error": "Invalid JSON returned from AI.",
                "raw_response_preview": cleaned_response[:500],
                "exception": str(json_error),
                "gp1": {"evidence": [], "summary": ""},
                "gp2": {"evidence": [], "summary": ""},
                "gp3": {"evidence": [], "summary": ""},
                "gp4": {"evidence": [], "summary": ""},
                "gp5": {"evidence": [], "summary": ""},
                "gp6": {"evidence": [], "summary": ""},
                "overall_summary": ""
            }
        
        # Validate and normalize structure
        for gp_num in range(1, 7):
            gp_key = f"gp{gp_num}"
            if gp_key not in portfolio_data:
                portfolio_data[gp_key] = {"evidence": [], "summary": ""}
            elif not isinstance(portfolio_data[gp_key], dict):
                portfolio_data[gp_key] = {"evidence": [], "summary": ""}
            else:
                if "evidence" not in portfolio_data[gp_key]:
                    portfolio_data[gp_key]["evidence"] = []
                elif not isinstance(portfolio_data[gp_key]["evidence"], list):
                    portfolio_data[gp_key]["evidence"] = []
                if "summary" not in portfolio_data[gp_key]:
                    portfolio_data[gp_key]["summary"] = ""
                elif not isinstance(portfolio_data[gp_key]["summary"], str):
                    portfolio_data[gp_key]["summary"] = str(portfolio_data[gp_key]["summary"])
        
        if "overall_summary" not in portfolio_data:
            portfolio_data["overall_summary"] = ""
        elif not isinstance(portfolio_data["overall_summary"], str):
            portfolio_data["overall_summary"] = str(portfolio_data["overall_summary"])
        
        # Remove error key if it exists (shouldn't happen in successful parse)
        portfolio_data.pop("error", None)
        portfolio_data.pop("raw_response_preview", None)
        portfolio_data.pop("exception", None)
        
        logger.info("Portfolio builder: Successfully parsed and validated portfolio data")
        return portfolio_data
        
    except Exception as e:
        # Log the full error
        logger.error(f"Portfolio builder: Unexpected error: {str(e)}", exc_info=True)
        
        # Return safe error structure instead of raising exception
        return {
            "error": f"Error building portfolio: {str(e)}",
            "gp1": {"evidence": [], "summary": ""},
            "gp2": {"evidence": [], "summary": ""},
            "gp3": {"evidence": [], "summary": ""},
            "gp4": {"evidence": [], "summary": ""},
            "gp5": {"evidence": [], "summary": ""},
            "gp6": {"evidence": [], "summary": ""},
            "overall_summary": ""
        }

