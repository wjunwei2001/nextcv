import streamlit as st
from openai import OpenAI
import re
import json

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
        "summary": "brief summary of the overall analysis and actionable insights for the candidate to get an edge in the application."
    }}
    
    For the recommended_skills, organize them in a logical learning path with clear prerequisites and priorities.
    Also for the recommended skills, the resume might not mention all the skills, but judge based on the resume to see if the candidate has the skills. 
    Do not mention skills in the recommended skills if you think that the candidate has the skills.

    eg. If the user has built a machine learning model, he/she most likely knows numpy, pandas, scikit-learn, etc.
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
def analyze_linkedin_profile(linkedin_url, career_path, country, industry, resume_text, api_key):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    You are an expert career coach tasked to help the user with their career development and LinkedIn optimization. Your thinking should be thorough. You can think step by step before and after each action you decide to take.
    The user wants to find out how to develop their career. Analyze the following LinkedIn profile URL and resume to provide comprehensive career development advice.

    LINKEDIN PROFILE URL:
    {linkedin_url}

    RESUME:
    {resume_text}
    
    DESIRED CAREER PATH/SPECIALIZATION:
    {career_path + " in " + industry + " in " + country}

    You must have a comprehensive understanding about the career path and the industry.
    Think carefully about what kind of skills expertise the industry today actually need according to the desired career pathway.
    Also think about whether the industry will play a big role/impact on the career type.
    
    Provide a comprehensive analysis in JSON format with the following structure based on the profile, resume, desired career path and the stage of career the user is at:
    1. Career Alignment: Evaluate how well the current profile and resume align with the desired career path.
    3. Networking Strategy: Recommend networking strategies and key connections to make.
    4. Skill Development: Identify key technical and soft skills to focus on.
    5. Profile Optimization: Provide concrete tips for optimizing the LinkedIn profile and resume.
    6. Industry Insights: Share deep insights about the industry, including trends and certifications.
    {{
        "career_alignment": {{
            "alignment_score": 0-100,
            "strengths": ["list of strengths that align with the desired path"],
            "gaps": ["list of immediate gaps or weaknesses for the desired path"]
        }},
        "networking_strategy": {{
            "key_connections": ["types of professionals to connect with"],
            "communities": ["relevant professional communities to join (be specific)"],
            "engagement_tactics": ["strategies for meaningful networking (give specific examples.)"]
        }},
        "skill_development": {{
            "technical_skills": [
                {{
                    "skill": "skill name",
                    "priority": "high/medium/low",
                    "resources": ["list of specific learning resources"],
                    "current_level": "Beginner/Intermediate/Advanced",
                    "gap_analysis": "analysis of current skill level vs required level"
                }}
            ],
            "soft_skills": [
                {{
                    "skill": "skill name",
                    "priority": "high/medium/low",
                    "development_approaches": ["list of ways to develop this soft skill"],
                    "current_level": "Beginner/Intermediate/Advanced",
                    "gap_analysis": "analysis of current skill level vs required level"
                }}
            ]
        }},
        "profile_optimization": {{
            "headline_suggestions": ["suggestions for LinkedIn headline based on the profile. be creative and generate based on the strength and interest of the user."],
            "about_section_tips": ["improvements for About section"],
            "experience_highlighting": ["tips on highlighting relevant experience"],
        }},
        "industry_insights": {{
            "trends": ["relevant and up-to-date industry trends"],
            "certifications": ["valuable certifications"],
            "thought_leaders": ["people to follow"]
        }},
        "summary": "brief summary of the overall career development advice based on the profile, resume, desired career path and the stage of career the user is at"
    }}
    
    Note: Focus on providing genuine value to the career seeker. Consider both the LinkedIn profile and resume in your analysis to provide a comprehensive view of the user's current position and how to progress towards their desired career path.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
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