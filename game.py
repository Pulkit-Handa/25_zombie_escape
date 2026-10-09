import pygame
import random
import math
import time

WIDTH, HEIGHT = 800, 560
FPS = 60
BG = (30,35,25)


class Zombie:
    SPEED = 1.5
    SIZE = 30
    HP = 3
    TYPE_NAME = "Standard"

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = (60,140,60)
        self.hp = self.HP
        self.wobble = random.uniform(0, 6.28)
        self.frame = 0

    def update(self, player_pos):
        px, py = player_pos
        cx, cy = self.rect.center
        dx, dy = px-cx, py-cy
        dist = (dx**2+dy**2)**0.5
        if dist:
            self.rect.x += int(dx/dist*self.SPEED)
            self.rect.y += int(dy/dist*self.SPEED)
        self.frame += 1

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.2)*3)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=5)
        # Draw eyes
        eye_spacing = max(4, self.SIZE // 5)
        for ex in [draw_rect.x + eye_spacing, draw_rect.x + self.SIZE - eye_spacing]:
            pygame.draw.circle(screen, (200,40,40), (ex, draw_rect.y + self.SIZE//3), 2)


class FastZombie(Zombie):
    SPEED = 3.0  # Twice as fast
    SIZE = 20    # Smaller
    HP = 1       # Dies in one hit
    TYPE_NAME = "Fast"

    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = (200, 100, 60)  # Orange color for distinction

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.2)*2)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=3)
        # Smaller eyes for smaller zombie
        eye_spacing = 3
        for ex in [draw_rect.x + 3, draw_rect.x + self.SIZE - 3]:
            pygame.draw.circle(screen, (200,40,40), (ex, draw_rect.y + 5), 1)


class TankZombie(Zombie):
    SPEED = 0.8  # Slower
    SIZE = 45    # Bigger
    HP = 6       # Takes 6 hits
    TYPE_NAME = "Tank"

    def __init__(self, x, y):
        super().__init__(x, y)
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.color = (30, 80, 30)  # Darker green for distinction

    def draw(self, screen):
        wobble_y = int(math.sin(self.frame*0.2)*2)
        draw_rect = self.rect.move(0, wobble_y)
        pygame.draw.rect(screen, self.color, draw_rect, border_radius=8)
        # Draw thick border for tank
        pygame.draw.rect(screen, (50, 120, 50), draw_rect, 2, border_radius=8)
        # Larger eyes for tank
        eye_spacing = 10
        for ex in [draw_rect.x + 8, draw_rect.x + self.SIZE - 8]:
            pygame.draw.circle(screen, (200,40,40), (ex, draw_rect.y + 12), 3)


def spawn_zombie(width, height, player_rect, margin=120, zombie_type="standard"):
    """Spawn a zombie of the specified type at a safe location"""
    zombie_class = {
        "standard": Zombie,
        "fast": FastZombie,
        "tank": TankZombie
    }.get(zombie_type, Zombie)
    
    while True:
        x = random.randint(0, width-50)
        y = random.randint(0, height-50)
        test_zombie = zombie_class(x, y)
        rect = test_zombie.rect
        if not rect.colliderect(player_rect.inflate(margin, margin)):
            return test_zombie


class Barrel:
    EXPLOSION_RADIUS = 100
    
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.color = (139, 69, 19)  # Brown color
        self.exploded = False

    def draw(self, screen):
        if not self.exploded:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=3)
            # Draw a simple highlight to make it look like a barrel
            pygame.draw.line(screen, (169, 89, 39), (self.rect.x + 5, self.rect.y + 8), 
                           (self.rect.x + 25, self.rect.y + 8), 2)

    def explode(self):
        self.exploded = True

    def get_explosion_rect(self):
        """Returns the explosion radius as a rect for collision detection"""
        return pygame.Rect(
            self.rect.centerx - self.EXPLOSION_RADIUS,
            self.rect.centery - self.EXPLOSION_RADIUS,
            self.EXPLOSION_RADIUS * 2,
            self.EXPLOSION_RADIUS * 2
        )


