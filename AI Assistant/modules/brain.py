class Brain:
    def think(self, text_input):
        # Simple logic for conversation
        if "hello" in text_input.lower():
            return "Hi there! I am your AI assistant."
        elif "time" in text_input.lower():
            return "I am not a clock, but it is time to code!"
        else:
            return "I heard you, but I don't know that command yet."