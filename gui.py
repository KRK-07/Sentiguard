import tkinter as tk
from tkinter import messagebox
from analyzer import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import threading
import sys, os, urllib.request, io
import datetime
import json
from mailer import send_alert_email
from PIL import Image, ImageTk
from voice_recorder import voice_recorder
from enhanced_mood_bg import EnhancedMoodBackground

def check_and_alert():
    try:
        with open("user_settings.json", "r") as f:
            settings = json.load(f)
        guardian_email = settings.get("guardian_email")
        if not guardian_email:
            return

        result = count_below_threshold()
        count, latest_line = result[0], result[1]
        if count > ALERT_LIMIT:
            send_alert_email(guardian_email, count)
            # Set alert status to latest line to avoid re-checking same lines
            set_alert_status(latest_line)
            messagebox.showinfo(
                "Guardian Alert Sent",
                f"An alert was sent to the guardian ({guardian_email}) because mood dropped below {THRESHOLD} more than {ALERT_LIMIT} times."
            )
    except Exception as e:
        print("Error during guardian alert check:", e)
        
        
def check_and_add_guardian_alert(alert_limit=None):
    ALERTS_LOG_FILE = "alerts_log.json"
    if alert_limit is None:
        from analyzer import ALERT_LIMIT
        alert_limit = ALERT_LIMIT  # Use consistent alert limit from analyzer
    
    result = count_below_threshold(return_lines=True)
    if len(result) == 3:
        count, latest_line, neg_lines = result
    else:
        count, latest_line = result
        neg_lines = []
    print(f"Debug: Alert check - Count: {count}, Limit: {alert_limit}, Latest line: {latest_line}")
    
    if count > alert_limit:
        alert_record = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "negative_count": count,
            "status": "Sent",
            "reason_lines": neg_lines
        }
        logs = []
        if os.path.exists(ALERTS_LOG_FILE):
            with open(ALERTS_LOG_FILE, "r") as f:
                loaded_data = json.load(f)
                # Ensure logs is always a list
                if isinstance(loaded_data, list):
                    logs = loaded_data
                else:
                    logs = []  # Reset to empty list if file contains invalid format
        logs.insert(0, alert_record)
        with open(ALERTS_LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
        # Set alert status to latest line to avoid re-checking same lines
        set_alert_status(latest_line)
        print(f"✅ Alert logged: {count} negative entries detected")
        
def initialize_user_settings(user_info):
    """Initialize or update user settings with Google auth info"""
    try:
        # Extract email from user_info (Google auth response)
        user_email = user_info.get("email", "")
        if not user_email:
            print("Warning: No email found in user info")
            return
        
        # Create user settings with Google user's email as guardian email
        settings = {
            "name": user_info.get("name", "User"),
            "google_id": user_info.get("id", ""),
            "guardian_email": user_email  # Use the logged-in user's email as guardian email
        }
        
        # Save to user_settings.json
        with open("user_settings.json", "w") as f:
            json.dump(settings, f, indent=4)
        
        print(f"✅ User settings updated - Guardian email set to: {user_email}")
        
    except Exception as e:
        print(f"Error updating user settings: {e}")

def launch_gui(user_info):
    # Initialize user settings with Google auth info
    initialize_user_settings(user_info)
    
    check_and_add_guardian_alert()
    root = tk.Tk()
    root.title("SentiGuard")
    root.geometry("900x600")
    root.configure(bg="#1e1e1e")
    
    # Global theme state
    is_light_mode = False
    # Global animation object to prevent garbage collection
    current_animation = None
    # Track current view for theme refresh
    current_view = None
    # Initialize mood background system
    mood_bg = EnhancedMoodBackground(root)
    
    # Update background based on current mood
    def update_mood_background():
        """Update background based on current mood"""
        try:
            current_mood = get_latest_mood()
            mood_bg.update_mood(current_mood)
        except Exception as e:
            print(f"Error updating mood background: {e}")
    
    # Start background animation
    mood_bg.start_animation()
    
    # Update mood background initially and periodically
    update_mood_background()
    
    def periodic_mood_update():
        """Periodically update mood background"""
        update_mood_background()
        root.after(2000, periodic_mood_update)  # Update every 2 seconds for responsiveness
    
    # Start periodic updates
    root.after(1000, periodic_mood_update)  # First update after 1 second
    
    def apply_theme():
        """Apply the current theme to all widgets"""
        nonlocal is_light_mode
        
        if is_light_mode:
            # Light mode colors
            bg_color = "#ffffff"
            fg_color = "#000000"
            sidebar_bg = "#f0f0f0"
            topbar_bg = "#f0f0f0"
            sidebar_fg = "#000000"
            main_bg = "#ffffff"
            accent_color = "#2966e3"
        else:
            # Dark mode colors
            bg_color = "#1e1e1e"
            fg_color = "#cccccc"
            sidebar_bg = "#111111"
            topbar_bg = "#1e1e1e"
            sidebar_fg = "white"
            main_bg = "#1e1e1e"
            accent_color = "#2966e3"
        
        # Update root background
        root.configure(bg=bg_color)
        
        # Update all widgets recursively
        def update_widget_theme(widget, default_bg, default_fg):
            try:
                widget_class = widget.winfo_class()
                
                if widget_class in ['Frame', 'Toplevel']:
                    # Special handling for known frames
                    current_bg = str(widget['bg'])
                    if current_bg in ['#111111', '#f0f0f0']:  # Sidebar
                        widget.configure(bg=sidebar_bg)
                    elif current_bg in ['#1e1e1e', '#f0f0f0'] and widget.winfo_height() < 100:  # Top bar
                        widget.configure(bg=topbar_bg)
                    else:
                        widget.configure(bg=default_bg)
                        
                elif widget_class in ['Label', 'Button']:
                    # Determine parent context
                    parent_bg = str(widget.master['bg']) if widget.master else default_bg
                    
                    if parent_bg in ['#111111', '#f0f0f0']:  # Sidebar elements
                        if widget_class == 'Button':
                            widget.configure(bg=sidebar_bg, fg=sidebar_fg, activebackground=sidebar_bg)
                        else:
                            widget.configure(bg=sidebar_bg, fg=sidebar_fg)
                    elif parent_bg in ['#1e1e1e', '#f0f0f0'] and widget.master.winfo_height() < 100:  # Top bar elements
                        widget.configure(bg=topbar_bg, fg=default_fg)
                    else:
                        # Main area elements
                        widget.configure(bg=default_bg, fg=default_fg)
                
                # Recursively update children
                for child in widget.winfo_children():
                    update_widget_theme(child, default_bg, default_fg)
                    
            except Exception:
                pass  # Ignore widgets that don't support these options
        
        # Apply theme to all widgets
        update_widget_theme(root, bg_color, fg_color)
        
        print(f"Theme applied: {'Light' if is_light_mode else 'Dark'} mode")
    
    def toggle_to_light_mode():
        """Switch to light mode"""
        nonlocal is_light_mode, current_view
        is_light_mode = True
        apply_theme()
        # Refresh current view to apply theme to graphs and settings
        if current_view == 'live_graph':
            show_live_graph()
        elif current_view == 'analysis':
            show_analysis()
        elif current_view == 'settings':
            show_settings()
    
    def toggle_to_dark_mode():
        """Switch to dark mode"""
        nonlocal is_light_mode, current_view
        is_light_mode = False
        apply_theme()
        # Refresh current view to apply theme to graphs and settings
        if current_view == 'live_graph':
            show_live_graph()
        elif current_view == 'analysis':
            show_analysis()
        elif current_view == 'settings':
            show_settings()

    def on_close():
        print("Exiting SentiGuard...")
        # Stop mood background animation
        mood_bg.stop_animation()
        mood_bg.destroy()
        
        # Stop voice recording if active
        if voice_recorder.is_recording:
            voice_recorder.stop_recording()
        
        # Clear keystrokes for user privacy
        try:
            if os.path.exists("keystrokes.txt"):
                with open("keystrokes.txt", "w") as f: 
                    f.write("")
                print("🔒 Keystrokes cleared for privacy")
        except Exception as e:
            print(f"Warning: Could not clear keystrokes file: {e}")
        
        # Clear alert logs for privacy
        try:
            if os.path.exists("alerts_log.json"):
                with open("alerts_log.json", "w") as f:
                    json.dump([], f)
                print("🔒 Alert logs cleared for privacy")
        except Exception as e:
            print(f"Warning: Could not clear alert logs: {e}")
        
        # Reset alert status to 0 when app closes
        reset_alert_status()
        root.destroy()
        sys.exit()

    root.protocol("WM_DELETE_WINDOW", on_close)
    
    # Handle window resize for background
    def on_window_resize(event):
        if event.widget == root:
            mood_bg.resize_canvas()
    
    root.bind("<Configure>", on_window_resize)

     # Top Bar
    top_bar = tk.Frame(root, bg="#1e1e1e", height=50)
    top_bar.pack(side="top", fill="x")
    title_label = tk.Label(
        top_bar, text="SentiGuard", fg="#cccccc", bg="#1e1e1e",
        font=("Segoe UI", 14, "bold")
    )
    title_label.pack(side="left", padx=20, pady=10)
    user_text = user_info if isinstance(user_info, str) else user_info["name"]
    user_icon = tk.Label(
        top_bar, text=f"\U0001F7E2 {user_text}", bg="#1e1e1e", fg="white", cursor="hand2"
    )
    user_icon.pack(side="right", padx=10)
    # settings_icon = tk.Label(top_bar, text="\u2699\ufe0f", bg="#1e1e1e", fg="white", cursor="hand2")
    # settings_icon.pack(side="right", padx=(0, 10))  # Removed duplicate settings icon

    # Sidebar
    sidebar = tk.Frame(root, bg="#111111", width=150)
    sidebar.pack(side="left", fill="y")
    def create_sidebar_btn(text, icon="\U0001F4CA"):
        return tk.Button(
            sidebar, text=f"{icon} {text}", bg="#111111", fg="white",
            relief="flat", font=("Segoe UI", 10), anchor="w",
            activebackground="#1e1e1e", activeforeground="cyan", padx=10
        )

    def clear_main_area():
        """Clear all widgets from main area"""
        nonlocal current_animation
        
        # Stop any running animation before clearing
        if current_animation:
            current_animation.event_source.stop()
            current_animation = None
            
        for widget in main_area.winfo_children():
            widget.destroy()
    
    def show_homepage():
        """Show the homepage with app name and quote"""
        clear_main_area()
        
        app_name_label = tk.Label(
            main_area,
            text="SentiGuard",
            font=("Segoe UI", 36, "bold"),
            bg="#1e1e1e",
            fg="#2966e3",
            cursor="hand2"
        )
        app_name_label.pack(pady=(70, 10))
        app_name_label.bind("<Button-1>", lambda e: show_homepage())  # Make clickable
        
        quote = (
            '"The greatest weapon against stress is our ability to choose one thought over another."'
            "\n– William James"
        )
        quote_label = tk.Label(
            main_area,
            text=quote,
            font=("Segoe UI", 15, "italic"),
            bg="#1e1e1e",
            fg="#ffaa00",
            wraplength=650,
            justify="center"
        )
        quote_label.pack(pady=(8, 30))

    def show_live_graph():
        """Show live graph in main area with theme support"""
        nonlocal current_animation, current_view
        
        # Set current view
        current_view = 'live_graph'
        
        # Stop any existing animation first
        if current_animation:
            current_animation.event_source.stop()
            current_animation = None
            
        check_and_add_guardian_alert()
        clear_main_area()
        
        # Get current theme colors
        if is_light_mode:
            bg_color = "#ffffff"
            fg_color = "#000000"
            graph_bg = "#f8f9fa"
            graph_fg = "#000000"
            grid_color = "#e0e0e0"
            line_color = "#2966e3"
        else:
            bg_color = "#1e1e1e"
            fg_color = "#cccccc"
            graph_bg = "#2a2a2a"
            graph_fg = "#ffffff"
            grid_color = "#444444"
            line_color = "#00ffff"
        
        # Title
        title_label = tk.Label(
            main_area,
            text="📈 Live Mood Trend",
            font=("Segoe UI", 24, "bold"),
            bg=bg_color,
            fg="#2966e3"
        )
        title_label.pack(pady=(20, 10))

        # Graph frame
        graph_frame = tk.Frame(main_area, bg=bg_color)
        graph_frame.pack(expand=True, fill="both", padx=20, pady=20)

        fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(graph_bg)
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        def animate(i):
            try:
                history = get_day_analysis()
                ax.clear()
                
                # Apply theme colors in animation
                ax.set_facecolor(graph_bg)
                line = None
                if history:
                    # Only show last 50 points for better performance
                    trimmed = history[-50:]
                    x_data = list(range(len(trimmed)))
                    y_data = [score for (_, score) in trimmed]
                    line = ax.plot(x_data, y_data, color=line_color, linestyle='-', marker='o', linewidth=2, markersize=4)[0]
                
                ax.set_title("Mood Trend (Live)", color=graph_fg, fontsize=14)
                ax.set_xlabel("Entry", color=graph_fg)
                ax.set_ylabel("Mood Score", color=graph_fg)
                ax.set_ylim(-1, 1)
                ax.grid(color=grid_color, alpha=0.3)
                ax.tick_params(colors=graph_fg)
                
                # Add reference lines
                ax.axhline(y=0, color=graph_fg, linestyle='-', alpha=0.3, linewidth=1)
                ax.axhline(y=0.3, color='#00ff41', linestyle='--', alpha=0.5, linewidth=1)
                ax.axhline(y=-0.3, color='#ff4757', linestyle='--', alpha=0.5, linewidth=1)
                
                # Only check alerts every 10th update to reduce overhead
                if i % 10 == 0:
                    check_and_alert()
                
                # Return the line for FuncAnimation
                return [line] if line else []
            except Exception as e:
                print(f"Error updating graph: {e}")
                return []

        # Reduce animation interval from 1000ms to 500ms for more responsiveness
        current_animation = FuncAnimation(fig, animate, interval=500)
        canvas.draw()

    def show_analysis():
        """Show enhanced analysis with time period bar charts"""
        nonlocal current_view
        
        # Set current view
        current_view = 'analysis'
        
        check_and_add_guardian_alert()
        clear_main_area()
        
        # Import additional required modules for statistics
        from analyzer import get_mood_statistics, get_mood_summary
        
        # Get current theme colors
        if is_light_mode:
            main_bg = "#ffffff"
            main_fg = "#000000"
            container_bg = "#f0f0f0"
            container_fg = "#000000"
            card_bg = "#e8e8e8"
        else:
            main_bg = "#1e1e1e"
            main_fg = "#cccccc"
            container_bg = "#2a2a2a"
            container_fg = "white"
            card_bg = "#2a2a2a"
        
        # Create main container with scrollable frame
        main_container = tk.Frame(main_area, bg=main_bg)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_container,
            text="📊 Mood Analytics Dashboard",
            font=("Segoe UI", 24, "bold"),
            bg=main_bg,
            fg="#2966e3"
        )
        title_label.pack(pady=(10, 20))
        
        # Current mood summary section
        current_mood_frame = tk.Frame(main_container, bg=container_bg, relief="flat", bd=1)
        current_mood_frame.pack(fill="x", pady=(0, 20), padx=20)
        
        mood_score = get_latest_mood()
        summary = get_mood_summary()
        
        # Current mood display
        current_title = tk.Label(
            current_mood_frame,
            text="Current Mood",
            font=("Segoe UI", 16, "bold"),
            bg=container_bg,
            fg=container_fg
        )
        current_title.pack(pady=(15, 5))
        
        if mood_score >= 0.3:
            mood_color = "#00ff41"
            mood_emoji = "�"
            mood_text = "Positive"
        elif mood_score <= -0.3:
            mood_color = "#ff4757"
            mood_emoji = "😞"
            mood_text = "Negative"
        else:
            mood_color = "#ffa726"
            mood_emoji = "😐"
            mood_text = "Neutral"
        
        # Mood display row
        mood_row = tk.Frame(current_mood_frame, bg=container_bg)
        mood_row.pack(pady=(5, 10))
        
        emoji_label = tk.Label(
            mood_row,
            text=mood_emoji,
            font=("Segoe UI", 32),
            bg=container_bg
        )
        emoji_label.pack(side="left", padx=(20, 10))
        
        mood_info_frame = tk.Frame(mood_row, bg=container_bg)
        mood_info_frame.pack(side="left")
        
        mood_label = tk.Label(
            mood_info_frame,
            text=f"{mood_text} ({mood_score:.3f})",
            font=("Segoe UI", 18, "bold"),
            fg=mood_color,
            bg=container_bg
        )
        mood_label.pack(anchor="w")
        
        summary_text_color = "#888888" if is_light_mode else "#cccccc"
        summary_label = tk.Label(
            mood_info_frame,
            text=f"Total entries: {summary['total_entries']} | Avg: {summary['avg_score']:.3f}",
            font=("Segoe UI", 11),
            fg=summary_text_color,
            bg=container_bg
        )
        summary_label.pack(anchor="w", pady=(5, 0))
        
        # Statistics summary cards
        stats_frame = tk.Frame(current_mood_frame, bg=container_bg)
        stats_frame.pack(pady=(5, 15))
        
        # Positive card
        pos_card = tk.Frame(stats_frame, bg="#1a4a2e", relief="flat", bd=1)
        pos_card.pack(side="left", padx=10, pady=5)
        tk.Label(pos_card, text="😊", font=("Segoe UI", 20), bg="#1a4a2e").pack(pady=(8, 2))
        tk.Label(pos_card, text=str(summary['positive_count']), font=("Segoe UI", 16, "bold"), fg="#00ff41", bg="#1a4a2e").pack()
        tk.Label(pos_card, text="Positive", font=("Segoe UI", 10), fg="white", bg="#1a4a2e").pack(pady=(0, 8))
        
        # Neutral card
        neu_card = tk.Frame(stats_frame, bg="#4a3c1a", relief="flat", bd=1)
        neu_card.pack(side="left", padx=10, pady=5)
        tk.Label(neu_card, text="😐", font=("Segoe UI", 20), bg="#4a3c1a").pack(pady=(8, 2))
        tk.Label(neu_card, text=str(summary['neutral_count']), font=("Segoe UI", 16, "bold"), fg="#ffa726", bg="#4a3c1a").pack()
        tk.Label(neu_card, text="Neutral", font=("Segoe UI", 10), fg="white", bg="#4a3c1a").pack(pady=(0, 8))
        
        # Negative card
        neg_card = tk.Frame(stats_frame, bg="#4a1a1a", relief="flat", bd=1)
        neg_card.pack(side="left", padx=10, pady=5)
        tk.Label(neg_card, text="😞", font=("Segoe UI", 20), bg="#4a1a1a").pack(pady=(8, 2))
        tk.Label(neg_card, text=str(summary['negative_count']), font=("Segoe UI", 16, "bold"), fg="#ff4757", bg="#4a1a1a").pack()
        tk.Label(neg_card, text="Negative", font=("Segoe UI", 10), fg="white", bg="#4a1a1a").pack(pady=(0, 8))
        
        # Chart section
        chart_frame = tk.Frame(main_container, bg=main_bg)
        chart_frame.pack(fill="both", expand=True, padx=20)
        
        # Period selector
        period_frame = tk.Frame(chart_frame, bg=main_bg)
        period_frame.pack(pady=(0, 10))
        
        tk.Label(
            period_frame,
            text="Time Period:",
            font=("Segoe UI", 12, "bold"),
            bg=main_bg,
            fg=main_fg
        ).pack(side="left", padx=(0, 10))
        
        # Period selection variables
        current_period = tk.StringVar(value="daily")
        current_chart_canvas = None
        
        def update_chart():
            nonlocal current_chart_canvas
            
            # Remove existing chart
            if current_chart_canvas:
                current_chart_canvas.destroy()
            
            # Get current theme colors
            if is_light_mode:
                chart_bg = "#ffffff"
                chart_fg = "#000000"
                plot_bg = "#f8f9fa"
                grid_color = "#e0e0e0"
                no_data_bg = "#ffffff"
                no_data_fg = "#666666"
            else:
                chart_bg = "#1e1e1e"
                chart_fg = "#ffffff"
                plot_bg = "#2a2a2a"
                grid_color = "#444444"
                no_data_bg = "#1e1e1e"
                no_data_fg = "#888888"
            
            period = current_period.get()
            stats_data = get_mood_statistics(period)
            
            if not stats_data:
                no_data_label = tk.Label(
                    chart_frame,
                    text="No data available for selected period",
                    font=("Segoe UI", 14),
                    bg=no_data_bg,
                    fg=no_data_fg
                )
                no_data_label.pack(pady=50)
                current_chart_canvas = no_data_label
                return
            
            # Create the bar chart with theme colors
            fig, ax = plt.subplots(figsize=(12, 6), dpi=90)
            fig.patch.set_facecolor(chart_bg)
            ax.set_facecolor(plot_bg)
            
            # Prepare data
            labels = [item['label'] for item in stats_data[-20:]]  # Show last 20 periods
            values = [item['value'] for item in stats_data[-20:]]
            counts = [item['count'] for item in stats_data[-20:]]
            
            # Create bars with colors based on sentiment
            colors = []
            for value in values:
                if value > 0.1:
                    colors.append('#00ff41')  # Green for positive
                elif value < -0.1:
                    colors.append('#ff4757')  # Red for negative
                else:
                    colors.append('#ffa726')  # Orange for neutral
            
            # Set edge color based on theme
            edge_color = chart_fg if is_light_mode else 'white'
            bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor=edge_color, linewidth=0.5)
            
            # Customize chart with theme colors
            ax.set_title(f'Mood Trends - {period.title()} View', color=chart_fg, fontsize=16, pad=20)
            ax.set_ylabel('Average Mood Score', color=chart_fg, fontsize=12)
            ax.set_ylim(-1, 1)
            ax.grid(color=grid_color, alpha=0.3, axis='y')
            ax.tick_params(colors=chart_fg, labelsize=10)
            
            # Add horizontal reference lines
            ax.axhline(y=0, color=chart_fg, linestyle='-', alpha=0.3, linewidth=1)
            ax.axhline(y=0.3, color='#00ff41', linestyle='--', alpha=0.5, linewidth=1)
            ax.axhline(y=-0.3, color='#ff4757', linestyle='--', alpha=0.5, linewidth=1)
            
            # Add value labels on bars
            for bar, value, count in zip(bars, values, counts):
                if count > 0:  # Only show labels for periods with data
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + (0.05 if height >= 0 else -0.08),
                           f'{value:.2f}',
                           ha='center', va='bottom' if height >= 0 else 'top',
                           color=chart_fg, fontsize=9, fontweight='bold')
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Embed the chart
            chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            chart_canvas.draw()
            chart_canvas.get_tk_widget().pack(fill="both", expand=True)
            current_chart_canvas = chart_canvas.get_tk_widget()
        
        # Period selection buttons
        periods = [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]
        for text, value in periods:
            btn = tk.Radiobutton(
                period_frame,
                text=text,
                variable=current_period,
                value=value,
                command=update_chart,
                bg=main_bg,
                fg=main_fg,
                selectcolor="#2966e3",
                activebackground="#2966e3",
                activeforeground="white",
                font=("Segoe UI", 11)
            )
            btn.pack(side="left", padx=5)
        
        # Initialize with daily view
        update_chart()
        
        # Update mood background when analysis is shown
        update_mood_background()

    def show_guardian():
        check_and_add_guardian_alert()
        popup = tk.Toplevel()
        popup.title("Guardian Dashboard")
        popup.geometry("700x450")
        popup.configure(bg="#23272A")
        popup.resizable(False, False)
        def get_current_alert_state():
            result = count_below_threshold(return_lines=True)
            if len(result) == 3:
                count = result[0]
            else:
                count = result[0]
            if count > 10:
                return "Armed", count
            else:
                return "Waiting", count

        state, since_last = get_current_alert_state()
        state_color = "red" if state == "Armed" else "lime green"
        tk.Label(
            popup,
            text=f"Current Alert State: {state}",
            fg=state_color,
            bg="#23272A",
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(20, 5))
        tk.Label(
            popup,
            text=f"Negative entries since last alert: {since_last}",
            fg="#fff",
            bg="#23272A",
            font=("Segoe UI", 11)
        ).pack(pady=(0, 15))

        ALERTS_LOG_FILE = "alerts_log.json"
        def load_alert_history():
            if not os.path.exists(ALERTS_LOG_FILE):
                return []
            with open(ALERTS_LOG_FILE, "r") as f:
                return json.load(f)
        logs = load_alert_history()
        table_frame = tk.Frame(popup, bg="#23272A")
        table_frame.pack(pady=(10, 0), padx=8, fill="x")
        headers = ["Date/Time", "Neg. Count", "Status", "Reason Excerpt"]
        for col, title in enumerate(headers):
            tk.Label(
                table_frame, text=title, fg="#FFBD39", bg="#23272A",
                font=("Segoe UI", 10, "bold"), padx=10, pady=7
            ).grid(row=0, column=col, sticky="nsew")
        if logs:
            for i, alert in enumerate(logs[:12], start=1):
                excerpt = " | ".join(alert["reason_lines"][:2]) + ("..." if len(alert["reason_lines"]) > 2 else "")
                row_bg = "#262d34" if i % 2 else "#23272A"
                for col, val in enumerate([alert["date"], str(alert["negative_count"]), alert["status"], excerpt]):
                    col_fg = "#7cffc0" if col==2 and val=="Sent" else "#fff"
                    lbl = tk.Label(
                        table_frame, text=val, fg=col_fg,
                        bg=row_bg, font=("Segoe UI", 10), padx=8, pady=5, anchor="w", justify="left"
                    )
                    lbl.grid(row=i, column=col, sticky="nsew")
                def make_popup(idx=i-1):
                    def cb(event):
                        detail = logs[idx]
                        dtl = tk.Toplevel(popup)
                        dtl.title("Alert Details")
                        dtl.geometry("420x280")
                        dtl.configure(bg="#21252c")
                        tk.Label(dtl, text=f"Date: {detail['date']}", fg="#FFBD39", bg="#21252c",
                              font=("Segoe UI", 11, "bold")).pack(pady=(13,5))
                        tk.Label(dtl, text="Negative entries triggering the alert:",
                              fg="#fff", bg="#21252c", font=("Segoe UI", 10, "bold")).pack()
                        t = tk.Text(dtl, wrap="word", width=48, height=10, bg="#252930", fg="#fff", font=("Segoe UI",10))
                        t.insert("end", "\n".join(detail["reason_lines"]))
                        t.config(state="disabled")
                        t.pack(padx=12, pady=10)
                    return cb
                table_frame.grid_slaves(row=i, column=3)[0].bind("<Button-1>", make_popup())
        else:
            tk.Label(table_frame, text="No guardian alerts yet.", fg="#888", bg="#23272A", font=("Segoe UI", 11, "italic")).grid(row=1, column=0, columnspan=4, pady=30)
        tk.Label(
            popup, text="Tip: Click 'Reason Excerpt' to view full alert details.", fg="#85e1fa",
            bg="#23272A", font=("Segoe UI", 11, "italic")
        ).pack(pady=17)
        
    main_area = tk.Frame(root, bg="#1e1e1e")
    main_area.pack(expand=True, fill="both", padx=20, pady=20)
    
    # Initialize homepage
    show_homepage()

    def show_settings():
        """Show settings in main area"""
        nonlocal current_view
        clear_main_area()
        current_view = "settings"
        
        # Get current theme colors
        if is_light_mode:
            main_bg = "#ffffff"
            main_fg = "#000000"
            container_bg = "#f0f0f0"
            container_fg = "#000000"
            panel_bg = "#e8e8e8"
            panel_fg = "#000000"
        else:
            main_bg = "#1e1e1e"
            main_fg = "#cccccc"
            container_bg = "#2a2a2a"
            container_fg = "#ffffff"
            panel_bg = "#2a2a2a"
            panel_fg = "#ffffff"
        
        # Title
        title_label = tk.Label(
            main_area,
            text="⚙️ Settings",
            font=("Segoe UI", 24, "bold"),
            bg=main_bg,
            fg="#2966e3"
        )
        title_label.pack(pady=(20, 20))

        # Settings container
        settings_frame = tk.Frame(main_area, bg=container_bg, relief="flat", bd=0)
        settings_frame.pack(pady=10, padx=50, fill="both", expand=True)

        # Tab frame for navigation
        tab_frame = tk.Frame(settings_frame, bg=container_bg)
        tab_frame.pack(fill="x", pady=(20, 10))
        
        # Center the tab buttons
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(1, weight=0)
        tab_frame.grid_columnconfigure(2, weight=0)
        tab_frame.grid_columnconfigure(3, weight=0)
        tab_frame.grid_columnconfigure(4, weight=1)

        # Content container for panels
        content_frame = tk.Frame(settings_frame, bg=container_bg)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Store current panel
        current_panel = {"panel": None}
        
        def clear_content():
            for widget in content_frame.winfo_children():
                widget.destroy()

        def show_preferences():
            clear_content()
            
            # Theme Selection
            tk.Label(
                content_frame, text="Theme Selection", bg=container_bg, fg=container_fg,
                font=("Segoe UI", 16, "bold")
            ).pack(anchor="w", pady=(20, 15))

            theme_frame = tk.Frame(content_frame, bg=container_bg)
            theme_frame.pack(fill="x", pady=10)

            btn_light = tk.Button(
                theme_frame, text="Light Mode", bg="#f0f0f0", fg="#333",
                font=("Segoe UI", 12, "bold"), bd=0, relief="flat", padx=30, pady=12,
                activebackground="#2966e3", activeforeground="white",
                command=toggle_to_light_mode
            )
            btn_light.pack(side="left", padx=(0, 10))

            btn_dark = tk.Button(
                theme_frame, text="Dark Mode", bg="#2966e3", fg="white",
                font=("Segoe UI", 12, "bold"), bd=0, relief="flat", padx=30, pady=12,
                activebackground="#2966e3", activeforeground="white",
                command=toggle_to_dark_mode
            )
            btn_dark.pack(side="left")

            # Privacy Settings
            tk.Label(
                content_frame, text="Privacy Settings", bg=container_bg, fg=container_fg,
                font=("Segoe UI", 16, "bold")
            ).pack(anchor="w", pady=(30, 15))

            privacy_text_color = "#666666" if is_light_mode else "#aaaaaa"
            privacy_info = tk.Label(
                content_frame, 
                text="• Keystrokes are automatically cleared when app closes\n• Voice recordings are processed locally\n• No data is sent to external servers\n• Mood history is preserved for timeline analytics (contains no text)", 
                bg=container_bg, fg=privacy_text_color,
                font=("Segoe UI", 11), justify="left"
            )
            privacy_info.pack(anchor="w", pady=5)
            
            # Privacy Actions
            privacy_actions_frame = tk.Frame(content_frame, bg=container_bg)
            privacy_actions_frame.pack(fill="x", pady=15)
            
            def clear_all_mood_history():
                """Clear mood history with confirmation"""
                result = messagebox.askyesno(
                    "Clear Mood History", 
                    "This will permanently delete all mood history data used for timeline analytics.\n\nAre you sure you want to continue?"
                )
                if result:
                    from analyzer import clear_mood_history
                    if clear_mood_history():
                        messagebox.showinfo("Privacy", "Mood history has been cleared successfully.")
                    else:
                        messagebox.showerror("Error", "Failed to clear mood history. Please try again.")
            
            clear_history_btn = tk.Button(
                privacy_actions_frame, text="Clear Mood History", bg="#d32f2f", fg="white",
                font=("Segoe UI", 11, "bold"), bd=0, relief="flat", padx=20, pady=8,
                activebackground="#b71c1c", activeforeground="white",
                command=clear_all_mood_history
            )
            clear_history_btn.pack(anchor="w", pady=5)

        def show_account():
            clear_content()
            
            try:
                # Load user info from settings
                with open("user_settings.json", "r") as f:
                    settings = json.load(f)
                
                # Account Info
                tk.Label(
                    content_frame, text="Account Information", bg=container_bg, fg=container_fg,
                    font=("Segoe UI", 16, "bold")
                ).pack(anchor="w", pady=(20, 15))

                account_frame = tk.Frame(content_frame, bg=container_bg)
                account_frame.pack(fill="x", pady=10)

                # User details
                tk.Label(
                    account_frame, text=f"Name: {settings.get('name', 'User')}", 
                    bg=container_bg, fg=container_fg, font=("Segoe UI", 12)
                ).pack(anchor="w", pady=3)

                tk.Label(
                    account_frame, text=f"Guardian Email: {settings.get('guardian_email', 'Not set')}", 
                    bg=container_bg, fg=container_fg, font=("Segoe UI", 12)
                ).pack(anchor="w", pady=3)

                detail_text_color = "#666666" if is_light_mode else "#aaaaaa"
                tk.Label(
                    account_frame, text=f"Google ID: {settings.get('google_id', 'Not set')}", 
                    bg=container_bg, fg=detail_text_color, font=("Segoe UI", 10)
                ).pack(anchor="w", pady=3)

            except Exception as e:
                tk.Label(
                    content_frame, text="Unable to load account information", 
                    bg=container_bg, fg="#ff6b6b", font=("Segoe UI", 12)
                ).pack(anchor="w", pady=20)

        def show_about():
            clear_content()
            
            # About section
            tk.Label(
                content_frame, text="About SentiGuard", bg=container_bg, fg=container_fg,
                font=("Segoe UI", 16, "bold")
            ).pack(anchor="w", pady=(20, 15))

            desc = (
                "SentiGuard is an innovative AI-powered desktop companion designed\n"
                "to passively monitor typing behavior for early signs of emotional distress.\n\n"
                "Our goal is to provide a real-time, privacy-first solution that\n"
                "supports mental well-being, especially for students and remote workers,\n"
                "by offering insights and alerting guardians for timely intervention."
            )
            
            tk.Label(
                content_frame, text=desc, bg=container_bg, fg=container_fg,
                font=("Segoe UI", 11), justify="left", wraplength=500
            ).pack(anchor="w", pady=10)

            developer_text_color = "#0066cc" if is_light_mode else "#aad6ff"
            tk.Label(
                content_frame, text="Developed by: xEN coders", bg=container_bg,
                fg=developer_text_color, font=("Segoe UI", 12, "italic")
            ).pack(anchor="w", pady=(20, 8))

        # Create tab buttons
        tabs = {}
        
        def create_tab_button(text, command, column):
            # Theme-aware button colors
            if is_light_mode:
                inactive_bg = "#e0e0e0"
                inactive_fg = "#333333"
            else:
                inactive_bg = "#f0f0f0"
                inactive_fg = "#333"
                
            btn = tk.Button(
                tab_frame, text=text,
                bg="#2966e3" if text == "Preferences" else inactive_bg,
                fg="white" if text == "Preferences" else inactive_fg,
                font=("Segoe UI", 12, "bold"), bd=0, padx=26, pady=13,
                activebackground="#2966e3", activeforeground="white",
                relief="flat", command=command
            )
            btn.grid(row=0, column=column, padx=(0 if column == 1 else 8, 0))
            return btn

        def switch_tab(tab_name, show_func):
            # Update button colors
            if is_light_mode:
                inactive_bg = "#e0e0e0"
                inactive_fg = "#333333"
            else:
                inactive_bg = "#f0f0f0"
                inactive_fg = "#333"
                
            for name, btn in tabs.items():
                if name == tab_name:
                    btn.config(bg="#2966e3", fg="white")
                else:
                    btn.config(bg=inactive_bg, fg=inactive_fg)
            # Show content
            show_func()

        tabs["Preferences"] = create_tab_button("Preferences", lambda: switch_tab("Preferences", show_preferences), 1)
        tabs["Account"] = create_tab_button("Account", lambda: switch_tab("Account", show_account), 2)
        tabs["About"] = create_tab_button("About", lambda: switch_tab("About", show_about), 3)

        # Show default panel
        show_preferences()

    def open_settings(event=None):
        show_settings()
    # settings_icon.bind("<Button-1>", open_settings)  # Removed since settings_icon is removed

    btn_live = create_sidebar_btn("Live Graph", "\U0001F4C8")
    btn_live.config(command=show_live_graph)
    btn_live.pack(fill="x", pady=(20, 5))

    btn_analysis = create_sidebar_btn("Analysis", "\U0001F4C9")
    btn_analysis.config(command=show_analysis)
    btn_analysis.pack(fill="x", pady=5)

    # Voice Recording Button
    voice_btn_text = tk.StringVar(value="🎤 Start Voice")
    voice_btn_color = tk.StringVar(value="#28a745")  # Green
    
    def toggle_voice_recording():
        try:
            if voice_recorder.is_recording:
                # Stop recording
                print("🛑 Stopping voice recording...")
                voice_recorder.stop_recording()
                voice_btn_text.set("🎤 Start Voice")
                voice_btn_color.set("#28a745")  # Green
                btn_voice.config(bg="#28a745", activebackground="#218838")
                print("✅ Voice recording stopped")
                
                # Show confirmation message
                messagebox.showinfo("Voice Recording", "🛑 Voice recording stopped successfully!")
                
            else:
                # Check if voice recorder is initialized
                if not voice_recorder.initialized:
                    messagebox.showerror(
                        "Voice Recording Error", 
                        "❌ Microphone not available!\n\n"
                        "Possible solutions:\n"
                        "• Check microphone permissions in Windows Settings\n"
                        "• Make sure no other app is using the microphone\n"
                        "• Restart the application"
                    )
                    return
                
                # Start recording
                print("🎙️ Starting voice recording...")
                success = voice_recorder.start_recording()
                if success:
                    voice_btn_text.set("⏹️ Stop Voice")
                    voice_btn_color.set("#dc3545")  # Red
                    btn_voice.config(bg="#dc3545", activebackground="#c82333")
                    print("✅ Voice recording started")
                    
                    # Show confirmation message
                    messagebox.showinfo(
                        "Voice Recording", 
                        "🎙️ Voice recording started!\n\n"
                        "Speak clearly into your microphone.\n"
                        "Your speech will be analyzed for mood sentiment."
                    )
                else:
                    print("❌ Failed to start voice recording")
                    messagebox.showerror(
                        "Voice Recording Error",
                        "❌ Failed to start voice recording!\n\n"
                        "Please check your microphone settings and try again."
                    )
        except Exception as e:
            print(f"❌ Error in voice recording toggle: {e}")
            # Reset to default state on error
            voice_btn_text.set("🎤 Start Voice")
            voice_btn_color.set("#28a745")
            btn_voice.config(bg="#28a745", activebackground="#218838")
            messagebox.showerror("Voice Recording Error", f"❌ An error occurred: {e}")
    
    btn_voice = tk.Button(
        sidebar, textvariable=voice_btn_text, bg="#28a745", fg="white",
        relief="flat", font=("Segoe UI", 10, "bold"), 
        activebackground="#218838", activeforeground="white",
        command=toggle_voice_recording, padx=10, pady=8
    )
    btn_voice.pack(fill="x", pady=5)

    # Settings Button
    btn_settings = create_sidebar_btn("Settings", "⚙️")
    btn_settings.config(command=show_settings)
    btn_settings.pack(fill="x", pady=5)

    # btn_guardian = create_sidebar_btn("Guardian", "\U0001F9D1\u200D\U0001F4BB")
    # btn_guardian.config(command=show_guardian)
    # btn_guardian.pack(fill="x", pady=5)
    root.mainloop()

    # # ========== Main Area ==========
    # main_area = tk.Frame(root, bg="#1e1e1e")
    # main_area.pack(expand=True, fill="both", padx=20, pady=20)

    # card_style = {
    #     "bg": "#2a2a2a",
    #     "fg": "#ffffff",
    #     "font": ("Segoe UI", 12, "bold"),
    #     "width": 25,
    #     "height": 5,
    #     "bd": 0,
    #     "relief": "flat"
    # }

    # graph_card = tk.Label(main_area, text="Last mood trend (work in progress)", **card_style)
    # graph_card.grid(row=0, column=0, padx=10, pady=10)

    # analysis_card = tk.Label(main_area, text="Analysis", **card_style)
    # analysis_card.grid(row=0, column=1, padx=10, pady=10)

    # guardian_card = tk.Label(main_area, text="Guardian Dashboard", **card_style)
    # guardian_card.grid(row=1, column=0, padx=10, pady=10)

    # root.mainloop()

