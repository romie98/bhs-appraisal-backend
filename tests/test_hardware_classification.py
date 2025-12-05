"""
Test cases for hardware classification in Evidence Classification Engine.

These tests ensure that computer hardware-related evidence (ports, components, cables, etc.)
is correctly classified as GP1 or GP2, and NEVER as GP6, GP5, GP4, or GP3.

Tests cover both photo evidence and lesson plan evidence extraction.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_service import (
    analyze_photo_evidence, 
    extract_lesson_evidence,
    _detect_hardware_content
)


class TestHardwareDetection:
    """Test the hardware detection function"""
    
    def test_detect_computer_ports_gp1(self):
        """Test detection of computer ports with GP1 keywords"""
        text = "Identify the ports on this computer. USB port, HDMI, VGA ports are shown."
        result = _detect_hardware_content(text)
        
        assert result["is_hardware"] is True
        assert len(result["gp1_keywords_found"]) > 0
        assert result["suggested_gp"] == "GP1"
    
    def test_detect_hardware_components(self):
        """Test detection of hardware components"""
        text = "This diagram shows the motherboard and internal components of a computer."
        result = _detect_hardware_content(text)
        
        assert result["is_hardware"] is True
        assert "motherboard" in result["gp1_keywords_found"] or "internal components" in result["gp1_keywords_found"]
    
    def test_detect_teaching_activity_gp2(self):
        """Test detection of teaching activity with hardware"""
        text = "Students will use this image to identify computer ports in a lesson activity."
        result = _detect_hardware_content(text)
        
        assert result["is_hardware"] is True
        assert len(result["gp2_keywords_found"]) > 0
        assert result["suggested_gp"] == "GP2"
    
    def test_detect_mixed_hardware_prioritizes_gp2(self):
        """Test that mixed hardware content (technical + teaching) prioritizes GP2"""
        text = "Technical analysis of computer ports. Students will complete an assignment identifying USB and HDMI ports."
        result = _detect_hardware_content(text)
        
        assert result["is_hardware"] is True
        assert len(result["gp1_keywords_found"]) > 0
        assert len(result["gp2_keywords_found"]) > 0
        assert result["suggested_gp"] == "GP2"  # Should prioritize GP2 when both present
    
    def test_detect_non_hardware_content(self):
        """Test that non-hardware content is not flagged"""
        text = "This is a lesson plan about mathematics. Students will solve equations."
        result = _detect_hardware_content(text)
        
        assert result["is_hardware"] is False
        assert result["suggested_gp"] is None


class TestHardwareClassification:
    """Test the full classification function with hardware content"""
    
    @patch('app.services.ai_service.send_to_ai')
    def test_hardware_classified_as_gp1_not_gp6(self, mock_send_to_ai):
        """Test that hardware content is classified as GP1, not GP6"""
        # Mock AI response that incorrectly tries to classify as GP6
        mock_response = """{
            "GP1": {"subsections": [], "justifications": {}},
            "GP2": {"subsections": [], "justifications": {}},
            "GP3": {"subsections": [], "justifications": {}},
            "GP4": {"subsections": [], "justifications": {}},
            "GP5": {"subsections": [], "justifications": {}},
            "GP6": {"subsections": ["GP6.1"], "justifications": {"GP6.1": "Hardware content"}}
        }"""
        mock_send_to_ai.return_value = mock_response
        
        ocr_text = "Identify the computer ports: USB port, HDMI, VGA"
        result = analyze_photo_evidence(ocr_text)
        
        # Hardware should NOT be in GP6
        assert len(result["GP6"]["subsections"]) == 0
        assert len(result["GP6"]["justifications"]) == 0
        
        # Hardware should be in GP1 (default assignment)
        assert len(result["GP1"]["subsections"]) > 0
        assert "GP1" in result["GP1"]["subsections"][0] or len(result["GP1"]["justifications"]) > 0
    
    @patch('app.services.ai_service.send_to_ai')
    def test_hardware_classified_as_gp2_when_teaching_context(self, mock_send_to_ai):
        """Test that hardware with teaching context is classified as GP2"""
        mock_response = """{
            "GP1": {"subsections": [], "justifications": {}},
            "GP2": {"subsections": [], "justifications": {}},
            "GP3": {"subsections": [], "justifications": {}},
            "GP4": {"subsections": [], "justifications": {}},
            "GP5": {"subsections": [], "justifications": {}},
            "GP6": {"subsections": ["GP6.1"], "justifications": {"GP6.1": "Hardware"}}
        }"""
        mock_send_to_ai.return_value = mock_response
        
        ocr_text = "Students will use this image to identify computer ports in a lesson activity"
        result = analyze_photo_evidence(ocr_text)
        
        # Should NOT be in GP6
        assert len(result["GP6"]["subsections"]) == 0
        
        # Should be in GP2 (teaching context)
        assert len(result["GP2"]["subsections"]) > 0
        assert "GP2" in result["GP2"]["subsections"][0]
    
    @patch('app.services.ai_service.send_to_ai')
    def test_hardware_removed_from_gp3_gp4_gp5(self, mock_send_to_ai):
        """Test that hardware content is removed from GP3, GP4, GP5"""
        # Mock AI response that incorrectly classifies hardware in multiple GPs
        mock_response = """{
            "GP1": {"subsections": [], "justifications": {}},
            "GP2": {"subsections": [], "justifications": {}},
            "GP3": {"subsections": ["GP3.1"], "justifications": {"GP3.1": "Hardware assessment"}},
            "GP4": {"subsections": ["GP4.1"], "justifications": {"GP4.1": "Hardware reflection"}},
            "GP5": {"subsections": ["GP5.1"], "justifications": {"GP5.1": "Hardware community"}},
            "GP6": {"subsections": ["GP6.1"], "justifications": {"GP6.1": "Hardware tech"}}
        }"""
        mock_send_to_ai.return_value = mock_response
        
        ocr_text = "Computer ports diagram showing USB, HDMI, and VGA ports"
        result = analyze_photo_evidence(ocr_text)
        
        # All should be cleared for hardware content
        assert len(result["GP3"]["subsections"]) == 0
        assert len(result["GP3"]["justifications"]) == 0
        assert len(result["GP4"]["subsections"]) == 0
        assert len(result["GP4"]["justifications"]) == 0
        assert len(result["GP5"]["subsections"]) == 0
        assert len(result["GP5"]["justifications"]) == 0
        assert len(result["GP6"]["subsections"]) == 0
        assert len(result["GP6"]["justifications"]) == 0
        
        # Should be assigned to GP1 or GP2
        has_gp1 = len(result["GP1"]["subsections"]) > 0 or len(result["GP1"]["justifications"]) > 0
        has_gp2 = len(result["GP2"]["subsections"]) > 0 or len(result["GP2"]["justifications"]) > 0
        assert has_gp1 or has_gp2, "Hardware must be classified in GP1 or GP2"
    
    @patch('app.services.ai_service.send_to_ai')
    def test_hardware_already_in_gp1_preserved(self, mock_send_to_ai):
        """Test that hardware correctly classified as GP1 is preserved"""
        mock_response = """{
            "GP1": {"subsections": ["GP1.3"], "justifications": {"GP1.3": "Technical hardware knowledge"}},
            "GP2": {"subsections": [], "justifications": {}},
            "GP3": {"subsections": [], "justifications": {}},
            "GP4": {"subsections": [], "justifications": {}},
            "GP5": {"subsections": [], "justifications": {}},
            "GP6": {"subsections": [], "justifications": {}}
        }"""
        mock_send_to_ai.return_value = mock_response
        
        ocr_text = "Identify the ports: USB port, HDMI, VGA. Technical analysis of components."
        result = analyze_photo_evidence(ocr_text)
        
        # GP1 should be preserved
        assert len(result["GP1"]["subsections"]) > 0
        assert "GP1.3" in result["GP1"]["subsections"]
        
        # GP6 should remain empty
        assert len(result["GP6"]["subsections"]) == 0
    
    @patch('app.services.ai_service.send_to_ai')
    def test_hardware_already_in_gp2_preserved(self, mock_send_to_ai):
        """Test that hardware correctly classified as GP2 is preserved"""
        mock_response = """{
            "GP1": {"subsections": [], "justifications": {}},
            "GP2": {"subsections": ["GP2.2"], "justifications": {"GP2.2": "Teaching with hardware images"}},
            "GP3": {"subsections": [], "justifications": {}},
            "GP4": {"subsections": [], "justifications": {}},
            "GP5": {"subsections": [], "justifications": {}},
            "GP6": {"subsections": [], "justifications": {}}
        }"""
        mock_send_to_ai.return_value = mock_response
        
        ocr_text = "Lesson activity: Students will identify computer ports in this image"
        result = analyze_photo_evidence(ocr_text)
        
        # GP2 should be preserved
        assert len(result["GP2"]["subsections"]) > 0
        assert "GP2.2" in result["GP2"]["subsections"]
        
        # GP6 should remain empty
        assert len(result["GP6"]["subsections"]) == 0
    
    @patch('app.services.ai_service.send_to_ai')
    def test_non_hardware_content_unaffected(self, mock_send_to_ai):
        """Test that non-hardware content classification is not affected"""
        mock_response = """{
            "GP1": {"subsections": [], "justifications": {}},
            "GP2": {"subsections": [], "justifications": {}},
            "GP3": {"subsections": ["GP3.1"], "justifications": {"GP3.1": "Assessment evidence"}},
            "GP4": {"subsections": [], "justifications": {}},
            "GP5": {"subsections": [], "justifications": {}},
            "GP6": {"subsections": ["GP6.1"], "justifications": {"GP6.1": "ICT use"}}
        }"""
        mock_send_to_ai.return_value = mock_response
        
        ocr_text = "This is a mathematics lesson plan with assessment activities"
        result = analyze_photo_evidence(ocr_text)
        
        # Non-hardware content should be preserved as-is
        assert len(result["GP3"]["subsections"]) > 0
        assert len(result["GP6"]["subsections"]) > 0  # GP6 is allowed for non-hardware


class TestHardwareKeywordDetection:
    """Test specific keyword detection scenarios"""
    
    def test_usb_port_keyword(self):
        """Test USB port keyword detection"""
        text = "USB port identification exercise"
        result = _detect_hardware_content(text)
        assert result["is_hardware"] is True
    
    def test_hdmi_keyword(self):
        """Test HDMI keyword detection"""
        text = "HDMI connector diagram"
        result = _detect_hardware_content(text)
        assert result["is_hardware"] is True
    
    def test_vga_keyword(self):
        """Test VGA keyword detection"""
        text = "VGA port shown in the image"
        result = _detect_hardware_content(text)
        assert result["is_hardware"] is True
    
    def test_motherboard_keyword(self):
        """Test motherboard keyword detection"""
        text = "Motherboard components diagram"
        result = _detect_hardware_content(text)
        assert result["is_hardware"] is True
        assert "motherboard" in result["gp1_keywords_found"]
    
    def test_lesson_activity_keyword(self):
        """Test lesson activity keyword detection"""
        text = "Lesson activity using computer hardware images"
        result = _detect_hardware_content(text)
        assert result["is_hardware"] is True
        assert len(result["gp2_keywords_found"]) > 0
        assert result["suggested_gp"] == "GP2"
    
    def test_student_task_keyword(self):
        """Test student task keyword detection"""
        text = "Student task: analyze the hardware components"
        result = _detect_hardware_content(text)
        assert result["is_hardware"] is True
        assert result["suggested_gp"] == "GP2"


class TestLessonPlanHardwareClassification:
    """Test hardware classification in lesson plan evidence extraction"""
    
    @patch('app.services.ai_service.send_to_ai')
    def test_lesson_plan_hardware_classified_as_gp1_not_gp6(self, mock_send_to_ai):
        """Test that hardware in lesson plans is classified as GP1, not GP6"""
        # Mock AI response that incorrectly tries to classify as GP6
        mock_response = """{
            "gp1": [],
            "gp2": [],
            "gp3": [],
            "gp4": [],
            "gp5": [],
            "gp6": ["Lesson uses computer ports and hardware components"],
            "strengths": [],
            "weaknesses": []
        }"""
        mock_send_to_ai.return_value = mock_response
        
        lesson_text = "Lesson Plan: Identify the computer ports - USB port, HDMI, VGA. Technical analysis of components."
        result = extract_lesson_evidence(lesson_text)
        
        # Hardware should NOT be in GP6
        assert len(result["gp6"]) == 0
        
        # Hardware should be in GP1 (default assignment)
        assert len(result["gp1"]) > 0
    
    @patch('app.services.ai_service.send_to_ai')
    def test_lesson_plan_hardware_classified_as_gp2_when_teaching_context(self, mock_send_to_ai):
        """Test that hardware with teaching context in lesson plans is classified as GP2"""
        mock_response = """{
            "gp1": [],
            "gp2": [],
            "gp3": [],
            "gp4": [],
            "gp5": [],
            "gp6": ["Students use hardware images"],
            "strengths": [],
            "weaknesses": []
        }"""
        mock_send_to_ai.return_value = mock_response
        
        lesson_text = "Students will use this image to identify computer ports in a lesson activity. Assignment on hardware components."
        result = extract_lesson_evidence(lesson_text)
        
        # Should NOT be in GP6
        assert len(result["gp6"]) == 0
        
        # Should be in GP2 (teaching context)
        assert len(result["gp2"]) > 0
    
    @patch('app.services.ai_service.send_to_ai')
    def test_lesson_plan_hardware_removed_from_gp3_gp4_gp5(self, mock_send_to_ai):
        """Test that hardware content is removed from GP3, GP4, GP5 in lesson plans"""
        # Mock AI response that incorrectly classifies hardware in multiple GPs
        mock_response = """{
            "gp1": [],
            "gp2": [],
            "gp3": ["Assessment of computer ports identification"],
            "gp4": ["Reflection on hardware teaching"],
            "gp5": ["Community engagement with hardware"],
            "gp6": ["Technology integration using hardware"],
            "strengths": [],
            "weaknesses": []
        }"""
        mock_send_to_ai.return_value = mock_response
        
        lesson_text = "Computer ports diagram showing USB, HDMI, and VGA ports. Students identify components."
        result = extract_lesson_evidence(lesson_text)
        
        # Hardware-related evidence should be filtered out from GP3, GP4, GP5, GP6
        # Check that hardware keywords are not in the evidence
        hardware_keywords = ["port", "ports", "usb", "hdmi", "vga", "hardware", "component"]
        
        for gp_key in ["gp3", "gp4", "gp5", "gp6"]:
            for evidence_item in result.get(gp_key, []):
                evidence_lower = evidence_item.lower()
                # Evidence should not contain hardware keywords (or should have been filtered)
                # Note: The filtering happens in post-processing, so we check the result
                assert not any(keyword in evidence_lower for keyword in hardware_keywords), \
                    f"Hardware keyword found in {gp_key}: {evidence_item}"
        
        # Should be assigned to GP1 or GP2
        has_gp1 = len(result.get("gp1", [])) > 0
        has_gp2 = len(result.get("gp2", [])) > 0
        assert has_gp1 or has_gp2, "Hardware must be classified in GP1 or GP2"
    
    @patch('app.services.ai_service.send_to_ai')
    def test_lesson_plan_hardware_already_in_gp1_preserved(self, mock_send_to_ai):
        """Test that hardware correctly classified as GP1 in lesson plans is preserved"""
        mock_response = """{
            "gp1": ["Technical knowledge of computer hardware components demonstrated"],
            "gp2": [],
            "gp3": [],
            "gp4": [],
            "gp5": [],
            "gp6": [],
            "strengths": [],
            "weaknesses": []
        }"""
        mock_send_to_ai.return_value = mock_response
        
        lesson_text = "Identify the ports: USB port, HDMI, VGA. Technical analysis of components."
        result = extract_lesson_evidence(lesson_text)
        
        # GP1 should be preserved
        assert len(result["gp1"]) > 0
        
        # GP6 should remain empty
        assert len(result["gp6"]) == 0
    
    @patch('app.services.ai_service.send_to_ai')
    def test_lesson_plan_hardware_already_in_gp2_preserved(self, mock_send_to_ai):
        """Test that hardware correctly classified as GP2 in lesson plans is preserved"""
        mock_response = """{
            "gp1": [],
            "gp2": ["Teaching strategy using hardware images in lesson activities"],
            "gp3": [],
            "gp4": [],
            "gp5": [],
            "gp6": [],
            "strengths": [],
            "weaknesses": []
        }"""
        mock_send_to_ai.return_value = mock_response
        
        lesson_text = "Lesson activity: Students will identify computer ports in this image"
        result = extract_lesson_evidence(lesson_text)
        
        # GP2 should be preserved
        assert len(result["gp2"]) > 0
        
        # GP6 should remain empty
        assert len(result["gp6"]) == 0
    
    @patch('app.services.ai_service.send_to_ai')
    def test_lesson_plan_non_hardware_content_unaffected(self, mock_send_to_ai):
        """Test that non-hardware content in lesson plans is not affected"""
        mock_response = """{
            "gp1": [],
            "gp2": [],
            "gp3": ["Assessment evidence"],
            "gp4": [],
            "gp5": [],
            "gp6": ["ICT use in mathematics lesson"],
            "strengths": [],
            "weaknesses": []
        }"""
        mock_send_to_ai.return_value = mock_response
        
        lesson_text = "This is a mathematics lesson plan with assessment activities and ICT tools"
        result = extract_lesson_evidence(lesson_text)
        
        # Non-hardware content should be preserved as-is
        assert len(result["gp3"]) > 0
        assert len(result["gp6"]) > 0  # GP6 is allowed for non-hardware


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

