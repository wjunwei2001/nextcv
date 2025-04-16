import streamlit as st
import PyPDF2
import docx
import os
import io
import json
import pandas as pd
import plotly.express as px
import textwrap
from openai import OpenAI
import re

# App setup
st.set_page_config(
    page_title="NextCV",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'linkedin_url' not in st.session_state:
    st.session_state.linkedin_url = ""
if 'career_path' not in st.session_state:
    st.session_state.career_path = ""
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'linkedin_analysis' not in st.session_state:
    st.session_state.linkedin_analysis = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'country' not in st.session_state:
    st.session_state.country = ""

# Function to extract text from various file formats
def extract_text_from_file(file):
    text = ""
    file_extension = os.path.splitext(file.name)[1].lower()
    
    if file_extension == '.pdf':
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
        except Exception as e:
            st.error(f"Error extracting text from PDF: {e}")
    elif file_extension in ['.docx', '.doc']:
        try:
            doc = docx.Document(io.BytesIO(file.read()))
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            st.error(f"Error extracting text from Word document: {e}")
    elif file_extension == '.txt':
        try:
            text = file.read().decode('utf-8')
        except Exception as e:
            st.error(f"Error reading text file: {e}")
    else:
        st.error("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
    
    return text

# Function to analyze resume using OpenAI
def analyze_resume_with_openai(resume_text, job_description, api_key):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    Analyze the following resume against the job description to provide detailed feedback. Think carefully from the perspective of someone who is hiring for the role.
    Focus on ATS compatibility, skill match, content improvements, and learning opportunities.
    
    RESUME:
    {resume_text}
    
    JOB DESCRIPTION:
    {job_description}
    
    Provide a comprehensive analysis in JSON format with the following structure:
    {{
        "match_percentage": 0-100,
        "ats_compatibility": {{
            "score": 0-100,
            "issues": ["list of ATS issues"],
            "recommendations": ["list of recommendations to improve ATS compatibility"]
        }},
        "skill_match": {{
            "matched_skills": ["list of matched skills"],
            "missing_skills": ["list of missing skills"],
            "recommended_skills": ["list of recommended skills to add"]
        }},
        "content_improvements": {{
            "sections_to_improve": ["list of sections that need improvement"],
            "wording_suggestions": ["list of wording improvements, be specific about this and give examples"],
            "format_suggestions": ["list of formatting improvements, be specific about this and give examples"]
        }},
        "learning_opportunities": {{
            "critical_skills_to_learn": ["list of critical skills to learn"],
            "resources": [
                {{
                    "skill": "skill name",
                    "resource_type": "course/book/certification/website",
                    "resource_name": "specific resource name",
                    "url": "resource url if applicable",
                    "estimated_time": "estimated time to complete (weeks/months)"
                }}
            ],
            "transferrable_skills": ["list of skills that are transferrable to other roles"]
        }},
        "summary": "brief summary of the overall analysis"
    }}
    
    Be specific, actionable, and detailed in your analysis. Focus on providing genuine value to the job seeker.
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
def analyze_linkedin_profile(linkedin_url, career_path, country, api_key):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    Analyze the following LinkedIn profile URL (carefully) and desired career path to provide career development advice. 
    Think carefully about what kind of skills expertise the industry today actually need according to the desired career pathway.
    Do 
    
    LINKEDIN PROFILE URL:
    {linkedin_url}
    
    DESIRED CAREER PATH/SPECIALIZATION:
    {career_path + " in " + country}
    
    Provide a comprehensive analysis in JSON format with the following structure:
    {{
        "career_alignment": {{
            "alignment_score": 0-100,
            "strengths": ["list of strengths that align with the desired path"],
            "gaps": ["list of gaps or weaknesses for the desired path"]
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
            "headline_suggestions": ["suggestions for LinkedIn headline"],
            "about_section_tips": ["improvements for About section"],
            "experience_highlighting": ["tips on highlighting relevant experience"],
            "skill_endorsements": ["skills to seek endorsements for"]
        }},
        "industry_insights": {{
            "trends": ["relevant industry trends"],
            "certifications": ["valuable certifications"],
            "thought_leaders": ["people to follow"]
        }},
        "summary": "brief summary of the overall career development advice"
    }}
    
    Note: Focus on providing genuine value to the career seeker.
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

# Main app interface
st.title("NextCV - Career Optimization Tool")
st.header("AI-Powered Resume and LinkedIn Analysis")
st.write("Optimize your resume for ATS and identify skill gaps with AI-powered analysis")

tabs = st.tabs(["Resume Analysis", "LinkedIn Career Path Analysis"])

with tabs[0]:

    col1, col2 = st.columns(2)

    with col1:
        st.header("1. Upload Your Resume")
        uploaded_file = st.file_uploader("", type=["pdf", "docx", "txt"])
        
        if uploaded_file is not None:
            with st.spinner("Extracting text from your resume..."):
                st.session_state.resume_text = extract_text_from_file(uploaded_file)
                if st.session_state.resume_text:
                    st.success(f"Successfully extracted text from {uploaded_file.name}")
                    with st.expander("Preview Extracted Text"):
                        st.text_area("", value=st.session_state.resume_text, height=300)

    with col2:
        st.header("2. Enter Job Description")
        st.session_state.job_description = st.text_area("Paste Job Description", height=300)

    # Analyze button
    if st.button("Analyze", key="analyze_button", use_container_width=True, 
                disabled=not (st.session_state.resume_text and st.session_state.job_description and st.session_state.api_key)):
        if not st.session_state.api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        elif not st.session_state.resume_text:
            st.error("Please upload your resume.")
        elif not st.session_state.job_description:
            st.error("Please enter a job description.")
        else:
            with st.spinner("Analyzing your resume against the job description..."):
                st.session_state.analysis_results = analyze_resume_with_openai(
                    st.session_state.resume_text, 
                    st.session_state.job_description,
                    st.session_state.api_key
                )

    # Display analysis results
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        st.header("Analysis Results")
        
        # Overall match
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Match Percentage", f"{results['match_percentage']}%")
            st.metric("ATS Compatibility", f"{results['ats_compatibility']['score']}%")
        
        with col2:
            st.subheader("Summary")
            st.write(results['summary'])
        
        # Tabs for detailed analysis
        tab1, tab2, tab3, tab4 = st.tabs(["ATS Compatibility", "Skills Analysis", "Content Improvements", "Learning Opportunities"])
        
        with tab1:
            st.subheader("ATS Compatibility Issues")
            if results['ats_compatibility']['issues']:
                for issue in results['ats_compatibility']['issues']:
                    st.warning(issue)
            else:
                st.success("No major ATS compatibility issues detected.")
                
            st.subheader("ATS Improvement Recommendations")
            for rec in results['ats_compatibility']['recommendations']:
                st.info(rec)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Matched Skills")
                for skill in results['skill_match']['matched_skills']:
                    st.success(skill)
            
            with col2:
                st.subheader("Missing Skills")
                for skill in results['skill_match']['missing_skills']:
                    st.error(skill)
            
            st.subheader("Recommended Skills to Add")
            for skill in results['skill_match']['recommended_skills']:
                st.info(skill)
            
            # Skills visualization
            if results['skill_match']['matched_skills'] or results['skill_match']['missing_skills']:
                skill_data = {
                    'Skill': results['skill_match']['matched_skills'] + results['skill_match']['missing_skills'],
                    'Status': ['Matched'] * len(results['skill_match']['matched_skills']) + 
                            ['Missing'] * len(results['skill_match']['missing_skills']),
                    'Count': [1] * (len(results['skill_match']['matched_skills']) + len(results['skill_match']['missing_skills']))
                }
                
                df = pd.DataFrame(skill_data)
                
                fig = px.bar(
                    df, 
                    x='Skill', 
                    y='Count',
                    color='Status',
                    color_discrete_map={'Matched': '#0068c9', 'Missing': '#ff4b4b'},
                    title='Skills Match Analysis',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Sections to Improve")
            for section in results['content_improvements']['sections_to_improve']:
                st.warning(section)
            
            st.subheader("Wording Suggestions")
            for suggestion in results['content_improvements']['wording_suggestions']:
                st.info(suggestion)
            
            st.subheader("Format Suggestions")
            for suggestion in results['content_improvements']['format_suggestions']:
                st.info(suggestion)
        
        with tab4:
            st.subheader("Critical Skills to Learn")
            for skill in results['learning_opportunities']['critical_skills_to_learn']:
                st.error(skill)
            
            st.subheader("Learning Resources")
            if results['learning_opportunities']['resources']:
                resources_df = pd.DataFrame(results['learning_opportunities']['resources'])
                st.dataframe(resources_df, use_container_width=True, hide_index=True)
            
            st.subheader("Transferrable Skills")
            for skill in results['learning_opportunities']['transferrable_skills']:
                st.success(skill)

with tabs[1]:
    st.header("LinkedIn Career Path Analysis")
    st.write("Get personalized career development advice based on your LinkedIn profile and desired career path")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.session_state.linkedin_url = st.text_input("LinkedIn Profile URL", 
                                             placeholder="https://www.linkedin.com/in/yourprofile/")
    
    with col2:
        st.session_state.career_path = st.text_input("Desired Career Path/Specialization", 
                                         placeholder="e.g., AI Development - ML Model Training, DevOps, Cloud Architecture, etc.")
    
    with col3:
        st.session_state.country = st.text_input("Country",
                                                 placeholder="e.g., Singapore, Sweden, USA, etc.")

    # Analyze button for LinkedIn
    if st.button("Analyze Career Path", key="analyze_linkedin_button", use_container_width=True, 
               disabled=not (st.session_state.linkedin_url and st.session_state.career_path and st.session_state.api_key)):
        if not st.session_state.api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        elif not st.session_state.linkedin_url:
            st.error("Please enter your LinkedIn profile URL.")
        elif not st.session_state.career_path:
            st.error("Please specify your desired career path.")
        else:
            with st.spinner("Analyzing your LinkedIn profile and career path..."):
                st.session_state.linkedin_analysis = analyze_linkedin_profile(
                    st.session_state.linkedin_url,
                    st.session_state.career_path,
                    st.session_state.country,
                    st.session_state.api_key
                )
    
    # Display LinkedIn analysis results
    if st.session_state.linkedin_analysis:
        results = st.session_state.linkedin_analysis
        
        st.header("Career Development Analysis")
        
        # Overall alignment
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric("Career Alignment", f"{results['career_alignment']['alignment_score']}%")
        
        with col2:
            st.subheader("Summary")
            st.write(results['summary'])
        
        # Tabs for detailed analysis
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Career Alignment", 
            "Development Plan", 
            "Skill Development", 
            "Profile Optimization",
            "Industry Insights"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Strengths")
                for strength in results['career_alignment']['strengths']:
                    st.success(strength)
            
            with col2:
                st.subheader("Gaps")
                for gap in results['career_alignment']['gaps']:
                    st.error(gap)
            
            st.subheader("Networking Strategy")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Key Connections**")
                for connection in results['networking_strategy']['key_connections']:
                    st.info(connection)
            
            with col2:
                st.write("**Communities**")
                for community in results['networking_strategy']['communities']:
                    st.info(community)
            
            with col3:
                st.write("**Engagement Tactics**")
                for tactic in results['networking_strategy']['engagement_tactics']:
                    st.info(tactic)
        
        with tab2:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Short-Term Actions (0-6 months)")
                for action in results['development_plan']['short_term_actions']:
                    st.info(action)
            
            with col2:
                st.subheader("Medium-Term Goals (6-18 months)")
                for goal in results['development_plan']['medium_term_goals']:
                    st.success(goal)
            
            with col3:
                st.subheader("Long-Term Milestones (18+ months)")
                for milestone in results['development_plan']['long_term_milestones']:
                    st.success(milestone)
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Technical Skills")
                for skill in results['skill_development']['technical_skills']:
                    with st.expander(f"{skill['skill']} (Priority: {skill['priority'].upper()})"):
                        st.write("**Recommended Resources:**")
                        for resource in skill['resources']:
                            st.info(resource)
            
            with col2:
                st.subheader("Soft Skills")
                for skill in results['skill_development']['soft_skills']:
                    with st.expander(f"{skill['skill']} (Priority: {skill['priority'].upper()})"):
                        st.write("**Development Approaches:**")
                        for approach in skill['development_approaches']:
                            st.info(approach)
        
        with tab4:
            st.subheader("LinkedIn Profile Optimization")
            
            with st.expander("Headline Suggestions"):
                for suggestion in results['profile_optimization']['headline_suggestions']:
                    st.info(suggestion)
            
            with st.expander("About Section Tips"):
                for tip in results['profile_optimization']['about_section_tips']:
                    st.info(tip)
            
            with st.expander("Experience Highlighting"):
                for tip in results['profile_optimization']['experience_highlighting']:
                    st.info(tip)
            
            with st.expander("Skill Endorsements"):
                for skill in results['profile_optimization']['skill_endorsements']:
                    st.info(skill)
        
        with tab5:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Industry Trends")
                for trend in results['industry_insights']['trends']:
                    st.info(trend)
            
            with col2:
                st.subheader("Valuable Certifications")
                for cert in results['industry_insights']['certifications']:
                    st.success(cert)
            
            with col3:
                st.subheader("Thought Leaders to Follow")
                for leader in results['industry_insights']['thought_leaders']:
                    st.info(leader)

# OpenAI API Key in sidebar
st.sidebar.header("Settings")
st.session_state.api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

# About section in sidebar
st.sidebar.header("About")
st.sidebar.info("""
This application uses AI to help you optimize your career prospects in two ways:

1. **Resume Analysis**: Upload your resume and a job description to get tailored recommendations for ATS optimization and skills improvement.

2. **Career Path Analysis**: Input your LinkedIn profile and desired career path to receive personalized career development guidance.

Your data is processed securely and is not stored after the session ends.
""")

# App footer
st.divider()
st.caption("Resume Analyzer - AI powered resume optimization tool")
st.caption("Note: This tool uses AI to analyze your resume and job description. Results should be used as guidance and may not reflect all aspects of hiring processes.")