import streamlit as st
from travelbuddy import TravelBuddy

st.title("🧳 TravelBuddy")
st.caption("Your enthusiastic weekend-getaway planner")

if "bot" not in st.session_state:
    st.session_state.bot = TravelBuddy()
    st.session_state.messages = [("assistant", st.session_state.bot.start())]

for role, text in st.session_state.messages:
    st.chat_message(role).write(text)

if prompt := st.chat_input("Type your answer..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append(("user", prompt))
    reply = st.session_state.bot.respond(prompt)
    st.chat_message("assistant").write(reply)
    st.session_state.messages.append(("assistant", reply))