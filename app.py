import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import random
import requests
from abacusai import ApiClient

api_key = 's2_e27c9419392d4b6699f252fcbe38aed7'
client = ApiClient(api_key)

client.list_use_cases()

class AbacusAIService:
    def __init__(self):
        self.api_key = "s2_e27c9419392d4b6699f252fcbe38aed7"
        self.base_url = "https://api.abacus.ai/api/v0"
        self.headers = {
            "apiKey": self.api_key
        }

    def list_projects(self):
        try:
            response = requests.get(
                f"{self.base_url}/listProjects",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error accessing Abacus AI: {e}")
            return None

    def get_project_details(self, project_id):
        try:
            response = requests.get(
                f"{self.base_url}/getProject",
                headers=self.headers,
                params={"projectId": project_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error getting project details: {e}")
            return None

    def make_prediction(self, project_id, input_data):
        try:
            response = requests.post(
                f"{self.base_url}/predict",
                headers=self.headers,
                json={
                    "projectId": project_id,
                    "data": input_data
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error making prediction: {e}")
            return None

# Initialize session state variables
if 'seats' not in st.session_state:
    rows = 10
    cols = 6
    st.session_state.seats = {
        f"{row}{chr(65+col)}": {
            "status": "available",
            "reservation_time": None,
            "reserved_by": None,
            "price": random.uniform(100, 200)
        } for row in range(1, rows + 1) for col in range(cols)
    }

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(random.randint(1000, 9999))

if 'reservations' not in st.session_state:
    st.session_state.reservations = []

if 'abacus_ai' not in st.session_state:
    st.session_state.abacus_ai = AbacusAIService()

def check_expired_reservations():
    current_time = datetime.now()
    for seat_id, seat_info in st.session_state.seats.items():
        if (seat_info["status"] == "reserved" and
            seat_info["reservation_time"] and
            (current_time - seat_info["reservation_time"]).total_seconds() > 900):
            seat_info["status"] = "available"
            seat_info["reservation_time"] = None
            seat_info["reserved_by"] = None

def get_seat_color(status):
    if status == "available":
        return "#90EE90"
    elif status == "reserved":
        return "#FFD700"
    else:
        return "#FF6B6B"

def create_seat_map():
    cols = st.columns(6)

    for seat_id, seat_info in st.session_state.seats.items():
        col_idx = ord(seat_id[-1]) - 65
        with cols[col_idx]:
            button_color = get_seat_color(seat_info["status"])
            if st.button(
                f"{seat_id}\n${seat_info['price']:.2f}",
                key=seat_id,
                help=f"Status: {seat_info['status']}",
                type="primary" if seat_info["status"] == "available" else "secondary"
            ):
                handle_seat_click(seat_id, seat_info)

def handle_seat_click(seat_id, seat_info):
    if seat_info["status"] != "available":
        st.error(f"Seat {seat_id} is not available!")
        return

    if st.session_state.seats[seat_id]["status"] == "available":
        st.session_state.seats[seat_id]["status"] = "reserved"
        st.session_state.seats[seat_id]["reservation_time"] = datetime.now()
        st.session_state.seats[seat_id]["reserved_by"] = st.session_state.user_id
        st.session_state.reservations.append(seat_id)
        st.success(f"Seat {seat_id} has been reserved! You have 15 minutes to complete the purchase.")
        st.rerun()

def purchase_seat(seat_id):
    if st.session_state.seats[seat_id]["reserved_by"] != st.session_state.user_id:
        st.error("This seat is not reserved by you!")
        return

    st.session_state.seats[seat_id]["status"] = "purchased"
    st.session_state.seats[seat_id]["reservation_time"] = None
    st.session_state.reservations.remove(seat_id)
    st.success(f"Seat {seat_id} has been purchased successfully!")
    st.rerun()

def cancel_reservation(seat_id):
    if st.session_state.seats[seat_id]["reserved_by"] != st.session_state.user_id:
        st.error("This seat is not reserved by you!")
        return

    st.session_state.seats[seat_id]["status"] = "available"
    st.session_state.seats[seat_id]["reservation_time"] = None
    st.session_state.seats[seat_id]["reserved_by"] = None
    st.session_state.reservations.remove(seat_id)
    st.success(f"Reservation for seat {seat_id} has been cancelled.")
    st.rerun()

def show_abacus_projects():
    st.sidebar.subheader("Abacus AI Integration")

    projects = st.session_state.abacus_ai.list_projects()
    if projects:
        project_names = [project['name'] for project in projects.get('projects', [])]
        selected_project = st.sidebar.selectbox("Select AI Model", project_names)

        if selected_project:
            project_id = next(
                project['id'] for project in projects['projects']
                if project['name'] == selected_project
            )
            st.session_state.current_project_id = project_id

            with st.sidebar.expander("Model Details"):
                details = st.session_state.abacus_ai.get_project_details(project_id)
                if details:
                    st.json(details)

def get_ai_recommendation(preferences):
    if hasattr(st.session_state, 'current_project_id'):
        input_data = {
            "window_seat": preferences["window"],
            "aisle_seat": preferences["aisle"],
            "front_section": preferences["front"],
            "price_range": preferences["price_range"]
        }

        prediction = st.session_state.abacus_ai.make_prediction(
            st.session_state.current_project_id,
            input_data
        )

        if prediction:
            return prediction
    return None

def main():
    st.title("✈️ Airplane Seat Reservation System with Abacus AI")

    # Show Abacus AI projects in sidebar
    show_abacus_projects()

    # Check expired reservations
    check_expired_reservations()

    # User ID display
    st.sidebar.write(f"Your User ID: {st.session_state.user_id}")

    # Seat preferences
    st.sidebar.subheader("Seat Preferences")
    preferences = {
        "window": st.sidebar.checkbox("Window Seat"),
        "aisle": st.sidebar.checkbox("Aisle Seat"),
        "front": st.sidebar.checkbox("Front Section"),
        "price_range": st.sidebar.slider(
            "Select Price Range",
            min_value=100.0,
            max_value=200.0,
            value=(100.0, 200.0),
            step=10.0
        )
    }

    if st.sidebar.button("Get AI Recommendations"):
        recommendations = get_ai_recommendation(preferences)
        if recommendations:
            st.sidebar.json(recommendations)

    # Main content
    st.subheader("Seat Map")
    st.write("Click on a seat to make a reservation")

    # Display seat map
    create_seat_map()

    # Legend
    st.write("\n")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟩 Available")
    with col2:
        st.markdown("🟨 Reserved")
    with col3:
        st.markdown("🟥 Purchased")

    # Show user's reservations
    if st.session_state.reservations:
        st.subheader("Your Current Reservations")
        for seat_id in st.session_state.reservations:
            col1, col2, col3 = st.columns([3,1,1])
            with col1:
                st.write(f"Seat {seat_id} - ${st.session_state.seats[seat_id]['price']:.2f}")
            with col2:
                if st.button("Purchase", key=f"purchase_{seat_id}"):
                    purchase_seat(seat_id)
            with col3:
                if st.button("Cancel", key=f"cancel_{seat_id}"):
                    cancel_reservation(seat_id)

    # Statistics
    st.subheader("Current Statistics")
    available = sum(1 for seat in st.session_state.seats.values() if seat["status"] == "available")
    reserved = sum(1 for seat in st.session_state.seats.values() if seat["status"] == "reserved")
    purchased = sum(1 for seat in st.session_state.seats.values() if seat["status"] == "purchased")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Available Seats", available)
    with col2:
        st.metric("Reserved Seats", reserved)
    with col3:
        st.metric("Purchased Seats", purchased)

if __name__ == "__main__":
    main()
