import streamlit as st
import PyPDF2
import docx
import os
import io
import json
import plotly.express as px
from openai import OpenAI
import re

# Function to extract text from various file formats
def extract_text_from_file(file):
    text = ""
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension == '.pdf':
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page_num in range(len(pdf_reader.pages)):
                # Extract text with layout preservation
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                # Clean up common PDF extraction artifacts while preserving structure
                # Fix hyphenation issues while preserving original text
                page_text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', page_text)
                # Fix line breaks within dates and company names
                page_text = re.sub(r'(\d{4})\s*\n\s*(\d{4})', r'\1-\2', page_text)
                page_text = re.sub(r'([A-Z][a-z]+)\s*\n\s*([A-Z][a-z]+)', r'\1 \2', page_text)
                # Preserve section headers
                page_text = re.sub(r'\n([A-Z][A-Z\s]+)\n', r'\n\n\1\n', page_text)
                # Fix bullet points and lists
                page_text = re.sub(r'\n\s*•\s*', '\n• ', page_text)
                # Preserve proper spacing between sections
                page_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', page_text)
                # Fix spacing around dates and periods
                page_text = re.sub(r'(\d{4})\s*-\s*(\d{4})', r'\1 - \2', page_text)
                page_text = re.sub(r'(\d{4})\s*–\s*(\d{4})', r'\1 – \2', page_text)
                
                text += page_text + "\n\n"
        except Exception as e:
            st.error(f"Error extracting text from PDF: {e}")
    elif file_extension in ['.docx', '.doc']:
        try:
            doc = docx.Document(io.BytesIO(file.read()))
            for para in doc.paragraphs:
                # Preserve paragraph breaks and formatting
                text += para.text.strip() + "\n\n"
        except Exception as e:
            st.error(f"Error extracting text from Word document: {e}")
    elif file_extension == '.txt':
        try:
            text = file.read().decode('utf-8')
            # Clean up text file formatting while preserving structure
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            text = re.sub(r'(\d{4})\s*-\s*(\d{4})', r'\1 - \2', text)
            text = re.sub(r'(\d{4})\s*–\s*(\d{4})', r'\1 – \2', text)
        except Exception as e:
            st.error(f"Error reading text file: {e}")
    else:
        st.error("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
    
    # Final cleanup while preserving structure
    text = text.strip()
    # Ensure consistent spacing around dates and periods
    text = re.sub(r'(\d{4})\s*-\s*(\d{4})', r'\1 - \2', text)
    text = re.sub(r'(\d{4})\s*–\s*(\d{4})', r'\1 – \2', text)
    # Ensure proper spacing around bullet points
    text = re.sub(r'\n\s*•\s*', '\n• ', text)
    # Ensure proper spacing between sections
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text

# Function to analyze resume using OpenAI
def analyze_resume_with_openai(resume_text, job_description, company, api_key):
    client = OpenAI(api_key=api_key)

    company_response = ""  # Initialize with empty string
    if company != "":
        company_prompt = f"""
        Search up information about the company {company}. 
        Given the context that the user is applying for a job at this company, give a summary about it."""

        company_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", 
                       "content": company_prompt}],
            temperature=0.2
        )
    
    prompt = f"""
    You are acting as both an experienced technical recruiter and hiring manager for {company}. 
    Analyze the following resume against the job description to provide detailed, strategic feedback.
    Focus on providing actionable insights that will help the candidate stand out.
    
    RESUME (note that the resume is extracted from a PDF file, so the formatting might be off):
    {resume_text}
    
    JOB DESCRIPTION:
    {job_description + " in " + company}

    Company Details:
    {company_response}
    
    Provide a comprehensive analysis in JSON format with the following structure:
    {{
        "match_percentage": 0-100,
        "skill_match": {{
            "matched_skills": ["list of matched skills"],
            "missing_skills": ["list of missing skills"],
            "recommended_skills": [
                {{
                    "skill": "skill name",
                    "category": "technical/soft/domain-specific",
                    "priority": "high/medium/low",
                    "prerequisites": ["list of prerequisite skills if any"],
                    "estimated_time": "estimated time to learn (weeks/months)",
                    "resources": ["list of specific learning resources"]
                }}
            ]
        }},
        "content_improvements": {{
            "sections_to_improve": ["list of sections that need improvement"],
            "wording_suggestions": ["list of wording improvements, be specific about this and give examples"],
            "format_suggestions": ["list of formatting improvements, be specific about this and give examples. But don't need to mention the formatting errors that could be due to the PDF extraction."]
        }},
        "company_specific_insights": {{
            "company_specific_skills": ["skills particularly valued by this company"],
            "company_projects": ["suggestions for projects or experiences that would impress this company"],
            "networking_opportunities": ["specific networking opportunities or events related to this company"],
            "company_resources": ["company-specific resources or programs the candidate could leverage"]
        }},
        "summary": "brief summary of the overall analysis"
    }}
    
    For the recommended_skills, organize them in a logical learning path with clear prerequisites and priorities.
    High priority skills should be those that are most critical for the role and can be learned relatively quickly.
    Medium priority skills are important but can be developed over time.
    Low priority skills are nice-to-have or more advanced skills.
    
    Be specific, actionable, and detailed in your analysis. Focus on providing genuine value to the job seeker.
    If a company is provided, emphasize company-specific insights and how the candidate can better position themselves for this particular role.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", 
                       "content": prompt}],
            temperature=0.2,
        )
        result = response.choices[0].message.content
        
        # Extract the JSON part from the response
        json_pattern = r'({[\s\S]*})'
        json_match = re.search(json_pattern, result)
        
        if json_match:
            json_data = json.loads(json_match.group(0))
            return json_data
        else:
            st.error("Failed to parse the API response.")
            return None
            
    except Exception as e:
        st.error(f"Error communicating with OpenAI API: {e}")
        return None
    
# Function to analyze LinkedIn profile
def analyze_linkedin_profile(linkedin_url, career_path, country, industry, api_key):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    You are an expert career coach tasked to help the user with his budding career development and linkedin optimization. Your thinking should be thorough. You can think step by step before and after each action you decide to take.
    The user, who is likely just starting out or is still studying right now, wants to find out how to develop their career. Analyze the following LinkedIn profile URL (carefully) and desired career path to provide career development advice. 
    
    LINKEDIN PROFILE URL:
    {linkedin_url}
    
    DESIRED CAREER PATH/SPECIALIZATION:
    {career_path + " in " + industry + " in " + country}

    You mus have a comprehensive understanding about the career path and the industry.
    Think carefully about what kind of skills expertise the industry today actually need according to the desired career pathway.
    Also think about whether the industry will play a big role/impact on the career type.
    
    Provide a comprehensive analysis in JSON format with the following structure based on the profile, desired career path and the stage of career the user is at:
    1. Career Alignment: Evaluate how well the current profile aligns with the desired career path.
    2. Development Plan: Suggest a detailed plan for skill development and career progression. Do not repeat the same skills that are already in the profile if they are sufficiently developed.
    3. Networking Strategy: Recommend networking strategies and key connections to make.
    4. Skill Development: Identify key technical and soft skills to focus on.
    5. Profile Optimization: Provide concrete tips for optimizing the LinkedIn profile.
    6. Industry Insights: Share deep insights about the industry, including trends and certifications.
    {{
        "career_alignment": {{
            "alignment_score": 0-100,
            "strengths": ["list of strengths that align with the desired path"],
            "gaps": ["list of immediate gaps or weaknesses for the desired path"]
        }},
        "development_plan": {{
            "short_term_actions": ["list of immediate actions to take (0-6 months)"],
            "medium_term_goals": ["list of medium-term goals (6-18 months)"],
            "long_term_milestones": ["list of long-term career milestones (18+ months)"]
        }},
        "networking_strategy": {{
            "key_connections": ["types of professionals to connect with"],
            "communities": ["relevant professional communities to join"],
            "engagement_tactics": ["strategies for meaningful networking"]
        }},
        "skill_development": {{
            "technical_skills": [
                {{
                    "skill": "skill name",
                    "priority": "high/medium/low",
                    "resources": ["list of specific learning resources"]
                }}
            ],
            "soft_skills": [
                {{
                    "skill": "skill name",
                    "priority": "high/medium/low",
                    "development_approaches": ["list of ways to develop this soft skill"]
                }}
            ]
        }},
        "profile_optimization": {{
            "headline_suggestions": ["suggestions for LinkedIn headline based on the profile"],
            "about_section_tips": ["improvements for About section"],
            "experience_highlighting": ["tips on highlighting relevant experience"],
            "skill_endorsements": ["skills to seek endorsements for"]
        }},
        "industry_insights": {{
            "trends": ["relevant and up-to-date industry trends"],
            "certifications": ["valuable certifications"],
            "thought_leaders": ["people to follow"]
        }},
        "summary": "brief summary of the overall career development advice based on the profile, desired career path and the stage of career the user is at"
    }}
    
    Note: Focus on providing genuine value to the career seeker.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        result = response.choices[0].message.content
        
        # Extract the JSON part from the response
        json_pattern = r'({[\s\S]*})'
        json_match = re.search(json_pattern, result)
        
        if json_match:
            json_data = json.loads(json_match.group(0))
            return json_data
        else:
            st.error("Failed to parse the API response.")
            return None
            
    except Exception as e:
        st.error(f"Error communicating with OpenAI API: {e}")
        return None