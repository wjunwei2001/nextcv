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
if 'company' not in st.session_state:
    st.session_state.company = ""
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
        uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)*", type=["pdf", "docx", "txt"])
        
        if uploaded_file is not None:
            with st.spinner("Extracting text from your resume..."):
                st.session_state.resume_text = extract_text_from_file(uploaded_file)
                if st.session_state.resume_text:
                    st.success(f"Successfully extracted text from {uploaded_file.name}")
                    with st.expander("Preview Extracted Text"):
                        st.text_area("", value=st.session_state.resume_text, height=300)
        else:
            st.warning("Please upload your resume to proceed")
        
    with col2:
        st.header("2. Enter Job Description")
        st.session_state.company = st.text_input("Company Name", placeholder="Enter the company you're applying to")
        st.session_state.job_description = st.text_area("Paste Job Description*", height=300, 
                                                      placeholder="Enter the job description here...")
        
        if not st.session_state.job_description:
            st.warning("Please enter a job description to proceed")
            

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
                    st.session_state.company,
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
        
        with col2:
            st.subheader("Summary")
            st.write(results['summary'])
        
        # Tabs for detailed analysis
        tab1, tab2, tab3, tab4 = st.tabs(["Skills Analysis", "Content Improvements", "Learning Opportunities", "Company Insights"])
        
        with tab1:
            st.subheader("Your Matching Skills")
            if results['skill_match']['matched_skills']:
                st.success("These are the skills you already have that match the job requirements:")
                for skill in results['skill_match']['matched_skills']:
                    st.markdown(f"✅ {skill}")
            else:
                st.warning("No matching skills found. Consider highlighting relevant skills from your experience.")
            
            st.subheader("Skills to Develop")
            if results['skill_match']['missing_skills']:
                st.error("These are the skills you need to develop for this role:")
                for skill in results['skill_match']['missing_skills']:
                    st.markdown(f"⚠️ {skill}")
            else:
                st.success("Great! You have all the required skills for this role.")
            
            st.subheader("Recommended Skills to Add")
            if results['skill_match']['recommended_skills']:
                st.info("These additional skills would make your profile even stronger:")
                for skill in results['skill_match']['recommended_skills']:
                    st.markdown(f"💡 {skill}")
            else:
                st.success("Your skill set is well-aligned with the role requirements.")
        
        with tab2:
            st.subheader("Sections to Improve")
            for section in results['content_improvements']['sections_to_improve']:
                st.warning(section)
            
            st.subheader("Wording Suggestions")
            for suggestion in results['content_improvements']['wording_suggestions']:
                st.info(suggestion)
            
            st.subheader("Format Suggestions")
            for suggestion in results['content_improvements']['format_suggestions']:
                st.info(suggestion)
        
        with tab3:
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

        with tab4:
            if st.session_state.company:
                st.subheader("Company-Specific Skills")
                for skill in results['company_specific_insights']['company_specific_skills']:
                    st.success(skill)
                
                st.subheader("Recommended Projects")
                for project in results['company_specific_insights']['company_projects']:
                    st.info(project)
                
                st.subheader("Networking Opportunities")
                for opportunity in results['company_specific_insights']['networking_opportunities']:
                    st.info(opportunity)
                
                st.subheader("Company Resources")
                for resource in results['company_specific_insights']['company_resources']:
                    st.info(resource)
            else:
                st.info("Enter a company name to get company-specific insights and recommendations.")

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