import google.generativeai as genai
import config
from PIL import Image
import time

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(config.AI_MODEL_NAME)
        self.chat_session = None
        self.uploaded_files = []

    def upload_context(self, video_path, drawing_path):
        self.uploaded_files = []

        # 1. Upload Video (if exists)
        if video_path:
            print(f"   [Cloud] Start Upload: {video_path}")
            video_file = genai.upload_file(path=video_path)
            
            while video_file.state.name == "PROCESSING":
                time.sleep(1)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                raise ValueError("Video processing failed.")
            self.uploaded_files.append(video_file)
        
        # 2. Upload Drawing
        print("   [Cloud] Uploading Drawing...")
        drawing_file = genai.upload_file(path=drawing_path)
        self.uploaded_files.append(drawing_file)
        
        # 3. Init Chat Session
        history = [
            {
                "role": "user",
                "parts": self.uploaded_files + ["Analyze this context. Wait for my question."]
            },
            {
                "role": "model",
                "parts": ["I have analyzed the video and drawing. I am ready to help. What is your question?"]
            }
        ]
        self.chat_session = self.model.start_chat(history=history)
        print("   [Cloud] Chat Session Ready.")
        return True

    def ask_question(self, user_prompt):
        if not self.chat_session:
            raise ValueError("No context uploaded.")
        print("   [Cloud] Sending Prompt...")
        response = self.chat_session.send_message(user_prompt)
        return response.text
    
    def clear_session(self):
        self.chat_session = None
        self.uploaded_files = []