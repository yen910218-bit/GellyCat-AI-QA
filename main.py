import pygame
import sys
import random
import os

# ==========================================
# 🔧 參數設定區
# ==========================================
WIDTH, HEIGHT = 800, 600
FPS = 60
GROUND_Y = 500
MAX_TEST_RUNS = 50
VICTORY_SCORE = 200  # [修改] 200分就通關 (加速測試流程)

# ==========================================
# 🛠️ 系統初始化
# ==========================================
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("虎科資管專案：AI Agent (200分通關 + 巨型連環刺)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28)

# 🎨 顏色
WHITE, BLACK, RED, GREEN, BLUE = (255,255,255), (0,0,0), (255,0,0), (0,150,0), (0,0,255)
SKY_BLUE, CLOUD_WHITE = (135,206,235), (255,255,255,180)
SOIL_BROWN, GRASS_GREEN = (139,69,19), (34,139,34)

try:
    if os.path.exists("assets/bgm.mp3"):
        pygame.mixer.music.load("assets/bgm.mp3")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
    jump_sfx = pygame.mixer.Sound("assets/jump.wav") if os.path.exists("assets/jump.wav") else None
    crash_sfx = pygame.mixer.Sound("assets/crash.wav") if os.path.exists("assets/crash.wav") else None
except:
    jump_sfx = crash_sfx = None

# ==========================================
# 📦 類別定義
# ==========================================

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = random.randint(4, 8)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (245, 245, 245, 200), (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x, self.vel_y = random.uniform(-2, 2), random.uniform(-1, -3)
        self.alpha = 255
    def update(self):
        self.rect.x += self.vel_x; self.rect.y += self.vel_y
        self.alpha -= 12
        if self.alpha <= 0: self.kill()
        else: self.image.set_alpha(self.alpha)

class Cloud(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.w, self.h = random.randint(100, 180), random.randint(40, 70)
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, CLOUD_WHITE, (0, 0, self.w, self.h))
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = WIDTH, random.randint(20, 230)
        self.speed = random.uniform(1.0, 2.5)
    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < -50: self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_w, self.base_h = 60, 60
        self.original_image = pygame.Surface((self.base_w, self.base_h))
        self.original_image.fill(RED)
        if os.path.exists("assets/player.png"):
            try: self.original_image = pygame.transform.scale(pygame.image.load("assets/player.png").convert_alpha(), (self.base_w, self.base_h))
            except: pass
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(midbottom=(150, GROUND_Y))
        self.mask = pygame.mask.from_surface(self.image)
        
        self.vel_y = 0
        self.gravity = 0.72
        self.jump_strength = -17.5 
        self.jump_count = 0
        self.trails = []
        self.current_w, self.current_h = float(self.base_w), float(self.base_h)

    def jump(self, p_group, power_ratio=1.0):
        if self.jump_count < 2:
            self.vel_y = self.jump_strength * power_ratio
            self.jump_count += 1
            if jump_sfx: jump_sfx.play()
            for _ in range(6): p_group.add(Particle(self.rect.centerx, self.rect.bottom))
            self.current_w = self.base_w * 0.7
            self.current_h = self.base_h * 1.3
            return True
        return False

    def cut_jump(self):
        if self.vel_y < -6: self.vel_y = -6

    def update(self, score):
        if score >= 25:
            self.trails.append((self.rect.copy(), self.image.copy()))
            if len(self.trails) > 8: self.trails.pop(0)
        else:
            self.trails.clear()

        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.bottom >= GROUND_Y:
            if self.vel_y > 0:
                self.vel_y = 0
                self.jump_count = 0
                self.rect.bottom = GROUND_Y
                self.current_w = self.base_w * 1.4
                self.current_h = self.base_h * 0.7
        
        self.current_w += (self.base_w - self.current_w) * 0.1
        self.current_h += (self.base_h - self.current_h) * 0.1
        
        scale_w, scale_h = max(1, int(self.current_w)), max(1, int(self.current_h))
        self.image = pygame.transform.scale(self.original_image, (scale_w, scale_h))
        old_bottom = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = old_bottom
        self.mask = pygame.mask.from_surface(pygame.transform.scale(self.image, (scale_w-4, scale_h-4)))

    def draw_trails(self, surface):
        for i, (t_rect, t_img) in enumerate(self.trails):
            t_img.set_alpha((i + 1) * 25)
            surface.blit(t_img, t_rect)

class Spike(pygame.sprite.Sprite):
    def __init__(self, speed, score):
        super().__init__()
        
        # 100分後開啟三連尖刺模式
        choices = ["SMALL", "NORMAL", "BIG"]
        weights = [20, 60, 20]
        
        if score > 100:
            choices.append("TRIPLE")
            weights = [15, 45, 15, 25] # 提高三連出現率 (25%)，讓魔王常出現
        
        self.spike_type = random.choices(choices, weights=weights)[0]
        
        # === 尺寸設定 ===
        if self.spike_type == "SMALL":
            self.w, self.h = 30, 30
            color = (150, 150, 150)
        elif self.spike_type == "BIG":
            self.w, self.h = 50, 65
            color = (50, 50, 50)
        elif self.spike_type == "TRIPLE":
            # [修改] 巨型化！寬度 120 (40*3)，高度 60 (跟大尖刺差不多高)
            self.w, self.h = 120, 60 
            color = (160, 0, 0) # 鮮豔的紅色
        else:
            self.w, self.h = 40, 40
            color = (100, 100, 100)
            
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        
        # === 繪圖 ===
        if self.spike_type == "TRIPLE":
            # 畫三個巨大的三角形 ▲▲▲
            for i in range(3):
                offset = i * 40 # 每個寬度40
                # 每個都是 40寬 x 60高
                pygame.draw.polygon(self.image, color, [(offset, self.h), (offset+40, self.h), (offset+20, 0)])
                # 加個黑色邊框讓它更明顯
                pygame.draw.polygon(self.image, BLACK, [(offset, self.h), (offset+40, self.h), (offset+20, 0)], 2)
        else:
            pygame.draw.polygon(self.image, color, [(0, self.h), (self.w, self.h), (self.w//2, 0)])
            if self.spike_type == "BIG": 
                pygame.draw.polygon(self.image, RED, [(0, self.h), (self.w, self.h), (self.w//2, 0)], 2)

        self.rect = self.image.get_rect(bottomleft=(WIDTH, GROUND_Y))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = speed
        self.scored = False

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0: self.kill()

# ==========================================
# 🎮 全域變數
# ==========================================
all_sprites = pygame.sprite.Group()
spikes = pygame.sprite.Group()
clouds = pygame.sprite.Group()
particles = pygame.sprite.Group()
player = None

SPAWN_SPIKE = pygame.USEREVENT + 1
SPAWN_CLOUD = pygame.USEREVENT + 2
pygame.time.set_timer(SPAWN_SPIKE, 1500)
pygame.time.set_timer(SPAWN_CLOUD, 2500)

ai_enabled = True
test_mode = False
game_over = False
score = 0
high_score = 0
test_scores = []
run_count = 0
current_speed_range = (7, 10)

def reset_game():
    global player, game_over, score, all_sprites, spikes, clouds, particles
    game_over = False
    score = 0
    all_sprites.empty(); spikes.empty(); clouds.empty(); particles.empty()
    player = Player()
    all_sprites.add(player)
    pygame.time.set_timer(SPAWN_SPIKE, 1500)

reset_game()

# ==========================================
# 🔄 主迴圈
# ==========================================
while True:
    if score < 10:
        diff_label, label_col = "LEVEL 1", GREEN
        current_speed_range, spawn_range = (7, 10), (1200, 1800)
    elif score < 25:
        diff_label, label_col = "LEVEL 2", BLUE
        current_speed_range, spawn_range = (10, 13), (900, 1400)
    else:
        diff_label, label_col = "LEVEL 3: HELL", RED
        max_v = min(22, 15 + (score - 25) * 0.2)
        current_speed_range = (14, max_v)
        spawn_range = (700, 1100) 

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        
        if not game_over:
            if event.type == SPAWN_SPIKE:
                safe_to_spawn = True
                for s in spikes:
                    if s.rect.right > WIDTH - 150: safe_to_spawn = False; break
                
                if safe_to_spawn:
                    s = Spike(random.uniform(*current_speed_range), score)
                    all_sprites.add(s); spikes.add(s)
                    
                    next_delay = random.randint(*spawn_range)
                    if s.spike_type == "TRIPLE":
                        next_delay += 500 # 巨型尖刺後要留更多空間
                    pygame.time.set_timer(SPAWN_SPIKE, next_delay)
                else:
                    pygame.time.set_timer(SPAWN_SPIKE, 200)

            if event.type == SPAWN_CLOUD:
                clouds.add(Cloud())
                pygame.time.set_timer(SPAWN_CLOUD, random.randint(3000, 6000))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a: ai_enabled = not ai_enabled
            if event.key == pygame.K_t: 
                test_mode = not test_mode
                run_count = 0; test_scores = []; reset_game()
            if event.key == pygame.K_r and game_over: reset_game() 
            if not ai_enabled and not game_over and event.key == pygame.K_SPACE:
                player.jump(particles, 1.0)
        
        if event.type == pygame.KEYUP:
            if not ai_enabled and not game_over and event.key == pygame.K_SPACE:
                player.cut_jump()

    # === AI Agent 邏輯 ===
    if ai_enabled and not game_over:
        threats = sorted([(s.rect.left - player.rect.right, s) for s in spikes if s.rect.left - player.rect.right > -100], key=lambda x: x[0])
        if threats:
            t1_dist, t1_spike = threats[0]
            t2_dist = threats[1][0] if len(threats) > 1 else 9999
            
            is_high_speed = t1_spike.speed > 13
            is_big = t1_spike.spike_type == "BIG"
            is_triple = t1_spike.spike_type == "TRIPLE"

            # [AI 修正] 針對巨型三連刺的微調
            # 因為三連刺現在變寬到 120，必須稍微晚一點跳(offset變小)，
            # 讓貓咪跳到尖刺的正上方，而不是起跳太早撞到前面的刺
            trigger_offset = 35 if is_big else (20 if is_triple else 25)

            if player.jump_count == 0:
                if t1_dist < (t1_spike.speed * 25 + trigger_offset): 
                    if is_high_speed or is_big or is_triple:
                        player.jump(particles, 1.0)
                    elif (t2_dist - t1_dist < 400): 
                        player.jump(particles, 0.85)
                    else: 
                        player.jump(particles, 1.0)

            elif player.jump_count == 1:
                t_land = (GROUND_Y - player.rect.bottom) / max(1, player.vel_y)
                pred_x = t1_dist - (t1_spike.speed * t_land)
                
                # 巨型三連刺的危險範圍加大到 100
                danger_zone = 100 if is_triple else (55 if is_big else 45)

                if -danger_zone < pred_x < danger_zone or (t2_dist < 350 and player.vel_y > 0):
                    if (not is_high_speed) and (not is_big) and (not is_triple) and (t2_dist < 300): 
                        player.jump(particles, 0.7)
                    else: 
                        player.jump(particles, 1.0)

    # === 遊戲更新 ===
    if not game_over:
        player.update(score)
        spikes.update(); clouds.update(); particles.update()
        for s in spikes:
            if s.rect.right < player.rect.left and not s.scored:
                score += 1; s.scored = True; high_score = max(high_score, score)
        
        if pygame.sprite.spritecollide(player, spikes, False, pygame.sprite.collide_mask):
            game_over = True
            if crash_sfx: crash_sfx.play()

        # [修改] 200分通關機制
        if test_mode and score >= VICTORY_SCORE:
            game_over = True
            print(f"🎉 Run {run_count+1} Cleared! Reached {VICTORY_SCORE}")

        if game_over: 
            if test_mode:
                run_count += 1; test_scores.append(score)
                print(f"🔄 Auto Run {run_count}/{MAX_TEST_RUNS} | Score: {score}")
                if run_count >= MAX_TEST_RUNS:
                    log_txt = f"Runs: {MAX_TEST_RUNS}\nAvg: {sum(test_scores)/len(test_scores):.2f}\nMax: {max(test_scores)}\nMin: {min(test_scores)}"
                    with open("test_log.txt", "w") as f: f.write(log_txt)
                    test_mode = False
                else: reset_game()
    else:
        clouds.update(); particles.update()

    # === 繪圖 ===
    screen.fill(SKY_BLUE); clouds.draw(screen); particles.draw(screen); player.draw_trails(screen)
    pygame.draw.rect(screen, SOIL_BROWN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.rect(screen, GRASS_GREEN, (0, GROUND_Y - 5, WIDTH, 5))
    all_sprites.draw(screen)
    
    screen.blit(font.render(f"SCORE: {score}", True, BLACK), (WIDTH-180, 10))
    screen.blit(font.render(f"HIGH: {high_score}", True, BLUE), (WIDTH-230, 45))
    mode_text = "AUTO TEST" if test_mode else ("AI AGENT" if ai_enabled else "MANUAL")
    mode_col = RED if test_mode else (GREEN if ai_enabled else BLACK)
    screen.blit(font.render(f"MODE: {mode_text}", True, mode_col), (10, 10))
    screen.blit(font.render(diff_label, True, label_col), (10, 45))
    
    if test_mode: screen.blit(font.render(f"RUN: {run_count}/{MAX_TEST_RUNS}", True, RED), (WIDTH//2-60, 80))
    elif game_over: 
        if score >= VICTORY_SCORE:
            # 通關訊息
            msg = font.render(f"MISSION CLEARED! ({VICTORY_SCORE}+)", True, BLUE)
            screen.blit(msg, (WIDTH//2-140, HEIGHT//2 - 40))
        screen.blit(font.render("Press 'R' to Restart", True, BLACK), (WIDTH//2-100, HEIGHT//2))

    pygame.display.flip()
    clock.tick(FPS)
