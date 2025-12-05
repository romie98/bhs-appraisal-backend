"""PDF Export Service using ReportLab"""
from io import BytesIO
from datetime import datetime, timedelta
from collections import defaultdict
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.modules.students.models import Student
from app.modules.assessments.models import Assessment, AssessmentScore
from app.modules.register.models import RegisterRecord, RegisterStatus


class PDFExportService:
    """Service for generating PDF reports"""
    
    # School information
    SCHOOL_NAME = "Belair High School"
    TEACHER_NAME = "Romario Cohen"
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Normal text style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica-Bold', 12)
        canvas_obj.setFillColor(colors.HexColor('#1e40af'))
        canvas_obj.drawString(inch, letter[1] - 0.5 * inch, self.SCHOOL_NAME)
        
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.setFillColor(colors.HexColor('#6b7280'))
        canvas_obj.drawString(inch, letter[1] - 0.7 * inch, f"Teacher: {self.TEACHER_NAME}")
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#9ca3af'))
        canvas_obj.drawCentredString(letter[0] / 2, 0.5 * inch, 
                                    f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        canvas_obj.drawCentredString(letter[0] / 2, 0.3 * inch, 
                                    f"Page {canvas_obj.getPageNumber()}")
        
        canvas_obj.restoreState()
    
    def generate_markbook_summary(self, db: Session, grade: str) -> BytesIO:
        """Generate Mark Book Summary PDF for a grade"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        # Title
        story.append(Paragraph("Mark Book Summary", self.styles['CustomTitle']))
        story.append(Paragraph(f"Grade {grade}", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Get students
        students = db.query(Student).filter(Student.grade == grade).all()
        
        # Get assessments
        assessments = db.query(Assessment).filter(Assessment.grade == grade).order_by(Assessment.date_assigned).all()
        
        if not students:
            story.append(Paragraph("No students found for this grade.", self.styles['CustomNormal']))
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            buffer.seek(0)
            return buffer
        
        # Summary statistics
        story.append(Paragraph("Summary Statistics", self.styles['CustomHeader']))
        
        summary_data = [
            ['Total Students', str(len(students))],
            ['Total Assessments', str(len(assessments))],
            ['Report Date', datetime.now().strftime('%B %d, %Y')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Student scores table
        if assessments:
            story.append(Paragraph("Student Assessment Scores", self.styles['CustomHeader']))
            
            # Table headers
            table_data = [['Student'] + [a.title[:20] for a in assessments] + ['Average']]
            
            # Get all scores
            all_scores = {}
            for assessment in assessments:
                scores = db.query(AssessmentScore).filter(AssessmentScore.assessment_id == assessment.id).all()
                for score in scores:
                    key = (score.student_id, assessment.id)
                    all_scores[key] = score
            
            # Add student rows
            for student in students:
                row = [f"{student.first_name} {student.last_name}"]
                total_percentage = 0
                valid_count = 0
                
                for assessment in assessments:
                    score = all_scores.get((student.id, assessment.id))
                    if score:
                        percentage = (score.score / assessment.total_marks) * 100
                        row.append(f"{score.score}/{assessment.total_marks}\n({percentage:.1f}%)")
                        total_percentage += percentage
                        valid_count += 1
                    else:
                        row.append("-")
                
                # Calculate average
                avg = (total_percentage / valid_count) if valid_count > 0 else 0
                row.append(f"{avg:.1f}%")
                table_data.append(row)
            
            # Create table
            col_widths = [2*inch] + [1.2*inch] * len(assessments) + [1*inch]
            student_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(student_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Assessment details
        if assessments:
            story.append(Paragraph("Assessment Details", self.styles['CustomHeader']))
            for assessment in assessments:
                story.append(Paragraph(f"<b>{assessment.title}</b> ({assessment.type})", self.styles['CustomNormal']))
                story.append(Paragraph(f"Total Marks: {assessment.total_marks} | Assigned: {assessment.date_assigned.strftime('%B %d, %Y')}", 
                                     self.styles['CustomNormal']))
                if assessment.date_due:
                    story.append(Paragraph(f"Due Date: {assessment.date_due.strftime('%B %d, %Y')}", 
                                         self.styles['CustomNormal']))
                story.append(Spacer(1, 0.1*inch))
        
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        buffer.seek(0)
        return buffer
    
    def generate_attendance_summary(self, db: Session, grade: str) -> BytesIO:
        """Generate Attendance Summary PDF for a grade"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        # Title
        story.append(Paragraph("Attendance Summary", self.styles['CustomTitle']))
        story.append(Paragraph(f"Grade {grade}", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Get students
        students = db.query(Student).filter(Student.grade == grade).all()
        
        if not students:
            story.append(Paragraph("No students found for this grade.", self.styles['CustomNormal']))
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            buffer.seek(0)
            return buffer
        
        # Get register records
        records = db.query(RegisterRecord).join(Student).filter(Student.grade == grade).order_by(RegisterRecord.date.desc()).all()
        
        # Weekly summary
        story.append(Paragraph("Weekly Attendance Summary", self.styles['CustomHeader']))
        
        # Group by week
        weekly_data = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})
        
        for record in records:
            week_start = record.date - timedelta(days=record.date.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            
            if record.status == RegisterStatus.PRESENT:
                weekly_data[week_key]['present'] += 1
            elif record.status == RegisterStatus.ABSENT:
                weekly_data[week_key]['absent'] += 1
            elif record.status == RegisterStatus.LATE:
                weekly_data[week_key]['late'] += 1
            elif record.status == RegisterStatus.EXCUSED:
                weekly_data[week_key]['excused'] += 1
        
        # Weekly table
        weekly_table_data = [['Week Starting', 'Present', 'Absent', 'Late', 'Excused', 'Rate']]
        for week_key in sorted(weekly_data.keys(), reverse=True)[:8]:  # Last 8 weeks
            week_data = weekly_data[week_key]
            total = week_data['present'] + week_data['absent'] + week_data['late'] + week_data['excused']
            rate = ((week_data['present'] + week_data['late'] + week_data['excused']) / total * 100) if total > 0 else 0
            
            weekly_table_data.append([
                datetime.strptime(week_key, '%Y-%m-%d').strftime('%b %d, %Y'),
                str(week_data['present']),
                str(week_data['absent']),
                str(week_data['late']),
                str(week_data['excused']),
                f"{rate:.1f}%"
            ])
        
        weekly_table = Table(weekly_table_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch], repeatRows=1)
        weekly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(weekly_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Monthly summary
        story.append(Paragraph("Monthly Attendance Summary", self.styles['CustomHeader']))
        
        monthly_data = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0, 'excused': 0})
        
        for record in records:
            month_key = record.date.strftime('%Y-%m')
            
            if record.status == RegisterStatus.PRESENT:
                monthly_data[month_key]['present'] += 1
            elif record.status == RegisterStatus.ABSENT:
                monthly_data[month_key]['absent'] += 1
            elif record.status == RegisterStatus.LATE:
                monthly_data[month_key]['late'] += 1
            elif record.status == RegisterStatus.EXCUSED:
                monthly_data[month_key]['excused'] += 1
        
        monthly_table_data = [['Month', 'Present', 'Absent', 'Late', 'Excused', 'Rate']]
        for month_key in sorted(monthly_data.keys(), reverse=True)[:6]:  # Last 6 months
            month_data = monthly_data[month_key]
            total = month_data['present'] + month_data['absent'] + month_data['late'] + month_data['excused']
            rate = ((month_data['present'] + month_data['late'] + month_data['excused']) / total * 100) if total > 0 else 0
            
            month_name = datetime.strptime(month_key + '-01', '%Y-%m-%d').strftime('%B %Y')
            monthly_table_data.append([
                month_name,
                str(month_data['present']),
                str(month_data['absent']),
                str(month_data['late']),
                str(month_data['excused']),
                f"{rate:.1f}%"
            ])
        
        monthly_table = Table(monthly_table_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch], repeatRows=1)
        monthly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(monthly_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Student attendance summary
        story.append(Paragraph("Individual Student Attendance", self.styles['CustomHeader']))
        
        student_attendance_data = [['Student', 'Present', 'Absent', 'Late', 'Excused', 'Rate']]
        
        for student in students:
            student_records = [r for r in records if r.student_id == student.id]
            counts = {'present': 0, 'absent': 0, 'late': 0, 'excused': 0}
            
            for record in student_records:
                if record.status == RegisterStatus.PRESENT:
                    counts['present'] += 1
                elif record.status == RegisterStatus.ABSENT:
                    counts['absent'] += 1
                elif record.status == RegisterStatus.LATE:
                    counts['late'] += 1
                elif record.status == RegisterStatus.EXCUSED:
                    counts['excused'] += 1
            
            total = sum(counts.values())
            rate = ((counts['present'] + counts['late'] + counts['excused']) / total * 100) if total > 0 else 0
            
            student_attendance_data.append([
                f"{student.first_name} {student.last_name}",
                str(counts['present']),
                str(counts['absent']),
                str(counts['late']),
                str(counts['excused']),
                f"{rate:.1f}%"
            ])
        
        student_table = Table(student_attendance_data, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch], repeatRows=1)
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(student_table)
        
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        buffer.seek(0)
        return buffer
    
    def generate_student_progress_report(self, db: Session, student_id: str) -> BytesIO:
        """Generate Student Progress Report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        # Get student
        student = db.query(Student).filter(Student.id == student_id).first()
        
        if not student:
            story.append(Paragraph("Student not found.", self.styles['CustomNormal']))
            doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
            buffer.seek(0)
            return buffer
        
        # Title
        story.append(Paragraph("Student Progress Report", self.styles['CustomTitle']))
        story.append(Paragraph(f"{student.first_name} {student.last_name}", self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Student information
        story.append(Paragraph("Student Information", self.styles['CustomHeader']))
        info_data = [
            ['Name', f"{student.first_name} {student.last_name}"],
            ['Grade', student.grade],
            ['Gender', student.gender or 'Not specified'],
            ['Parent Contact', student.parent_contact or 'Not provided'],
            ['Report Date', datetime.now().strftime('%B %d, %Y')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Assessment scores
        story.append(Paragraph("Assessment Performance", self.styles['CustomHeader']))
        
        # Get assessments for student's grade
        assessments = db.query(Assessment).filter(Assessment.grade == student.grade).order_by(Assessment.date_assigned).all()
        
        # Get scores
        scores = db.query(AssessmentScore).filter(AssessmentScore.student_id == student_id).all()
        score_map = {score.assessment_id: score for score in scores}
        
        if assessments:
            score_data = [['Assessment', 'Type', 'Score', 'Total', 'Percentage', 'Date']]
            
            total_percentage = 0
            valid_count = 0
            
            for assessment in assessments:
                score = score_map.get(assessment.id)
                if score:
                    percentage = (score.score / assessment.total_marks) * 100
                    score_data.append([
                        assessment.title,
                        assessment.type,
                        f"{score.score:.1f}",
                        str(assessment.total_marks),
                        f"{percentage:.1f}%",
                        assessment.date_assigned.strftime('%b %d, %Y')
                    ])
                    total_percentage += percentage
                    valid_count += 1
                else:
                    score_data.append([
                        assessment.title,
                        assessment.type,
                        "-",
                        str(assessment.total_marks),
                        "-",
                        assessment.date_assigned.strftime('%b %d, %Y')
                    ])
            
            score_table = Table(score_data, colWidths=[2*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch], repeatRows=1)
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Overall average
            if valid_count > 0:
                overall_avg = total_percentage / valid_count
                story.append(Paragraph(f"<b>Overall Average: {overall_avg:.1f}%</b>", self.styles['CustomNormal']))
                story.append(Spacer(1, 0.3*inch))
        
        # Attendance summary
        story.append(Paragraph("Attendance Summary", self.styles['CustomHeader']))
        
        attendance_records = db.query(RegisterRecord).filter(RegisterRecord.student_id == student_id).all()
        
        counts = {'present': 0, 'absent': 0, 'late': 0, 'excused': 0}
        for record in attendance_records:
            if record.status == RegisterStatus.PRESENT:
                counts['present'] += 1
            elif record.status == RegisterStatus.ABSENT:
                counts['absent'] += 1
            elif record.status == RegisterStatus.LATE:
                counts['late'] += 1
            elif record.status == RegisterStatus.EXCUSED:
                counts['excused'] += 1
        
        total_attendance = sum(counts.values())
        attendance_rate = ((counts['present'] + counts['late'] + counts['excused']) / total_attendance * 100) if total_attendance > 0 else 0
        
        attendance_data = [
            ['Status', 'Count'],
            ['Present', str(counts['present'])],
            ['Absent', str(counts['absent'])],
            ['Late', str(counts['late'])],
            ['Excused', str(counts['excused'])],
            ['Total Days', str(total_attendance)],
            ['Attendance Rate', f"{attendance_rate:.1f}%"]
        ]
        
        attendance_table = Table(attendance_data, colWidths=[2*inch, 2*inch])
        attendance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(attendance_table)
        
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        buffer.seek(0)
        return buffer

