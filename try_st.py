import streamlit as st
from io import StringIO
import base64

send_image = st.file_uploader("Choose a file")
if send_image:
    file_bytestream = send_image.getvalue()
    base64_encoded = base64.b64encode(file_bytestream).decode("utf-8")
    st.write(base64_encoded)