# ====== SETTINGS PANEL FOR SentiGuard - Interactive/Colorful Version ======
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, user_info, main_area, top_bar, sidebar, app_name_label, quote_label, light_mode_func, dark_mode_func):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("440x580")
        self.configure(bg="#23272A")
        self.resizable(False, False)
        self.parent = parent
        self.dark_mode = True

        self.main_area = main_area
        self.top_bar = top_bar
        self.sidebar = sidebar
        self.app_name_label = app_name_label
        self.quote_label = quote_label
        
        # Store theme functions from main GUI
        self.light_mode_func = light_mode_func
        self.dark_mode_func = dark_mode_func

        # --- Modern, colorful tab row ---
        tab_frame = tk.Frame(self, bg="#23272A")
        tab_frame.pack(fill="x", pady=(18, 9))
        self.tabs = {}
        self.panels = {}

        # Configure the tab_frame to center the buttons
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(1, weight=0)
        tab_frame.grid_columnconfigure(2, weight=0)
        tab_frame.grid_columnconfigure(3, weight=0)
        tab_frame.grid_columnconfigure(4, weight=1)

        for i, tab_name in enumerate(("Preferences", "Account", "About")):
            btn = tk.Button(
                tab_frame, text=tab_name,
                bg="#f0f0f0" if i != 0 else "#2966e3",
                fg="#333" if i != 0 else "white",
                font=("Segoe UI", 12, "bold"), bd=0, padx=26, pady=13,
                activebackground="#2966e3", activeforeground="white",
                relief="flat",
                command=lambda n=tab_name: self.show_panel(n)
            )
            btn.grid(row=0, column=i+1, padx=(0 if i == 0 else 8, 0))
            self.tabs[tab_name] = btn

        container = tk.Frame(self, bg="#23272A")
        container.pack(fill="both", expand=True)
        self.panel_container = container

        self.create_preferences_panel()
        self.create_account_panel(user_info)
        self.create_about_panel()
        self.show_panel("Preferences")

    def show_panel(self, tab_name):
        for name, panel in self.panels.items():
            panel.forget()
        for name, btn in self.tabs.items():
            if name == tab_name:
                btn.config(bg="#2966e3", fg="white")
            else:
                btn.config(bg="#f0f0f0", fg="#333")
        self.panels[tab_name].pack(fill="both", expand=True)

    def create_preferences_panel(self):
        frame = tk.Frame(self.panel_container, bg="#23272A")
        tk.Label(
            frame, text="Theme Selection", bg="#23272A", fg="#fff",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=32, pady=(38, 14))

        self.theme = tk.StringVar(value="Dark")
        btn_light = tk.Button(
            frame, text="Light Mode", bg="#f0f0f0", fg="#333",
            font=("Segoe UI", 12, "bold"), bd=0, relief="flat", padx=34, pady=13,
            activebackground="#2966e3", activeforeground="white",
            command=lambda: self.set_theme("Light")
        )
        btn_dark = tk.Button(
            frame, text="Dark Mode", bg="#2966e3", fg="white",
            font=("Segoe UI", 12, "bold"), bd=0, relief="flat", padx=34, pady=13,
            activebackground="#2966e3", activeforeground="white",
            command=lambda: self.set_theme("Dark")
        )
        btn_light.place(x=40, y=78, width=145)
        btn_dark.place(x=200, y=78, width=145)
        self.btn_light = btn_light
        self.btn_dark = btn_dark
        frame.pack_propagate(False)

        def update_buttons():
            current = self.theme.get()
            if current == "Light":
                self.btn_light.config(bg="#2966e3", fg="white")
                self.btn_dark.config(bg="#f0f0f0", fg="#333")
            else:
                self.btn_dark.config(bg="#2966e3", fg="white")
                self.btn_light.config(bg="#f0f0f0", fg="#333")

        self.update_buttons = update_buttons

        self.set_theme = self._set_theme  # bind with full context
        self.update_buttons()
        self.panels["Preferences"] = frame

    def _set_theme(self, theme):
        self.theme.set(theme)
        self.update_buttons()
        
        # Call the main GUI theme functions
        if theme == "Light":
            self.light_mode_func()
        else:
            self.dark_mode_func()
            
        print(f"Settings window theme changed to: {theme}")

    def create_account_panel(self, user_info):
        frame = tk.Frame(self.panel_container, bg="#23272A")
        with urllib.request.urlopen(user_info["picture"]) as u:
            raw_data = u.read()
        #self.image = tk.PhotoImage(data=base64.encodebytes(raw_data))
        image = ImageTk.PhotoImage(Image.open(io.BytesIO(raw_data)))
        name = user_info.get("name", "User") if hasattr(user_info, "get") else getattr(user_info, "name", "User")
        label = tk.Label(frame, image=image)
        # Keep a reference to prevent garbage collection (this is correct tkinter usage)
        setattr(label, 'image_ref', image)  # type: ignore
        label.pack(pady=(50, 10))
        tk.Label(frame, text=f"Name: {name}", bg="#23272A", fg="#fff", font=("Segoe UI", 12)).pack(pady=3)
        self.panels["Account"] = frame

    def create_about_panel(self):
        frame = tk.Frame(self.panel_container, bg="#23272A")
        desc = (
            "SentiGuard is an innovative AI-powered desktop companion designed\n"
            "to passively monitor typing behavior for early signs of emotional distress.\n\n"
            "Our goal is to provide a real-time, privacy-first solution that\n"
            "supports mental well-being, especially for students and remote workers,\n"
            "by offering insights and alerting guardians for timely intervention."
        )
        tk.Label(frame, text=desc, bg="#23272A", fg="#fff",
                 font=("Segoe UI", 11), justify="left", wraplength=380
                 ).pack(pady=(52, 8), padx=18)
        tk.Label(frame, text="Developed by: xEN coders", bg="#23272A",
                 fg="#aad6ff", font=("Segoe UI", 12, "italic")).pack(pady=(12, 8), padx=18)
        self.panels["About"] = frame
