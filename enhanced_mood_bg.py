#!/usr/bin/env python3
"""
Enhanced Mood Background with Wave Effects
Provides more sophisticated animations and effects
"""

import tkinter as tk
import math
import random
import time
from mood_background import MoodBackground

class EnhancedMoodBackground(MoodBackground):
    """Enhanced version with wave effects and better animations"""
    
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        
        # Wave animation parameters
        self.wave_offset = 0
        self.wave_amplitude = 30
        self.wave_frequency = 0.02
        self.wave_speed = 0.05
        
        # Enhanced particle system
        self.particle_count = 20  # Slightly fewer for better performance
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
                self.canvas.delete("background")  # type: ignore
            
            # Create base gradient
            super().create_gradient(colors, width, height)
            
            # Add wave effects
            self.create_wave_effects(colors, width, height)
            
        except Exception as e:
            print(f"Error creating enhanced gradient: {e}")
    
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
                    self.canvas.create_polygon(  # type: ignore
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
                
            self.canvas.delete("particles")  # type: ignore
            
            colors = self.mood_colors[self.current_mood]
            particle_color = colors['particle']
            
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()  # type: ignore
            canvas_height = self.canvas.winfo_height()  # type: ignore
            
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
                self.canvas.create_oval(  # type: ignore
                    particle['x'] - glow_size, particle['y'] - glow_size,
                    particle['x'] + glow_size, particle['y'] + glow_size,
                    fill=color,
                    outline="",
                    stipple="gray12",
                    tags="particles"
                )
                
                self.canvas.create_oval(  # type: ignore
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
