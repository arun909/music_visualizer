import pygame
import numpy as np
import pyaudio
import random
import math

# Initialize Pygame
pygame.init()

# Get screen dimensions
screen_info = pygame.display.Info()
WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN)
pygame.display.set_caption("Interactive Sonic Realm")

# Advanced Color Palette
COLORS = [
    (63, 81, 181),    # Deep Blue
    (0, 150, 136),    # Teal
    (233, 30, 99),    # Pink
    (255, 152, 0),    # Orange
    (156, 39, 176),   # Purple
    (76, 175, 80),    # Green
    (255, 87, 34)     # Deep Orange
]

# Background Options
BACKGROUNDS = [
    "gradient",  # Smooth gradient
    "particles",  # Particle-based background
    "solid"  # Solid color background
]
current_background = 0  # Start with gradient

class AdvancedParticleSystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.particles = []
        self.center_attractor = {
            'x': width // 2,
            'y': height // 2,
            'strength': 0
        }

    def create_particles(self, amplitude):
        if random.random() < amplitude:
            num_particles = int(amplitude * 100)
            for _ in range(num_particles):
                self.particles.append({
                    'x': random.randint(0, self.width),
                    'y': random.randint(0, self.height),
                    'vx': random.uniform(-2, 2),
                    'vy': random.uniform(-2, 2),
                    'color': random.choice(COLORS),
                    'size': random.uniform(2, 6),
                    'lifetime': random.uniform(30, 90),
                    'phase': random.uniform(0, 2 * math.pi),
                    'wave_amplitude': random.uniform(1, 3)
                })

    def update_particles(self, amplitude):
        self.center_attractor['strength'] = amplitude * 5
        for particle in self.particles[:]:
            dx = self.center_attractor['x'] - particle['x']
            dy = self.center_attractor['y'] - particle['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            particle['phase'] += 0.1
            wave_x = math.sin(particle['phase']) * particle['wave_amplitude']
            wave_y = math.cos(particle['phase']) * particle['wave_amplitude']
            
            if distance > 0:
                attraction_factor = self.center_attractor['strength'] / distance
                particle['vx'] += dx / distance * attraction_factor + wave_x
                particle['vy'] += dy / distance * attraction_factor + wave_y
            
            particle['vx'] += random.uniform(-0.5, 0.5)
            particle['vy'] += random.uniform(-0.5, 0.5)
            
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            particle['x'] = particle['x'] % self.width
            particle['y'] = particle['y'] % self.height
            
            particle['lifetime'] -= 1
            
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)

    def render_particles(self, screen):
        for particle in self.particles:
            for i in range(3):
                glow_surface = pygame.Surface((particle['size'] * (3 - i), 
                                               particle['size'] * (3 - i)), 
                                              pygame.SRCALPHA)
                glow_color = particle['color'] + (50 - i * 15,)
                pygame.draw.circle(
                    glow_surface, 
                    glow_color, 
                    (int(glow_surface.get_width() // 2), 
                     int(glow_surface.get_height() // 2)), 
                    int(glow_surface.get_width() // 2)
                )
                screen.blit(
                    glow_surface, 
                    (particle['x'] - glow_surface.get_width() // 2, 
                     particle['y'] - glow_surface.get_height() // 2)
                )

class MusicVisualizer:
    def __init__(self):
        # Audio Setup
        self.pyaudio = pyaudio.PyAudio()
        self.stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )

        # Visualization Parameters
        self.bars = 52
        self.bar_width = WIDTH // self.bars
        self.smooth_data = [0] * self.bars
        
        # Particle System
        self.particle_system = AdvancedParticleSystem(WIDTH, HEIGHT)

    def get_frequency_data(self):
        data = np.frombuffer(self.stream.read(1024), dtype=np.int16)
        windowed_data = data * np.hanning(len(data))
        fft_data = np.abs(np.fft.fft(windowed_data)[:512])
        fft_data = fft_data / np.max(fft_data)
        
        downsampled = np.interp(
            np.linspace(0, len(fft_data), self.bars), 
            range(len(fft_data)), 
            fft_data
        )
        
        return downsampled

    def render_background(self, amplitude):
        global current_background
        if BACKGROUNDS[current_background] == "gradient":
            # Gradient background
            for y in range(HEIGHT):
                r = int(10 + amplitude * 50 * (y / HEIGHT))
                g = int(10 + amplitude * 30 * (y / HEIGHT))
                b = int(20 + amplitude * 40 * (y / HEIGHT))
                pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
        elif BACKGROUNDS[current_background] == "particles":
            # Particle-based background
            self.particle_system.render_particles(screen)
        elif BACKGROUNDS[current_background] == "solid":
            # Solid color background
            screen.fill((10, 10, 20))

    def render_amplifier_ui(self, amplitude, freq_data):
        # Amplifier-like UI
        ui_width = 300
        ui_height = 200
        ui_x = WIDTH - ui_width - 20
        ui_y = HEIGHT - ui_height - 20

        # Draw amplifier box
        pygame.draw.rect(screen, (50, 50, 50), (ui_x, ui_y, ui_width, ui_height), border_radius=10)
        pygame.draw.rect(screen, (30, 30, 30), (ui_x + 5, ui_y + 5, ui_width - 10, ui_height - 10), border_radius=8)

        # Draw amplitude meter
        meter_height = int(amplitude * 100)
        pygame.draw.rect(screen, (0, 255, 0), (ui_x + 20, ui_y + ui_height - 20 - meter_height, 20, meter_height))

        # Draw frequency peaks
        for i, magnitude in enumerate(freq_data[:10]):
            peak_height = int(magnitude * 50)
            pygame.draw.rect(screen, (255, 0, 0), (ui_x + 60 + i * 20, ui_y + ui_height - 20 - peak_height, 10, peak_height))

        # Draw labels
        font = pygame.font.SysFont("Arial", 16)
        label = font.render("Amplifier", True, (255, 255, 255))
        screen.blit(label, (ui_x + 20, ui_y + 10))

    def render(self, freq_data, amplitude):
        # Render background
        self.render_background(amplitude)

        # Render frequency bars
        for i, magnitude in enumerate(freq_data):
            bar_height = int(magnitude * HEIGHT * 2)
            color = COLORS[i % len(COLORS)]
            bar_surface = pygame.Surface((self.bar_width, bar_height), pygame.SRCALPHA)
            bar_surface.fill(color + (100,))
            screen.blit(bar_surface, (i * self.bar_width, HEIGHT - bar_height))

        # Render amplifier UI
        self.render_amplifier_ui(amplitude, freq_data)

    def run(self):
        global current_background
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:  # Change background on 'B' key press
                        current_background = (current_background + 1) % len(BACKGROUNDS)

            # Get frequency data
            freq_data = self.get_frequency_data()
            amplitude = np.mean(freq_data)

            # Generate and update particles
            self.particle_system.create_particles(amplitude)
            self.particle_system.update_particles(amplitude)

            # Render visualization
            self.render(freq_data, amplitude)

            # Update display
            pygame.display.flip()
            clock.tick(60)

        # Cleanup
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio.terminate()
        pygame.quit()

# Run the visualizer
if __name__ == "__main__":
    visualizer = MusicVisualizer()
    visualizer.run()