from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import glob
from gtts import gTTS
import pygame
import speech_recognition as sr
import tempfile
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Configure shared questions folder - use absolute path based on current file location
QUESTIONS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_questions")
os.makedirs(QUESTIONS_FOLDER, exist_ok=True)

class TalkingChatbot:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        pygame.mixer.init()
        
        # Try to initialize microphone, but don't fail if it's not available
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            print("Microphone initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize microphone: {e}")
            print("Voice recognition features may not work properly")
    
    def speak_text(self, text):
        """Convert text to speech and play it"""
        try:
            # Clean the text for TTS (remove markdown formatting)
            clean_text = self.clean_text_for_speech(text)
            
            tts = gTTS(text=clean_text, lang='en', slow=False)
            
            # Create temp directory if it doesn't exist
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create a unique filename
            temp_filename = f"tts_{int(time.time() * 1000)}.mp3"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Save TTS audio to file
            tts.save(temp_path)
            
            # Verify file exists before playing
            if not os.path.exists(temp_path):
                raise Exception(f"TTS file was not created: {temp_path}")
            
            # Play the audio
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up - ensure pygame is completely done
            pygame.mixer.music.unload()  # Explicitly unload the music
            time.sleep(1.0)  # Give more time for pygame to release the file
            
            # Try to delete the file with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        break
                except Exception as cleanup_error:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Warning: Could not delete temp file {temp_path} after {max_retries} attempts: {cleanup_error}")
                    else:
                        time.sleep(0.5)  # Wait before retrying
                
            return True
            
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return False
    
    def clean_text_for_speech(self, text):
        """Clean text for better speech synthesis"""
        # Remove markdown formatting
        clean_text = text.replace('**', '')
        clean_text = clean_text.replace('*', '')
        clean_text = clean_text.replace('_', '')
        
        # Remove question numbers if present
        lines = clean_text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('1.', '2.', '3.', '4.', '5.')):
                cleaned_lines.append(line)
            elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                # Remove the number and clean up
                cleaned_lines.append(line[2:].strip())
        
        return ' '.join(cleaned_lines)
    
    def listen_for_response(self, timeout=30):
        """Listen for user's spoken response"""
        if self.microphone is None:
            print("Microphone not available - cannot listen for response")
            return "MICROPHONE_NOT_AVAILABLE"
            
        try:
            with self.microphone as source:
                print("Listening for response...")
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=60)
                
            # Recognize speech
            response = self.recognizer.recognize_google(audio)
            print(f"User said: {response}")
            return response
            
        except sr.WaitTimeoutError:
            return "TIMEOUT"
        except sr.UnknownValueError:
            return "UNKNOWN"
        except sr.RequestError as e:
            print(f"Error with speech recognition: {e}")
            return "ERROR"

# Global chatbot instance
chatbot = TalkingChatbot()

