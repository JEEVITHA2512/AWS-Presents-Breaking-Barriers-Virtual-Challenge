from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import os
import PyPDF2
import re
import json
import datetime
import uuid
from io import BytesIO
import time
import boto3

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['QUESTIONS_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_questions")

# Create required directories
os.makedirs(app.config['QUESTIONS_FOLDER'], exist_ok=True)

# AWS Bedrock configuration
AWS_REGION = "us-east-1"  # Change as needed
BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"  # Example model, update as needed

# Initialize Bedrock client
bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

# Predefined technical keywords
TECHNICAL_KEYWORDS = {
    'programming_languages': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin', 'swift', 'typescript'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'oracle', 'sqlite', 'nosql'],
    'cloud_platforms': ['aws', 'azure', 'gcp', 'google cloud', 'cloud computing', 'docker', 'kubernetes', 'terraform'],
    'frameworks': ['django', 'flask', 'react', 'angular', 'vue', 'spring', 'express', 'laravel', 'rails'],
    'data_science': ['machine learning', 'deep learning', 'data science', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'ai', 'artificial intelligence'],
    'tools': ['git', 'jenkins', 'jira', 'confluence', 'slack', 'docker', 'linux', 'bash', 'powershell'],
    'web_technologies': ['html', 'css', 'rest api', 'graphql', 'json', 'xml', 'microservices', 'api']
}

# Flatten all keywords into a single list for matching
ALL_KEYWORDS = []
for category, keywords in TECHNICAL_KEYWORDS.items():
    ALL_KEYWORDS.extend(keywords)

def check_bedrock_connection():
    """Check if AWS Bedrock is accessible"""
    try:
        prompt = "Hello"
        body = {
            "prompt": prompt,
            "max_tokens": 10
        }
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        # The structure of the result depends on the model; adjust as needed
        return True
    except Exception as e:
        print(f"Bedrock connection error: {e}")
        return False

def generate_with_bedrock(prompt):
    """Generate text using AWS Bedrock"""
    try:
        body = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.7
        }
        response = bedrock_client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response['body'].read())
        # The structure of the result depends on the model; adjust as needed
        return result.get("completion", "").strip()
    except Exception as e:
        print(f"Error generating with Bedrock: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def find_matching_keywords(text):
    """Find matching keywords in the extracted text"""
    text_lower = text.lower()
    matched_keywords = []
    
    for keyword in ALL_KEYWORDS:
        # Use word boundaries to match whole words
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            matched_keywords.append(keyword)
    
    # Categorize matched keywords
    categorized_matches = {}
    for category, keywords in TECHNICAL_KEYWORDS.items():
        category_matches = [kw for kw in matched_keywords if kw in keywords]
        if category_matches:
            categorized_matches[category] = category_matches
    
    return matched_keywords, categorized_matches

def generate_questions(keywords):
    """Generate technical questions using AWS Bedrock based on matched keywords"""
    # Create a more structured prompt for better question generation
    prompt = f"""You are an experienced technical interviewer. Based on the following technical skills found in a candidate's resume: {', '.join(keywords[:10])}

Generate exactly 5 technical interview questions. Each question should:
- Test practical knowledge and experience
- Be specific to the technologies mentioned
- Be challenging but fair for someone with these skills
- Focus on real-world scenarios

Format your response as a numbered list (1., 2., 3., 4., 5.) with each question on a new line.

Questions:
1."""

    print(f"Generating questions for keywords: {keywords[:10]}")  # Debug print
    
    response = generate_with_bedrock(prompt)
    
    if not response:
        # Fallback questions if Bedrock fails
        return [
            "1. Can you explain your experience with the main technologies in your resume?",
            "2. Describe a challenging project you worked on and how you solved technical problems.",
            "3. How do you stay updated with the latest developments in your technical stack?",
            "4. Walk me through your approach to debugging a complex issue.",
            "5. What best practices do you follow when working with your primary technologies?"
        ]
    
    # Parse the response to extract questions
    lines = response.split('\n')
    questions = []
    
    for line in lines:
        line = line.strip()
        # Look for numbered questions
        if re.match(r'^\d+\.', line) and len(line) > 5:
            questions.append(line)
    
    # If we don't have enough questions, try to extract any question-like sentences
    if len(questions) < 5:
        for line in lines:
            line = line.strip()
            if line.endswith('?') and len(line) > 20:
                if not any(q.endswith(line) for q in questions):
                    questions.append(line)
    
    # Ensure we have exactly 5 questions
    questions = questions[:5]
    
    # If still not enough, pad with generic questions
    while len(questions) < 5:
        questions.append(f"{len(questions) + 1}. Tell me about your experience with {keywords[len(questions) % len(keywords)] if keywords else 'software development'}.")
    
    print(f"Generated {len(questions)} questions")  # Debug print
    return questions

def save_questions_to_file(questions, session_id):
    """Save generated questions to a file"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"questions_{session_id}_{timestamp}.json"
    filepath = os.path.join(app.config['QUESTIONS_FOLDER'], filename)
    
    data = {
        'session_id': session_id,
        'timestamp': timestamp,
        'questions': questions,
        'answers': [None] * len(questions),  # Initialize empty answers
        'current_question': 0
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

def load_questions_file(filename):
    """Load questions and answers from file"""
    filepath = os.path.join(app.config['QUESTIONS_FOLDER'], filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return None

def save_answer_to_file(filename, question_index, answer):
    """Save user's answer to the questions file"""
    filepath = os.path.join(app.config['QUESTIONS_FOLDER'], filename)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        data['answers'][question_index] = answer
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    except:
        return False

@app.route('/')
def index():
    return render_template('thinking_index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    # Check Bedrock connection first
    if not check_bedrock_connection():
        return jsonify({
            'error': f'Cannot connect to AWS Bedrock. Please make sure your AWS credentials and Bedrock access are set correctly.',
            'troubleshooting': [
                'Set your AWS credentials using aws configure',
                f'Check if you have access to model: {BEDROCK_MODEL_ID}',
                'Verify your AWS account has sufficient permissions and quota'
            ]
        }), 500
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Generate session ID if not exists
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            
            # Extract text from PDF
            pdf_file = BytesIO(file.read())
            extracted_text = extract_text_from_pdf(pdf_file)
            
            if extracted_text.startswith("Error"):
                return jsonify({'error': extracted_text}), 400
            
            # Find matching keywords
            matched_keywords, categorized_matches = find_matching_keywords(extracted_text)
            
            if not matched_keywords:
                return jsonify({
                    'error': 'No technical keywords found in the resume. Please ensure your resume contains technical skills.'
                }), 400
            
            # Generate questions using AWS Bedrock
            questions = generate_questions(matched_keywords)
            
            # Save questions to file
            questions_file = save_questions_to_file(questions, session['session_id'])
            
            return jsonify({
                'success': True,
                'questions': questions,
                'matched_keywords': matched_keywords,
                'categorized_keywords': categorized_matches,
                'session_id': session['session_id'],
                'questions_file': questions_file,
                'message': f'Resume analyzed successfully! Found {len(matched_keywords)} technical skills. Questions have been generated and saved.'
            })
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type. Please upload a PDF file.'}), 400

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Submit user's answer to a question"""
    data = request.get_json()
    questions_file = data.get('questions_file')
    question_index = data.get('question_index')
    answer = data.get('answer')
    
    if not all([questions_file, question_index is not None, answer]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Save answer to file
    if save_answer_to_file(questions_file, question_index, answer):
        # Get next question if available
        questions_data = load_questions_file(questions_file)
        next_index = question_index + 1
        
        if next_index < len(questions_data['questions']):
            next_question = questions_data['questions'][next_index]
            return jsonify({
                'success': True,
                'message': 'Answer saved successfully',
                'next_question': next_question,
                'is_last_question': False
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Answer saved successfully',
                'is_last_question': True
            })
    else:
        return jsonify({'error': 'Failed to save answer'}), 500

@app.route('/get_answers', methods=['GET'])
def get_answers():
    """Get all questions and answers for a session"""
    questions_file = request.args.get('questions_file')
    if not questions_file:
        return jsonify({'error': 'No questions file specified'}), 400
    
    questions_data = load_questions_file(questions_file)
    if not questions_data:
        return jsonify({'error': 'Questions file not found'}), 404
    
    return jsonify({
        'success': True,
        'questions': questions_data['questions'],
        'answers': questions_data['answers'],
        'timestamp': questions_data['timestamp']
    })

@app.route('/keywords')
def show_keywords():
    """Show all available keywords for reference"""
    return jsonify({'technical_keywords': TECHNICAL_KEYWORDS})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'thinking_app'})

if __name__ == '__main__':
    print("Starting AuroraVoice Resume Analyzer...")
    print(f"Using AWS Bedrock model: {BEDROCK_MODEL_ID}")
    
    if check_bedrock_connection():
        print("AWS Bedrock connection successful!")
    else:
        print("Warning: Cannot connect to AWS Bedrock. Please make sure:")
        print("  1. Set your AWS credentials using aws configure")
        print(f"  2. You have access to the model: {BEDROCK_MODEL_ID}")
        print("  3. Your AWS account has sufficient permissions and quota")
    
    app.run(debug=True, port=5000)