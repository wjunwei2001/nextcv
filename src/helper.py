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
    

def create_cytoscape_html(nodes, edges, styles):
    return f"""
    <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.1/cytoscape.min.js"></script>
            <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
            <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
            <style>
                .cy-container {{
                    position: relative;
                    width: 100%;
                    height: 600px;
                }}
                #cy {{
                    width: 100%;
                    height: 100%;
                    display: block;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    position: absolute;
                }}
                .control-button {{
                    padding: 8px 16px;
                    margin: 5px;
                    border-radius: 4px;
                    border: 1px solid #ccc;
                    background-color: rgba(255, 255, 255, 0.9);
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.2s;
                }}
                .control-button:hover {{
                    background-color: rgba(240, 240, 240, 0.9);
                }}
                #controls {{
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    display: flex;
                    gap: 10px;
                    z-index: 999;
                }}
            </style>
        </head>
        <body>
            <div class="cy-container">
                <div id="cy"></div>
                <div id="controls">
                    <button id="resetLayout" class="control-button">Reset Layout</button>
                </div>
            </div>
            <script>
                // Register the dagre layout
                cytoscape.use(cytoscapeDagre);
                
                var cy = cytoscape({{
                    container: document.getElementById('cy'),
                    elements: {{
                        nodes: {json.dumps(nodes)},
                        edges: {json.dumps(edges)}
                    }},
                    style: {json.dumps(styles)},
                    layout: {{
                        name: 'dagre',
                        rankDir: 'TB',
                        ranker: 'network-simplex',
                        nodeDimensionsIncludeLabels: true,
                        spacingFactor: 1,
                        edgeSep: 40,
                        rankSep: 90,
                        animate: true,
                        animationDuration: 500,
                        fit: true,
                        padding: 50
                    }},
                    wheelSensitivity: 0.2  // Reduce scroll zoom sensitivity
                }});
                
                // Add interactivity
                cy.on('tap', 'node', function(evt){{
                    var node = evt.target;
                    cy.elements().removeClass('highlighted');
                    node.addClass('highlighted');
                    node.neighborhood().addClass('highlighted');
                }});
                
                cy.on('mouseover', 'node', function(evt){{
                    var node = evt.target;
                    node.addClass('hover');
                    
                    // Show tooltip with node info
                    var info = node.data('info');
                    if (info) {{
                        var tooltip = document.createElement('div');
                        tooltip.className = 'tooltip';
                        tooltip.innerHTML = info;
                        tooltip.style.position = 'absolute';
                        tooltip.style.left = evt.renderedPosition.x + 'px';
                        tooltip.style.top = (evt.renderedPosition.y - 10) + 'px';
                        tooltip.style.background = 'rgba(0,0,0,0.8)';
                        tooltip.style.color = 'white';
                        tooltip.style.padding = '5px 10px';
                        tooltip.style.borderRadius = '3px';
                        tooltip.style.fontSize = '14px';
                        tooltip.style.zIndex = 1000;
                        document.body.appendChild(tooltip);
                        node.data('tooltip', tooltip);
                    }}
                }});
                
                cy.on('mouseout', 'node', function(evt){{
                    var node = evt.target;
                    node.removeClass('hover');
                    
                    // Remove tooltip
                    var tooltip = node.data('tooltip');
                    if (tooltip) {{
                        tooltip.remove();
                        node.removeData('tooltip');
                    }}
                }});
                
                // Center the graph
                cy.fit();
                cy.center();
                
                // Add button functionality
                document.getElementById('resetLayout').addEventListener('click', function() {{
                    cy.layout({{
                        name: 'dagre',
                        rankDir: 'TB',
                        ranker: 'network-simplex',
                        nodeDimensionsIncludeLabels: true,
                        spacingFactor: 1,
                        edgeSep: 40,
                        rankSep: 90,
                        animate: true,
                        animationDuration: 500,
                        fit: true,
                        padding: 50
                    }}).run();
                }});
            </script>
        </body>
    </html>
    """