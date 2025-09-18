import re
import os
import pdfplumber
import docx

# ---------------- Resume As Text Extraction ---------------- #
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=2)
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception as e:
        print(f"Error reading DOCX: {e}")
    return ""

def clean_lines(text: str):
    """Clean and return non-empty lines."""
    return [line.strip() for line in text.split("\n") if line.strip()]

# ---------------- Resume Parsing ---------------- #
def extract_resume_data(file_path: str) -> dict:
    """Extract structured resume data from PDF or DOCX."""
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    # Extract text
    if file_path.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        return {"error": "Unsupported file format"}

    if not text:
        return {"error": "Could not extract text from file"}

    lines = clean_lines(text)
    full_text = " ".join(lines)

    # --- Contact Info ---
    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text)
    phone = re.search(r"(\+\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", full_text)
    linkedin = re.search(r"linkedin\.com/in/[\w-]+", full_text)
    github = re.search(r"github\.com/[\w-]+", full_text)

    # --- Name Heuristic ---
    name = "Unknown"
    for line in lines[:5]:
        if not re.search(f"{email}|{phone}|{linkedin}|{github}", line):
            if re.match(r"^[A-Z][a-z]+(?: [A-Z][a-z]+)+$", line):
                name = line
                break

    # --- Section Headers ---
    SECTIONS = {
        "experience": r"Experience|Work\s*History|Professional\s*Experience|Career",
        "education": r"Education|Academic\s*Background",
        "skills": r"Skills|Technical\s*Skills|Core\s*Competencies",
        "projects": r"Projects|Portfolio|Key\s*Projects",
        "certifications": r"Certifications|Licenses|Training",
        "achievements": r"Awards|Honors|Achievements"
    }

    # Dynamic section extraction
    section_regex = "|".join(SECTIONS.values())
    matches = list(re.finditer(rf"({section_regex})", text, re.IGNORECASE))
    extracted_sections = {}
    for i, match in enumerate(matches):
        start_index = match.end()
        end_index = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start_index:end_index].strip()
        for section_name, pattern in SECTIONS.items():
            if re.match(pattern, match.group(0), re.IGNORECASE):
                extracted_sections[section_name] = section_text
                break

    # --- Summary / About ---
    summary = ""
    summary_match = re.search(
        r"(?:summary|profile|objective|about me|bio)\s*([\s\S]+?)(?=\n(?:{})|\Z)".format("|".join(SECTIONS.values())),
        full_text,
        re.IGNORECASE
    )
    if summary_match:
        summary = " ".join(summary_match.group(1).split()[:50]).strip()
    else:
        summary_lines = []
        for line in lines:
            if re.search(section_regex, line, re.IGNORECASE):
                break
            summary_lines.append(line)
        summary = " ".join(summary_lines[:10]).strip()
    if not summary:
        summary = "Motivated professional seeking opportunities."

    # --- Skills ---
    skills_list = []
    skills_text = extracted_sections.get("skills", "")
    if skills_text:
        skills_list = [s.strip() for s in re.split(r'[,;•\n\t]+', skills_text) if s.strip() and len(s.split()) < 5]

    # --- Projects ---
    projects_list = []
    proj_text = extracted_sections.get("projects", "")
    if proj_text:
        project_lines = re.findall(r".+?(?:\d{4}|\(.*\))?[\s\n]", proj_text, re.MULTILINE)
        projects_list = [line.strip() for line in project_lines if len(line) > 15]

    # --- Education ---
    education_list = []
    edu_text = extracted_sections.get("education", "")
    if edu_text:
        edu_patterns = re.findall(
            r".+?(?:(?:B\.S\.|B\.A\.|M\.S\.|M\.A\.|Ph\.D|Bachelor's|Master's|PhD|University|College|School|B\.Tech|M\.Tech)|(?:of\s+Science|of\s+Arts)).+?(?:\d{4})?",
            edu_text,
            re.IGNORECASE
        )
        education_list = [line.strip() for line in edu_patterns]

    # --- Experience ---
    experience_list = []
    exp_text = extracted_sections.get("experience", "")
    if exp_text:
        job_patterns = re.findall(r".+?\d{4}.+?\d{4}", exp_text, re.IGNORECASE)
        experience_list = [line.strip() for line in job_patterns]
        if not experience_list:
            job_patterns = re.findall(
                r".*?(?:Developer|Engineer|Manager|Analyst|Intern|Freelancer|Consultant|Specialist|Data Scientist|Software|Senior|Junior|Director).*",
                exp_text,
                re.IGNORECASE
            )
            experience_list = [line.strip() for line in job_patterns if len(line) > 15]

    return {
        "hero": {"name": name, "bio": generate_bio({"about": {"summary": summary}, "skills": skills_list, "experience": experience_list})},
        "about": {"summary": summary},
        "skills": skills_list,
        "experience": experience_list,
        "projects": projects_list,
        "education": education_list,
        "contact": {
            "email": email.group(0) if email else "",
            "phone": phone.group(0) if phone else "",
            "linkedin": linkedin.group(0) if linkedin else "",
            "github": github.group(0) if github else ""
        }
    }

# ---------------- Bio Generator ---------------- #
def generate_bio(parsed_data: dict) -> str:
    """
    Generate a concise bio from parsed resume data or simply a combination pf data.
    """
    summary = parsed_data.get("about", {}).get("summary", "")
    skills = parsed_data.get("skills", [])
    top_skills = ", ".join(skills[:8])
    experience = parsed_data.get("experience", [])
    exp_highlight = experience[0][:100] + ("..." if experience and len(experience[0]) > 100 else "")

    bio_parts = []
    if summary:
        bio_parts.append(summary)
    if top_skills:
        bio_parts.append(f"Skilled in {top_skills}.")
    if exp_highlight:
        bio_parts.append(f"Experience includes: {exp_highlight}")

    bio = " ".join(bio_parts).strip()
    if not bio:
        bio = "Motivated professional seeking opportunities to grow and contribute."

    return bio