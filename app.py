import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from utils.data_manager import DataManager
from utils.notifications import NotificationManager
from utils.analytics import AnalyticsManager

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.user_profile = {}
    st.session_state.expenses = []
    st.session_state.groups = []
    st.session_state.badges = []

# Initialize managers
data_manager = DataManager()
notification_manager = NotificationManager()
analytics_manager = AnalyticsManager()

def main():
    st.set_page_config(
        page_title="AI Expense Tracker",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load user data
    data_manager.load_user_data()
    
    # Check if user needs onboarding
    if not st.session_state.initialized or not st.session_state.user_profile:
        show_onboarding()
    else:
        show_main_app()

def show_onboarding():
    st.title("🎓 Welcome to AI Expense Tracker")
    st.markdown("### Let's set up your personalized expense tracking!")
    
    with st.form("onboarding_form"):
        st.subheader("Personal Information")
        name = st.text_input("Your Name", placeholder="Enter your name")
        
        st.subheader("Financial Goals")
        daily_limit = st.number_input("Daily Spending Limit (₹)", min_value=100, max_value=10000, value=500, step=50)
        
        savings_goal_amount = st.number_input("Savings Goal Amount (₹)", min_value=1000, max_value=1000000, value=10000, step=1000)
        savings_goal_reason = st.text_input("What are you saving for?", placeholder="e.g., New laptop, Trip, Emergency fund")
        
        st.subheader("Preferences")
        preferred_categories = st.multiselect(
            "Select your main spending categories:",
            ["Groceries", "Fast Food", "Transportation", "Entertainment", "Education", "Clothes", "Health", "Other"],
            default=["Groceries", "Fast Food", "Transportation", "Entertainment"]
        )
        
        alert_threshold = st.slider("Alert when daily spending reaches (% of limit):", 50, 90, 80)
        
        submitted = st.form_submit_button("Start Tracking! 🚀", use_container_width=True)
        
        if submitted and name:
            # Save user profile
            st.session_state.user_profile = {
                "name": name,
                "daily_limit": daily_limit,
                "savings_goal_amount": savings_goal_amount,
                "savings_goal_reason": savings_goal_reason,
                "preferred_categories": preferred_categories,
                "alert_threshold": alert_threshold,
                "created_date": datetime.now().isoformat(),
                "total_saved": 0
            }
            st.session_state.initialized = True
            data_manager.save_user_data()
            st.success("Profile created successfully! 🎉")
            st.rerun()

def show_main_app():
    # Sidebar
    with st.sidebar:
        st.title("💰 AI Expense Tracker")
        st.write(f"Welcome back, {st.session_state.user_profile['name']}! 👋")
        
        # Daily summary
        today = datetime.now().date()
        today_expenses = [exp for exp in st.session_state.expenses 
                         if datetime.fromisoformat(exp['date']).date() == today]
        today_spent = sum(exp['amount'] for exp in today_expenses)
        daily_limit = st.session_state.user_profile['daily_limit']
        remaining = daily_limit - today_spent
        
        st.metric("Today's Spending", f"₹{today_spent:.2f}", f"₹{remaining:.2f} remaining")
        
        # Progress bar
        progress = min(today_spent / daily_limit, 1.0)
        st.progress(progress)
        
        # Quick stats
        st.subheader("Quick Stats")
        total_expenses = len(st.session_state.expenses)
        st.write(f"📊 Total Transactions: {total_expenses}")
        
        if st.session_state.expenses:
            avg_daily = sum(exp['amount'] for exp in st.session_state.expenses) / max(len(set(datetime.fromisoformat(exp['date']).date() for exp in st.session_state.expenses)), 1)
            st.write(f"📈 Avg Daily Spend: ₹{avg_daily:.2f}")
        
        # Savings goal progress
        savings_progress = st.session_state.user_profile.get('total_saved', 0) / st.session_state.user_profile['savings_goal_amount']
        st.subheader("Savings Goal")
        st.progress(min(savings_progress, 1.0))
        st.write(f"₹{st.session_state.user_profile.get('total_saved', 0):.2f} / ₹{st.session_state.user_profile['savings_goal_amount']:.2f}")
        st.write(f"Goal: {st.session_state.user_profile['savings_goal_reason']}")

    # Main content
    st.title("📊 Dashboard Overview")
    
    # Show notifications
    notification_manager.show_daily_alerts()
    notification_manager.show_motivational_messages()
    
    # Quick add expense
    with st.expander("➕ Quick Add Expense", expanded=False):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            quick_description = st.text_input("Description", placeholder="What did you buy?", key="quick_desc")
        with col2:
            quick_amount = st.number_input("Amount (₹)", min_value=0.01, value=100.0, key="quick_amount")
        with col3:
            if st.button("Add Expense", use_container_width=True):
                if quick_description and quick_amount > 0:
                    from utils.categorization import ExpenseCategorizer
                    categorizer = ExpenseCategorizer()
                    category = categorizer.categorize_expense(quick_description, quick_amount)
                    
                    new_expense = {
                        "id": len(st.session_state.expenses) + 1,
                        "date": datetime.now().isoformat(),
                        "description": quick_description,
                        "amount": quick_amount,
                        "category": category,
                        "type": "manual"
                    }
                    st.session_state.expenses.append(new_expense)
                    data_manager.save_user_data()
                    st.success(f"Added ₹{quick_amount:.2f} expense for {category}")
                    st.rerun()

    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Today's Budget", f"₹{daily_limit}", f"₹{remaining:.2f} left")
    
    with col2:
        weekly_expenses = [exp for exp in st.session_state.expenses 
                          if datetime.fromisoformat(exp['date']).date() >= today - timedelta(days=7)]
        weekly_spent = sum(exp['amount'] for exp in weekly_expenses)
        st.metric("This Week", f"₹{weekly_spent:.2f}")
    
    with col3:
        monthly_expenses = [exp for exp in st.session_state.expenses 
                           if datetime.fromisoformat(exp['date']).date() >= today - timedelta(days=30)]
        monthly_spent = sum(exp['amount'] for exp in monthly_expenses)
        st.metric("This Month", f"₹{monthly_spent:.2f}")
    
    with col4:
        badges_count = len(st.session_state.badges)
        st.metric("Badges Earned", badges_count, "🏆")

    # Recent transactions
    if st.session_state.expenses:
        st.subheader("Recent Transactions")
        recent_expenses = sorted(st.session_state.expenses, key=lambda x: x['date'], reverse=True)[:5]
        
        for exp in recent_expenses:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{exp['description']}**")
            with col2:
                st.write(f"₹{exp['amount']:.2f}")
            with col3:
                st.write(exp['category'])
            with col4:
                date_obj = datetime.fromisoformat(exp['date'])
                st.write(date_obj.strftime("%m/%d"))
    else:
        st.info("No expenses recorded yet. Add your first expense using the form above!")

if __name__ == "__main__":
    main()
