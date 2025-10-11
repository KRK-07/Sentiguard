#!/usr/bin/env python3
"""
Mood Background Module for Sentiguard
Provides basic mood-responsive background animations
"""

import tkinter as tk
import math
import random
import time
import threading

class MoodBackground:
    """Basic mood-responsive background with simple animations"""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.canvas = None
        self.animation_running = False
        self.animation_thread = None
        self.current_mood = "neutral"
        self.particles = []
        self.particle_count = 15
        
        # Define basic mood color palettes
        self.mood_colors = {
            "very_positive": {
                "primary": (34, 139, 34),       # Forest Green
                "secondary": (144, 238, 144),   # Light Green
                "accent": (0, 128, 0),          # Green
                "particle": (255, 255, 255)    # White
            },
            "positive": {
                "primary": (50, 205, 50),       # Lime Green
                "secondary": (152, 251, 152),   # Pale Green
                "accent": (34, 139, 34),        # Forest Green
                "particle": (255, 255, 255)    # White
            },
            "neutral": {
                "primary": (105, 105, 105),     # Dim Gray
                "secondary": (169, 169, 169),   # Dark Gray
                "accent": (128, 128, 128),      # Gray
                "particle": (211, 211, 211)    # Light Gray
            },
            "slightly_negative": {
                "primary": (255, 99, 71),       # Tomato Red
                "secondary": (255, 160, 122),   # Light Salmon
                "accent": (220, 20, 60),        # Crimson
                "particle": (255, 255, 255)    # White
            },
            "negative": {
                "primary": (220, 20, 60),       # Crimson
                "secondary": (255, 105, 180),   # Hot Pink
                "accent": (178, 34, 34),        # Fire Brick
                "particle": (255, 200, 200)    # Light Pink
            },
            "very_negative": {
                "primary": (139, 0, 0),         # Dark Red
                "secondary": (178, 34, 34),     # Fire Brick
                "accent": (220, 20, 60),        # Crimson
                "particle": (255, 182, 193)    # Light Pink
            }
        }
        
        self.setup_canvas()
        self.create_particles()
        self.start_animation()
    
    def setup_canvas(self):
        """Setup the background canvas"""
        try:
            self.canvas = tk.Canvas(
                self.parent,
                highlightthickness=0,
                bd=0
            )
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            self.canvas.lower()  # Send to back
            
        except Exception as e:
            print(f"Error setting up mood background canvas: {e}")
    
    def categorize_mood(self, mood_score):
        """Convert mood score to mood category"""
        if mood_score >= 0.6:
            return "very_positive"
        elif mood_score >= 0.2:
            return "positive"
        elif mood_score >= -0.1:
            return "neutral"
        elif mood_score >= -0.4:
            return "slightly_negative"
        elif mood_score >= -0.7:
            return "negative"
        else:
            return "very_negative"
    
    def update_mood(self, mood_score):
        """Update background based on mood score"""
        try:
            new_mood = self.categorize_mood(mood_score)
            if new_mood != self.current_mood:
                self.current_mood = new_mood
                self.redraw_background()
                
        except Exception as e:
            print(f"Error updating mood background: {e}")
    
    def create_particles(self):
        """Create basic floating particles"""
        self.particles = []
        for i in range(self.particle_count):
            particle = {
                'x': random.uniform(0, 800),
                'y': random.uniform(0, 600),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.3, 0.3),
                'size': random.uniform(2, 4),
                'opacity': random.uniform(0.3, 0.7),
                'phase': random.uniform(0, 2 * math.pi)
            }
            self.particles.append(particle)
    
    def create_gradient(self, colors, width, height):
        """Create basic gradient background"""
        try:
            if not self.canvas:
                return
                
            # Clear previous background
            self.canvas.delete("background")
                
            primary = colors['primary']
            secondary = colors['secondary']
            
            # Create simple vertical gradient
            steps = 30
            for i in range(steps):
                y1 = int(height * i / steps)
                y2 = int(height * (i + 1) / steps)
                
                # Interpolate between primary and secondary colors
                ratio = i / (steps - 1) if steps > 1 else 0
                r = int(primary[0] + (secondary[0] - primary[0]) * ratio)
                g = int(primary[1] + (secondary[1] - primary[1]) * ratio)
                b = int(primary[2] + (secondary[2] - primary[2]) * ratio)
                
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                self.canvas.create_rectangle(
                    0, y1, width, y2,
                    fill=color,
                    outline="",
                    tags="background"
                )
                
        except Exception as e:
            print(f"Error creating gradient: {e}")
    
    def update_particles(self):
        """Update basic particle system"""
        try:
            if not self.canvas:
                return
                
            self.canvas.delete("particles")
            
            colors = self.mood_colors[self.current_mood]
            particle_color = colors['particle']
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            for particle in self.particles:
                # Update particle position
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['phase'] += 0.02
                
                # Add gentle floating motion
                particle['x'] += math.sin(particle['phase']) * 0.2
                particle['y'] += math.cos(particle['phase'] * 0.8) * 0.1
                
                # Wrap around screen
                if particle['x'] < -10:
                    particle['x'] = canvas_width + 10
                elif particle['x'] > canvas_width + 10:
                    particle['x'] = -10
                if particle['y'] < -10:
                    particle['y'] = canvas_height + 10
                elif particle['y'] > canvas_height + 10:
                    particle['y'] = -10
                
                # Draw particle
                r, g, b = particle_color
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                self.canvas.create_oval(
                    particle['x'] - particle['size'], particle['y'] - particle['size'],
                    particle['x'] + particle['size'], particle['y'] + particle['size'],
                    fill=color,
                    outline="",
                    tags="particles"
                )
                
        except Exception as e:
            print(f"Error updating particles: {e}")
    
    def redraw_background(self):
        """Redraw the entire background"""
        try:
            if not self.canvas:
                return
                
            # Get canvas dimensions
            self.canvas.update_idletasks()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width > 1 and height > 1:
                colors = self.mood_colors[self.current_mood]
                self.create_gradient(colors, width, height)
                
        except Exception as e:
            print(f"Error redrawing background: {e}")
    
    def start_animation(self):
        """Start the background animation"""
        if not self.animation_running:
            self.animation_running = True
            self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.animation_thread.start()
    
    def stop_animation(self):
        """Stop the background animation"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
    
    def _animation_loop(self):
        """Basic animation loop"""
        while self.animation_running:
            try:
                # Update particles
                self.parent.after_idle(self.update_particles)
                
                # Occasional background redraws
                if random.random() < 0.1:  # 10% chance each frame
                    self.parent.after_idle(self.redraw_background)
                
                time.sleep(0.05)  # ~20 FPS
                
            except Exception as e:
                print(f"Animation loop error: {e}")
                break
    
    def destroy(self):
        """Clean up resources"""
        self.stop_animation()
        if self.canvas:
            self.canvas.destroy()

# Test function
if __name__ == "__main__":
    import tkinter as tk
    
    def test_mood_background():
        root = tk.Tk()
        root.title("Mood Background Test")
        root.geometry("800x600")
        
        bg = MoodBackground(root)
        
        # Test different moods
        moods = [0.8, 0.3, 0.0, -0.3, -0.6, -0.9]
        mood_index = 0
        
        def cycle_mood():
            nonlocal mood_index
            bg.update_mood(moods[mood_index])
            mood_index = (mood_index + 1) % len(moods)
            root.after(3000, cycle_mood)  # Change every 3 seconds
        
        cycle_mood()
        root.mainloop()
    
    test_mood_background()