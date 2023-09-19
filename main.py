import streamlit as st
from agents.sql_agent_factory import agent_factory
from streamlit_chat import message
class ChatHistory:
    
    def __init__(self):
        self.history = st.session_state.get("history", [])
        st.session_state["history"] = self.history

    def default_greeting(self):
        return "Welcome to Q-STOCK BOT, How can I help you?"

    def initialize_user_history(self):
        if "user" not in st.session_state:
            st.session_state["user"] = []

    def initialize_assistant_history(self):
        if "assistant" not in st.session_state:
            st.session_state["assistant"] = [self.default_greeting()]

    def initialize(self):
        self.initialize_user_history()
        self.initialize_assistant_history()

    def append(self, mode, message):
        st.session_state[mode].append(message)
    def generate_messages(self, container):
        if st.session_state["assistant"]:
            with container:
                for i in range(len(st.session_state["assistant"])):
                    if i < len(st.session_state["user"]):
                        message(
                            st.session_state["user"][i],
                            is_user=True,
                            key=f"history_{i}_user",
                            avatar_style="big-smile",
                        )
                    message(st.session_state["assistant"][i], key=str(i), avatar_style="thumbs")
def chat_interface():
    # Instantiate the ChatHistory class
    history = ChatHistory()

    # Initialize chat history
    history.initialize()

    # Create containers for chat responses and user prompts
    response_container, prompt_container = st.container(), st.container()

    # Display the initial greeting from the chatbot
    with response_container:
        message(st.session_state["assistant"][0], key="initial_greeting", avatar_style="thumbs")

    # Display the prompt form
    user_input = st.text_input("You: ", "")


    # Wait for user's input
    try:
        if user_input:
            if user_input.lower() == 'exit':
                st.write("Goodbye!")
            else:
                agent_executor = agent_factory()  # Assuming you've set up agent_factory from your previous code
                result = agent_executor.run(user_input)

                # Determine the type of response message based on user query
                if any(word in user_input.lower() for word in ["what", "where", "how", "when"]):
                    response_msg = "Based on your query, here's the response:\n"
                else:
                    response_msg = "Here's the information you requested:\n"

                if not result:  # If there's no result, adjust the response message
                    response_msg = "Sorry, I couldn't find any answer based on your query."
                else:
                    response_msg += result  # Append the result to the response message

                # Update the chat history
                history.append("user", user_input)
                history.append("assistant", response_msg)

                with response_container:
                    # Display the chat messages excluding the initial greeting
                    for i in range(1, len(st.session_state["assistant"])):
                        message(st.session_state["user"][i-1], is_user=True, key=f"history_{i-1}_user", avatar_style="big-smile")
                        message(st.session_state["assistant"][i], key=str(i), avatar_style="thumbs")
    except Exception as e:
        st.write(f"Error: {str(e)}")

    # Any other UI elements or functionality can go here

if __name__ == "__main__":
    chat_interface()
