import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar
from collections import defaultdict
from mongodb1 import *

def main_layout():
    """
    Main layout for the Performance section
    Displays student performance analytics and visualizations
    """
    st.subheader("📊 My Performance Dashboard", divider="orange", text_alignment="center")
    
    # Check if user is logged in
    if "roll_number" not in st.session_state or not st.session_state["roll_number"]:
        st.warning("⚠️ Please log in to view performance data")
        return
    
    # Fetch student data
    student_data = fetch_student_data()
    if not student_data:
        st.info("ℹ️ No performance data available yet. Start learning and saving your progress!")
        return
    
    # Create two columns
    col1, col2 = st.columns([1, 2], border=True, gap="small")
    
    # Column 1: Navigation and general info
    with col1:
        st.subheader("📋 Navigation", divider="blue")
        
        # Radio options
        view_option = st.radio(
            "Select View",
            ["📌 General Overview", "📈 Advanced Statistics"],
            key="performance_view"
        )
        
        # Display student info in sidebar style
        st.subheader("👤 Student Profile", divider="blue")
        with st.container(border=True):
            st.write(f"**📛 Name:** {st.session_state.get('student_name', 'N/A')}")
            st.write(f"**🎯 Roll Number:** {st.session_state.get('roll_number', 'N/A')}")
            st.write(f"**📚 Course:** {st.session_state.get('subject', 'N/A')}")
            st.write(f"**🏛️ Department:** {st.session_state.get('department', 'N/A')}")
            st.write(f"**📅 Batch:** {st.session_state.get('year', 'N/A')}")
        
        # Quick stats
        if student_data:
            st.subheader("⚡ Quick Stats", divider="blue")
            with st.container(border=True):
                total_sessions = sum(len(entry.get("study_time", [])) for entry in student_data.get("track", []))
                total_days = len(student_data.get("track", []))
                total_study_time = calculate_total_study_time(student_data)
                
                st.metric("📅 Active Days", total_days)
                st.metric("🔄 Total Sessions", total_sessions)
                st.metric("⏱️ Total Study Time", format_time(total_study_time))
    
    # Column 2: Content display
    with col2:
        if view_option == "📌 General Overview":
            display_general_overview(student_data)
        else:
            display_advanced_stats(student_data)

def fetch_student_data():
    """
    Fetch the current student's data from the database
    """
    try:
        collection = st.session_state.get("collection")
        if collection is None:
            return None
        
        student_roll = st.session_state.get("roll_number")
        
        # Query the database
        course_data = collection.find_one({
            "academicYear": st.session_state.get("year"),
            "department": st.session_state.get("department"),
            "courseName": st.session_state.get("subject"),
            "enrolledStudents.student_roll_number": student_roll
        })
        
        if not course_data:
            return None
        
        # Find the student
        for student in course_data.get("enrolledStudents", []):
            if student.get("student_roll_number") == student_roll:
                return student
        
        return None
    except Exception as e:
        st.error(f"❌ Error fetching data: {str(e)}")
        return None

def calculate_session_duration(session_str):
    """
    Calculate duration of a session in seconds
    """
    try:
        if " - " in session_str:
            parts = session_str.split(" - ")
            if len(parts) == 2:
                login_time = parts[0].strip()
                logout_time = parts[1].strip()
                
                login_dt = datetime.strptime(login_time, "%H:%M:%S")
                logout_dt = datetime.strptime(logout_time, "%H:%M:%S")
                
                diff_seconds = (logout_dt - login_dt).total_seconds()
                
                # Handle crossing midnight
                if diff_seconds < 0:
                    diff_seconds += 86400
                
                return diff_seconds if diff_seconds > 0 and diff_seconds < 86400 else 0
    except:
        pass
    return 0

def calculate_total_study_time(student_data):
    """
    Calculate total study time in seconds
    """
    total_seconds = 0
    for entry in student_data.get("track", []):
        for session in entry.get("study_time", []):
            total_seconds += calculate_session_duration(session)
    return total_seconds