@app.route('/')
def index():
    return render_template('talking_index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'talking_app'})

@app.route('/api/load_questions')
def load_questions():
    """Load available question files"""
    try:
        question_files = glob.glob(os.path.join(QUESTIONS_FOLDER, '*.json'))
        files_info = []
        
        for file_path in question_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                files_info.append({
                    'filename': os.path.basename(file_path),
                    'session_id': data.get('session_id', 'Unknown'),
                    'timestamp': data.get('timestamp', 'Unknown'),
                    'total_questions': len(data.get('questions', [])),
                    'current_question': data.get('current_question', 0)
                })
        
        return jsonify({'files': files_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/start_session/<filename>')
def start_session(filename):
    """Start a question session with a specific file"""
    try:
        file_path = os.path.join(QUESTIONS_FOLDER, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        current_q = data.get('current_question', 0)
        
        if current_q >= len(data['questions']):
            return jsonify({
                'status': 'completed',
                'message': 'All questions have been answered!'
            })
        
        return jsonify({
            'status': 'ready',
            'session_data': data,
            'current_question_index': current_q,
            'current_question': data['questions'][current_q],
            'total_questions': len(data['questions'])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/speak_question', methods=['POST'])
def speak_question():
    """Speak the current question"""
    try:
        data = request.json
        question_text = data.get('question', '')
        
        # Speak the question in a separate thread to avoid blocking
        def speak_async():
            success = chatbot.speak_text(question_text)
            if not success:
                print("Failed to speak question")
        
        thread = threading.Thread(target=speak_async)
        thread.start()
        
        return jsonify({'status': 'speaking'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/listen_response', methods=['POST'])
def listen_response():
    """Listen for user's response"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        timeout = data.get('timeout', 30)
        filename = data.get('filename')  # Get the filename from the request
        question_index = data.get('question_index')  # Get the question index
        
        if not all([filename, question_index is not None]):
            return jsonify({'error': 'Missing filename or question_index'}), 400
        
        # Listen for response
        response = chatbot.listen_for_response(timeout=timeout)
        
        # Immediately save the response to avoid losing it
        if response not in ['TIMEOUT', 'UNKNOWN', 'ERROR']:
            try:
                file_path = os.path.join(QUESTIONS_FOLDER, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Create answer data
                answer_data = {
                    'text': response,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'type': 'voice_response',
                    'status': 'success'
                }
                
                # Update answer
                session_data['answers'][question_index] = answer_data
                session_data['current_question'] = question_index + 1
                
                # Save updated data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                    
            except Exception as save_error:
                print(f"Error saving response: {save_error}")
                # Continue even if save fails, we'll return the response anyway
        
        return jsonify({
            'response': response,
            'status': 'success' if response not in ['TIMEOUT', 'UNKNOWN', 'ERROR'] else 'failed',
            'filename': filename,
            'question_index': question_index
        })
        
    except Exception as e:
        print(f"Error in listen_response: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_answer', methods=['POST'])
def save_answer():
    """Save user's answer to the questions file (fallback for when immediate save fails)"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        filename = data.get('filename')
        question_index = data.get('question_index')
        answer = data.get('answer')
        
        print(f"Save answer request data: {data}")  # Debug log
        
        if not all([filename, question_index is not None, answer]):
            missing = []
            if not filename: missing.append('filename')
            if question_index is None: missing.append('question_index')
            if not answer: missing.append('answer')
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing)}',
                'received_data': data
            }), 400
        
        file_path = os.path.join(QUESTIONS_FOLDER, filename)
        
        # Load current data
        with open(file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Create answer data
        answer_data = {
            'text': answer,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'voice_response',
            'status': 'success'
        }
        
        # Update answer
        session_data['answers'][question_index] = answer_data
        session_data['current_question'] = question_index + 1
        
        # Save updated data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Check if there are more questions
        if session_data['current_question'] >= len(session_data['questions']):
            return jsonify({
                'status': 'completed',
                'message': 'All questions completed! Great job!'
            })
        
        next_question = session_data['questions'][session_data['current_question']]
        
        return jsonify({
            'status': 'next_question',
            'next_question': next_question,
            'current_index': session_data['current_question'],
            'total_questions': len(session_data['questions'])
        })
        
    except Exception as e:
        print(f"Error saving answer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/skip_question', methods=['POST'])
def skip_question():
    """Skip to the next question"""
    try:
        data = request.json
        filename = data.get('filename')
        question_index = data.get('question_index')
        
        if not all([filename, question_index is not None]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        file_path = os.path.join(QUESTIONS_FOLDER, filename)
        
        # Load current data
        with open(file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # Create a structured skip record
        skip_data = {
            'text': 'SKIPPED',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'type': 'skipped',
            'status': 'skipped'
        }
        
        # Update answer and move to next
        session_data['answers'][question_index] = skip_data
        session_data['current_question'] = question_index + 1
        
        # Save updated data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Check if there are more questions
        if session_data['current_question'] >= len(session_data['questions']):
            return jsonify({
                'status': 'completed',
                'message': 'All questions completed!'
            })
        
        next_question = session_data['questions'][session_data['current_question']]
        
        return jsonify({
            'status': 'next_question',
            'next_question': next_question,
            'current_index': session_data['current_question'],
            'total_questions': len(session_data['questions'])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create questions directory if it doesn't exist
    os.makedirs(QUESTIONS_FOLDER, exist_ok=True)
    
    print("Starting Talking Chatbot...")
    print("Make sure you have a microphone connected and permissions granted.")
    app.run(host='0.0.0.0', port=5001, debug=True)