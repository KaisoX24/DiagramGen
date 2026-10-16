class UserOptChoice:
    def __init__(self):
        pass

    def _select_provider():
        "Prompts the user for the Model Provider"
        providers={
            1:"openai",
            2:"google_genai",
            3:"anthropic",
            4:"ollama"
        }
        while True:
            try:
                opt = int(input("Model Provider:\n1. OpenAi\n2. Gemini\n3. Anthropic\n4. Ollama (Local)\n(1/4): "))
                if opt in providers:
                    print(f"Using {providers[opt]} as model provider")
                    return providers[opt]
                print("Please select a valid option.")
            except ValueError:
                print("Please enter a number.")

    def _select_model(provider:str):
        "Prompts the user for the Model to use"
        while True:
            model = input(f"Which {provider} Model you want to use: ")
            if not model:
                print("Please Provide Valid Model Name")
                continue
            print(f"Using {model} for the Generation")
            return model
        