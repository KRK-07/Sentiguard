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

# AI Companion Import (Optional - graceful fallback if not available)
try:
    from ai_companion import ai_companion, chat_with_ai, get_mood_suggestions
    AI_AVAILABLE = True
    print("✅ AI Companion loaded successfully")
except ImportError as e:
    AI_AVAILABLE = False
    print(f"⚠️  AI Companion not available: {e}")
    print("💡 AI chat will be disabled. Install OpenAI package for enhanced features.")
except Exception as e:
    AI_AVAILABLE = False
    print(f"⚠️  AI Companion initialization error: {e}")

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
    
    # Global reference for theme button updates
    theme_button_updater = None
    
    def toggle_to_light_mode():
        """Switch to light mode"""
        nonlocal is_light_mode, current_view, theme_button_updater
        is_light_mode = True
        apply_theme()
        
        # Update theme buttons if they exist
        if theme_button_updater:
            root.after(10, theme_button_updater)
        
        # Refresh current view to apply theme to graphs and settings
        if current_view == 'live_graph':
            show_live_graph()
        elif current_view == 'analysis':
            show_analysis()
        elif current_view == 'settings':
            show_settings()
    
    def toggle_to_dark_mode():
        """Switch to dark mode"""
        nonlocal is_light_mode, current_view, theme_button_updater
        is_light_mode = False
        apply_theme()
        
        # Update theme buttons if they exist
        if theme_button_updater:
            root.after(10, theme_button_updater)
        
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

    def show_ai_chat():
        """Show AI Chat interface in main area"""
        nonlocal current_view
        clear_main_area()
        current_view = "ai_chat"
        
        if not AI_AVAILABLE:
            # Show AI unavailable message
            unavailable_frame = tk.Frame(main_area, bg="#1e1e1e" if not is_light_mode else "#ffffff")
            unavailable_frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            title_label = tk.Label(
                unavailable_frame,
                text="🤖 AI Chat",
                font=("Segoe UI", 24, "bold"),
                bg="#1e1e1e" if not is_light_mode else "#ffffff",
                fg="#2966e3"
            )
            title_label.pack(pady=(20, 20))
            
            info_text = (
                "AI Chat is currently unavailable.\n\n"
                "To enable AI-powered conversations:\n"
                "1. Install required packages: pip install openai\n"
                "2. Get an OpenAI API key from platform.openai.com\n"
                "3. Set environment variable: OPENAI_API_KEY=your_key\n\n"
                "The app will continue to work normally without AI chat."
            )
            
            info_label = tk.Label(
                unavailable_frame,
                text=info_text,
                font=("Segoe UI", 12),
                bg="#1e1e1e" if not is_light_mode else "#ffffff",
                fg="#cccccc" if not is_light_mode else "#666666",
                justify="center"
            )
            info_label.pack(pady=20)
            
            return
        
        # Get current theme colors
        if is_light_mode:
            main_bg = "#ffffff"
            main_fg = "#000000"
            chat_bg = "#f8f9fa"
            input_bg = "#ffffff"
            input_fg = "#000000"
            button_bg = "#2966e3"
            user_msg_bg = "#2966e3"
            ai_msg_bg = "#e9ecef"
            ai_msg_fg = "#000000"
        else:
            main_bg = "#1e1e1e"
            main_fg = "#cccccc"
            chat_bg = "#2a2a2a"
            input_bg = "#333333"
            input_fg = "#ffffff"
            button_bg = "#2966e3"
            user_msg_bg = "#2966e3"
            ai_msg_bg = "#3a3a3a"
            ai_msg_fg = "#ffffff"
        
        # Title
        title_label = tk.Label(
            main_area,
            text="🤖 AI Companion Chat",
            font=("Segoe UI", 24, "bold"),
            bg=main_bg,
            fg="#2966e3"
        )
        title_label.pack(pady=(20, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_area,
            text="Your empathetic AI companion is here to listen and support you 💙",
            font=("Segoe UI", 12),
            bg=main_bg,
            fg=main_fg
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Chat container
        chat_container = tk.Frame(main_area, bg=main_bg)
        chat_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Input area (pack first so it gets space)
        input_frame = tk.Frame(chat_container, bg=main_bg)
        input_frame.pack(side="bottom", fill="x", pady=(15, 0))
        
        # Chat display area with scrollbar
        chat_frame = tk.Frame(chat_container, bg=chat_bg, relief="flat", bd=1)
        chat_frame.pack(fill="both", expand=True)
        
        # Scrollable text widget for chat
        chat_scrollbar = tk.Scrollbar(chat_frame)
        chat_scrollbar.pack(side="right", fill="y")
        
        chat_display = tk.Text(
            chat_frame,
            bg=chat_bg,
            fg=main_fg,
            font=("Segoe UI", 11),
            wrap="word",
            yscrollcommand=chat_scrollbar.set,
            state="disabled",
            relief="flat",
            bd=10,
            padx=15,
            pady=15
        )
        chat_display.pack(side="left", fill="both", expand=True)
        chat_scrollbar.config(command=chat_display.yview)
        
        # Configure text tags for styling
        chat_display.tag_configure("user", foreground="white", background=user_msg_bg, 
                                   font=("Segoe UI", 11, "normal"), justify="right")
        chat_display.tag_configure("ai", foreground=ai_msg_fg, background=ai_msg_bg,
                                   font=("Segoe UI", 11, "normal"), justify="left")
        chat_display.tag_configure("timestamp", foreground="#888888", font=("Segoe UI", 9))
        chat_display.tag_configure("mood", foreground="#2966e3", font=("Segoe UI", 10, "italic"))
        
        # Current mood indicator
        current_mood = get_latest_mood()
        mood_text = f"Current mood: {current_mood:.2f}"
        if current_mood >= 0.2:
            mood_emoji = "😊"
        elif current_mood <= -0.2:
            mood_emoji = "😔" 
        else:
            mood_emoji = "😐"
        
        mood_label = tk.Label(
            input_frame,
            text=f"{mood_emoji} {mood_text}",
            font=("Segoe UI", 10),
            bg=main_bg,
            fg="#2966e3"
        )
        mood_label.pack(anchor="w", pady=(0, 5))
        
        # Message input
        input_row = tk.Frame(input_frame, bg=main_bg)
        input_row.pack(fill="x")
        
        message_var = tk.StringVar()
        message_entry = tk.Entry(
            input_row,
            textvariable=message_var,
            font=("Segoe UI", 12),
            bg=input_bg,
            fg=input_fg,
            relief="solid",
            bd=2,
            highlightthickness=1,
            highlightcolor="#2966e3"
        )
        message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Add placeholder text
        placeholder_text = "Type your message here..."
        message_entry.insert(0, placeholder_text)
        message_entry.config(fg="#888888")
        
        def on_entry_click(event):
            if message_entry.get() == placeholder_text:
                message_entry.delete(0, "end")
                message_entry.config(fg=input_fg)
        
        def on_focus_out(event):
            if message_entry.get() == "":
                message_entry.insert(0, placeholder_text)
                message_entry.config(fg="#888888")
        
        message_entry.bind('<FocusIn>', on_entry_click)
        message_entry.bind('<FocusOut>', on_focus_out)
        
        # Send button
        send_button = tk.Button(
            input_row,
            text="Send 💬",
            font=("Segoe UI", 12, "bold"),
            bg=button_bg,
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            activebackground="#1e4d8b",
            activeforeground="white"
        )
        send_button.pack(side="right")
        
        # Chat state
        chat_state = {"processing": False}
        
        def add_message_to_chat(message, sender="user", show_mood=False):
            """Add a message to the chat display"""
            chat_display.config(state="normal")
            
            # Add timestamp
            timestamp = datetime.datetime.now().strftime("%H:%M")
            
            if sender == "user":
                # User message (right-aligned)
                chat_display.insert("end", f"\n🙋‍♀️ You ({timestamp})\n", "timestamp")
                
                # Add mood info if requested
                if show_mood:
                    mood_info = f"Mood: {current_mood:.2f} "
                    chat_display.insert("end", mood_info, "mood")
                
                chat_display.insert("end", f"{message}\n", "user")
                
            else:
                # AI message (left-aligned) 
                chat_display.insert("end", f"\n🤖 AI Companion ({timestamp})\n", "timestamp")
                chat_display.insert("end", f"{message}\n", "ai")
            
            chat_display.insert("end", "\n")
            chat_display.config(state="disabled")
            
            # Auto-scroll to bottom
            chat_display.see("end")
        
        async def send_message():
            """Send message to AI and display response"""
            if chat_state["processing"]:
                return
                
            message = message_var.get().strip()
            if not message or message == placeholder_text:
                return
            
            # Update UI state
            chat_state["processing"] = True
            send_button.config(text="Sending...", state="disabled")
            message_entry.config(state="disabled")
            
            try:
                # Add user message to chat
                add_message_to_chat(message, sender="user", show_mood=True)
                message_var.set("")  # Clear input
                
                # Get current mood for context
                current_mood = get_latest_mood()
                
                # Determine mood trend (simplified)
                history = get_day_analysis()
                if len(history) >= 2:
                    recent_scores = [score for _, score in history[-5:]]
                    if len(recent_scores) >= 2:
                        trend = "improving" if recent_scores[-1] > recent_scores[0] else "declining"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
                
                # Get AI response
                response = await chat_with_ai(message, current_mood, trend)
                
                # Add AI response to chat
                add_message_to_chat(response, sender="ai")
                
                # Get mood-based suggestions if mood is concerning
                if current_mood < -0.3:
                    suggestions = get_mood_suggestions(current_mood)
                    if suggestions:
                        suggestion_text = f"\n💡 Here are some gentle suggestions that might help:\n• {suggestions[0]}\n• {suggestions[1]}"
                        add_message_to_chat(suggestion_text, sender="ai")
                
            except Exception as e:
                error_msg = "I'm having trouble responding right now. Please try again in a moment."
                add_message_to_chat(error_msg, sender="ai")
                print(f"AI chat error: {e}")
            
            finally:
                # Reset UI state
                chat_state["processing"] = False
                send_button.config(text="Send 💬", state="normal")
                message_entry.config(state="normal")
                message_entry.focus()
        
        def on_send_click():
            """Handle send button click"""
            import asyncio
            
            # Run async function in thread to avoid blocking GUI
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(send_message())
                finally:
                    loop.close()
            
            threading.Thread(target=run_async, daemon=True).start()
        
        def on_enter_key(event):
            """Handle Enter key press"""
            if not chat_state["processing"]:
                on_send_click()
            return "break"  # Prevent default behavior
        
        # Bind events
        send_button.config(command=on_send_click)
        message_entry.bind("<Return>", on_enter_key)
        
        # Add welcome message
        welcome_msg = (
            "Hello! I'm your AI companion here to support you. 😊\n\n"
            "I can see that your current mood is being monitored, and I'm here to listen "
            "and provide gentle support based on how you're feeling.\n\n"
            "Feel free to share what's on your mind, ask questions, or just say hello!"
        )
        add_message_to_chat(welcome_msg, sender="ai")
        
        # Focus on input
        message_entry.focus()
        
        # Show proactive check-in if appropriate
        recent_patterns = {
            'mood_declining': current_mood < -0.3,
            'stress_detected': current_mood < -0.4,
            'improvement_noted': current_mood > 0.4
        }
        
        # Add proactive message after a short delay
        def add_proactive_message():
            try:
                if AI_AVAILABLE:
                    from ai_companion import get_proactive_message
                    proactive_msg = get_proactive_message(recent_patterns)
                    if proactive_msg:
                        root.after(2000, lambda: add_message_to_chat(proactive_msg, sender="ai"))
            except:
                pass
        
        root.after(1000, add_proactive_message)

    def show_personalized_insights():
        """Show AI-powered personalized insights in main area"""
        nonlocal current_view
        clear_main_area()
        current_view = "insights"
        
        # Get current theme colors
        if is_light_mode:
            bg_color = "#ffffff"
            text_color = "#333333"
            secondary_color = "#666666" 
            card_bg = "#f8f9fa"
            accent_color = "#2966e3"
        else:
            bg_color = "#1e1e1e"
            text_color = "#ffffff"
            secondary_color = "#cccccc"
            card_bg = "#2d3748"
            accent_color = "#4299e1"
        
        # Optimized container structure with minimal padding
        insights_container = tk.Frame(main_area, bg=bg_color)
        insights_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Compact header section
        header_frame = tk.Frame(insights_container, bg=bg_color)
        header_frame.pack(fill="x", pady=(5, 15))
        
        # Compact title
        title_label = tk.Label(
            header_frame,
            text="🔮 AI Personalized Insights",
            font=("Segoe UI", 22, "bold"),
            bg=bg_color,
            fg=accent_color
        )
        title_label.pack()
        
        # Compact subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="AI-powered analysis of your mental health patterns",
            font=("Segoe UI", 11),
            bg=bg_color,
            fg=secondary_color,
            wraplength=600
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Improved responsive layout function
        def update_responsive_layout():
            try:
                container_width = insights_container.winfo_width()
                if container_width > 1:
                    # More conservative font scaling
                    if container_width < 500:
                        title_label.configure(font=("Segoe UI", 18, "bold"))
                        subtitle_label.configure(font=("Segoe UI", 10), wraplength=container_width - 50)
                    elif container_width < 700:
                        title_label.configure(font=("Segoe UI", 20, "bold"))
                        subtitle_label.configure(font=("Segoe UI", 10), wraplength=container_width - 40)
                    elif container_width < 1000:
                        title_label.configure(font=("Segoe UI", 22, "bold"))
                        subtitle_label.configure(font=("Segoe UI", 11), wraplength=600)
                    else:
                        title_label.configure(font=("Segoe UI", 24, "bold"))
                        subtitle_label.configure(font=("Segoe UI", 11), wraplength=700)
            except:
                pass
        
        # Bind responsive updates with proper timing
        insights_container.bind("<Configure>", lambda e: root.after(20, update_responsive_layout))
        root.after(150, update_responsive_layout)
        
        # Compact loading indicator
        loading_frame = tk.Frame(insights_container, bg=bg_color)
        loading_frame.pack(fill="both", expand=True)
        
        # Center the loading content vertically and horizontally
        loading_center = tk.Frame(loading_frame, bg=bg_color)
        loading_center.pack(expand=True)
        
        loading_label = tk.Label(
            loading_center,
            text="🧠 Analyzing your patterns with AI...\nThis may take a moment.",
            font=("Segoe UI", 14),
            bg=bg_color,
            fg=accent_color,
            justify="center"
        )
        loading_label.pack(pady=(0, 10))
        
        # Compact progress indicator
        progress_dots = tk.Label(
            loading_center,
            text="● ● ●",
            font=("Segoe UI", 18),
            bg=bg_color,
            fg=secondary_color
        )
        progress_dots.pack()
        
        # Animate progress dots
        def animate_progress():
            current_text = progress_dots.cget("text")
            if current_text == "● ● ●":
                progress_dots.config(text="○ ● ●")
            elif current_text == "○ ● ●":
                progress_dots.config(text="● ○ ●")
            elif current_text == "● ○ ●":
                progress_dots.config(text="● ● ○")
            else:
                progress_dots.config(text="● ● ●")
            
            # Continue animation if still loading
            if loading_frame.winfo_exists():
                root.after(500, animate_progress)
        
        animate_progress()
        
        def load_insights_async():
            """Load insights in background thread"""
            import asyncio
            from personalized_insights import get_personalized_insights
            
            async def get_insights():
                try:
                    insights_summary = await get_personalized_insights()
                    root.after(0, lambda: display_insights(insights_summary))
                except Exception as e:
                    root.after(0, lambda: display_error(str(e)))
            
            # Run in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(get_insights())
            finally:
                loop.close()
        
        def display_insights(insights_summary):
            """Display the generated insights"""
            # Clear loading
            loading_frame.destroy()
            
            if not insights_summary:
                # Compact no data display
                no_data_frame = tk.Frame(insights_container, bg=bg_color)
                no_data_frame.pack(expand=True)
                
                no_data_icon = tk.Label(
                    no_data_frame,
                    text="📊",
                    font=("Segoe UI", 48),
                    bg=bg_color,
                    fg=secondary_color
                )
                no_data_icon.pack(pady=(20, 15))
                
                no_data_label = tk.Label(
                    no_data_frame,
                    text="Not enough data for AI insights yet!\n\nKeep using Sentiguard to unlock personalized insights.",
                    font=("Segoe UI", 12),
                    bg=bg_color,
                    fg=text_color,
                    justify="center",
                    wraplength=400
                )
                no_data_label.pack()
                
                return
            
            # Compact scrollable content area
            content_container = tk.Frame(insights_container, bg=bg_color)
            content_container.pack(fill="both", expand=True, pady=(5, 0))
            
            canvas = tk.Canvas(content_container, bg=bg_color, highlightthickness=0)
            scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
            
            # Scrollable frame optimized for different window sizes
            scrollable_frame = tk.Frame(canvas, bg=bg_color)
            
            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                # Center the content horizontally
                canvas_width = canvas.winfo_width()
                frame_width = scrollable_frame.winfo_reqwidth()
                if canvas_width > frame_width:
                    x_offset = (canvas_width - frame_width) // 2
                else:
                    x_offset = 0
                canvas.coords("content_frame", x_offset, 0)
            
            scrollable_frame.bind("<Configure>", on_frame_configure)
            
            # Create window with centering capability
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="content_frame")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Update canvas scroll region and centering on canvas resize
            def on_canvas_configure(event):
                on_frame_configure(None)
            
            canvas.bind("<Configure>", on_canvas_configure)
            
            # Adaptive content wrapper
            content_wrapper = tk.Frame(scrollable_frame, bg=bg_color)
            content_wrapper.pack(fill="x", padx=15)
            
            # Compact summary card
            summary_card = tk.Frame(content_wrapper, bg=card_bg, relief="solid", bd=1)
            summary_card.pack(fill="x", pady=(5, 15), ipady=3)
            
            summary_title = tk.Label(
                summary_card,
                text="💙 Your Personal Summary",
                font=("Segoe UI", 15, "bold"),
                bg=card_bg,
                fg=accent_color
            )
            summary_title.pack(pady=(15, 8))
            
            summary_text = tk.Label(
                summary_card,
                text=insights_summary.personal_message,
                font=("Segoe UI", 11),
                bg=card_bg,
                fg=text_color,
                wraplength=600,
                justify="left"
            )
            summary_text.pack(pady=(0, 15), padx=20)
            
            # Optimized responsive content function
            def update_content_responsive():
                try:
                    container_width = insights_container.winfo_width()
                    if container_width > 1:
                        # More conservative sizing for better windowed mode
                        if container_width < 500:
                            wrap_length = container_width - 80
                            title_font = ("Segoe UI", 13, "bold")
                            text_font = ("Segoe UI", 10)
                        elif container_width < 700:
                            wrap_length = container_width - 100
                            title_font = ("Segoe UI", 14, "bold")
                            text_font = ("Segoe UI", 10)
                        elif container_width < 900:
                            wrap_length = 600
                            title_font = ("Segoe UI", 15, "bold")
                            text_font = ("Segoe UI", 11)
                        else:
                            wrap_length = 650
                            title_font = ("Segoe UI", 15, "bold")
                            text_font = ("Segoe UI", 11)
                        
                        # Update elements conservatively
                        wrap_length = max(300, wrap_length)
                        summary_title.configure(font=title_font)
                        summary_text.configure(font=text_font, wraplength=wrap_length)
                        
                        # Update insight cards more conservatively
                        for widget in content_wrapper.winfo_children():
                            if isinstance(widget, tk.Frame) and widget.cget("relief") == "solid":
                                for child in widget.winfo_children():
                                    if isinstance(child, tk.Label):
                                        current_wrap = child.cget("wraplength")
                                        if current_wrap and current_wrap > 0:
                                            child.configure(wraplength=wrap_length - 30)
                except:
                    pass
            
            # Optimized update timing
            content_wrapper.bind("<Configure>", lambda e: root.after(30, update_content_responsive))
            root.after(100, update_content_responsive)
            
            # Compact insights overview
            overview_frame = tk.Frame(content_wrapper, bg=bg_color)
            overview_frame.pack(fill="x", pady=(0, 10))
            
            stats_text = f"📈 {insights_summary.total_insights} insights • 🔥 {insights_summary.high_priority_count} high priority • 🎯 {insights_summary.main_theme}"
            stats_label = tk.Label(
                overview_frame,
                text=stats_text,
                font=("Segoe UI", 10),
                bg=bg_color,
                fg=secondary_color
            )
            stats_label.pack()
            
            # Compact individual insights
            for i, insight in enumerate(insights_summary.insights, 1):
                insight_card = tk.Frame(content_wrapper, bg=card_bg, relief="solid", bd=1)
                insight_card.pack(fill="x", pady=6, ipady=2)
                
                # Header with title and priority
                header_frame = tk.Frame(insight_card, bg=card_bg)
                header_frame.pack(fill="x", pady=(10, 0))
                
                title_label = tk.Label(
                    header_frame,
                    text=insight.title,
                    font=("Segoe UI", 12, "bold"),
                    bg=card_bg,
                    fg=accent_color
                )
                title_label.pack(side="left", padx=(12, 0))
                
                # Priority indicator
                priority_colors = {1: "#dc3545", 2: "#fd7e14", 3: "#ffc107", 4: "#28a745", 5: "#6c757d"}
                priority_texts = {1: "High", 2: "Med-High", 3: "Medium", 4: "Low", 5: "Info"}
                
                priority_label = tk.Label(
                    header_frame,
                    text=priority_texts.get(insight.priority, "Med"),
                    font=("Segoe UI", 9, "bold"),
                    bg=priority_colors.get(insight.priority, "#6c757d"),
                    fg="white",
                    padx=6,
                    pady=2
                )
                priority_label.pack(side="right", padx=(0, 15))
                
                # Confidence indicator
                confidence_frame = tk.Frame(insight_card, bg=card_bg)
                confidence_frame.pack(fill="x", padx=15)
                
                confidence_label = tk.Label(
                    confidence_frame,
                    text=f"AI Confidence: {insight.confidence:.0%}",
                    font=("Segoe UI", 9),
                    bg=card_bg,
                    fg=secondary_color
                )
                confidence_label.pack(side="left")
                
                # Compact main insight content
                content_label = tk.Label(
                    insight_card,
                    text=insight.content,
                    font=("Segoe UI", 10),
                    bg=card_bg,
                    fg=text_color,
                    wraplength=600,
                    justify="left"
                )
                content_label.pack(pady=10, padx=15, anchor="w")
                
                # Actionable steps (if available)
                if insight.actionable_steps:
                    actions_title = tk.Label(
                        insight_card,
                        text="💡 Actions:",
                        font=("Segoe UI", 9, "bold"),
                        bg=card_bg,
                        fg=accent_color
                    )
                    actions_title.pack(anchor="w", padx=12, pady=(5, 3))
                    
                    for action in insight.actionable_steps:
                        action_label = tk.Label(
                            insight_card,
                            text=f"• {action}",
                            font=("Segoe UI", 9),
                            bg=card_bg,
                            fg=text_color,
                            wraplength=550,
                            justify="left"
                        )
                        action_label.pack(anchor="w", padx=25, pady=1)
                
                # Minimal bottom padding
                tk.Frame(insight_card, bg=card_bg, height=5).pack()
            
            # Compact refresh button
            refresh_frame = tk.Frame(content_wrapper, bg=bg_color)
            refresh_frame.pack(fill="x", pady=20)
            
            refresh_button = tk.Button(
                refresh_frame,
                text="🔄 Refresh Insights",
                font=("Segoe UI", 10, "bold"),
                bg=accent_color,
                fg="white",
                relief="flat",
                padx=20,
                pady=8,
                cursor="hand2",
                activebackground="#1e5bb8" if not is_light_mode else "#1952cc",
                activeforeground="white",
                command=lambda: refresh_insights()
            )
            refresh_button.pack()
            
            # Add hover effects
            def on_button_enter(e):
                refresh_button.config(bg="#1e5bb8" if not is_light_mode else "#1952cc")
            
            def on_button_leave(e):
                refresh_button.config(bg=accent_color)
            
            refresh_button.bind("<Enter>", on_button_enter)
            refresh_button.bind("<Leave>", on_button_leave)
            
            # Pack scrollable components with proper layout
            canvas.pack(side="left", fill="both", expand=True, padx=(0, 2))
            scrollbar.pack(side="right", fill="y")
            
            # Enable mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def display_error(error_message):
            """Display error message"""
            loading_frame.destroy()
            
            error_container = tk.Frame(insights_container, bg=bg_color)
            error_container.pack(fill="both", expand=True)
            
            error_frame = tk.Frame(error_container, bg=bg_color)
            error_frame.pack(expand=True)
            
            error_icon = tk.Label(
                error_frame,
                text="⚠️",
                font=("Segoe UI", 56),
                bg=bg_color,
                fg="#dc3545"
            )
            error_icon.pack(pady=20)
            
            error_label = tk.Label(
                error_frame,
                text=f"Error generating insights:\n{error_message}\n\nTry again in a moment.",
                font=("Segoe UI", 12),
                bg=bg_color,
                fg=text_color,
                justify="center"
            )
            error_label.pack(pady=10)
        
        def refresh_insights():
            """Refresh insights by calling the function again"""
            show_personalized_insights()
        
        # Start loading insights in background
        threading.Thread(target=load_insights_async, daemon=True).start()

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

            # Create theme toggle buttons with proper state management
            btn_light = tk.Button(
                theme_frame, text="Light Mode", 
                font=("Segoe UI", 12, "bold"), bd=0, relief="flat", padx=30, pady=12,
                cursor="hand2"
            )
            btn_light.pack(side="left", padx=(0, 10))

            btn_dark = tk.Button(
                theme_frame, text="Dark Mode",
                font=("Segoe UI", 12, "bold"), bd=0, relief="flat", padx=30, pady=12,
                cursor="hand2"
            )
            btn_dark.pack(side="left")
            
            # Function to update button states with smooth transitions
            def update_theme_buttons():
                if is_light_mode:
                    # Light mode active
                    btn_light.config(
                        bg="#2966e3", fg="white",
                        activebackground="#1e5bb8", activeforeground="white"
                    )
                    btn_dark.config(
                        bg="#f0f0f0", fg="#333",
                        activebackground="#e0e0e0", activeforeground="#333"
                    )
                else:
                    # Dark mode active  
                    btn_dark.config(
                        bg="#2966e3", fg="white",
                        activebackground="#1e5bb8", activeforeground="white"
                    )
                    btn_light.config(
                        bg="#4a4a4a", fg="#ffffff",
                        activebackground="#5a5a5a", activeforeground="#ffffff"
                    )
            
            # Register this update function globally so other theme changes can call it
            nonlocal theme_button_updater
            theme_button_updater = update_theme_buttons
            
            # Enhanced toggle functions with button updates
            def enhanced_toggle_to_light():
                toggle_to_light_mode()
                
            def enhanced_toggle_to_dark():
                toggle_to_dark_mode()
            
            # Bind enhanced functions
            btn_light.config(command=enhanced_toggle_to_light)
            btn_dark.config(command=enhanced_toggle_to_dark)
            
            # Add smooth hover effects
            def on_light_enter(e):
                if is_light_mode:
                    btn_light.config(bg="#1e5bb8")
                else:
                    btn_light.config(bg="#5a5a5a")
            
            def on_light_leave(e):
                update_theme_buttons()
                
            def on_dark_enter(e):
                if not is_light_mode:
                    btn_dark.config(bg="#1e5bb8") 
                else:
                    btn_dark.config(bg="#e0e0e0")
            
            def on_dark_leave(e):
                update_theme_buttons()
            
            btn_light.bind("<Enter>", on_light_enter)
            btn_light.bind("<Leave>", on_light_leave)
            btn_dark.bind("<Enter>", on_dark_enter)
            btn_dark.bind("<Leave>", on_dark_leave)
            
            # Initial button state setup
            update_theme_buttons()

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

    # AI Chat Button (with availability indicator)
    ai_icon = "🤖" if AI_AVAILABLE else "🤖💤"
    ai_text = "AI Chat" if AI_AVAILABLE else "AI Chat (Off)"
    btn_ai_chat = create_sidebar_btn(ai_text, ai_icon)
    btn_ai_chat.config(command=show_ai_chat)
    btn_ai_chat.pack(fill="x", pady=5)

    # Personalized Insights Button
    btn_insights = create_sidebar_btn("AI Insights", "🔮")
    btn_insights.config(command=show_personalized_insights)
    btn_insights.pack(fill="x", pady=5)

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
