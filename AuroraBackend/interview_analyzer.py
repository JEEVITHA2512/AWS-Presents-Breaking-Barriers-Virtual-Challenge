import json
import os
import requests
import pyttsx3
import subprocess
import webbrowser
import time
import openai
from datetime import datetime
from typing import Dict, List, Tuple
from flask import Flask, render_template_string, request, redirect, url_for, jsonify, render_template

class InterviewAnalyzer:
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the Interview Analyzer
        
        Args:
            openai_api_key: OpenAI API key (if not provided, will use default key)
        """
        self.openai_api_key = openai_api_key or "sk-None-UqWvfA6oQMNrlK2CIl05T3BlbkFJHzWdeLqRSnRE780XkgHi"  # Direct API key
        self.openai_model = "gpt-4o-mini"  # Updated to use gpt-4o-mini
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
    def setup_tts(self):
        """Configure text-to-speech settings"""
        try:
            # Set speech rate (words per minute)
            self.tts_engine.setProperty('rate', 180)
            
            # Set volume (0.0 to 1.0)
            self.tts_engine.setProperty('volume', 0.9)
            
            # Try to set a clearer voice if available
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice if available, otherwise use first voice
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    self.tts_engine.setProperty('voice', voices[0].id)
        except Exception as e:
            print(f"Warning: TTS setup encountered an issue: {e}")
    
    def load_interview_data(self, file_path: str) -> Dict:
        """Load interview data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Interview file not found: {file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {file_path}")
    
    def query_openai(self, prompt: str) -> str:
        """Send query to OpenAI model"""
        if not self.openai_api_key:
            return "Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a friendly technical interviewer giving brief, human feedback. Keep responses under 200 words and conversational."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,  # Reduced for shorter responses
                temperature=0.7  # Slightly higher for more human-like responses
            )
            
            return response.choices[0].message.content.strip()
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_individual_answer(self, question: str, answer: str, question_num: int) -> Dict:
        """Analyze a single question-answer pair"""
        prompt = f"""
You are a friendly technical interviewer giving quick, human feedback. 

Question {question_num}: {question}
Answer: {answer}

Give a brief, conversational analysis (max 200 words) covering:
- Technical accuracy (1-10)
- Key strengths (1-2 points)
- Areas to improve (1-2 points)
- Overall impression

Keep it friendly and constructive, like you're talking to a colleague.
"""
        
        response = self.query_openai(prompt)
        return {
            'question_num': question_num,
            'question': question,
            'answer': answer,
            'analysis': response
        }
    
    def get_overall_assessment(self, interview_data: Dict, individual_analyses: List[Dict]) -> Dict:
        """Get overall assessment and hiring recommendation"""
        
        # Prepare summary of all responses for overall evaluation
        summary = "Interview Summary:\n\n"
        for i, analysis in enumerate(individual_analyses, 1):
            summary += f"Q{i}: {analysis['question'][:80]}...\n"
            answer = analysis['answer']
            if answer is None:
                answer = "No answer"
            else:
                answer = str(answer)
            summary += f"Answer: {answer[:100]}...\n\n"
        
        prompt = f"""
You are a senior hiring manager giving final feedback to a candidate.

{summary}

Give a brief, human assessment (max 200 words) including:
- Overall technical competency (1-10)
- Hiring recommendation (HIRE/CONDITIONAL HIRE/DO NOT HIRE)
- 2-3 main strengths
- 2-3 areas to work on
- Final thoughts

Write like you're having a friendly conversation with the candidate.
"""
        
        response = self.query_openai(prompt)
        
        # Extract hiring decision from response
        hiring_decision = "CONDITIONAL HIRE"  # Default
        if "DO NOT HIRE" in response.upper():
            hiring_decision = "DO NOT HIRE"
        elif "HIRE" in response.upper() and "CONDITIONAL" not in response.upper():
            hiring_decision = "HIRE"
        
        return {
            'overall_analysis': response,
            'hiring_decision': hiring_decision,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def speak_text(self, text: str):
        """Convert text to speech"""
        try:
            print(f"\n🔊 Speaking: {text[:100]}...")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
    
    def format_results_for_speech(self, overall_assessment: Dict) -> str:
        """Format results in a speech-friendly manner"""
        decision = overall_assessment['hiring_decision']
        
        speech_text = f"""
Interview Analysis Complete. 

Hiring Decision: {decision}.

{overall_assessment['overall_analysis']}

Analysis completed on {overall_assessment['timestamp']}.
"""
        return speech_text
    
    def save_detailed_report(self, interview_data: Dict, individual_analyses: List[Dict], 
                           overall_assessment: Dict, output_file: str):
        """Save detailed analysis report to file"""
        report = {
            'session_info': {
                'session_id': interview_data.get('session_id', 'N/A'),
                'timestamp': interview_data.get('timestamp', 'N/A'),
                'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            'hiring_decision': overall_assessment['hiring_decision'],
            'individual_question_analyses': individual_analyses,
            'overall_assessment': overall_assessment,
            'summary': {
                'total_questions': len(individual_analyses),
                'questions_answered': interview_data.get('current_question', len(individual_analyses))
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed report saved to: {output_file}")
    
    def launch_talking_app(self):
        """Launch the talking app in a new process and open the browser"""
        try:
            # Get the absolute path to the talking app (in the same directory)
            talking_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'talking_app.py')
            
            # Launch the Flask app in a new process
            subprocess.Popen(['python', talking_app_path], 
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Wait a moment for the server to start
            time.sleep(2)
            
            # Open the browser to the talking app
            webbrowser.open('http://localhost:5001')
            
            return True
        except Exception as e:
            print(f"Error launching talking app: {e}")
            return False
    
    def analyze_interview(self, file_path: str, speak_results: bool = True) -> Dict:
        """Main method to analyze interview responses"""
        print("Starting Interview Analysis...")
        print("=" * 50)
        
        # Load interview data
        try:
            interview_data = self.load_interview_data(file_path)
            print(f"Loaded interview data for session: {interview_data.get('session_id', 'N/A')}")
        except Exception as e:
            print(f"Error loading interview data: {e}")
            return None
        
        # Analyze each question-answer pair
        individual_analyses = []
        questions = interview_data.get('questions', [])
        answers = interview_data.get('answers', [])
        
        print(f"\nAnalyzing {len(questions)} questions...")
        
        for i, (question, answer) in enumerate(zip(questions, answers), 1):
            print(f"\nAnalyzing Question {i}...")
            analysis = self.analyze_individual_answer(question, answer, i)
            individual_analyses.append(analysis)
            print(f"Question {i} analysis complete")
        
        # Get overall assessment
        print(f"\nGenerating overall assessment...")
        overall_assessment = self.get_overall_assessment(interview_data, individual_analyses)
        
        # Display results
        print("\n" + "=" * 50)
        print("INTERVIEW ANALYSIS RESULTS")
        print("=" * 50)
        print(f"HIRING DECISION: {overall_assessment['hiring_decision']}")
        print(f"Analysis Date: {overall_assessment['timestamp']}")
        print("\nDETAILED ASSESSMENT:")
        print(overall_assessment['overall_analysis'])
        
        # Save detailed report
        output_file = f"interview_analysis_{interview_data.get('session_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.save_detailed_report(interview_data, individual_analyses, overall_assessment, output_file)
        
        # Speak results if requested
        if speak_results:
            print("\nReading results aloud...")
            speech_text = self.format_results_for_speech(overall_assessment)
            self.speak_text(speech_text)
        
        # Note: Talking app launch removed - speech is now handled via Flask UI
        
        return {
            'interview_data': interview_data,
            'individual_analyses': individual_analyses,
            'overall_assessment': overall_assessment,
            'report_file': output_file
        }

app = Flask(__name__)

# HTML template for displaying results
RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Interview Analyzer Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f7f7f7; }
        .container { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #ccc; max-width: 800px; margin: auto; }
        h1 { color: #2c3e50; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 4px; }
        .success { color: green; }
        .error { color: red; }
        .btn { background: #3498db; color: #fff; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #217dbb; }
        .btn:disabled { background: #bdc3c7; cursor: not-allowed; }
        .speak-btn { background: #27ae60; }
        .speak-btn:hover { background: #229954; }
        .delete-btn { background: #e74c3c; }
        .delete-btn:hover { background: #c0392b; }
        .status { margin: 10px 0; padding: 10px; border-radius: 4px; }
        .status.success { background: #d5f4e6; color: #27ae60; }
        .status.error { background: #fadbd8; color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Interview Analyzer Results</h1>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% elif results %}
            <h2>Hiring Decision: <span class="success">{{ results['overall_assessment']['hiring_decision'] }}</span></h2>
            <h3>Overall Assessment</h3>
            <pre>{{ results['overall_assessment']['overall_analysis'] }}</pre>
            
            <div id="status"></div>
            
            <div class="button-group">
                <button class="btn speak-btn" onclick="speakResults()" id="speakBtn">
                    🔊 Speak Results
                </button>
                <form method="post" action="{{ url_for('cleanup') }}" style="display: inline;">
                    <button class="btn delete-btn" type="submit">🗑️ Delete All Files in shared_questions</button>
                </form>
            </div>
            
            <h3>Individual Question Analyses</h3>
            <ul>
            {% for analysis in results['individual_analyses'] %}
                <li>
                    <strong>Q{{ analysis['question_num'] }}: {{ analysis['question'] }}</strong><br>
                    <em>Answer:</em> {{ analysis['answer'] }}<br>
                    <em>Analysis:</em> {{ analysis['analysis'] }}
                </li>
            {% endfor %}
            </ul>
            <h3>Report File</h3>
            <pre>{{ results['report_file'] }}</pre>
        {% else %}
            <p class="error">No results available. Please try again.</p>
        {% endif %}
        <br><a href="/">&larr; Back to file selection</a>
    </div>
    
    {% if results %}
    <script>
        function speakResults() {
            const speakBtn = document.getElementById('speakBtn');
            const statusDiv = document.getElementById('status');
            
            // Disable button and show loading
            speakBtn.disabled = true;
            speakBtn.textContent = '🔊 Speaking...';
            statusDiv.innerHTML = '<div class="status">Speaking results...</div>';
            
            // Get the hiring decision and overall analysis
            const hiringDecision = '{{ results["overall_assessment"]["hiring_decision"] }}';
            const overallAnalysis = '{{ results["overall_assessment"]["overall_analysis"] }}';
            
            // Send request to speak results
            fetch('/speak_results', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `hiring_decision=${encodeURIComponent(hiringDecision)}&overall_analysis=${encodeURIComponent(overallAnalysis)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusDiv.innerHTML = '<div class="status success">✅ Results spoken successfully!</div>';
                } else {
                    statusDiv.innerHTML = '<div class="status error">❌ Error: ' + data.message + '</div>';
                }
            })
            .catch(error => {
                statusDiv.innerHTML = '<div class="status error">❌ Error: ' + error.message + '</div>';
            })
            .finally(() => {
                // Re-enable button
                speakBtn.disabled = false;
                speakBtn.textContent = '🔊 Speak Results';
            });
        }
    </script>
    {% endif %}
</body>
</html>
'''

SELECT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Select Interview File</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f7f7f7; }
        .container { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #ccc; max-width: 600px; margin: auto; }
        h1 { color: #2c3e50; }
        ul { list-style: none; padding: 0; }
        li { margin-bottom: 10px; }
        .btn { background: #3498db; color: #fff; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #217dbb; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Select Interview File</h1>
        {% if files %}
        <ul>
            {% for file in files %}
            <li>
                <form method="post" action="{{ url_for('analyze') }}">
                    <input type="hidden" name="filename" value="{{ file }}">
                    <button class="btn" type="submit">Analyze</button> {{ file }}
                </form>
            </li>
            {% endfor %}
        </ul>
        {% else %}
            <p>No JSON files found in shared_questions folder.</p>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    """Main route - redirect to analysis page"""
    return redirect(url_for('analysis'))

@app.route('/analysis')
def analysis():
    """Show the analysis page"""
    return render_template('analysis.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'interview_analyzer'})

@app.route('/auto_analyze', methods=['POST'])
def auto_analyze():
    """Automatically analyze the only file in shared_questions folder"""
    try:
        questions_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_questions")
        
        # Check if shared_questions folder exists
        if not os.path.exists(questions_folder):
            return jsonify({'error': 'shared_questions folder not found'})
        
        # Find JSON files in the folder
        json_files = [f for f in os.listdir(questions_folder) if f.endswith('.json')]
        
        if not json_files:
            return jsonify({'error': 'No JSON files found in shared_questions folder'})
        
        if len(json_files) > 1:
            return jsonify({'error': f'Multiple files found ({len(json_files)}). Please ensure only one file is in shared_questions folder.'})
        
        # Use the single JSON file found
        filename = json_files[0]
        file_path = os.path.join(questions_folder, filename)
        
        # Check if file exists and is readable
        if not os.path.exists(file_path):
            return jsonify({'error': f'File not found: {filename}'})
        
        # Run analysis
        analyzer = InterviewAnalyzer()
        results = analyzer.analyze_interview(file_path, speak_results=False)
        
        if results is None:
            return jsonify({'error': 'Analysis failed - no results returned'})
        
        return jsonify(results)
        
    except FileNotFoundError as e:
        return jsonify({'error': f'File not found: {str(e)}'})
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON format: {str(e)}'})
    except Exception as e:
        return jsonify({'error': f'Analysis error: {str(e)}'})

@app.route('/analyze', methods=['POST'])
def analyze():
    """Legacy analyze route - kept for compatibility"""
    filename = request.form.get('filename')
    questions_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_questions")
    file_path = os.path.join(questions_folder, filename)
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return render_template_string(RESULT_TEMPLATE, results=None, error=f"File not found: {filename}")
        
        analyzer = InterviewAnalyzer()
        results = analyzer.analyze_interview(file_path, speak_results=False)  # Don't auto-speak, let user control it
        
        if results is None:
            return render_template_string(RESULT_TEMPLATE, results=None, error="Analysis failed - no results returned")
        
        error = None
    except FileNotFoundError as e:
        error = f"File not found: {str(e)}"
        results = None
    except json.JSONDecodeError as e:
        error = f"Invalid JSON format in file: {str(e)}"
        results = None
    except Exception as e:
        error = f"Analysis error: {str(e)}"
        results = None
    
    return render_template_string(RESULT_TEMPLATE, results=results, error=error)

@app.route('/speak_results', methods=['POST'])
def speak_results():
    """Speak the analysis results"""
    try:
        # Get the results data from the form
        hiring_decision = request.form.get('hiring_decision', '')
        overall_analysis = request.form.get('overall_analysis', '')
        
        # Create analyzer instance and speak the results
        analyzer = InterviewAnalyzer()
        speech_text = f"Interview Analysis Complete. Hiring Decision: {hiring_decision}. {overall_analysis}"
        analyzer.speak_text(speech_text)
        
        return jsonify({'status': 'success', 'message': 'Results spoken successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup():
    questions_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_questions")
    for f in os.listdir(questions_folder):
        file_path = os.path.join(questions_folder, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
    return redirect(url_for('index'))

def main():
    """Main function to run the interview analyzer"""
    # Configuration - use absolute path based on current file location
    QUESTIONS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_questions")
    
    # Initialize analyzer
    analyzer = InterviewAnalyzer()
    
    # Auto-detect JSON files in the questions folder
    if not os.path.exists(QUESTIONS_FOLDER):
        os.makedirs(QUESTIONS_FOLDER)
        print(f"📁 Created '{QUESTIONS_FOLDER}' folder")
        print("Please place your interview JSON file in this folder and run again")
        return
    
    # Find JSON files in the questions folder
    json_files = [f for f in os.listdir(QUESTIONS_FOLDER) if f.endswith('.json')]
    
    if not json_files:
        print(f"❌ No JSON files found in '{QUESTIONS_FOLDER}' folder")
        print("Please place your interview JSON file in the 'questions' folder")
        print("Supported format: any .json file with questions and answers")
        return
    
    if len(json_files) == 1:
        # Use the single JSON file found
        interview_file = json_files[0]
        file_path = os.path.join(QUESTIONS_FOLDER, interview_file)
        print(f"📁 Found interview file: {interview_file}")
    else:
        # Multiple JSON files found, let user choose
        print(f"📁 Found {len(json_files)} JSON files in '{QUESTIONS_FOLDER}':")
        for i, file in enumerate(json_files, 1):
            print(f"  {i}. {file}")
        
        try:
            choice = input("\nEnter the number of the file to analyze (or press Enter for the first one): ").strip()
            if choice == "":
                interview_file = json_files[0]
            else:
                index = int(choice) - 1
                if 0 <= index < len(json_files):
                    interview_file = json_files[index]
                else:
                    print("❌ Invalid selection. Using the first file.")
                    interview_file = json_files[0]
        except ValueError:
            print("❌ Invalid input. Using the first file.")
            interview_file = json_files[0]
        
        file_path = os.path.join(QUESTIONS_FOLDER, interview_file)
        print(f"📁 Selected file: {interview_file}")
    
    # Check if file exists (should exist since we found it, but double-check)
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("Please ensure your interview JSON file is in the 'questions' folder")
        return
    
    # Run analysis
    try:
        results = analyzer.analyze_interview(file_path, speak_results=True)
        
        if results:
            print(f"\n🎉 Analysis completed successfully!")
            print(f"📄 Detailed report: {results['report_file']}")
            
            # Quick summary
            decision = results['overall_assessment']['hiring_decision']
            if decision == "HIRE":
                print("✅ Recommendation: HIRE - Candidate shows strong technical competency")
            elif decision == "CONDITIONAL HIRE":
                print("⚠️ Recommendation: CONDITIONAL HIRE - Candidate needs some development")
            else:
                print("❌ Recommendation: DO NOT HIRE - Candidate needs significant improvement")
                
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        main()
    else:
        app.run(debug=True, port=5002)