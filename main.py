import pygame
import sys
import random
import os

# --- 1. 診斷與初始化 ---
def check_assets():
    required = ["assets/player.png", "assets/bgm.mp3", "assets/jump.wav", "assets/crash.wav"]
    for f in required:
        if not os.path.exists(f):
            print(f"⚠️ 警告：缺少檔案 {f}")

check_assets()

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("虎科資管前導專案：跳吧果凍貓AI Agent")

# --- 🎵 載入資源 ---
WHITE, BLACK, RED, GREEN, BLUE = (255,255,255), (0,0,0), (255,0,0), (0,150,0), (0,0,255)
SKY_BLUE, CLOUD_WHITE = (135,206,235), (255,255,255,180)
SOIL_BROWN, GRASS_GREEN = (139,69,19), (34,139,34)

# 載入音效
try:
    pygame.mixer.music.load("assets/bgm.mp3")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)
    jump_sfx = pygame.mixer.Sound("assets/jump.wav")
    crash_sfx = pygame.mixer.Sound("assets/crash.wav")
except:
    jump_sfx = crash_sfx = None

GROUND_Y, FPS = 500, 60
clock = pygame.time.Clock()

# --- 2. 煙霧粒子類別 ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = random.randint(4, 8)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (245, 245, 245, 200), (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x, self.vel_y, self.alpha = random.uniform(-2, 2), random.uniform(-1, -3), 255
    def update(self):
        self.rect.x += self.vel_x; self.rect.y += self.vel_y; self.alpha -= 12
        if self.alpha <= 0: self.kill()
        else: self.image.set_alpha(self.alpha)

