# NextCV - AI-Powered Career Optimization Tool

NextCV is an intelligent career optimization platform that helps job seekers enhance their resumes and plan their career paths using advanced AI analysis. The tool provides personalized insights and actionable recommendations to help users stand out in their job applications and career development.

## Features

### 1. Resume Analysis
- **AI-Powered Resume Review**: Get detailed analysis of your resume against job descriptions
- **Skill Gap Analysis**: Identify missing skills and get recommendations for development
- **Content Optimization**: Receive specific suggestions for improving resume content and formatting
- **Company-Specific Insights**: Get tailored advice based on the company you're applying to

### 2. Career Path Analysis
- **Comprehensive Career Assessment**: Analyze your current position and desired career path
- **Skill Development Roadmap**: Get personalized learning paths with prioritized skills
- **Networking Strategy**: Receive targeted networking recommendations
- **Profile Optimization**: Get specific tips for improving both your resume and LinkedIn profile
- **Industry Insights**: Stay informed about relevant trends and certifications

## Getting Started

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Streamlit

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nextcv.git
cd nextcv
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

### Running the Application

1. Start the Streamlit app:
```bash
streamlit run src/app.py
```

2. Open your browser and navigate to:
```
http://localhost:8501
```

## Usage

### Resume Analysis
1. Upload your resume (PDF, DOCX, or TXT)
2. Enter the job description
3. Optionally provide the company name
4. Click "Analyze" to get detailed feedback

### Career Path Analysis
1. Upload your resume
2. Enter your LinkedIn profile URL
3. Specify your desired career path
4. Select your target industry and country
5. Click "Analyze Career Path" for personalized guidance

## Features in Detail

### Resume Analysis Features
- **Match Percentage**: See how well your resume aligns with the job requirements
- **Skill Matching**: Identify which skills you already have and which ones you need to develop
- **Content Improvements**: Get specific suggestions for enhancing your resume content
- **Formatting Tips**: Receive advice on improving your resume's visual presentation
- **Company-Specific Recommendations**: Get tailored advice based on the company's culture and requirements

### Career Path Analysis Features
- **Career Alignment Score**: Understand how well your current profile aligns with your desired path
- **Skill Development Plan**: Get a prioritized list of skills to develop
- **Networking Strategy**: Receive specific recommendations for building your professional network
- **Profile Optimization**: Get tips for improving both your resume and LinkedIn profile
- **Industry Insights**: Stay updated with relevant trends and certifications

## Technologies Used

- **Streamlit**: Web application framework
- **OpenAI API**: AI-powered analysis and recommendations
- **Cytoscape.js**: Interactive skill visualization
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX file handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT API
- Streamlit for the web framework
- Cytoscape.js for the visualization capabilities

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Roadmap

- [ ] Add support for more file formats
- [ ] Implement ATS optimization features
- [ ] Add progress tracking for skill development
- [ ] Integrate with job boards
- [ ] Add multi-language support