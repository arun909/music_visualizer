
import pygame
import numpy as np
import pyaudio
import colorsys

class MusicVisualizer:
    def __init__(self):
        pygame.init()
        
        # Window settings
        self.display_info = pygame.display.Info()
        self.WIDTH = 800
        self.HEIGHT = 600
        self.fullscreen = False
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Music Visualizer")
        
        # Audio settings


        self.CHUNK = 1025
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        # Visualization settings
        self.params = {
            'sensitivity': 15.0,
            'bar_width': 6,  # Decreased bar width
            'show_peaks': True,
            'color_hue': 0.5  # Initial color hue for the bars
        }
        
        self.BAR_COUNT = self.WIDTH // (self.params['bar_width'] + 2)
        self.prev_heights = np.ones(self.BAR_COUNT) * (self.HEIGHT // 4)  # Start at a quarter height
        self.peak_heights = np.zeros(self.BAR_COUNT)
    
    def update_dimensions(self, width, height):
        self.WIDTH = width
        self.HEIGHT = height
        self.BAR_COUNT = self.WIDTH // (self.params['bar_width'] + 2)
        self.prev_heights = np.ones(self.BAR_COUNT) * (self.HEIGHT // 4)
        self.peak_heights = np.zeros(self.BAR_COUNT)
    
    def get_audio_data(self):
        try:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.float32)
            
            # Take absolute value to get magnitude
            audio_data = np.abs(audio_data)
            
            # Perform FFT
            fft_data = np.abs(np.fft.fft(audio_data)[:self.CHUNK//2])
            
            # Apply logarithmic scaling to better represent audio frequencies
            fft_data = np.log10(fft_data + 1)
            
            # Normalize the data
            fft_data = fft_data / (np.max(fft_data) + 1e-10)
            
            # Create frequency bins
            bins = np.array_split(fft_data, self.BAR_COUNT)
            bar_values = [np.mean(bin) for bin in bins]
            
            # Additional scaling to make the visualization more responsive
            bar_values = np.array(bar_values) * 2.0
            
            return bar_values
            
        except Exception as e:
            print(f"Audio error: {e}")
            return np.zeros(self.BAR_COUNT)
    
    def draw_gradient_background(self, audio_data):
        # Generate a cool gradient background based on the bass
        bass = np.mean(audio_data[:5]) if len(audio_data) > 5 else 0
        hue = (self.params['color_hue'] + bass * 0.2) % 1.0
        saturation = 0.7 + min(0.2, bass * 0.5)
        value = 0.4 + min(0.3, bass * 0.3)

        # Create color gradients
        top_color = colorsys.hsv_to_rgb(hue, saturation, value)
        bottom_color = colorsys.hsv_to_rgb((hue + 0.1) % 1.0, saturation, value)

        # Convert to RGB values (scaled to 255)
        top_color = tuple(int(c * 255) for c in top_color)
        bottom_color = tuple(int(c * 255) for c in bottom_color)
        
        # Draw gradient background
        for y in range(self.HEIGHT):
            ratio = y / self.HEIGHT
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.WIDTH, y))
    
    def draw_visualizer(self, audio_data):
        # Calculate bass for background pulse
        bass = np.mean(audio_data[:5]) if len(audio_data) > 5 else 0
        
        # Draw bars with a smoother, cooler look
        min_height = 20  # Minimum height to prevent bars from shrinking to zero
        for i, amplitude in enumerate(audio_data):
            # Smooth transitions
            self.prev_heights[i] = self.prev_heights[i] * 0.7 + amplitude * 0.3
            
            # Calculate bar height with improved scaling
            height = int(self.prev_heights[i] * self.HEIGHT * self.params['sensitivity'] / 15.0)
            
            # Prevent bars from going too small (minimum height)
            height = max(min_height, height)
            
            # Calculate position
            x = i * (self.params['bar_width'] + 2) + 10
            y = self.HEIGHT - height - 10
            
            # Smooth color transition based on the color_hue parameter
            hue = (self.params['color_hue'] + i/self.BAR_COUNT + bass * 0.2) % 1.0
            sat = 0.8 + min(0.2, amplitude * 0.5)  # Increase saturation with amplitude
            val = 0.9 + min(0.1, amplitude * 0.3)  # Increase brightness with amplitude
            rgb = colorsys.hsv_to_rgb(hue, sat, val)
            color = tuple(int(c * 255) for c in rgb)
            
            # Draw bar with rounded corners and a gradient
            pygame.draw.rect(self.screen, color,
                           (x, y, self.params['bar_width'], height),
                           border_radius=5)
            
            # Update and draw peaks
            if self.params['show_peaks']:
                self.peak_heights[i] = max(height, self.peak_heights[i] * 0.95)
                peak_y = self.HEIGHT - self.peak_heights[i] - 10
                peak_y = max(10, peak_y)  # Prevent peaks from going off screen
                pygame.draw.rect(self.screen, (255, 255, 255),
                               (x, peak_y, self.params['bar_width'], 2))
    
    def draw_slider(self):
        # Slider for controlling sensitivity inside a box
        box_x = self.WIDTH - 210
        box_y = self.HEIGHT - 150
        box_width = 180
        box_height = 120
        
        # Draw box background with rounded corners
        pygame.draw.rect(self.screen, (50, 50, 50), (box_x, box_y, box_width, box_height), border_radius=15)
        
        # Slider for controlling sensitivity
        slider_x = box_x + 10
        slider_y = box_y + 40
        slider_width = box_width - 20
        slider_height = 10
        slider_position = (self.params['sensitivity'] - 1.0) / 29.0 * slider_width + slider_x
        
        # Draw slider background
        pygame.draw.rect(self.screen, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height))
        
        # Draw the slider handle
        pygame.draw.circle(self.screen, (255, 0, 0), (int(slider_position), slider_y + slider_height // 2), 10)
    
    def draw_color_slider(self):
        # Slider for controlling the color hue of the bars inside the same box
        slider_x = self.WIDTH - 210 + 10
        slider_y = self.HEIGHT - 150 + 70
        slider_width = 160
        slider_height = 10
        slider_position = self.params['color_hue'] * slider_width + slider_x
        
        # Draw color slider background
        pygame.draw.rect(self.screen, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height))
        
        # Draw the slider handle
        pygame.draw.circle(self.screen, (255, 255, 255), (int(slider_position), slider_y + slider_height // 2), 10)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        dragging_slider = False
        dragging_color_slider = False
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_f:
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.screen = pygame.display.set_mode(
                                (self.display_info.current_w, self.display_info.current_h),
                                pygame.FULLSCREEN)
                            self.update_dimensions(self.display_info.current_w, 
                                                 self.display_info.current_h)
                        else:
                            self.screen = pygame.display.set_mode((800, 600), 
                                                                pygame.RESIZABLE)
                            self.update_dimensions(800, 600)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        slider_x = self.WIDTH - 210 + 10
                        slider_y = self.HEIGHT - 150 + 40
                        slider_width = 160
                        if slider_x <= event.pos[0] <= slider_x + slider_width and slider_y - 10 <= event.pos[1] <= slider_y + 20:
                            dragging_slider = True
                            self.update_sensitivity(event.pos[0], slider_x, slider_width)
                        color_slider_x = self.WIDTH - 210 + 10
                        color_slider_y = self.HEIGHT - 150 + 70
                        if color_slider_x <= event.pos[0] <= color_slider_x + slider_width and color_slider_y - 10 <= event.pos[1] <= color_slider_y + 20:
                            dragging_color_slider = True
                            self.update_color_hue(event.pos[0], color_slider_x, slider_width)
                elif event.type == pygame.MOUSEMOTION:
                    if dragging_slider:
                        self.update_sensitivity(event.pos[0], self.WIDTH - 210 + 10, 160)
                    if dragging_color_slider:
                        self.update_color_hue(event.pos[0], self.WIDTH - 210 + 10, 160)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        dragging_slider = False
                        dragging_color_slider = False
                elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.update_dimensions(event.w, event.h)
            
            self.screen.fill((0, 0, 0))  # Clear screen
            
            # Get audio data and update visualization
            audio_data = self.get_audio_data()
            
            # Draw gradient background
            self.draw_gradient_background(audio_data)
            
            # Draw visualizer
            self.draw_visualizer(audio_data)
            self.draw_slider()
            self.draw_color_slider()
            
            pygame.display.flip()  # Update the screen
            clock.tick(60)  # Limit to 60 FPS

        pygame.quit()

    def update_sensitivity(self, x_pos, slider_x, slider_width):
        self.params['sensitivity'] = ((x_pos - slider_x) / slider_width) * 30.0 + 1.0
        self.params['sensitivity'] = min(max(self.params['sensitivity'], 1.0), 30.0)
    
    def update_color_hue(self, x_pos, slider_x, slider_width):
        self.params['color_hue'] = (x_pos - slider_x) / slider_width
        self.params['color_hue'] = min(max(self.params['color_hue'], 0.0), 1.0)

# Running the visualizer
if __name__ == "__main__":
    visualizer = MusicVisualizer()
    visualizer.run()


 
      

     
