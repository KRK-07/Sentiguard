#!/usr/bin/env python3
"""
Enhanced Mood Background with Wave Effects
Provides sophisticated animations and effects based on user mood
"""

import tkinter as tk
import math
import random
import time
import threading

class EnhancedMoodBackground:
    """Enhanced mood-responsive background with wave effects and particles"""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.canvas = None
        self.animation_running = False
        self.animation_thread = None
        self.current_mood = "neutral"
        
        # Wave animation parameters
        self.wave_offset = 0
        self.wave_amplitude = 30
        self.wave_frequency = 0.02
        self.wave_speed = 0.05
        
        # Enhanced particle system
        self.particle_count = 20
        self.particles = []
        
        # Define mood color palettes
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
        self.create_enhanced_particles()
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
        self.create_enhanced_particles()
    
    def create_enhanced_particles(self):
        """Create enhanced particles with different behaviors"""
        self.particles = []
        for i in range(self.particle_count):
            particle_type = random.choice(['floater', 'orbiter', 'drifter'])
            
            if particle_type == 'floater':
                particle = {
                    'type': 'floater',
                    'x': random.uniform(0, 800),
                    'y': random.uniform(0, 600),
                    'vx': random.uniform(-0.3, 0.3),
                    'vy': random.uniform(-0.5, -0.1),
                    'size': random.uniform(2, 5),
                    'opacity': random.uniform(0.3, 0.7),
                    'phase': random.uniform(0, 2 * math.pi),
                    'pulse_speed': random.uniform(0.02, 0.05)
                }
            elif particle_type == 'orbiter':
                center_x = random.uniform(200, 600)
                center_y = random.uniform(150, 450)
                particle = {
                    'type': 'orbiter',
                    'center_x': center_x,
                    'center_y': center_y,
                    'radius': random.uniform(50, 150),
                    'angle': random.uniform(0, 2 * math.pi),
                    'angular_speed': random.uniform(0.005, 0.02),
                    'size': random.uniform(1, 3),
                    'opacity': random.uniform(0.2, 0.4),
                    'x': center_x,
                    'y': center_y
                }
            else:  # drifter
                particle = {
                    'type': 'drifter',
                    'x': random.uniform(0, 800),
                    'y': random.uniform(0, 600),
                    'vx': random.uniform(-0.2, 0.2),
                    'vy': random.uniform(-0.3, 0.3),
                    'size': random.uniform(1, 4),
                    'opacity': random.uniform(0.1, 0.3),
                    'phase': random.uniform(0, 2 * math.pi),
                    'size_pulse': random.uniform(0.01, 0.03)
                }
            
            self.particles.append(particle)
    
    def create_gradient(self, colors, width, height):
        """Create enhanced gradient with wave effects"""
        try:
            # Clear canvas
            if self.canvas:
                self.canvas.delete("background")
            
            # Create base gradient
            self._create_base_gradient(colors, width, height)
            
            # Add wave effects
            self.create_wave_effects(colors, width, height)
            
        except Exception as e:
            print(f"Error creating enhanced gradient: {e}")
    
    def _create_base_gradient(self, colors, width, height):
        """Create the base gradient background"""
        try:
            if not self.canvas:
                return
                
            primary = colors['primary']
            secondary = colors['secondary']
            
            # Create vertical gradient
            steps = 50
            for i in range(steps):
                y1 = int(height * i / steps)
                y2 = int(height * (i + 1) / steps)
                
                # Interpolate between primary and secondary colors
                ratio = i / (steps - 1)
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
            print(f"Error creating base gradient: {e}")
    
    def create_wave_effects(self, colors, width, height):
        """Create flowing wave effects"""
        try:
            if not self.canvas:
                return
                
            accent = colors['accent']
            wave_color = f"#{accent[0]:02x}{accent[1]:02x}{accent[2]:02x}"
            
            # Create multiple wave layers
            for layer in range(3):
                wave_points = []
                opacity = 0.3 - (layer * 0.1)
                amplitude = self.wave_amplitude * (1 - layer * 0.3)
                frequency = self.wave_frequency * (1 + layer * 0.5)
                
                for x in range(-20, width + 40, 15):
                    y_base = height * (0.3 + layer * 0.2)
                    y = y_base + math.sin((x * frequency) + self.wave_offset + (layer * math.pi/3)) * amplitude
                    wave_points.extend([x, y])
                
                # Add bottom points to close the shape
                if len(wave_points) >= 4:
                    wave_points.extend([width + 40, height + 20])
                    wave_points.extend([-20, height + 20])
                
                if len(wave_points) >= 6:
                    # Create filled polygon for wave
                    fill_color = self.blend_colors(colors['primary'], colors['secondary'], 0.5 + layer * 0.2)
                    self.canvas.create_polygon(
                        wave_points,
                        fill=fill_color,
                        outline="",
                        stipple="gray25" if layer > 0 else "",
                        tags="background"
                    )
            
            # Update wave animation
            self.wave_offset += self.wave_speed
            
        except Exception as e:
            print(f"Error creating wave effects: {e}")
    
    def blend_colors(self, color1, color2, factor):
        """Blend two RGB colors"""
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_particles(self):
        """Update enhanced particle system"""
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
                if particle['type'] == 'floater':
                    # Update floater particles with faster movement
                    particle['x'] += particle['vx'] * 1.3
                    particle['y'] += particle['vy'] * 1.3
                    particle['phase'] += particle['pulse_speed'] * 1.5  # Faster phase changes
                    
                    # Add gentle floating motion with more responsiveness
                    particle['x'] += math.sin(particle['phase']) * 0.4
                    particle['y'] += math.cos(particle['phase'] * 0.7) * 0.3
                    
                    # Reset if off screen
                    if particle['y'] < -20:
                        particle['y'] = canvas_height + 20
                        particle['x'] = random.uniform(-10, canvas_width + 10)
                    
                    if particle['x'] < -20 or particle['x'] > canvas_width + 20:
                        particle['x'] = random.uniform(0, canvas_width)
                    
                    # Dynamic size based on pulse
                    dynamic_size = particle['size'] * (1 + math.sin(particle['phase'] * 2) * 0.2)
                    
                elif particle['type'] == 'orbiter':
                    # Update orbiter particles with faster orbital speed
                    particle['angle'] += particle['angular_speed'] * 1.4  # Faster orbits
                    particle['x'] = particle['center_x'] + math.cos(particle['angle']) * particle['radius']
                    particle['y'] = particle['center_y'] + math.sin(particle['angle']) * particle['radius'] * 0.6
                    dynamic_size = particle['size']
                    
                else:  # drifter
                    # Update drifter particles with more responsive movement
                    particle['x'] += particle['vx'] * 1.2
                    particle['y'] += particle['vy'] * 1.2
                    particle['phase'] += particle['size_pulse'] * 1.3  # Faster size pulsing
                    
                    # Gentle random walk with slightly more variation
                    particle['vx'] += random.uniform(-0.015, 0.015)
                    particle['vy'] += random.uniform(-0.015, 0.015)
                    
                    # Clamp velocities
                    particle['vx'] = max(-0.5, min(0.5, particle['vx']))
                    particle['vy'] = max(-0.5, min(0.5, particle['vy']))
                    
                    # Wrap around screen
                    if particle['x'] < -10:
                        particle['x'] = canvas_width + 10
                    elif particle['x'] > canvas_width + 10:
                        particle['x'] = -10
                    if particle['y'] < -10:
                        particle['y'] = canvas_height + 10
                    elif particle['y'] > canvas_height + 10:
                        particle['y'] = -10
                    
                    dynamic_size = particle['size'] * (1 + math.sin(particle['phase']) * 0.3)
                
                # Draw particle with mood-based color
                r = int(particle_color[0])
                g = int(particle_color[1])
                b = int(particle_color[2])
                
                # Add some color variation
                color_variance = 30
                r = max(0, min(255, r + random.randint(-color_variance, color_variance)))
                g = max(0, min(255, g + random.randint(-color_variance, color_variance)))
                b = max(0, min(255, b + random.randint(-color_variance, color_variance)))
                
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Create particle with glow effect
                glow_size = dynamic_size * 1.5
                self.canvas.create_oval(
                    particle['x'] - glow_size, particle['y'] - glow_size,
                    particle['x'] + glow_size, particle['y'] + glow_size,
                    fill=color,
                    outline="",
                    stipple="gray12",
                    tags="particles"
                )
                
                self.canvas.create_oval(
                    particle['x'] - dynamic_size, particle['y'] - dynamic_size,
                    particle['x'] + dynamic_size, particle['y'] + dynamic_size,
                    fill=color,
                    outline="",
                    tags="particles"
                )
                
        except Exception as e:
            print(f"Error updating enhanced particles: {e}")
    
    def _animation_loop(self):
        """Enhanced animation loop with wave updates"""
        while self.animation_running:
            try:
                # Update particles and waves
                self.parent.after_idle(self.update_particles)
                
                # More frequent background redraws for smoother mood transitions
                if random.random() < 0.2:  # 20% chance each frame for faster updates
                    self.parent.after_idle(self.redraw_background)
                
                time.sleep(0.03)  # ~33 FPS for much more responsive animations
                
            except Exception as e:
                print(f"Enhanced animation loop error: {e}")
                break