SPEED = 4


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (60,160,220)
        self.bullets = []
        self.shoot_cooldown = 0
        self.health = 3
        self.max_health = 3
        self.invincibility_timer = 0
        self.invincibility_duration = 120  # 2 seconds at 60 FPS
        self.ammo = 12
        self.max_ammo = 12
        self.reload_timer = 0
        self.reload_duration = 120  # 2 seconds at 60 FPS
        self.is_reloading = False

    def move(self, keys, width, height):
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = SPEED
        self.rect.x = max(0, min(width-self.rect.width, self.rect.x+dx))
        self.rect.y = max(0, min(height-self.rect.height, self.rect.y+dy))
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
        if self.reload_timer > 0:
            self.reload_timer -= 1
            if self.reload_timer == 0:
                self.is_reloading = False
                self.ammo = self.max_ammo

    def take_damage(self):
        if self.invincibility_timer <= 0:
            self.health -= 1
            self.invincibility_timer = self.invincibility_duration
            return self.health <= 0
        return False

    def shoot(self, target_pos):
        if self.shoot_cooldown > 0: return
        if self.is_reloading: return
        if self.ammo <= 0:
            self.start_reload()
            return
        cx, cy = self.rect.center
        tx, ty = target_pos
        dx, dy = tx-cx, ty-cy
        dist = (dx**2+dy**2)**0.5
        if dist == 0: return
        vx, vy = dx/dist*10, dy/dist*10
        self.bullets.append([cx-4, cy-4, vx, vy])
        self.ammo -= 1
        self.shoot_cooldown = 15

    def start_reload(self):
        if not self.is_reloading and self.ammo < self.max_ammo:
            self.is_reloading = True
            self.reload_timer = self.reload_duration

    def update_bullets(self, width, height):
        live = []
        for b in self.bullets:
            b[0] += b[2]; b[1] += b[3]
            if 0 <= b[0] <= width and 0 <= b[1] <= height:
                live.append(b)
        self.bullets = live

    def draw(self, screen):
        # Draw player with invincibility flashing effect
        if self.invincibility_timer > 0 and (self.invincibility_timer // 10) % 2 == 0:
            # Flash every 10 frames during invincibility
            pygame.draw.rect(screen, (100, 100, 100), self.rect, border_radius=6)
        elif self.is_reloading:
            # Draw in orange during reload
            pygame.draw.rect(screen, (255, 165, 0), self.rect, border_radius=6)
        else:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=6)
        for b in self.bullets:
            pygame.draw.circle(screen, (255,220,60), (int(b[0]), int(b[1])), 5)


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Zombie Escape")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 24)
        self.big_font = pygame.font.SysFont("monospace", 44, bold=True)
        self.reset()

    def reset(self):
        self.player = Player(WIDTH//2, HEIGHT//2)
        # Initial wave has only standard zombies
        self.zombies = [spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_type="standard") for _ in range(4)]
        self.barrels = self.spawn_barrels()
        self.score = 0
        self.wave = 1
        self.kills = 0
        self.kills_to_next = 8
        self.game_over = False
        self.start_time = time.time()

    def spawn_barrels(self):
        """Spawn 4 barrels at random positions on the map"""
        barrels = []
        barrel_count = 4
        attempts = 0
        max_attempts = 100
        
        while len(barrels) < barrel_count and attempts < max_attempts:
            x = random.randint(50, WIDTH - 80)
            y = random.randint(80, HEIGHT - 80)
            barrel_rect = pygame.Rect(x, y, 30, 30)
            
            # Check if barrel doesn't overlap with player or other barrels
            too_close = False
            if barrel_rect.colliderect(self.player.rect.inflate(100, 100)):
                too_close = True
            for barrel in barrels:
                if barrel_rect.colliderect(barrel.rect.inflate(80, 80)):
                    too_close = True
                    break
            
            if not too_close:
                barrels.append(Barrel(x, y))
            
            attempts += 1
        
        return barrels

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.game_over:
                self.reset()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not self.game_over:
                self.player.start_reload()
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                self.player.shoot(event.pos)
        return True

    def update(self):
        if self.game_over: return
        keys = pygame.key.get_pressed()
        self.player.move(keys, WIDTH, HEIGHT)
        self.player.update_bullets(WIDTH, HEIGHT)
        self.score = int(time.time() - self.start_time)

        for z in self.zombies:
            z.update(self.player.rect.center)
            if z.rect.colliderect(self.player.rect):
                if self.player.take_damage():
                    self.game_over = True

        # Check barrel collisions with bullets
        bullets_to_remove = []
        barrels_to_explode = []
        
        for b in self.player.bullets[:]:
            bx, by = int(b[0]), int(b[1])
            bullet_point = (bx, by)
            
            # Check collision with barrels
            for barrel in self.barrels:
                if not barrel.exploded and barrel.rect.collidepoint(bullet_point):
                    barrel.explode()
                    barrels_to_explode.append(barrel)
                    if b in self.player.bullets:
                        bullets_to_remove.append(b)
                    break
        
        # Handle explosions and destroy nearby zombies
        dead = []
        for barrel in barrels_to_explode:
            explosion_rect = barrel.get_explosion_rect()
            for z in self.zombies:
                if explosion_rect.colliderect(z.rect):
                    if z not in dead:
                        dead.append(z)
        
        # Remove bullets that hit barrels
        for b in bullets_to_remove:
            if b in self.player.bullets:
                self.player.bullets.remove(b)
        
        # Check zombie collisions with bullets (excluding barrel-hit bullets)
        for z in self.zombies:
            for b in self.player.bullets[:]:
                bx, by = int(b[0]), int(b[1])
                if z.rect.collidepoint(bx, by):
                    if z.hit():
                        dead.append(z)
                    if b in self.player.bullets:
                        self.player.bullets.remove(b)
                    break
        for z in dead:
            if z in self.zombies:
                self.zombies.remove(z)
                self.kills += 1
                self.score += 10

        if self.kills >= self.kills_to_next:
            self.kills = 0
            self.wave += 1
            self.kills_to_next = 8 + self.wave * 2
            
            # Spawn mixed zombie types for the new wave
            total_zombies = self.wave + 3
            
            # Wave progression: introduce new types as player advances
            if self.wave == 1:
                # Wave 1: All standard
                for _ in range(total_zombies):
                    self.zombies.append(spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_type="standard"))
            elif self.wave == 2:
                # Wave 2: Mix standard and fast
                for i in range(total_zombies):
                    zombie_type = "fast" if i % 2 == 0 else "standard"
                    self.zombies.append(spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_type=zombie_type))
            else:
                # Wave 3+: Mix all three types
                for i in range(total_zombies):
                    if i % 3 == 0:
                        zombie_type = "tank"
                    elif i % 3 == 1:
                        zombie_type = "fast"
                    else:
                        zombie_type = "standard"
                    self.zombies.append(spawn_zombie(WIDTH, HEIGHT, self.player.rect, zombie_type=zombie_type))

    def draw(self):
        self.screen.fill(BG)
        for x in range(0, WIDTH, 60):
            pygame.draw.line(self.screen, (40,45,35), (x,0), (x,HEIGHT), 1)
        for y in range(0, HEIGHT, 60):
            pygame.draw.line(self.screen, (40,45,35), (0,y), (WIDTH,y), 1)
        
        # Draw barrels
        for barrel in self.barrels:
            barrel.draw(self.screen)
            # Draw explosion effect visually
            if barrel.exploded:
                pygame.draw.circle(self.screen, (255, 100, 0), barrel.rect.center, Barrel.EXPLOSION_RADIUS, 2)
        
        for z in self.zombies: z.draw(self.screen)
        self.player.draw(self.screen)
        hud_bg = pygame.Rect(0, 0, WIDTH, 40)
        pygame.draw.rect(self.screen, (15,20,15), hud_bg)
        reload_status = "RELOADING..." if self.player.is_reloading else f"Ammo: {self.player.ammo}/12"
        active_barrels = sum(1 for barrel in self.barrels if not barrel.exploded)
        hud = self.font.render(
            f"Wave: {self.wave}  Health: {self.player.health}/3  {reload_status}  Barrels: {active_barrels}/4  Score: {self.score}  Kills: {self.kills}/{self.kills_to_next}",
            True, (160,220,120))
        self.screen.blit(hud, (8, 8))
        if self.game_over:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0,0,0,160))
            self.screen.blit(ov, (0,0))
            m = self.big_font.render("DEVOURED!", True, (180,40,40))
            s = self.font.render(f"Wave {self.wave} | Score {self.score} | Press R", True, (200,200,200))
            self.screen.blit(m, (WIDTH//2-m.get_width()//2, HEIGHT//2-40))
            self.screen.blit(s, (WIDTH//2-s.get_width()//2, HEIGHT//2+20))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
