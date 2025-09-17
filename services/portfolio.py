try:
    from resume_parser import resumeparse
    USE_RESUME_PARSER = True
except Exception as e:
    print("⚠️ resume-parser not available:", e)
    USE_RESUME_PARSER = False

from services.parser import extract_resume_data  # fallback


def resume_to_portfolio(file_path: str) -> dict:
    """
    Convert a resume file into portfolio-ready JSON.
    Uses resume-parser if available, else falls back to regex parser.
    """

    if USE_RESUME_PARSER:
        try:
            parsed = resumeparse.read_file(file_path)

            return {
                "hero": {
                    "name": parsed.get("name", "Unknown"),
                    "bio": "Auto-extracted from resume"
                },
                "about": {
                    "summary": parsed.get("total_exp", "") 
                               or "Motivated professional seeking opportunities."
                },
                "skills": parsed.get("skills", []),
                "experience": parsed.get("experience", []),
                "education": parsed.get("education", []),
                "certifications": parsed.get("certifications", []),
                "contact": {
                    "email": parsed.get("email", ""),
                    "phone": parsed.get("phone", ""),
                    "linkedin": parsed.get("linkedin", ""),
                    "github": parsed.get("github", "")
                }
            }

        except Exception as e:
            print("⚠️ resume-parser failed, falling back:", e)

    # fallback to regex parser if resume-parser is unavailable/broken
    return extract_resume_data(file_path)