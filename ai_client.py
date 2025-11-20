import time
import google.generativeai as genai
import config

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(config.AI_MODEL_NAME)
        
        # FIX: We now use a single variable, not a list
        self.active_file = None 
        self.file_type = None   # "video" or "image"

    def upload_context(self, file_path):
        """
        Smartly uploads either a video or an image based on the file extension.
        """
        print(f"   [Cloud] Start Upload: {file_path}")
        
        # Upload the single file
        uploaded_file = genai.upload_file(path=file_path)
        
        # Check if it is a video (requires processing wait)
        if "video" in uploaded_file.mime_type:
            self.file_type = "video"
            print("   [Cloud] Processing Video...")
            
            # Wait loop
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise ValueError("Video processing failed.")
        else:
            self.file_type = "image"
            print("   [Cloud] Image Uploaded.")

        # FIX: Store into self.active_file (singular)
        self.active_file = uploaded_file
        print("   [Cloud] Context Ready.")
        return True

    def ask_question(self, user_prompt):
        # FIX: Check self.active_file (not active_context_files)
        if not self.active_file:
            raise ValueError("No context uploaded yet!")

        # Dynamic System Prompt based on file type
        context_desc = "Video of user activity" if self.file_type == "video" else "Screenshot of user screen"
        
        prompt = f"""
        You are an Expert Software Mentor.
        
        INPUT CONTEXT:
        1. **{context_desc}**: Analyze this strictly.
        2. **User Question**: "{user_prompt}"
        
        TASK:
        Identify the issue visible in the {self.file_type} and provide a step-by-step solution.
        """
        
        # FIX: Pass self.active_file in the list
        response = self.model.generate_content([self.active_file, prompt])
        return response.text