#!/usr/bin/env python3
"""
Dynamic Background System for SentiGuard
Provides mood-responsive gradients and animated particles
"""

import tkinter as tk
import random
import threading
import time
import math

class MoodBackground:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.canvas = None
        self.particles = []
        self.current_mood = "neutral"
        self.animation_running = False
        self.animation_thread = None
        
        # Mood color schemes (RGB values)
        self.mood_colors = {
            'positive': {
                'primary': (34, 139, 34),      # Forest Green
                'secondary': (50, 205, 50),    # Lime Green  
                'accent': (144, 238, 144),     # Light Green
                'particle': (255, 255, 255, 0.6)  # White particles
            },
            'negative': {
                'primary': (139, 34, 34),      # Dark Red
                'secondary': (205, 50, 50),    # Red
                'accent': (238, 144, 144),     # Light Red
                'particle': (255, 200, 200, 0.4)  # Pink particles
            },
            'neutral': {
                'primary': (34, 50, 139),      # Dark Blue
                'secondary': (50, 100, 205),   # Blue
                'accent': (144, 180, 238),     # Light Blue
                'particle': (200, 220, 255, 0.5)  # Light Blue particles
            }
        }
        
        self.particle_count = 25
        self.setup_canvas()
        self.create_particles()
        
    def setup_canvas(self):
        """Create the background canvas"""
        if self.canvas:
            self.canvas.destroy()
            
        # Create canvas that covers the entire parent
        self.canvas = tk.Canvas(
            self.parent,
            highlightthickness=0,
            bg='#1e1e1e'
        )
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Send canvas to back so other widgets appear on top
        self.parent.update()
        for child in self.parent.winfo_children():
            if child != self.canvas:
                child.lift()  # Bring other widgets to front
        
    def create_particles(self):
        """Create floating particles for ambient effect"""
        self.particles = []
        for _ in range(self.particle_count):
            particle = {
                'x': random.uniform(0, 800),
                'y': random.uniform(0, 600),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.8, -0.2),
                'size': random.uniform(2, 6),
                'opacity': random.uniform(0.2, 0.6),
                'phase': random.uniform(0, 2 * math.pi)
            }
            self.particles.append(particle)
    
    def update_mood(self, mood_score):
        """Update background based on mood score"""
        if mood_score >= 0.3:
            new_mood = 'positive'
        elif mood_score <= -0.3:
            new_mood = 'negative'
        else:
            new_mood = 'neutral'
            
        if new_mood != self.current_mood:
            self.current_mood = new_mood
            self.redraw_background()
    
    def create_gradient(self, colors, width, height):
        """Create a gradient background"""
        try:
            # Clear canvas
            self.canvas.delete("background")  # type: ignore
            
            # Create radial gradient effect using multiple overlapping rectangles
            center_x, center_y = width // 2, height // 2
            max_radius = max(width, height)
            
            primary = colors['primary']
            secondary = colors['secondary']
            accent = colors['accent']
            
            # Create multiple gradient layers
            steps = 50
            for i in range(steps):
                # Calculate position and size
                progress = i / steps
                radius = int(max_radius * progress)
                
                # Interpolate colors
                r = int(primary[0] + (secondary[0] - primary[0]) * progress)
                g = int(primary[1] + (secondary[1] - primary[1]) * progress)
                b = int(primary[2] + (secondary[2] - primary[2]) * progress)
                
                # Create color with slight transparency
                alpha = int(255 * (0.8 - progress * 0.3))
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Draw circle
                x1, y1 = center_x - radius, center_y - radius
                x2, y2 = center_x + radius, center_y + radius
                
                if self.canvas:
                    self.canvas.create_oval(
                        x1, y1, x2, y2,
                        fill=color,
                        outline="",
                        tags="background"
                    )  # type: ignore
            
            # Add subtle overlay pattern
            self.create_overlay_pattern(colors, width, height)
            
        except Exception as e:
            print(f"Error creating gradient: {e}")
    
    def create_overlay_pattern(self, colors, width, height):
        """Create subtle overlay patterns"""
        try:
            accent = colors['accent']
            pattern_color = f"#{accent[0]:02x}{accent[1]:02x}{accent[2]:02x}"
            
            # Create flowing wave pattern
            wave_points = []
            for x in range(0, width + 20, 20):
                y = height // 2 + math.sin(x * 0.01) * 30
                wave_points.extend([x, y])
            
            if len(wave_points) >= 4 and self.canvas:
                self.canvas.create_line(
                    wave_points,
                    fill=pattern_color,
                    width=2,
                    smooth=True,
                    tags="background"
                )
            
            # Add some geometric accents
            for i in range(3):
                x = random.uniform(width * 0.1, width * 0.9)
                y = random.uniform(height * 0.1, height * 0.9)
                size = random.uniform(20, 40)
                
                if self.canvas:
                    self.canvas.create_oval(
                        x - size, y - size, x + size, y + size,
                        outline=pattern_color,
                        width=1,
                        fill="",
                        tags="background"
                )
                
        except Exception as e:
            print(f"Error creating overlay: {e}")
    
    def update_particles(self):
        """Update particle positions and draw them"""
        try:
            if self.canvas:
                self.canvas.delete("particles")
            
            colors = self.mood_colors[self.current_mood]
            particle_color = colors['particle']
            
            for particle in self.particles:
                # Update position with faster movement
                particle['x'] += particle['vx'] * 1.2
                particle['y'] += particle['vy'] * 1.2
                particle['phase'] += 0.03  # Faster phase changes
                
                # Add floating effect
                float_offset = math.sin(particle['phase']) * 0.5
                particle['x'] += float_offset
                
                # Reset particle if it goes off screen
                if self.canvas:
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()
                else:
                    canvas_width = 800  # Default width
                    canvas_height = 600  # Default height
                
                if canvas_width > 1 and canvas_height > 1:  # Valid dimensions
                    if particle['y'] < -10:
                        particle['y'] = canvas_height + 10
                        particle['x'] = random.uniform(0, canvas_width)
                    
                    if particle['x'] < -10:
                        particle['x'] = canvas_width + 10
                    elif particle['x'] > canvas_width + 10:
                        particle['x'] = -10
                    
                    # Draw particle
                    size = particle['size']
                    opacity = int(255 * particle['opacity'])
                    
                    # Create particle color with current mood
                    r = int(particle_color[0])
                    g = int(particle_color[1])
                    b = int(particle_color[2])
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    if self.canvas:
                        self.canvas.create_oval(
                            particle['x'] - size, particle['y'] - size,
                            particle['x'] + size, particle['y'] + size,
                            fill=color,
                            outline="",
                            tags="particles"
                        )
                    
        except Exception as e:
            print(f"Error updating particles: {e}")
    
    def redraw_background(self):
        """Redraw the entire background"""
        try:
            # Get canvas dimensions
            self.canvas.update_idletasks()  # type: ignore
            width = self.canvas.winfo_width()  # type: ignore
            height = self.canvas.winfo_height()  # type: ignore
            
            if width > 1 and height > 1:  # Valid dimensions
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
        """Main animation loop"""
        while self.animation_running:
            try:
                # Update particles in main thread
                self.parent.after_idle(self.update_particles)
                time.sleep(0.02)  # ~50 FPS for more responsive animations
            except Exception as e:
                print(f"Animation loop error: {e}")
                break
    
    def resize_canvas(self, event=None):
        """Handle canvas resize"""
        self.parent.after_idle(self.redraw_background)
    
    def destroy(self):
        """Clean up resources"""
        self.stop_animation()
        if self.canvas:
            self.canvas.destroy()
