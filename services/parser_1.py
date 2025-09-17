import pdfplumber
import docx
import re
from typing import List, Dict, Optional
import spacy
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Load the English language model
    nlp = spacy.load("en_core_web_sm")
except:
    logger.warning("Spacy model not found. Some features will be limited.")
    nlp = None

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from PDF file with improved error handling."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""
    return text


def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from DOCX file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def clean_lines(text: str) -> List[str]:
    """Split text into clean lines and remove extra whitespace."""
    lines = []
    for line in text.split("\n"):
        line = re.sub(r'\s+', ' ', line.strip())
        if line:
            lines.append(line)
    return lines

def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information from text."""
    contact_info = {
        'email': '',
        'phone': '',
        'linkedin': '',
        'location': ''
    }
    
    # Email pattern
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_match:
        contact_info['email'] = email_match.group()
    
    # Phone pattern (various formats)
    phone_patterns = [
        r'\+?[\d\s-]{10,}',  # Generic number pattern
        r'\(\d{3}\)\s*\d{3}[-\s]?\d{4}',  # (123) 456-7890
        r'\d{3}[-\s]?\d{3}[-\s]?\d{4}'  # 123-456-7890
    ]
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            contact_info['phone'] = phone_match.group().strip()
            break
    
    # LinkedIn URL
    linkedin_match = re.search(r'linkedin\.com/\S+', text, re.I)
    if linkedin_match:
        contact_info['linkedin'] = 'https://www.' + linkedin_match.group()
    
    # Location (if NLP is available)
    if nlp:
        doc = nlp(text[:1000])  # Process first 1000 chars for efficiency
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                contact_info['location'] = ent.text
                break
    
    return contact_info

def extract_dates(text: str) -> List[datetime]:
    """Extract dates from text using various formats."""
    date_patterns = [
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* ?\d{4}',
        r'\d{2}/\d{2}/\d{4}',
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}-\d{2}-\d{4}'
    ]
    dates = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.I)
        for match in matches:
            try:
                date_str = match.group()
                # Convert to datetime object (implement based on format)
                # dates.append(parsed_date)
                dates.append(date_str)
            except:
                continue
    return dates

def extract_resume_data(file_path: str) -> dict:
    """Extract comprehensive information from a resume file."""
    try:
        # Step 1: Load text
        if file_path.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            return {"error": "Unsupported file format. Use PDF or DOCX."}

        if not text.strip():
            return {"error": "Could not extract text from file"}

        lines = clean_lines(text)
        text_lower = text.lower()

        # Step 2: Name extraction with improved patterns
        first_line = lines[0] if lines else ""
        name = "Unknown"

        # Various name patterns
        name_patterns = [
            r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$",  # Standard name format
            r"^[A-Z]+\s+[A-Z][a-z]+$",  # ALL CAPS first name
            r"^[A-Z][a-z]+\s+[A-Z]+$",  # Last name in ALL CAPS
            r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b"  # Name anywhere in text
        ]

        # Try each pattern
        for pattern in name_patterns:
            for line in lines[:5]:  # Check first 5 lines
                if re.match(pattern, line):
                    candidate = line
                    # Avoid false positives
                    if not any(bad in candidate for bad in [
                        "Mother", "Father", "School", "College", "University",
                        "Resume", "Curriculum", "Vitae", "CV"
                    ]):
                        name = candidate
                        break
            if name != "Unknown":
                break

        # Step 3: Contact Information
        contact_info = extract_contact_info(text)

        # Step 4: About / Summary with improved pattern matching
        summary_patterns = [
            r"(?:professional\s+summary|summary|profile|objective|about\s+me)(?:\s*:?\s*)(.*?)(?:skills|education|experience|technical|competencies)",
            r"(?:career\s+objective|personal\s+statement)(?:\s*:?\s*)(.*?)(?:skills|education|experience)",
        ]
        
        summary = ""
        for pattern in summary_patterns:
            summary_match = re.search(pattern, text, re.I | re.S)
            if summary_match:
                summary = summary_match.group(1).strip()
                break
        
        if not summary and len(lines) > 5:
            summary = " ".join(lines[1:4])  # Skip name, take next few lines

        # Step 5: Skills with categorization
        SKILL_CATEGORIES = {
            'programming': ['python', 'java', 'javascript', 'c++', 'ruby', 'php', 'swift', 'kotlin'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'node', 'django', 'flask'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis'],
            'tools': ['git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'analytical']
        }

        skills_section = re.search(
            r"(?:skills|technical\s+competencies|technical\s+skills|core\s+competencies)(?:\s*:?\s*)(.*?)(?:education|experience|projects|training|achievements|certifications|languages)",
            text,
            re.S | re.I,
        )

        skills = {'uncategorized': []}
        if skills_section:
            skills_text = skills_section.group(1)
            # Split by common delimiters
            raw_skills = re.split(r'[,|•|\-|\n]', skills_text)
            
            for skill in raw_skills:
                skill = skill.strip().lower()
                if len(skill) < 2:
                    continue
                
                # Categorize skill
                categorized = False
                for category, keywords in SKILL_CATEGORIES.items():
                    if any(keyword in skill for keyword in keywords):
                        if category not in skills:
                            skills[category] = []
                        skills[category].append(skill.capitalize())
                        categorized = True
                        break
                
                if not categorized:
                    skills['uncategorized'].append(skill.capitalize())

        # Step 6: Experience with improved extraction
        experience_entries = []
        exp_section = re.search(
            r"(?:experience|employment|work\s+history)(?:\s*:?\s*)(.*?)(?:education|projects|skills|certifications|achievements)",
            text,
            re.S | re.I
        )
        
        if exp_section:
            exp_text = exp_section.group(1)
            # Split into entries
            entries = re.split(r'\n(?=[A-Z])', exp_text)
            
            for entry in entries:
                if len(entry.strip()) < 10:  # Skip very short entries
                    continue
                    
                # Extract components
                company = ""
                position = ""
                dates = ""
                description = []
                
                lines = entry.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Look for dates
                    if re.search(r'(19|20)\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', line, re.I):
                        dates = line
                    # Look for position/company
                    elif re.match(r'^[A-Z]', line):
                        if not position:
                            position = line
                        elif not company:
                            company = line
                    else:
                        description.append(line)
                
                experience_entries.append({
                    'company': company,
                    'position': position,
                    'dates': dates,
                    'description': description
                })

        # Step 7: Projects with better structure
        projects = []
        projects_section = re.search(
            r"(?:projects|personal\s+projects|academic\s+projects)(?:\s*:?\s*)(.*?)(?:achievements|certifications|education|skills|experience)",
            text,
            re.S | re.I,
        )
        
        if projects_section:
            project_text = projects_section.group(1)
            # Split into individual projects
            project_entries = re.split(r'\n(?=[A-Z])', project_text)
            
            for entry in project_entries:
                if len(entry.strip()) < 10:
                    continue
                
                lines = entry.split('\n')
                project = {
                    'name': '',
                    'technologies': [],
                    'description': [],
                    'duration': ''
                }
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if not project['name']:
                        project['name'] = line
                    elif re.search(r'(?:technology|tech stack|tools used)(?:\s*:?\s*)(.*)', line, re.I):
                        techs = re.split(r'[,|•|\-]', line)
                        project['technologies'].extend([t.strip() for t in techs if t.strip()])
                    elif re.search(r'(19|20)\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', line, re.I):
                        project['duration'] = line
                    else:
                        project['description'].append(line)
                
                if project['name']:
                    projects.append(project)

        # Step 8: Education with degree/major detection
        education = []
        EDU_KEYWORDS = {
            'degree': ['b.tech', 'b.e.', 'bachelor', 'master', 'mba', 'phd', 'm.tech', 'm.e.', 'diploma'],
            'major': ['computer science', 'information technology', 'electronics', 'mechanical', 'civil', 'electrical'],
            'institute': ['university', 'college', 'institute', 'school']
        }
        
        edu_section = re.search(
            r"(?:education|academics|qualification)(?:\s*:?\s*)(.*?)(?:projects|experience|training|achievements|certifications|skills)",
            text,
            re.S | re.I,
        )
        
        if edu_section:
            edu_text = edu_section.group(1)
            entries = re.split(r'\n(?=[A-Z])', edu_text)
            
            for entry in entries:
                if len(entry.strip()) < 10:
                    continue
                
                edu_entry = {
                    'degree': '',
                    'major': '',
                    'institute': '',
                    'duration': '',
                    'score': ''
                }
                
                # Look for degree
                for degree in EDU_KEYWORDS['degree']:
                    if re.search(degree, entry, re.I):
                        edu_entry['degree'] = re.search(f".*{degree}.*", entry, re.I).group(0)
                        break
                
                # Look for major
                for major in EDU_KEYWORDS['major']:
                    if re.search(major, entry, re.I):
                        edu_entry['major'] = major
                        break
                
                # Look for institute
                for inst_key in EDU_KEYWORDS['institute']:
                    inst_match = re.search(f".*{inst_key}.*", entry, re.I)
                    if inst_match:
                        edu_entry['institute'] = inst_match.group(0)
                        break
                
                # Look for duration/year
                year_match = re.search(r'(19|20)\d{2}(?:\s*-\s*(19|20)\d{2})?', entry)
                if year_match:
                    edu_entry['duration'] = year_match.group(0)
                
                # Look for score/percentage
                score_match = re.search(r'(?:cgpa|gpa|percentage|score)\s*:?\s*([\d.]+)', entry, re.I)
                if score_match:
                    edu_entry['score'] = score_match.group(1)
                
                if edu_entry['degree'] or edu_entry['institute']:
                    education.append(edu_entry)

        # Step 9: Certifications
        certifications = []
        cert_section = re.search(
            r"(?:certifications?|achievements)(?:\s*:?\s*)(.*?)(?:education|skills|experience|projects|languages)",
            text,
            re.S | re.I,
        )
        
        if cert_section:
            cert_text = cert_section.group(1)
            for line in cert_text.split('\n'):
                line = line.strip()
                if len(line) > 10 and not line.lower().startswith(('education', 'skills', 'experience')):
                    certifications.append(line)

        return {
            "hero": {
                "name": name,
                "contact": contact_info,
                "bio": "Auto-extracted from resume"
            },
            "about": {
                "summary": summary
            },
            "skills": skills,
            "experience": experience_entries,
            "projects": projects,
            "education": education,
            "certifications": certifications
        }

    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        return {"error": f"Failed to process resume: {str(e)}"}