import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from helper import extract_text_from_file, analyze_resume_with_openai, analyze_linkedin_profile

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
if 'industry' not in st.session_state:
    st.session_state.industry = ""



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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.session_state.linkedin_url = st.text_input("LinkedIn Profile URL", 
                                             placeholder="https://www.linkedin.com/in/yourprofile/")
    
    with col2:
        st.session_state.career_path = st.text_input("Desired Career Path/Specialization", 
                                         placeholder="e.g., AI Development - ML Model Training, DevOps, Cloud Architecture, etc.")
    
    with col3:
        st.session_state.country = st.text_input("Country",
                                                 placeholder="e.g., Singapore, Sweden, USA, etc.")
        
    with col4:
        industries = [
            "Industry Agnostic",
            "Technology & Software",
            "Finance & Banking",
            "Healthcare & Medical",
            "Manufacturing & Engineering",
            "Retail & E-commerce",
            "Education & Training",
            "Media & Entertainment",
            "Real Estate & Construction",
            "Energy & Utilities",
            "Transportation & Logistics",
            "Consulting & Professional Services",
            "Hospitality & Tourism",
            "Telecommunications",
            "Government & Public Sector",
            "Other (Please specify)"
        ]
        selected_industry = st.selectbox("Industry", industries)
        if selected_industry == "Other (Please specify)":
            st.session_state.industry = st.text_input("Specify your industry")
        else:
            st.session_state.industry = selected_industry

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
                    st.session_state.industry,
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