def format_time(seconds):
    """
    Format time in seconds to readable format
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def display_general_overview(student_data):
    """
    Display general overview with key information
    """
    st.subheader("📌 General Overview", divider="blue")
    
    # Process track data
    track_data = student_data.get("track", [])
    
    if not track_data:
        st.info("ℹ️ No tracking data available")
        return
    
    # Prepare data for visualization
    daily_data = []
    weekday_stats = defaultdict(int)
    hour_stats = defaultdict(int)
    
    for entry in track_data:
        date_str = entry.get("date", "")
        sessions = entry.get("study_time", [])
        
        daily_seconds = 0
        for session in sessions:
            duration = calculate_session_duration(session)
            daily_seconds += duration
            
            # Extract hour from start time
            try:
                if " - " in session:
                    start_time = session.split(" - ")[0].strip()
                    hour = int(start_time.split(":")[0])
                    hour_stats[hour] += duration
            except:
                pass
        
        if daily_seconds > 0:
            # Parse date
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                weekday = date_obj.strftime("%A")
                weekday_stats[weekday] += daily_seconds
                
                daily_data.append({
                    "Date": date_str,
                    "Sessions": len(sessions),
                    "Study Time (seconds)": daily_seconds,
                    "Study Time": format_time(daily_seconds),
                    "Weekday": weekday
                })
            except:
                continue
    
    # Sort daily data by date
    daily_data.sort(key=lambda x: x["Date"])
    
    # Display metrics
    if daily_data:
        st.subheader("📈 Key Metrics", divider="green")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("📅 Total Days", len(daily_data))
        with col_b:
            total_sessions = sum(item["Sessions"] for item in daily_data)
            st.metric("🔄 Total Sessions", total_sessions)
        with col_c:
            total_time = sum(item["Study Time (seconds)"] for item in daily_data)
            st.metric("⏱️ Total Study Time", format_time(total_time))
        with col_d:
            if daily_data:
                avg_time = sum(item["Study Time (seconds)"] for item in daily_data) / len(daily_data)
                st.metric("📊 Avg Daily Time", format_time(avg_time))
        
        # Recent activity
        st.subheader("📋 Recent Activity", divider="green")
        
        # Show last 5 entries
        recent_data = daily_data[-5:] if len(daily_data) >= 5 else daily_data
        recent_data.reverse()
        
        for item in recent_data:
            with st.container(border=True):
                col_date, col_sessions, col_time = st.columns([2, 1, 2])
                col_date.write(f"**📅 {item['Date']}** ({item['Weekday']})")
                col_sessions.write(f"📝 {item['Sessions']} sessions")
                col_time.write(f"⏱️ {item['Study Time']}")
        
        # Weekday distribution (small chart)
        if weekday_stats:
            st.subheader("📊 Weekday Activity Distribution", divider="green")
            
            # Prepare data for chart
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_data = []
            for day in weekdays:
                weekday_data.append({
                    "Weekday": day,
                    "Study Time (seconds)": weekday_stats.get(day, 0)
                })
            
            df_weekday = pd.DataFrame(weekday_data)
            
            # Create bar chart
            fig = px.bar(
                df_weekday,
                x="Weekday",
                y="Study Time (seconds)",
                title="Study Time by Weekday",
                color="Study Time (seconds)",
                color_continuous_scale="Viridis",
                labels={"Study Time (seconds)": "Study Time (seconds)"}
            )
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Study Time (seconds)",
                showlegend=False,
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No valid study sessions found")

def display_advanced_stats(student_data):
    """
    Display advanced statistics with visualizations
    """
    st.subheader("📈 Advanced Statistics", divider="blue")
    
    track_data = student_data.get("track", [])
    
    if not track_data:
        st.info("ℹ️ No tracking data available")
        return
    
    # Prepare comprehensive data
    daily_data = []
    weekday_stats = defaultdict(int)
    hour_stats = defaultdict(int)
    session_lengths = []
    
    for entry in track_data:
        date_str = entry.get("date", "")
        sessions = entry.get("study_time", [])
        
        daily_seconds = 0
        for session in sessions:
            duration = calculate_session_duration(session)
            if duration > 0:
                daily_seconds += duration
                session_lengths.append(duration)
            
            # Extract hour from start time
            try:
                if " - " in session:
                    start_time = session.split(" - ")[0].strip()
                    hour = int(start_time.split(":")[0])
                    hour_stats[hour] += duration
            except:
                pass
        
        if daily_seconds > 0:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                weekday = date_obj.strftime("%A")
                weekday_stats[weekday] += daily_seconds
                
                daily_data.append({
                    "Date": date_obj,
                    "DateStr": date_str,
                    "Sessions": len(sessions),
                    "Study Time (seconds)": daily_seconds,
                    "Study Time": format_time(daily_seconds),
                    "Weekday": weekday,
                    "Month": date_obj.strftime("%B"),
                    "Week": date_obj.isocalendar()[1]
                })
            except:
                continue
    
    if not daily_data:
        st.info("ℹ️ No valid study sessions found")
        return
    
    # Visualization options
    viz_options = [
        "📊 Study Time Over Time",
        "📈 Cumulative Study Progress",
        "📅 Weekday Heatmap",
        "🕐 Hourly Activity Pattern",
        "📏 Session Duration Distribution",
        "📊 Monthly Study Comparison",
        "📈 Weekly Progress Trend",
        "🌡️ Activity Intensity Heatmap",
        "📊 Study Consistency Score",
        "📈 Performance vs Average",
        "📅 Day of Week Analysis",
        "🕐 Peak Study Hours",
        "📊 Study Pattern Radar",
        "📈 Progress Timeline",
        "📊 Overall Performance Summary"
    ]
    
    selected_viz = st.selectbox(
        "🎯 Select Visualization",
        viz_options,
        key="viz_select"
    )
    
    df = pd.DataFrame(daily_data)
    
    # Generate selected visualization
    if selected_viz == "📊 Study Time Over Time":
        fig = px.bar(
            df,
            x="DateStr",
            y="Study Time (seconds)",
            title="Study Time Per Day",
            color="Study Time (seconds)",
            color_continuous_scale="Viridis",
            labels={"Study Time (seconds)": "Study Time (seconds)", "DateStr": "Date"}
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Study Time (seconds)",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows how much time you studied each day")
    
    elif selected_viz == "📈 Cumulative Study Progress":
        df_sorted = df.sort_values("Date")
        df_sorted["Cumulative Time"] = df_sorted["Study Time (seconds)"].cumsum()
        
        fig = px.line(
            df_sorted,
            x="DateStr",
            y="Cumulative Time",
            title="Cumulative Study Time Over Time",
            markers=True,
            labels={"Cumulative Time": "Cumulative Study Time (seconds)", "DateStr": "Date"}
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Cumulative Study Time (seconds)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows your total study time accumulating over time")
    
    elif selected_viz == "📅 Weekday Heatmap":
        # Create heatmap data
        heatmap_data = []
        for weekday in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            row = {"Weekday": weekday}
            for week in sorted(df["Week"].unique()):
                week_data = df[(df["Week"] == week) & (df["Weekday"] == weekday)]
                row[f"Week {week}"] = week_data["Study Time (seconds)"].sum() if not week_data.empty else 0
            heatmap_data.append(row)
        
        df_heatmap = pd.DataFrame(heatmap_data)
        df_heatmap = df_heatmap.set_index("Weekday")
        
        fig = px.imshow(
            df_heatmap,
            title="Study Time Heatmap (Weekday vs Week)",
            labels=dict(x="Week", y="Weekday", color="Study Time (seconds)"),
            color_continuous_scale="Viridis",
            aspect="auto"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows which days of the week and which weeks you studied the most")
    
    elif selected_viz == "🕐 Hourly Activity Pattern":
        # Prepare hourly data
        hours = list(range(24))
        hour_data = [hour_stats.get(h, 0) for h in hours]
        
        df_hours = pd.DataFrame({
            "Hour": hours,
            "Study Time (seconds)": hour_data
        })
        
        fig = px.bar(
            df_hours,
            x="Hour",
            y="Study Time (seconds)",
            title="Study Activity by Hour of Day",
            color="Study Time (seconds)",
            color_continuous_scale="Plasma",
            labels={"Study Time (seconds)": "Study Time (seconds)", "Hour": "Hour of Day (24h)"}
        )
        fig.update_layout(
            xaxis_title="Hour of Day",
            yaxis_title="Study Time (seconds)",
            showlegend=False,
            height=400,
            xaxis=dict(tickmode="linear", tick0=0, dtick=2)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows which hours of the day you're most productive")
    
    elif selected_viz == "📏 Session Duration Distribution":
        if session_lengths:
            fig = px.histogram(
                x=session_lengths,
                nbins=20,
                title="Session Duration Distribution",
                labels={"x": "Session Duration (seconds)", "y": "Frequency"},
                color_discrete_sequence=["#FF6B6B"]
            )
            fig.update_layout(
                xaxis_title="Session Duration (seconds)",
                yaxis_title="Number of Sessions",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            st.info("💡 Shows how long your typical study sessions are")
        else:
            st.info("ℹ️ No valid session data available")
    
    elif selected_viz == "📊 Monthly Study Comparison":
        monthly_data = df.groupby("Month")["Study Time (seconds)"].sum().reset_index()
        
        fig = px.bar(
            monthly_data,
            x="Month",
            y="Study Time (seconds)",
            title="Total Study Time by Month",
            color="Study Time (seconds)",
            color_continuous_scale="Viridis",
            labels={"Study Time (seconds)": "Study Time (seconds)", "Month": "Month"}
        )
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Total Study Time (seconds)",
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Compares your study time across different months")
    
    elif selected_viz == "📈 Weekly Progress Trend":
        weekly_data = df.groupby("Week")["Study Time (seconds)"].sum().reset_index()
        
        fig = px.line(
            weekly_data,
            x="Week",
            y="Study Time (seconds)",
            title="Weekly Study Trend",
            markers=True,
            labels={"Study Time (seconds)": "Study Time (seconds)", "Week": "Week Number"}
        )
        fig.update_layout(
            xaxis_title="Week",
            yaxis_title="Study Time (seconds)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows your study trend week by week")
    
    elif selected_viz == "🌡️ Activity Intensity Heatmap":
        # Create a comprehensive heatmap
        pivot_data = df.pivot_table(
            values="Study Time (seconds)",
            index="Weekday",
            columns="Week",
            aggfunc="sum",
            fill_value=0
        )
        
        # Reorder weekdays
        weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        pivot_data = pivot_data.reindex(weekday_order)
        
        fig = px.imshow(
            pivot_data,
            title="Study Intensity Heatmap",
            labels=dict(x="Week", y="Weekday", color="Study Time (seconds)"),
            color_continuous_scale="Reds",
            aspect="auto"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows study intensity with red being higher activity")
    
    elif selected_viz == "📊 Study Consistency Score":
        # Calculate consistency metrics
        if len(df) >= 3:
            daily_times = df["Study Time (seconds)"].values
            mean_time = daily_times.mean()
            std_time = daily_times.std()
            consistency_score = 100 - (std_time / mean_time * 100) if mean_time > 0 else 0
            consistency_score = max(0, min(100, consistency_score))
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=consistency_score,
                title={"text": "Study Consistency Score", "font": {"size": 24}},
                delta={"reference": 50},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "#FF6B6B"},
                    "steps": [
                        {"range": [0, 25], "color": "#FFE4E1"},
                        {"range": [25, 50], "color": "#FFD700"},
                        {"range": [50, 75], "color": "#90EE90"},
                        {"range": [75, 100], "color": "#32CD32"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 90
                    }
                }
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(f"💡 Consistency score: {consistency_score:.1f}% - {'Excellent!' if consistency_score > 80 else 'Good!' if consistency_score > 60 else 'Keep going!'}")
        else:
            st.info("ℹ️ Need at least 3 days of data for consistency analysis")
    
    elif selected_viz == "📈 Performance vs Average":
        # Calculate daily average
        avg_daily = df["Study Time (seconds)"].mean()
        
        df["Above Average"] = df["Study Time (seconds)"] > avg_daily
        df["Deviation"] = df["Study Time (seconds)"] - avg_daily
        
        colors = ["#FF6B6B" if not above else "#4ECDC4" for above in df["Above Average"]]
        
        fig = px.bar(
            df,
            x="DateStr",
            y="Study Time (seconds)",
            title=f"Daily Performance vs Average ({format_time(avg_daily)})",
            labels={"Study Time (seconds)": "Study Time (seconds)", "DateStr": "Date"}
        )
        fig.update_traces(marker_color=colors)
        fig.add_hline(y=avg_daily, line_dash="dash", line_color="red", annotation_text="Average")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Study Time (seconds)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows how each day compares to your daily average")
    
    elif selected_viz == "📅 Day of Week Analysis":
        # Prepare weekday data with averages
        weekday_data = []
        for weekday in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            weekday_seconds = weekday_stats.get(weekday, 0)
            weekday_count = len(df[df["Weekday"] == weekday])
            avg_seconds = weekday_seconds / weekday_count if weekday_count > 0 else 0
            weekday_data.append({
                "Weekday": weekday,
                "Total Time": weekday_seconds,
                "Average Time": avg_seconds,
                "Days Active": weekday_count
            })
        
        df_weekday = pd.DataFrame(weekday_data)
        
        # Create subplot with two charts
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Total Study Time by Weekday", "Average Study Time by Weekday"),
            vertical_spacing=0.15
        )
        
        fig.add_trace(
            go.Bar(x=df_weekday["Weekday"], y=df_weekday["Total Time"], name="Total Time", marker_color="#FF6B6B"),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=df_weekday["Weekday"], y=df_weekday["Average Time"], name="Average Time", marker_color="#4ECDC4"),
            row=2, col=1
        )
        
        fig.update_layout(height=500, showlegend=False)
        fig.update_xaxes(title_text="Weekday", row=2, col=1)
        fig.update_yaxes(title_text="Total Study Time (seconds)", row=1, col=1)
        fig.update_yaxes(title_text="Average Study Time (seconds)", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Shows both total and average study time by day of the week")
    
    elif selected_viz == "🕐 Peak Study Hours":
        # Prepare hour data
        hours = list(range(24))
        hour_data = [hour_stats.get(h, 0) for h in hours]
        
        # Find peak hours
        peak_hours = []
        max_time = max(hour_data) if hour_data else 0
        if max_time > 0:
            for i, time in enumerate(hour_data):
                if time >= max_time * 0.8:  # Within 80% of peak
                    peak_hours.append(i)
        
        df_hours = pd.DataFrame({
            "Hour": hours,
            "Study Time (seconds)": hour_data
        })
        
        # Create highlight colors
        colors = ["#FF6B6B" if h in peak_hours else "#4ECDC4" for h in hours]
        
        fig = px.bar(
            df_hours,
            x="Hour",
            y="Study Time (seconds)",
            title="Peak Study Hours Analysis",
            labels={"Study Time (seconds)": "Study Time (seconds)", "Hour": "Hour of Day (24h)"}
        )
        fig.update_traces(marker_color=colors)
        fig.update_layout(
            xaxis_title="Hour of Day",
            yaxis_title="Study Time (seconds)",
            height=400,
            xaxis=dict(tickmode="linear", tick0=0, dtick=2)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        if peak_hours:
            peak_str = ", ".join([f"{h}:00-{h+1}:00" for h in peak_hours[:3]])
            st.info(f"💡 Your peak study hours: {peak_str}")
        else:
            st.info("💡 No peak hours identified yet")
    
    elif selected_viz == "📊 Study Pattern Radar":
        # Create radar chart for study patterns
        categories = ["Consistency", "Frequency", "Duration", "Weekend Activity", "Peak Hours"]
        
        # Calculate scores (0-100)
        # Consistency: based on daily variation
        daily_times = df["Study Time (seconds)"].values
        if len(daily_times) >= 3:
            consistency = 100 - (daily_times.std() / daily_times.mean() * 100) if daily_times.mean() > 0 else 0
            consistency = max(0, min(100, consistency))
        else:
            consistency = 50
        
        # Frequency: days with sessions / total days
        total_days = len(df)
        active_days = len(df[df["Study Time (seconds)"] > 0])
        frequency = (active_days / total_days * 100) if total_days > 0 else 0
        
        # Duration: average session length
        if session_lengths:
            avg_duration = sum(session_lengths) / len(session_lengths)
            duration = min(100, (avg_duration / 3600) * 20)  # Scale: 5 hours = 100
        else:
            duration = 0
        
        # Weekend activity
        weekend_seconds = weekday_stats.get("Saturday", 0) + weekday_stats.get("Sunday", 0)
        total_seconds = sum(weekday_stats.values())
        weekend_activity = (weekend_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        # Peak hours
        if hour_stats:
            max_hour = max(hour_stats.values())
            peak_hours_score = (max_hour / sum(hour_stats.values()) * 100 * 2) if sum(hour_stats.values()) > 0 else 0
            peak_hours_score = min(100, peak_hours_score)
        else:
            peak_hours_score = 0
        
        values = [consistency, frequency, duration, weekend_activity, peak_hours_score]
        
        fig = go.Figure(data=go.Radar(
            r=values,
            theta=categories,
            fill='toself',
            name='Study Pattern',
            line_color='#FF6B6B',
            fillcolor='rgba(255, 107, 107, 0.3)'
        ))
        fig.update_layout(
            title="Study Pattern Radar Chart",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Radar chart showing different aspects of your study habits")
    
    elif selected_viz == "📈 Progress Timeline":
        # Create a comprehensive timeline
        df_sorted = df.sort_values("Date")
        df_sorted["Day"] = range(1, len(df_sorted) + 1)
        df_sorted["Cumulative"] = df_sorted["Study Time (seconds)"].cumsum()
        df_sorted["Moving Average"] = df_sorted["Study Time (seconds)"].rolling(window=min(3, len(df_sorted)), min_periods=1).mean()
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Daily Study Time with Moving Average", "Cumulative Study Time"),
            vertical_spacing=0.15
        )
        
        fig.add_trace(
            go.Bar(x=df_sorted["DateStr"], y=df_sorted["Study Time (seconds)"], name="Daily", marker_color="#4ECDC4"),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df_sorted["DateStr"], y=df_sorted["Moving Average"], name="Moving Average", line=dict(color="#FF6B6B", width=2)),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=df_sorted["DateStr"], y=df_sorted["Cumulative"], name="Cumulative", fill="tozeroy", line=dict(color="#45B7D1", width=2)),
            row=2, col=1
        )
        
        fig.update_layout(height=500)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Study Time (seconds)", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Time (seconds)", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Complete timeline showing daily, average, and cumulative study time")
    
    elif selected_viz == "📊 Overall Performance Summary":
        # Comprehensive summary with multiple metrics
        st.subheader("📊 Performance Summary Dashboard", divider="blue")
        
        # Calculate metrics
        total_days = len(daily_data)
        total_sessions = sum(item["Sessions"] for item in daily_data)
        total_time = sum(item["Study Time (seconds)"] for item in daily_data)
        avg_daily = total_time / total_days if total_days > 0 else 0
        max_day = max(daily_data, key=lambda x: x["Study Time (seconds)"]) if daily_data else None
        
        # Create metrics grid
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 Active Days", total_days)
        with col2:
            st.metric("🔄 Total Sessions", total_sessions)
        with col3:
            st.metric("⏱️ Total Time", format_time(total_time))
        with col4:
            st.metric("📊 Avg/Day", format_time(avg_daily))
        
        # Best day
        if max_day:
            st.success(f"🏆 **Best Day:** {max_day['DateStr']} - {max_day['Study Time']} with {max_day['Sessions']} sessions")
        
        # Create summary charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Weekday distribution pie chart
            weekday_data = []
            for weekday in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
                time = weekday_stats.get(weekday, 0)
                if time > 0:
                    weekday_data.append({"Weekday": weekday, "Time": time})
            
            if weekday_data:
                df_pie = pd.DataFrame(weekday_data)
                fig = px.pie(
                    df_pie,
                    values="Time",
                    names="Weekday",
                    title="Weekday Distribution",
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            # Hour distribution
            hours = list(range(24))
            hour_data = [hour_stats.get(h, 0) for h in hours]
            df_hours = pd.DataFrame({"Hour": hours, "Time": hour_data})
            
            fig = px.area(
                df_hours,
                x="Hour",
                y="Time",
                title="Hourly Distribution",
                color_discrete_sequence=["#FF6B6B"]
            )
            fig.update_layout(height=300, xaxis=dict(tickmode="linear", tick0=0, dtick=4))
            st.plotly_chart(fig, use_container_width=True)
        
        # Additional insights
        st.subheader("💡 Key Insights", divider="green")
        
        insights = []
        
        # Find most productive weekday
        if weekday_stats:
            best_weekday = max(weekday_stats.items(), key=lambda x: x[1])
            insights.append(f"📈 **Most Productive Day:** {best_weekday[0]}")
        
        # Find peak hour
        if hour_stats:
            peak_hour = max(hour_stats.items(), key=lambda x: x[1])
            insights.append(f"🕐 **Peak Study Hour:** {peak_hour[0]}:00")
        
        # Average session length
        if session_lengths:
            avg_session = sum(session_lengths) / len(session_lengths)
            insights.append(f"⏱️ **Average Session Length:** {format_time(avg_session)}")
        
        for insight in insights:
            st.write(insight)

def main4():
    """
    Wrapper function for the performance section
    Called from mainFile.py when 'My Performance' is selected
    """
    main_layout()