# --- 3. 雲朵類別 ---
class Cloud(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width, self.height = random.randint(100, 180), random.randint(40, 70)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, CLOUD_WHITE, (0, 0, self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = WIDTH, random.randint(20, 230) 
        self.speed = random.uniform(1.0, 2.5)
    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < -50: self.kill()

# --- 4. 玩家類別 ---
class Player(pygame.sprite.Sprite):
    def __init__(self, base_w=60, base_h=60):
        super().__init__()
        self.target_w, self.target_h = base_w, base_h
        self.current_w, self.current_h = base_w, base_h
        try:
            self.original_image = pygame.image.load("assets/player.png").convert_alpha()
        except:
            self.original_image = pygame.Surface((base_w, base_h)); self.original_image.fill(RED)
        
        self.image = pygame.transform.scale(self.original_image, (base_w, base_h))
        self.rect = self.image.get_rect(); self.rect.midbottom = (150, GROUND_Y)
        self.mask = pygame.mask.from_surface(self.image)
        self.speed, self.vel_y, self.gravity, self.jump_strength, self.jump_count = 8, 0, 0.72, -17.5, 0
        self.trails = []

    def jump(self, p_group):
        if self.jump_count < 2:
            self.vel_y = self.jump_strength
            self.jump_count += 1
            if jump_sfx: jump_sfx.play()
            for _ in range(6): p_group.add(Particle(self.rect.centerx, self.rect.bottom))
            self.current_w, self.current_h = self.target_w * 0.8, self.target_h * 1.2
            return True
        return False

    def update(self, current_score):
        # 殘影觸發：Level 3 (25分) 開啟
        if current_score >= 25:
            self.trails.append((self.rect.copy(), self.image.copy()))
            if len(self.trails) > 8: self.trails.pop(0)
        else:
            if self.trails: self.trails.pop(0)

        self.vel_y += self.gravity; self.rect.y += self.vel_y
        if self.rect.bottom >= GROUND_Y:
            if self.vel_y > 0:
                if self.vel_y > 5: self.current_w, self.current_h = self.target_w * 1.2, self.target_h * 0.8
                self.rect.bottom = GROUND_Y
                self.vel_y, self.jump_count = 0, 0
        
        self.current_w += (self.target_w - self.current_w) * 0.2
        self.current_h += (self.target_h - self.current_h) * 0.2
        old_bottom = self.rect.midbottom
        self.image = pygame.transform.scale(self.original_image, (int(self.current_w), int(self.current_h)))
        self.rect = self.image.get_rect(); self.rect.midbottom = old_bottom
        # 碰撞優化
        small_surface = pygame.transform.scale(self.original_image, (max(1, int(self.current_w - 4)), max(1, int(self.current_h - 4))))
        self.mask = pygame.mask.from_surface(small_surface)

    def draw_trails(self, surface):
        for i, (t_rect, t_img) in enumerate(self.trails):
            alpha = (i + 1) * 25; t_img.set_alpha(alpha); surface.blit(t_img, t_rect)

# --- 5. 尖刺類別 ---
class Spike(pygame.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        c = random.randint(80, 150)
        pygame.draw.polygon(self.image, (c-20, c-20, c-20), [(0, 40), (40, 40), (20, 0)])
        self.rect = self.image.get_rect(); self.rect.left, self.rect.bottom = WIDTH, GROUND_Y
        self.mask = pygame.mask.from_surface(self.image)
        self.speed, self.scored = speed, False
    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0: self.kill()

# --- 6. 遊戲變數 ---
all_sprites, spikes, clouds, particles = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
player = Player(); all_sprites.add(player)
SPAWN_SPIKE, SPAWN_CLOUD = pygame.USEREVENT + 1, pygame.USEREVENT + 2
pygame.time.set_timer(SPAWN_SPIKE, 1500); pygame.time.set_timer(SPAWN_CLOUD, 2500) 
ai_enabled, game_over, score, high_score = True, False, 0, 0
font = pygame.font.SysFont("Arial", 28)

# --- 7. 主迴圈 ---
while True:
    toggled_this_frame = jumped_this_frame = False
    if score < 10:
        diff_label, label_col, speed_range, spawn_range = "LEVEL 1", GREEN, (7, 10), (1200, 1800)
    elif score < 25:
        diff_label, label_col, speed_range, spawn_range = "LEVEL 2", BLUE, (10, 13), (800, 1300)
    else:
        diff_label, label_col = "LEVEL 3: HELL", RED
        max_v = min(19, 15 + (score - 25) * 0.18)
        speed_range, spawn_range = (14, max_v), (550, 950) 

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if not game_over:
            if event.type == SPAWN_SPIKE:
                s = Spike(random.uniform(speed_range[0], speed_range[1]))
                all_sprites.add(s); spikes.add(s)
                pygame.time.set_timer(SPAWN_SPIKE, random.randint(spawn_range[0], spawn_range[1]))
            if event.type == SPAWN_CLOUD:
                clouds.add(Cloud()); pygame.time.set_timer(SPAWN_CLOUD, random.randint(3000, 6000))
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a: ai_enabled = not ai_enabled; toggled_this_frame = True
            if event.key == pygame.K_r and game_over:
                game_over, score = False, 0
                pygame.mixer.music.play(-1) # 重播 BGM
                all_sprites.empty(); spikes.empty(); clouds.empty(); particles.empty()
                player = Player(); all_sprites.add(player)
            if not ai_enabled and not game_over and event.key == pygame.K_SPACE:
                if not jumped_this_frame and player.jump(particles): jumped_this_frame = True
        if event.type == pygame.TEXTINPUT and not toggled_this_frame:
            if event.text.lower() == 'a': ai_enabled = not ai_enabled; toggled_this_frame = True

    # --- 🤖 AI Agent 強化邏輯 ---
    if ai_enabled and not game_over:
        threats = sorted([(s.rect.left - player.rect.right, s) for s in spikes if s.rect.left - player.rect.right > -100], key=lambda x: x[0])
        if threats:
            t1_dist, t1_spike = threats[0]
            if t1_dist < -20 and len(threats) > 1: t1_dist, t1_spike = threats[1]
            if player.jump_count == 0:
                if t1_dist < (t1_spike.speed * 25 + 25): player.jump(particles)
            elif player.jump_count == 1:
                if score >= 25:
                    # 💡 落地點預判補丁
                    t_land = (GROUND_Y - player.rect.bottom) / max(1, player.vel_y)
                    predicted_land_x = t1_dist - (t1_spike.speed * t_land)
                    if -45 < predicted_land_x < 45 or (len(threats) > 1 and threats[1][0] < 320):
                        if player.vel_y > -5: player.jump(particles)
                else:
                    if len(threats) > 1 and threats[1][0] < 220: player.jump(particles)

    if not game_over:
        player.update(score)
        spikes.update(); clouds.update(); particles.update()
        for s in spikes:
            if s.rect.right < player.rect.left and not s.scored:
                score += 1; s.scored = True; high_score = max(high_score, score)
        if pygame.sprite.spritecollide(player, spikes, False, pygame.sprite.collide_mask):
            game_over = True
            pygame.mixer.music.stop()
            if crash_sfx: crash_sfx.play()
    else:
        clouds.update(); particles.update()

    # --- 繪製 ---
    screen.fill(SKY_BLUE); clouds.draw(screen); particles.draw(screen); player.draw_trails(screen)
    pygame.draw.rect(screen, SOIL_BROWN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.rect(screen, GRASS_GREEN, (0, GROUND_Y - 5, WIDTH, 5))
    all_sprites.draw(screen)
    
    st_col = GREEN if ai_enabled else RED
    screen.blit(font.render(f"SCORE: {score}", True, BLACK), (WIDTH - 180, 10))
    screen.blit(font.render(f"HIGH SCORE: {high_score}", True, BLUE), (WIDTH - 230, 45))
    screen.blit(font.render(f"MODE: {'AI' if ai_enabled else 'MANUAL'}", True, st_col), (10, 10))
    screen.blit(font.render(diff_label, True, label_col), (10, 45))

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((255, 255, 255, 150))
        screen.blit(overlay, (0, 0))
        msg = font.render(f"CRASHED! FINAL: {score} | BEST: {high_score}", True, RED)
        screen.blit(msg, (WIDTH//2 - 200, HEIGHT//2 - 20)); screen.blit(font.render("Press 'R' to Restart", True, BLACK), (WIDTH//2 - 100, HEIGHT//2 + 30))

    pygame.display.flip(); clock.tick(FPS)