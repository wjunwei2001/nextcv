import os
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from helper import extract_text_from_file, create_cytoscape_html
from llm_functions import analyze_resume_with_openai, analyze_linkedin_profile
import networkx as nx
import plotly.graph_objects as go
import streamlit.components.v1 as components
import json


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
st.header("AI-Powered Resume and Career Path Analysis")
st.write("Optimize your resume for your job application and identify skill gaps with AI-powered analysis")

tabs = st.tabs(["Resume Analysis", "Career Path Analysis"])

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
                        st.text_area("", value=st.session_state.resume_text, key='resumeAnalysis', height=300)
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
        tab1, tab2, tab3 = st.tabs(["Skills Analysis", "Content Improvements", "Company Insights"])
        
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
            
            st.subheader("Recommended Skills Development Path")
            if results['skill_match']['recommended_skills']:
                # Prepare data for Cytoscape
                cyto_nodes = []
                cyto_edges = []
                prereq_map = {}  # To track existing prerequisites
                
                # Add root node
                cyto_nodes.append({
                    'data': {
                        'id': 'desired-job',
                        'label': 'Desired Job',
                        'type': 'root',
                        'info': ''
                    }
                })
                
                # Group skills by priority
                priority_groups = {
                    'high': [],
                    'medium': [],
                    'low': []
                }
                
                for skill_data in results['skill_match']['recommended_skills']:
                    priority_groups[skill_data['priority']].append(skill_data)
                
                # First pass: Add all main skill nodes
                skill_nodes = {}  # Track skill nodes by their labels
                for priority in ['high', 'medium', 'low']:
                    skills = priority_groups[priority]
                    if skills:
                        for skill_data in skills:
                            skill_id = f"skill-{len(cyto_nodes)}"
                            skill = skill_data['skill']
                            
                            # Add skill node
                            cyto_nodes.append({
                                'data': {
                                    'id': skill_id,
                                    'label': skill,
                                    'type': priority,
                                    'info': f"Priority: {priority.title()}\nCategory: {skill_data['category']}\nEst. Time: {skill_data['estimated_time']}"
                                }
                            })
                            
                            # Connect to root
                            cyto_edges.append({
                                'data': {
                                    'source': 'desired-job',
                                    'target': skill_id
                                }
                            })
                            
                            skill_nodes[skill] = skill_id
                
                # Second pass: Add prerequisites and connect them
                for priority in ['high', 'medium', 'low']:
                    skills = priority_groups[priority]
                    if skills:
                        for skill_data in skills:
                            skill_id = skill_nodes[skill_data['skill']]
                            
                            # Add prerequisites if any
                            if skill_data.get('prerequisites'):
                                for prereq in skill_data['prerequisites']:
                                    # Check if this prerequisite already exists
                                    if prereq not in prereq_map:
                                        prereq_id = f"prereq-{len(cyto_nodes)}"
                                        prereq_map[prereq] = prereq_id
                                        
                                        # Add new prerequisite node
                                        cyto_nodes.append({
                                            'data': {
                                                'id': prereq_id,
                                                'label': prereq,
                                                'type': 'prerequisite',
                                                'info': f"Prerequisite for multiple skills"
                                            }
                                        })
                                    else:
                                        prereq_id = prereq_map[prereq]
                                    
                                    # Connect prerequisite to skill
                                    cyto_edges.append({
                                        'data': {
                                            'source': skill_id,
                                            'target': prereq_id
                                        }
                                    })
                
                # Define Cytoscape styles
                cyto_styles = [
                    {
                        'selector': 'node',
                        'style': {
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '12px',
                            'width': '30px',
                            'height': '30px',
                            'padding': '5px'
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'width': 2,
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle',
                            'line-color': '#888',
                            'target-arrow-color': '#888',
                            'opacity': 0.8
                        }
                    },
                    {
                        'selector': 'node[type="root"]',
                        'style': {
                            'background-color': '#6E7C7C',
                            'font-weight': 'bold',
                            'font-size': '16px'
                        }
                    },
                    {
                        'selector': 'node[type="high"]',
                        'style': {
                            'background-color': '#E63946',
                        }
                    },
                    {
                        'selector': 'node[type="medium"]',
                        'style': {
                            'background-color': '#F9C74F'
                        }
                    },
                    {
                        'selector': 'node[type="low"]',
                        'style': {
                            'background-color': '#90BE6D'
                        }
                    },
                    {
                        'selector': 'node[type="prerequisite"]',
                        'style': {
                            'background-color': '#43AA8B',
                            'font-size': '12px',
                        }
                    },
                    {
                        'selector': '.highlighted',
                        'style': {
                            'border-width': '3px',
                            'border-color': '#000',
                            'border-opacity': 1,
                            'z-index': 999
                        }
                    },
                    {
                        'selector': '.hover',
                        'style': {
                            'border-width': '2px',
                            'border-color': '#fff',
                            'border-opacity': 1,
                            'z-index': 999
                        }
                    }
                ]
                
                # Create columns for chart and legend
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Render Cytoscape graph
                    components.html(
                        create_cytoscape_html(cyto_nodes, cyto_edges, cyto_styles),
                        height=600,
                    )
                
                with col2:
                    # Create a custom legend with color explanations
                    st.markdown("### Priority Legend")
                    st.markdown(
                        """
                        <style>
                        .priority-box {
                            display: inline-block;
                            width: 15px;
                            height: 15px;
                            margin-right: 8px;
                            vertical-align: middle;
                            border-radius: 50%;
                        }
                        .priority-text {
                            vertical-align: middle;
                            font-size: 16px;
                        }
                        </style>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    priorities = [
                        {"name": "High Priority", "color": "#E63946", "description": "Learn these skills first"},
                        {"name": "Medium Priority", "color": "#F9C74F", "description": "Focus on these next"},
                        {"name": "Low Priority", "color": "#90BE6D", "description": "Nice to have skills"},
                        {"name": "Prerequisites", "color": "#43AA8B", "description": "Required foundation"}
                    ]
                    
                    for p in priorities:
                        st.markdown(
                            f"""
                            <div>
                                <span class="priority-box" style="background-color: {p['color']};"></span>
                                <span class="priority-text"><b>{p['name']}</b></span>
                            </div>
                            <div style="margin-left: 23px; margin-bottom: 10px; font-size: 14px;">{p['description']}</div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                    st.markdown("### How to use")
                    st.markdown(
                        """
                        - **Click** nodes to highlight them
                        - **Hover** over nodes for details
                        - **Drag** nodes to rearrange
                        - **Scroll** to zoom in/out
                        - Start with red nodes and work down
                        """
                    )
                
                # Interactive Skills Explorer
                st.subheader("Skills Explorer")
                
                filtered_skills = [
                    skill for skill in results['skill_match']['recommended_skills'] 
                ]
                
                # Display filtered skills in an expandable format
                if filtered_skills:
                    for skill_data in filtered_skills:
                        priority_color = {
                            "high": "#E63946",
                            "medium": "#F9C74F", 
                            "low": "#90BE6D"
                        }.get(skill_data['priority'], "#43AA8B")
                        
                        with st.expander(f"📊 {skill_data['skill']} ({skill_data['priority'].title()} Priority)"):
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.markdown(f"**Category:** {skill_data['category']}")
                                st.markdown(f"**Est. Time:** {skill_data['estimated_time']}")
                                
                                if skill_data.get('prerequisites'):
                                    st.markdown("**Prerequisites:**")
                                    for prereq in skill_data['prerequisites']:
                                        st.markdown(f"- {prereq}")
                            
                            with col2:
                                if skill_data.get('resources'):
                                    st.markdown("**Learning Resources:**")
                                    for i, resource in enumerate(skill_data['resources']):
                                        st.markdown(f"{i+1}. {resource}")
                                
                                # Add a progress tracking placeholder (in a real app, this could be interactive)
                                st.progress(0)
                                st.caption("Track your progress learning this skill")
                else:
                    st.info("No skills match your selected priority filters.")

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
    st.header("Career Path Analysis")
    st.write("Get personalized career development advice based on your LinkedIn profile, resume, and desired career path")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Your Resume")
        uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX, or TXT)*", type=["pdf", "docx", "txt"], key="linkedin_resume")
        
        if uploaded_file is not None:
            with st.spinner("Extracting text from your resume..."):
                resume_text = extract_text_from_file(uploaded_file)
                if resume_text:
                    st.success(f"Successfully extracted text from {uploaded_file.name}")
                    with st.expander("Preview Extracted Text"):
                        st.text_area("", value=resume_text, height=300)
        else:
            st.warning("Please upload your resume to proceed")
    
    with col2:
        st.subheader("2. Enter Career Details")
        st.session_state.linkedin_url = st.text_input("LinkedIn Profile URL", 
                                             placeholder="https://www.linkedin.com/in/yourprofile/")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.session_state.career_path = st.text_input("Desired Career Path/Specialization", 
                                         placeholder="e.g., AI Development - ML Model Training, DevOps, Cloud Architecture, etc.")
        
    with col4:
        st.session_state.country = st.text_input("Country",
                                                 placeholder="e.g., Singapore, Sweden, USA, etc.")
    
    col5, col6 = st.columns(2)
    
    with col5:
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
               disabled=not (st.session_state.linkedin_url and st.session_state.career_path and st.session_state.api_key and resume_text)):
        if not st.session_state.api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
        elif not st.session_state.linkedin_url:
            st.error("Please enter your LinkedIn profile URL.")
        elif not st.session_state.career_path:
            st.error("Please specify your desired career path.")
        elif not resume_text:
            st.error("Please upload your resume.")
        else:
            with st.spinner("Analyzing your LinkedIn profile, resume, and career path..."):
                st.session_state.linkedin_analysis = analyze_linkedin_profile(
                    st.session_state.linkedin_url,
                    st.session_state.career_path,
                    st.session_state.country,
                    st.session_state.industry,
                    resume_text,
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
        tab1, tab2, tab3, tab4 = st.tabs([
            "Career Alignment", 
            # "Development Plan", 
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
        
        # with tab2:
        #     col1, col2, col3 = st.columns(3)
            
        #     with col1:
        #         st.subheader("Short-Term Actions (0-6 months)")
        #         for action in results['development_plan']['short_term_actions']:
        #             st.info(action)
            
        #     with col2:
        #         st.subheader("Medium-Term Goals (6-18 months)")
        #         for goal in results['development_plan']['medium_term_goals']:
        #             st.success(goal)
            
        #     with col3:
        #         st.subheader("Long-Term Milestones (18+ months)")
        #         for milestone in results['development_plan']['long_term_milestones']:
        #             st.success(milestone)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Technical Skills")
                for skill in results['skill_development']['technical_skills']:
                    with st.expander(f"{skill['skill']} (Priority: {skill['priority'].upper()})"):
                        st.write(f"**Current Level:** {skill['current_level']}")
                        st.write(f"**Gap Analysis:** {skill['gap_analysis']}")
                        st.write("**Recommended Resources:**")
                        for resource in skill['resources']:
                            st.info(resource)
            
            with col2:
                st.subheader("Soft Skills")
                for skill in results['skill_development']['soft_skills']:
                    with st.expander(f"{skill['skill']} (Priority: {skill['priority'].upper()})"):
                        st.write(f"**Current Level:** {skill['current_level']}")
                        st.write(f"**Gap Analysis:** {skill['gap_analysis']}")
                        st.write("**Development Approaches:**")
                        for approach in skill['development_approaches']:
                            st.info(approach)
        
        with tab3:
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
        
        with tab4:
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
# st.sidebar.header("Settings")
# st.session_state.api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
st.session_state.api_key = st.secrets["OPENAI_API_KEY"]

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

